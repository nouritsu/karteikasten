//! State and keys. Two views: the issue queue, and one word with its audio and
//! sentence candidates (the pickers) and the recorder.

use std::fs;
use std::path::{Path, PathBuf};
use std::time::{Duration, SystemTime};

use anyhow::Result;
use ratatui::DefaultTerminal;
use ratatui::crossterm::event::{self, Event, KeyCode, KeyEvent, KeyEventKind, KeyModifiers};
use ratatui::widgets::ListState;

use crate::audio::{Fetch, Fetched, Player, Recording};
use crate::config::{self, Config};
use crate::db::{Database, Severity, Word};
use crate::overrides::Overrides;
use crate::ui;

#[derive(Debug, Clone, Copy, PartialEq, Eq)]
pub enum View {
    Queue,
    Word,
}

#[derive(Debug, Clone, Copy, PartialEq, Eq)]
pub enum Focus {
    Audio,
    Sentences,
}

/// A row of the audio picker.
#[derive(Debug, Clone, PartialEq, Eq)]
pub enum AudioRow {
    Own(PathBuf),
    Commons(usize), // index into the word's candidates
}

pub struct App {
    pub root: PathBuf,
    pub config: Config,
    pub db: Database,
    pub db_time: Option<SystemTime>,
    pub overrides: Overrides,
    pub view: View,
    /// Indices into db.words, in queue order.
    pub queue: Vec<usize>,
    pub queue_state: ListState,
    pub show_all: bool,
    pub filter: String,
    pub typing: bool,
    pub word: usize,
    pub focus: Focus,
    pub audio_state: ListState,
    pub sentence_state: ListState,
    pub status: String,
    pub recording: Option<Recording>,
    pub fetch: Option<Fetch>,
    player: Player,
    quit: bool,
}

/// Blocking first, then warnings, each by rank; words without issues are left out.
pub fn issue_queue(words: &[Word]) -> Vec<usize> {
    let mut queue: Vec<usize> = (0..words.len()).filter(|&i| !words[i].issues.is_empty()).collect();
    queue.sort_by_key(|&i| (words[i].worst(), words[i].rank));
    queue
}

impl App {
    pub fn new(root: &Path) -> Result<Self> {
        let db_path = root.join("data/work/curation.sqlite");
        let db = Database::load(&db_path)?;
        let db_time = fs::metadata(&db_path).and_then(|m| m.modified()).ok();
        let mut app = App {
            root: root.to_owned(),
            config: Config::load(&root.join("curate/curate.toml"))?,
            db,
            db_time,
            overrides: Overrides::load(&root.join("overrides"))?,
            view: View::Queue,
            queue: Vec::new(),
            queue_state: ListState::default(),
            show_all: false,
            filter: String::new(),
            typing: false,
            word: 0,
            focus: Focus::Audio,
            audio_state: ListState::default(),
            sentence_state: ListState::default(),
            status: String::new(),
            recording: None,
            fetch: None,
            player: Player::default(),
            quit: false,
        };
        app.rebuild_queue();
        Ok(app)
    }

    pub fn run(&mut self, terminal: &mut DefaultTerminal) -> Result<()> {
        while !self.quit {
            terminal.draw(|frame| ui::draw(frame, self))?;
            self.poll_fetch();
            if event::poll(Duration::from_millis(200))?
                && let Event::Key(key) = event::read()?
                && key.kind == KeyEventKind::Press
                && let Err(error) = self.key(key)
            {
                self.status = format!("error: {error:#}");
            }
        }
        self.shutdown();
        Ok(())
    }

    fn shutdown(&mut self) {
        self.player.stop();
        if let Some(recording) = self.recording.take() {
            let _ = recording.stop();
        }
        if let Some(fetch) = self.fetch.take() {
            fetch.cancel();
        }
    }

    // -- data for the views ------------------------------------------------------------------

    pub fn current(&self) -> &Word {
        &self.db.words[self.word]
    }

    pub fn blocking_counts(&self) -> (usize, usize, usize) {
        let words = &self.db.words;
        let blocking = words.iter().filter(|w| w.worst() == Some(Severity::Blocking)).count();
        let top500 = words
            .iter()
            .filter(|w| w.rank <= 500 && w.worst() == Some(Severity::Blocking))
            .count();
        let warnings = words.iter().filter(|w| w.worst() == Some(Severity::Warning)).count();
        (blocking, top500, warnings)
    }

