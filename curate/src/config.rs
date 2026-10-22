//! curate/curate.toml: the commands the tool runs to record, play and fetch audio.
//!
//! Each command is a template split on whitespace; `{out}` and `{file}` are filled in
//! after the split, so a file name with spaces stays one argument. No shell is involved.

use std::fs;
use std::path::Path;

use anyhow::{Context, Result, bail};

/// ffmpeg capture through PipeWire's PulseAudio server, mono 48 kHz; `{out}` names the file.
pub const DEFAULT_RECORD: &str =
    "ffmpeg -nostdin -hide_banner -loglevel error -f pulse -i default -ac 1 -ar 48000 -y {out}";
pub const DEFAULT_PLAY: &str = "ffplay -nodisp -autoexit -loglevel quiet {file}";
/// Adds a Commons file to the snapshot (data/raw, sources.lock.json) so it can be played.
pub const DEFAULT_FETCH: &str = "karteikasten-pipeline fetch --commons {file}";

#[derive(Debug, Clone, PartialEq, Eq)]
pub struct Config {
    pub record_cmd: String,
    pub play_cmd: String,
    pub fetch_cmd: String,
}

impl Default for Config {
    fn default() -> Self {
        Config {
            record_cmd: DEFAULT_RECORD.to_owned(),
            play_cmd: DEFAULT_PLAY.to_owned(),
            fetch_cmd: DEFAULT_FETCH.to_owned(),
        }
    }
}

impl Config {
    /// The file's values over the defaults; a missing file means the defaults.
    pub fn load(path: &Path) -> Result<Self> {
        let mut config = Config::default();
        if !path.exists() {
            return Ok(config);
        }
        let text = fs::read_to_string(path).with_context(|| format!("reading {}", path.display()))?;
        config.merge(&text).with_context(|| format!("in {}", path.display()))?;
        Ok(config)
    }

    fn merge(&mut self, text: &str) -> Result<()> {
        let doc: toml_edit::DocumentMut = text.parse()?;
        for (key, slot) in [
            ("record_cmd", &mut self.record_cmd),
            ("play_cmd", &mut self.play_cmd),
            ("fetch_cmd", &mut self.fetch_cmd),
        ] {
            if let Some(item) = doc.get(key) {
                let Some(value) = item.as_str() else {
                    bail!("{key} must be a string")
                };
                if value.split_whitespace().next().is_none() {
                    bail!("{key} is empty");
                }
                *slot = value.to_owned();
            }
        }
        Ok(())
    }
}

/// argv for a command template with `{key}` replaced by `value`.
pub fn command(template: &str, key: &str, value: &str) -> Vec<String> {
    let placeholder = format!("{{{key}}}");
    template
        .split_whitespace()
        .map(|part| part.replace(&placeholder, value))
        .collect()
}

#[cfg(test)]
mod tests {
    use super::*;

    #[test]
    fn a_file_name_with_spaces_stays_one_argument() {
        let argv = command(
            DEFAULT_PLAY,
            "file",
            "data/raw/commons/audio/LL-Q188 (deu)-X-fahren.wav",
        );
        assert_eq!(
            argv.last().unwrap(),
            "data/raw/commons/audio/LL-Q188 (deu)-X-fahren.wav"
        );
        assert_eq!(argv[0], "ffplay");
    }

    #[test]
    fn the_file_overrides_the_defaults() {
        let mut config = Config::default();
        config.merge("play_cmd = \"mpv --no-video {file}\"\n").unwrap();
        assert_eq!(config.play_cmd, "mpv --no-video {file}");
        assert_eq!(config.record_cmd, DEFAULT_RECORD);
        assert!(config.merge("play_cmd = 3\n").is_err());
        assert!(config.merge("play_cmd = \"  \"\n").is_err());
    }
}
