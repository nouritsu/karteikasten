//! The child processes behind playback, recording and fetching (commands from config.rs).
//!
//! Children get no terminal: their output would scribble over the TUI.

use std::io::Read;
use std::path::{Path, PathBuf};
use std::process::{Child, Command, ExitStatus, Stdio};

use anyhow::{Context, Result, bail};

fn spawn(argv: &[String], cwd: &Path, stderr: Stdio) -> Result<Child> {
    let Some((program, args)) = argv.split_first() else {
        bail!("empty command")
    };
    Command::new(program)
        .args(args)
        .current_dir(cwd)
        .stdin(Stdio::null())
        .stdout(Stdio::null())
        .stderr(stderr)
        .spawn()
        .with_context(|| format!("cannot run {program} (commands are set in curate/curate.toml)"))
}

/// One sound at a time: playing another stops the last.
#[derive(Default)]
pub struct Player {
    child: Option<Child>,
}

impl Player {
    pub fn play(&mut self, argv: &[String], cwd: &Path) -> Result<()> {
        self.stop();
        self.child = Some(spawn(argv, cwd, Stdio::null())?);
        Ok(())
    }

    pub fn stop(&mut self) {
        if let Some(mut child) = self.child.take() {
            let _ = child.kill();
            let _ = child.wait();
        }
    }
}

/// A running capture; SIGINT stops it so ffmpeg finishes the file properly.
pub struct Recording {
    child: Child,
    pub word: String,
    pub path: PathBuf,
}

impl Recording {
    pub fn start(argv: &[String], cwd: &Path, word: &str, path: &Path) -> Result<Self> {
        if let Some(dir) = path.parent() {
            std::fs::create_dir_all(dir).with_context(|| format!("creating {}", dir.display()))?;
        }
        Ok(Recording {
            child: spawn(argv, cwd, Stdio::null())?,
            word: word.to_owned(),
            path: path.to_owned(),
        })
    }

    pub fn stop(mut self) -> Result<ExitStatus> {
        let pid = libc::pid_t::try_from(self.child.id()).context("process id out of range")?;
        // SAFETY: kill(2) on our own child's pid; the child has not been reaped yet.
        unsafe { libc::kill(pid, libc::SIGINT) };
        Ok(self.child.wait()?)
    }
}

/// A Commons file being added to the snapshot, to play once it lands.
pub struct Fetch {
    child: Child,
    pub file: String,
    pub path: PathBuf,
}

pub enum Fetched {
    Running,
    Done,
    Failed(String),
}

impl Fetch {
    pub fn start(argv: &[String], cwd: &Path, file: &str, path: &Path) -> Result<Self> {
        Ok(Fetch {
            child: spawn(argv, cwd, Stdio::piped())?,
            file: file.to_owned(),
            path: path.to_owned(),
        })
    }

    pub fn poll(&mut self) -> Fetched {
        match self.child.try_wait() {
            Ok(None) => Fetched::Running,
            Ok(Some(status)) if status.success() && self.path.exists() => Fetched::Done,
            Ok(Some(status)) => {
                let mut err = String::new();
                if let Some(mut pipe) = self.child.stderr.take() {
                    let _ = pipe.read_to_string(&mut err);
                }
                let last = err
                    .lines()
                    .rev()
                    .find(|l| !l.trim().is_empty())
                    .unwrap_or("")
                    .trim()
                    .to_owned();
                Fetched::Failed(if last.is_empty() {
                    format!("fetch exited with {status}")
                } else {
                    last
                })
            }
            Err(error) => Fetched::Failed(error.to_string()),
        }
    }

    pub fn cancel(mut self) {
        let _ = self.child.kill();
        let _ = self.child.wait();
    }
}