    /// Overrides saved after the database was written: the deck does not show them yet.
    pub fn overrides_newer(&self) -> bool {
        let Some(db_time) = self.db_time else { return false };
        let dir = &self.overrides.dir;
        let mut files = vec![
            dir.join("words.toml"),
            dir.join("sentences.toml"),
            dir.join("closed_classes.toml"),
        ];
        if let Ok(entries) = fs::read_dir(dir.join("audio")) {
            files.extend(entries.filter_map(|e| e.ok().map(|e| e.path())));
        }
        files
            .iter()
            .any(|f| fs::metadata(f).and_then(|m| m.modified()).is_ok_and(|t| t > db_time))
    }

    pub fn audio_rows(&self) -> Vec<AudioRow> {
        let id = &self.current().id;
        let mut rows: Vec<AudioRow> = self.overrides.recording(id).into_iter().map(AudioRow::Own).collect();
        rows.extend((0..self.db.audio.get(id).map_or(0, Vec::len)).map(AudioRow::Commons));
        rows
    }

    /// Pinned first in pin order, then the deck's picks, then the rest by score.
    pub fn sentence_rows(&self) -> Vec<usize> {
        let id = &self.current().id;
        let Some(candidates) = self.db.sentences.get(id) else {
            return Vec::new();
        };
        let pins = self.overrides.pins(id);
        let mut rows: Vec<usize> = (0..candidates.len()).collect();
        rows.sort_by_key(|&i| {
            let c = &candidates[i];
            (pins.iter().position(|p| *p == c.id).unwrap_or(usize::MAX), !c.picked, i)
        });
        rows
    }

    fn rebuild_queue(&mut self) {
        let words = &self.db.words;
        self.queue = if !self.filter.is_empty() {
            let needle = self.filter.to_lowercase();
            (0..words.len())
                .filter(|&i| words[i].lemma.to_lowercase().contains(&needle))
                .collect()
        } else if self.show_all {
            (0..words.len()).collect()
        } else {
            issue_queue(words)
        };
        self.queue_state
            .select(if self.queue.is_empty() { None } else { Some(0) });
    }

    // -- keys --------------------------------------------------------------------------------

    fn key(&mut self, key: KeyEvent) -> Result<()> {
        if key.modifiers.contains(KeyModifiers::CONTROL) && key.code == KeyCode::Char('c') {
            self.quit = true;
            return Ok(());
        }
        match self.view {
            View::Queue if self.typing => self.search_key(key.code),
            View::Queue => self.queue_key(key.code),
            View::Word => self.word_key(key.code)?,
        }
        Ok(())
    }

    fn search_key(&mut self, code: KeyCode) {
        match code {
            KeyCode::Char(c) => self.filter.push(c),
            KeyCode::Backspace => {
                self.filter.pop();
            }
            KeyCode::Enter => self.typing = false,
            KeyCode::Esc => {
                self.typing = false;
                self.filter.clear();
            }
            _ => return,
        }
        self.rebuild_queue();
    }

    fn queue_key(&mut self, code: KeyCode) {
        let len = self.queue.len();
        match code {
            KeyCode::Char('q') => self.quit = true,
            KeyCode::Char('j') | KeyCode::Down => move_by(&mut self.queue_state, len, 1),
            KeyCode::Char('k') | KeyCode::Up => move_by(&mut self.queue_state, len, -1),
            KeyCode::PageDown => move_by(&mut self.queue_state, len, 20),
            KeyCode::PageUp => move_by(&mut self.queue_state, len, -20),
            KeyCode::Char('g') | KeyCode::Home => move_by(&mut self.queue_state, len, -(len as isize)),
            KeyCode::Char('G') | KeyCode::End => move_by(&mut self.queue_state, len, len as isize),
            KeyCode::Char('/') => {
                self.typing = true;
                self.filter.clear();
                self.rebuild_queue();
            }
            KeyCode::Esc if !self.filter.is_empty() => {
                self.filter.clear();
                self.rebuild_queue();
            }
            KeyCode::Char('t') => {
                self.show_all = !self.show_all;
                self.filter.clear();
                self.rebuild_queue();
            }
            KeyCode::Enter => {
                if let Some(selected) = self.queue_state.selected() {
                    self.open(self.queue[selected]);
                }
            }
            _ => {}
        }
    }

    fn open(&mut self, word: usize) {
        self.word = word;
        self.view = View::Word;
        self.focus = Focus::Audio;
        self.audio_state.select(Some(0));
        self.sentence_state.select(Some(0));
        self.status.clear();
    }

