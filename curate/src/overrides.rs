//! overrides/: what the tool writes, and the next build applies.
//!
//! - words.toml `[audio]`: the Commons file a word uses instead of the build's pick.
//! - sentences.toml `[pin]` / `[ban]`: sentence ids per word, pins shown first in order.
//! - audio/: own recordings named by word id with `#` as `_` (Hand_noun_1.flac).
//!
//! Edits go through toml_edit, so comments, order and layout survive and a save
//! changes only the entries it touches; every change is saved at once.

use std::fs;
use std::path::{Path, PathBuf};

use anyhow::{Context, Result};
use toml_edit::{Array, DocumentMut, Item, Table, value};

pub const RECORDING_SUFFIXES: [&str; 5] = ["flac", "wav", "ogg", "opus", "mp3"];
/// words.toml tables keyed by word id (spec: Overrides; pipeline overrides.py).
const WORD_TABLES: [&str; 6] = ["exclude", "merge", "gloss_en", "gloss_de", "no_cognate", "audio"];

/// One TOML file, edited in place.
pub struct TomlFile {
    pub path: PathBuf,
    doc: DocumentMut,
}

impl TomlFile {
    pub fn load(path: &Path) -> Result<Self> {
        let text = if path.exists() {
            fs::read_to_string(path).with_context(|| format!("reading {}", path.display()))?
        } else {
            String::new()
        };
        Self::parse(path.to_owned(), &text)
    }

    pub fn parse(path: PathBuf, text: &str) -> Result<Self> {
        let doc = text.parse().with_context(|| format!("parsing {}", path.display()))?;
        Ok(TomlFile { path, doc })
    }

    pub fn text(&self) -> String {
        self.doc.to_string()
    }

    /// Write through a temporary file, so a crash never leaves half a file.
    pub fn save(&self) -> Result<()> {
        let tmp = self.path.with_extension("toml.tmp");
        fs::write(&tmp, self.text()).with_context(|| format!("writing {}", tmp.display()))?;
        fs::rename(&tmp, &self.path).with_context(|| format!("replacing {}", self.path.display()))
    }

    fn get(&self, table: &str, key: &str) -> Option<&Item> {
        self.doc.get(table)?.as_table_like()?.get(key)
    }

    pub fn has(&self, table: &str, key: &str) -> bool {
        self.get(table, key).is_some()
    }

    pub fn get_str(&self, table: &str, key: &str) -> Option<String> {
        self.get(table, key)?.as_str().map(str::to_owned)
    }

    pub fn get_strs(&self, table: &str, key: &str) -> Vec<String> {
        self.get(table, key)
            .and_then(Item::as_array)
            .map(|a| a.iter().filter_map(|v| v.as_str().map(str::to_owned)).collect())
            .unwrap_or_default()
    }

    fn table_mut(&mut self, table: &str) -> &mut Table {
        if !self.doc.contains_key(table) {
            // Undecorated: toml_edit puts a blank line before it unless it comes first.
            self.doc.insert(table, Item::Table(Table::new()));
        }
        self.doc[table]
            .as_table_mut()
            .expect("override tables are standard tables")
    }

    pub fn set_str(&mut self, table: &str, key: &str, text: &str) {
        self.table_mut(table).insert(key, value(text));
    }

    /// An empty list removes the key, and a table left empty goes too (unless a
    /// comment sits above it).
    pub fn set_strs(&mut self, table: &str, key: &str, values: &[String]) {
        if values.is_empty() {
            self.remove(table, key);
        } else {
            let array: Array = values.iter().map(String::as_str).collect();
            self.table_mut(table).insert(key, value(array));
        }
    }

    pub fn remove(&mut self, table: &str, key: &str) {
        let Some(t) = self.doc.get_mut(table).and_then(Item::as_table_mut) else {
            return;
        };
        t.remove(key);
        let commented = t
            .decor()
            .prefix()
            .and_then(|p| p.as_str())
            .is_some_and(|p| p.contains('#'));
        if t.is_empty() && !commented {
            self.doc.remove(table);
        }
    }
}

