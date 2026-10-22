//! Curation tool: turns the pipeline's candidates in data/work/curation.sqlite
//! into committed overrides/*.toml and own recordings in overrides/audio/.
//!
//! `nix run .#curate [-- --root DIR]`; the checkout is found by walking up from the
//! current directory to config/pipeline.toml, as the pipeline does.

mod app;
mod audio;
mod config;
mod db;
mod overrides;
mod ui;

use std::path::{Path, PathBuf};

use anyhow::{Context, Result, bail};

const MARKER: &str = "config/pipeline.toml";
const USAGE: &str = "usage: curate [--root DIR]\n\n\
Reads data/work/curation.sqlite (written by `nix run .#build`) and writes overrides/.\n\
Commands for recording, playback and fetching: curate/curate.toml.";

fn find_root(start: &Path) -> Result<PathBuf> {
    let start = start.canonicalize().with_context(|| format!("{}", start.display()))?;
    start
        .ancestors()
        .find(|dir| dir.join(MARKER).is_file())
        .map(Path::to_path_buf)
        .with_context(|| {
            format!(
                "no {MARKER} in {} or any parent; run this inside the checkout",
                start.display()
            )
        })
}

fn main() -> Result<()> {
    let mut args = std::env::args().skip(1);
    let mut root = None;
    while let Some(arg) = args.next() {
        match arg.as_str() {
            "--root" => root = Some(PathBuf::from(args.next().context("--root needs a directory")?)),
            "-h" | "--help" => {
                println!("{USAGE}");
                return Ok(());
            }
            other => bail!("unknown argument {other}\n\n{USAGE}"),
        }
    }
    let root = find_root(&root.unwrap_or(std::env::current_dir()?))?;
    // Load before taking over the terminal, so errors print plainly.
    let mut app = app::App::new(&root)?;
    let mut terminal = ratatui::init();
    let result = app.run(&mut terminal);
    ratatui::restore();
    result
}