    fn word_key(&mut self, code: KeyCode) -> Result<()> {
        let focused_len = match self.focus {
            Focus::Audio => self.audio_rows().len(),
            Focus::Sentences => self.sentence_rows().len(),
        };
        let state = match self.focus {
            Focus::Audio => &mut self.audio_state,
            Focus::Sentences => &mut self.sentence_state,
        };
        match code {
            KeyCode::Esc | KeyCode::Char('q') => {
                self.player.stop();
                self.view = View::Queue;
            }
            KeyCode::Tab | KeyCode::BackTab => {
                self.focus = if self.focus == Focus::Audio {
                    Focus::Sentences
                } else {
                    Focus::Audio
                };
            }
            KeyCode::Char('j' | 'n') | KeyCode::Down => move_by(state, focused_len, 1),
            KeyCode::Char('k' | 'p') | KeyCode::Up => move_by(state, focused_len, -1),
            KeyCode::Char('a') => self.accept()?,
            KeyCode::Char('x') => self.reject()?,
            KeyCode::Char(' ') => self.play()?,
            KeyCode::Char('r') => self.record()?,
            _ => {}
        }
        Ok(())
    }

    fn selected_audio(&self) -> Option<AudioRow> {
        self.audio_rows().get(self.audio_state.selected()?).cloned()
    }

    fn selected_sentence(&self) -> Option<String> {
        let id = &self.current().id;
        let row = *self.sentence_rows().get(self.sentence_state.selected()?)?;
        Some(self.db.sentences[id][row].id.clone())
    }

    fn accept(&mut self) -> Result<()> {
        let id = self.current().id.clone();
        match self.focus {
            Focus::Audio => match self.selected_audio() {
                Some(AudioRow::Own(_)) => {
                    self.status = "an own recording always wins; delete its file to drop it".into();
                }
                Some(AudioRow::Commons(i)) => {
                    let candidate = self.db.audio[&id][i].clone();
                    if !candidate.usable {
                        self.status = format!(
                            "{}: Commons names no author or licence, so it cannot ship",
                            candidate.file
                        );
                    } else if self.overrides.audio_pin(&id).as_deref() == Some(candidate.file.as_str()) {
                        self.status = format!("{} is already pinned; x removes the pin", candidate.file);
                    } else {
                        self.overrides.pin_audio(&id, &candidate.file)?;
                        self.status = format!("pinned {} in words.toml [audio]", candidate.file);
                    }
                }
                None => {}
            },
            Focus::Sentences => {
                if let Some(sentence) = self.selected_sentence() {
                    let pinned = self.overrides.toggle_pin(&id, &sentence)?;
                    self.status = format!(
                        "{} {sentence} in sentences.toml",
                        if pinned { "pinned" } else { "unpinned" }
                    );
                }
            }
        }
        Ok(())
    }

    fn reject(&mut self) -> Result<()> {
        let id = self.current().id.clone();
        match self.focus {
            Focus::Audio => {
                let pin = self.overrides.audio_pin(&id);
                match self.selected_audio() {
                    Some(AudioRow::Commons(i)) if pin.as_deref() == Some(self.db.audio[&id][i].file.as_str()) => {
                        self.overrides.unpin_audio(&id)?;
                        self.status = "pin removed: the build picks again".into();
                    }
                    _ => self.status = "x removes an audio pin; a pins another file, r records your own".into(),
                }
            }
            Focus::Sentences => {
                if let Some(sentence) = self.selected_sentence() {
                    let banned = self.overrides.toggle_ban(&id, &sentence)?;
                    self.status = format!(
                        "{} {sentence} in sentences.toml",
                        if banned { "banned" } else { "unbanned" }
                    );
                }
            }
        }
        Ok(())
    }

    fn play(&mut self) -> Result<()> {
        if self.focus != Focus::Audio {
            self.status = "Space plays the audio row under the cursor (Tab switches)".into();
            return Ok(());
        }
        let id = self.current().id.clone();
        let file = match self.selected_audio() {
            Some(AudioRow::Own(path)) => path,
            Some(AudioRow::Commons(i)) => {
                let name = self.db.audio[&id][i].file.clone();
                let path = self.root.join("data/raw/commons/audio").join(&name);
                if !path.exists() {
                    if let Some(old) = self.fetch.take() {
                        old.cancel();
                    }
                    let argv = config::command(&self.config.fetch_cmd, "file", &name);
                    self.fetch = Some(Fetch::start(&argv, &self.root, &name, &path)?);
                    self.status = format!("fetching {name} from Commons…");
                    return Ok(());
                }
                path
            }
            None => return Ok(()),
        };
        self.play_file(&file)
    }

    fn play_file(&mut self, file: &Path) -> Result<()> {
        let argv = config::command(&self.config.play_cmd, "file", &file.to_string_lossy());
        self.player.play(&argv, &self.root)?;
        self.status = format!("playing {}", file.file_name().unwrap_or_default().to_string_lossy());
        Ok(())
    }