pub struct Overrides {
    pub dir: PathBuf,
    pub words: TomlFile,
    pub sentences: TomlFile,
}

/// Hand#noun#1 -> Hand_noun_1, the name of a word's own recording.
pub fn file_stem(id: &str) -> String {
    id.replace('#', "_")
}

impl Overrides {
    pub fn load(dir: &Path) -> Result<Self> {
        Ok(Overrides {
            dir: dir.to_owned(),
            words: TomlFile::load(&dir.join("words.toml"))?,
            sentences: TomlFile::load(&dir.join("sentences.toml"))?,
        })
    }

    pub fn audio_pin(&self, id: &str) -> Option<String> {
        self.words.get_str("audio", id)
    }

    pub fn pin_audio(&mut self, id: &str, file: &str) -> Result<()> {
        self.words.set_str("audio", id, file);
        self.words.save()
    }

    pub fn unpin_audio(&mut self, id: &str) -> Result<()> {
        self.words.remove("audio", id);
        self.words.save()
    }

    pub fn pins(&self, id: &str) -> Vec<String> {
        self.sentences.get_strs("pin", id)
    }

    pub fn bans(&self, id: &str) -> Vec<String> {
        self.sentences.get_strs("ban", id)
    }

    /// Pin a sentence (appended, so pins keep the order they were made in), or unpin it.
    /// A pinned sentence is never banned. Returns whether it is pinned now.
    pub fn toggle_pin(&mut self, id: &str, sentence: &str) -> Result<bool> {
        let pinned = self.toggle("pin", "ban", id, sentence);
        self.sentences.save()?;
        Ok(pinned)
    }

    /// Ban a sentence, or lift the ban. Returns whether it is banned now.
    pub fn toggle_ban(&mut self, id: &str, sentence: &str) -> Result<bool> {
        let banned = self.toggle("ban", "pin", id, sentence);
        self.sentences.save()?;
        Ok(banned)
    }

    fn toggle(&mut self, table: &str, other: &str, id: &str, sentence: &str) -> bool {
        let mut list = self.sentences.get_strs(table, id);
        let on = if let Some(at) = list.iter().position(|s| s == sentence) {
            list.remove(at);
            false
        } else {
            list.push(sentence.to_owned());
            let rest: Vec<String> = self
                .sentences
                .get_strs(other, id)
                .into_iter()
                .filter(|s| s != sentence)
                .collect();
            if rest.len() != self.sentences.get_strs(other, id).len() {
                self.sentences.set_strs(other, id, &rest);
            }
            true
        };
        self.sentences.set_strs(table, id, &list);
        on
    }

    pub fn recording(&self, id: &str) -> Option<PathBuf> {
        let stem = file_stem(id);
        RECORDING_SUFFIXES
            .iter()
            .map(|s| self.dir.join("audio").join(format!("{stem}.{s}")))
            .find(|p| p.exists())
    }

    /// Where a new recording goes: over the existing one, else a new FLAC file.
    pub fn recording_target(&self, id: &str) -> PathBuf {
        self.recording(id)
            .unwrap_or_else(|| self.dir.join("audio").join(format!("{}.flac", file_stem(id))))
    }

    /// Any override names this word.
    pub fn touches(&self, id: &str) -> bool {
        WORD_TABLES.iter().any(|t| self.words.has(t, id))
            || self.sentences.has("pin", id)
            || self.sentences.has("ban", id)
            || self.recording(id).is_some()
    }
}

#[cfg(test)]
mod tests {
    use super::*;

    // The shapes the real files use: comments above tables and entries, quoted ids,
    // inline tables, arrays, blank lines.
    const SAMPLE: &str = r#"# Word-level curation, re-applied on every build.
#
# Holds: include/exclude.

# Lemma ids dropped from the ranking, with the reason.
[exclude]
"äh#intj#1" = "filler (hesitation sound), per the spec's tricky-word list"

[preposition]

# vor (rank 75). en categories: acc, dat; de tags: dat.
#   Checked 2026-10-22: two-way.
"vor#prep#1" = { cases = ["dat", "acc"] }
"in#prep#1" = { cases = ["dat", "acc"], contractions = ["im", "ins"] }

[pin]
"Hand#noun#1" = ["tatoeba:2", "tatoeba:3"]
"#;

