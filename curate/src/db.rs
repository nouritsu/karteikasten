//! data/work/curation.sqlite, written by every build (pipeline/karteikasten_pipeline/curation.py).

use std::collections::HashMap;
use std::path::Path;

use anyhow::{Context, Result};
use rusqlite::{Connection, OpenFlags, OptionalExtension};
use serde_json::Value;

#[derive(Debug, Clone, Copy, PartialEq, Eq, PartialOrd, Ord)]
pub enum Severity {
    Blocking,
    Warning,
}

#[derive(Debug, Clone)]
pub struct Issue {
    pub severity: Severity,
    pub code: String,
    pub detail: String,
}

#[derive(Debug, Clone)]
pub struct Word {
    pub id: String,
    pub rank: u32,
    pub lemma: String,
    pub pos: String,
    /// The word's record in the deck's words.json.
    pub card: Value,
    /// Blocking first.
    pub issues: Vec<Issue>,
}

impl Word {
    pub fn worst(&self) -> Option<Severity> {
        self.issues.iter().map(|i| i.severity).min()
    }
}

#[derive(Debug, Clone)]
pub struct AudioCandidate {
    pub file: String,
    pub author: Option<String>,
    pub license: Option<String>,
    pub region: Option<String>,
    /// Commons names an author and a licence (and, for public builds, not NC/ND).
    pub usable: bool,
    /// The build's pick, before overrides.
    pub picked: bool,
}

#[derive(Debug, Clone)]
pub struct SentenceCandidate {
    pub id: String,
    pub de: String,
    pub en: Option<String>,
    pub author: Option<String>,
    pub native: bool,
    pub score: f64,
    /// In the deck now.
    pub picked: bool,
}

#[derive(Debug, Default)]
pub struct Database {
    pub deck_version: String,
    /// By rank.
    pub words: Vec<Word>,
    pub audio: HashMap<String, Vec<AudioCandidate>>,
    /// Best score first.
    pub sentences: HashMap<String, Vec<SentenceCandidate>>,
}

impl Database {
    pub fn load(path: &Path) -> Result<Self> {
        let con = Connection::open_with_flags(path, OpenFlags::SQLITE_OPEN_READ_ONLY)
            .with_context(|| format!("opening {}; run `nix run .#build` first", path.display()))?;
        let deck_version = con
            .query_row("SELECT value FROM meta WHERE key = 'deck_version'", [], |r| r.get(0))
            .optional()
            .ok()
            .flatten()
            .with_context(|| format!("{} is from an older build; run `nix run .#build`", path.display()))?;

        let mut issues: HashMap<String, Vec<Issue>> = HashMap::new();
        let mut stmt = con.prepare("SELECT word_id, severity, code, detail FROM issue")?;
        for row in stmt.query_map([], |r| {
            Ok((
                r.get::<_, String>(0)?,
                r.get::<_, String>(1)?,
                r.get::<_, String>(2)?,
                r.get::<_, String>(3)?,
            ))
        })? {
            let (id, severity, code, detail) = row?;
            let severity = if severity == "blocking" {
                Severity::Blocking
            } else {
                Severity::Warning
            };
            issues.entry(id).or_default().push(Issue { severity, code, detail });
        }

        let mut words = Vec::new();
        let mut stmt = con.prepare("SELECT id, rank, lemma, pos, card FROM word ORDER BY rank, id")?;
        for row in stmt.query_map([], |r| {
            Ok((
                r.get::<_, String>(0)?,
                r.get(1)?,
                r.get(2)?,
                r.get(3)?,
                r.get::<_, String>(4)?,
            ))
        })? {
            let (id, rank, lemma, pos, card) = row?;
            let card = serde_json::from_str(&card).with_context(|| format!("card of {id}"))?;
            let mut found = issues.remove(&id).unwrap_or_default();
            found.sort_by_key(|i| i.severity);
            words.push(Word {
                id,
                rank,
                lemma,
                pos,
                card,
                issues: found,
            });
        }

        let mut audio: HashMap<String, Vec<AudioCandidate>> = HashMap::new();
        let mut stmt = con.prepare(
            "SELECT word_id, file, author, license, region, usable, picked FROM audio_candidate ORDER BY word_id, file",
        )?;
        for row in stmt.query_map([], |r| {
            Ok((
                r.get::<_, String>(0)?,
                AudioCandidate {
                    file: r.get(1)?,
                    author: r.get(2)?,
                    license: r.get(3)?,
                    region: r.get(4)?,
                    usable: r.get(5)?,
                    picked: r.get(6)?,
                },
            ))
        })? {
            let (id, candidate) = row?;
            audio.entry(id).or_default().push(candidate);
        }

        let mut sentences: HashMap<String, Vec<SentenceCandidate>> = HashMap::new();
        let mut stmt = con.prepare(
            "SELECT word_id, sentence_id, de, en, author, native, score, picked FROM sentence_candidate \
             ORDER BY word_id, score DESC, sentence_id",
        )?;
        for row in stmt.query_map([], |r| {
            Ok((
                r.get::<_, String>(0)?,
                SentenceCandidate {
                    id: r.get(1)?,
                    de: r.get(2)?,
                    en: r.get(3)?,
                    author: r.get(4)?,
                    native: r.get(5)?,
                    score: r.get(6)?,
                    picked: r.get(7)?,
                },
            ))
        })? {
            let (id, candidate) = row?;
            sentences.entry(id).or_default().push(candidate);
        }

        Ok(Database {
            deck_version,
            words,
            audio,
            sentences,
        })
    }
}