    fn poll_fetch(&mut self) {
        let Some(fetch) = self.fetch.as_mut() else { return };
        match fetch.poll() {
            Fetched::Running => {}
            Fetched::Done => {
                let path = fetch.path.clone();
                self.fetch = None;
                if let Err(error) = self.play_file(&path) {
                    self.status = format!("error: {error:#}");
                }
            }
            Fetched::Failed(message) => {
                self.status = format!("fetching {} failed: {message}", fetch.file);
                self.fetch = None;
            }
        }
    }

    fn record(&mut self) -> Result<()> {
        if let Some(recording) = self.recording.take() {
            let path = recording.path.clone();
            // ffmpeg exits 255 on SIGINT after closing the file properly: judge by the file.
            let status = recording.stop()?;
            self.status = if fs::metadata(&path).is_ok_and(|m| m.len() > 0) {
                format!(
                    "saved {}; a build needs [recordings] author and license in config/pipeline.toml",
                    path.strip_prefix(&self.root).unwrap_or(&path).display()
                )
            } else {
                format!("recording failed ({status}); check record_cmd in curate/curate.toml")
            };
            self.audio_state.select(Some(0));
            return Ok(());
        }
        self.player.stop();
        let id = self.current().id.clone();
        let path = self.overrides.recording_target(&id);
        let argv = config::command(&self.config.record_cmd, "out", &path.to_string_lossy());
        self.recording = Some(Recording::start(&argv, &self.root, &id, &path)?);
        self.status = format!("recording {}… r stops", self.current().lemma);
        Ok(())
    }
}

fn move_by(state: &mut ListState, len: usize, delta: isize) {
    if len == 0 {
        state.select(None);
        return;
    }
    let current = state.selected().unwrap_or(0) as isize;
    state.select(Some((current + delta).clamp(0, len as isize - 1) as usize));
}

#[cfg(test)]
mod tests {
    use super::*;
    use crate::db::Issue;

    fn word(id: &str, rank: u32, severities: &[Severity]) -> Word {
        let issues = severities
            .iter()
            .map(|&severity| Issue {
                severity,
                code: "x".into(),
                detail: "x".into(),
            })
            .collect();
        Word {
            id: id.into(),
            rank,
            lemma: id.into(),
            pos: "noun".into(),
            card: serde_json::Value::Null,
            issues,
        }
    }

    #[test]
    fn the_queue_puts_blocking_first_then_rank() {
        let words = vec![
            word("a", 1, &[Severity::Warning]),
            word("b", 2, &[]),
            word("c", 3, &[Severity::Blocking, Severity::Warning]),
            word("d", 4, &[Severity::Warning]),
            word("e", 5, &[Severity::Blocking]),
        ];
        let order: Vec<&str> = issue_queue(&words).iter().map(|&i| words[i].id.as_str()).collect();
        assert_eq!(order, ["c", "e", "a", "d"]);
    }

    /// Draws both views from the checkout's real database (skipped without one);
    /// CURATE_SHOW=1 prints the screens.
    #[test]
    fn draws_the_real_database() {
        use ratatui::Terminal;
        use ratatui::backend::TestBackend;

        let root = Path::new(env!("CARGO_MANIFEST_DIR")).join("..");
        if !root.join("data/work/curation.sqlite").exists() {
            return;
        }
        let mut app = App::new(&root.canonicalize().unwrap()).unwrap();
        let mut terminal = Terminal::new(TestBackend::new(140, 40)).unwrap();
        let mut screens = Vec::new();
        terminal.draw(|f| ui::draw(f, &mut app)).unwrap();
        screens.push(format!("{}", terminal.backend()));
        let hand = app.db.words.iter().position(|w| w.id == "Hand#noun#1").unwrap();
        app.open(hand);
        app.focus = Focus::Sentences;
        terminal.draw(|f| ui::draw(f, &mut app)).unwrap();
        screens.push(format!("{}", terminal.backend()));
        if std::env::var_os("CURATE_SHOW").is_some() {
            println!("{}", screens.join("\n"));
        }
        assert!(screens[1].contains("Hand"));
    }

    #[test]
    fn moving_stays_inside_the_list() {
        let mut state = ListState::default();
        move_by(&mut state, 3, 5);
        assert_eq!(state.selected(), Some(2));
        move_by(&mut state, 3, -9);
        assert_eq!(state.selected(), Some(0));
        move_by(&mut state, 0, 1);
        assert_eq!(state.selected(), None);
    }
}