    fn sample(text: &str) -> TomlFile {
        TomlFile::parse(PathBuf::from("sample.toml"), text).unwrap()
    }

    #[test]
    fn files_round_trip_unchanged() {
        assert_eq!(sample(SAMPLE).text(), SAMPLE);
    }

    #[test]
    fn the_real_override_files_round_trip_unchanged() {
        // Present in a checkout (cargo test in the dev shell); the Nix build sees curate/ only.
        let dir = Path::new(env!("CARGO_MANIFEST_DIR")).join("../overrides");
        for name in ["words.toml", "sentences.toml", "closed_classes.toml"] {
            let Ok(text) = fs::read_to_string(dir.join(name)) else {
                continue;
            };
            assert_eq!(sample(&text).text(), text, "{name}");
        }
    }

    #[test]
    fn an_edit_undone_leaves_the_file_as_it_was() {
        for text in [SAMPLE, "# Pinned and banned example sentences per word.\n", ""] {
            let mut file = sample(text);
            file.set_strs("ban", "Haus#noun#1", &["tatoeba:9".to_owned()]);
            file.set_str("audio", "Haus#noun#1", "De-Haus2.ogg");
            assert_ne!(file.text(), text);
            file.remove("audio", "Haus#noun#1");
            file.set_strs("ban", "Haus#noun#1", &[]);
            assert_eq!(file.text(), text);
        }
    }

    #[test]
    fn edits_touch_only_their_entries() {
        let mut file = sample(SAMPLE);
        file.set_strs("pin", "Hand#noun#1", &["tatoeba:3".to_owned()]);
        file.set_str("audio", "Hand#noun#1", "De-Hand2.ogg");
        let text = file.text();
        assert!(text.contains("\"Hand#noun#1\" = [\"tatoeba:3\"]"));
        assert!(
            text.ends_with("\n[audio]\n\"Hand#noun#1\" = \"De-Hand2.ogg\"\n"),
            "{text}"
        );
        assert!(text.contains("#   Checked 2026-10-22: two-way.\n\"vor#prep#1\""));
        let again = sample(&text);
        assert_eq!(again.get_str("audio", "Hand#noun#1").as_deref(), Some("De-Hand2.ogg"));
        assert_eq!(again.get_strs("pin", "Hand#noun#1"), ["tatoeba:3"]);
    }

    #[test]
    fn pins_and_bans_exclude_each_other() {
        let dir = std::env::temp_dir().join(format!("curate-test-{}", std::process::id()));
        fs::create_dir_all(&dir).unwrap();
        let mut over = Overrides::load(&dir).unwrap();
        assert!(over.toggle_ban("Hand#noun#1", "tatoeba:1").unwrap());
        assert!(over.toggle_pin("Hand#noun#1", "tatoeba:2").unwrap());
        assert!(over.toggle_pin("Hand#noun#1", "tatoeba:1").unwrap());
        assert_eq!(over.pins("Hand#noun#1"), ["tatoeba:2", "tatoeba:1"]);
        assert!(over.bans("Hand#noun#1").is_empty());
        assert!(!over.toggle_pin("Hand#noun#1", "tatoeba:2").unwrap());
        assert_eq!(over.pins("Hand#noun#1"), ["tatoeba:1"]);
        let saved = fs::read_to_string(dir.join("sentences.toml")).unwrap();
        assert_eq!(saved, "[pin]\n\"Hand#noun#1\" = [\"tatoeba:1\"]\n");
        assert!(over.touches("Hand#noun#1") && !over.touches("Haus#noun#1"));
        fs::remove_dir_all(&dir).unwrap();
    }
}
