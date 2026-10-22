//! Drawing. Rounded blocks with inset titles, like the app; ANSI colours, so the
//! terminal's own theme (Catppuccin Latte or Mocha) decides the shades.

use ratatui::Frame;
use ratatui::layout::{Constraint, Layout, Rect};
use ratatui::style::{Color, Modifier, Style};
use ratatui::text::{Line, Span};
use ratatui::widgets::{Block, BorderType, List, ListItem, Paragraph, Wrap};
use serde_json::Value;

use crate::app::{App, AudioRow, Focus, View};
use crate::db::Severity;

const ACCENT: Color = Color::Magenta;
const DIM: Style = Style::new().fg(Color::DarkGray);

fn block(title: String, focused: bool) -> Block<'static> {
    let style = if focused { Style::new().fg(ACCENT) } else { Style::new() };
    Block::bordered()
        .border_type(BorderType::Rounded)
        .border_style(style)
        .title(Span::styled(format!(" {title} "), style.add_modifier(Modifier::BOLD)))
}

fn severity_mark(severity: Option<Severity>) -> Span<'static> {
    match severity {
        Some(Severity::Blocking) => Span::styled("✗", Style::new().fg(Color::Red)),
        Some(Severity::Warning) => Span::styled("!", Style::new().fg(Color::Yellow)),
        None => Span::styled("·", DIM),
    }
}

fn highlight() -> Style {
    Style::new().add_modifier(Modifier::REVERSED)
}

pub fn draw(frame: &mut Frame, app: &mut App) {
    let [header, body, footer] =
        Layout::vertical([Constraint::Length(1), Constraint::Min(5), Constraint::Length(2)]).areas(frame.area());
    draw_header(frame, header, app);
    match app.view {
        View::Queue => draw_queue(frame, body, app),
        View::Word => draw_word(frame, body, app),
    }
    draw_footer(frame, footer, app);
}

fn draw_header(frame: &mut Frame, area: Rect, app: &App) {
    let (blocking, top500, warnings) = app.blocking_counts();
    let mut spans = vec![
        Span::styled(" curate ", Style::new().fg(ACCENT).add_modifier(Modifier::BOLD)),
        Span::raw(format!("· deck {} · ", app.db.deck_version)),
        Span::styled(format!("{blocking} blocking"), Style::new().fg(Color::Red)),
        Span::raw(format!(" ({top500} in the top 500) · ")),
        Span::styled(format!("{warnings} with warnings"), Style::new().fg(Color::Yellow)),
    ];
    if app.overrides_newer() {
        spans.push(Span::styled(
            " · overrides changed: nix run .#build",
            Style::new().fg(ACCENT),
        ));
    }
    frame.render_widget(Line::from(spans), area);
}

fn draw_footer(frame: &mut Frame, area: Rect, app: &App) {
    let keys = match app.view {
        View::Queue if app.typing => "type to search · Enter keep · Esc clear",
        View::Queue => "j/k move · Enter open · / search · t all words / issues · q quit",
        View::Word => "Tab audio/sentences · j/k n/p move · a accept · x reject · Space play · r record · Esc back",
    };
    let status = if let Some(recording) = &app.recording {
        Span::styled(
            format!(" ● recording {} … r stops", recording.word),
            Style::new().fg(Color::Red),
        )
    } else {
        Span::styled(format!(" {}", app.status), Style::new().fg(ACCENT))
    };
    let lines = vec![Line::from(status), Line::from(Span::styled(format!(" {keys}"), DIM))];
    frame.render_widget(Paragraph::new(lines), area);
}

fn draw_queue(frame: &mut Frame, area: Rect, app: &mut App) {
    let title = if !app.filter.is_empty() || app.typing {
        format!(
            "Search: {}{} · {}",
            app.filter,
            if app.typing { "▏" } else { "" },
            app.queue.len()
        )
    } else if app.show_all {
        format!("All words · {}", app.queue.len())
    } else {
        format!("Issues · {} words", app.queue.len())
    };
    let items: Vec<ListItem> = app
        .queue
        .iter()
        .map(|&i| {
            let w = &app.db.words[i];
            let codes: Vec<&str> = w.issues.iter().map(|i| i.code.as_str()).collect();
            let touched = if app.overrides.touches(&w.id) { "✎" } else { " " };
            ListItem::new(Line::from(vec![
                severity_mark(w.worst()),
                Span::raw(format!(" {:>5} ", w.rank)),
                Span::styled(format!("{:<22}", w.lemma), Style::new().add_modifier(Modifier::BOLD)),
                Span::styled(format!("{:<9}", w.pos), DIM),
                Span::styled(format!("{touched} "), Style::new().fg(ACCENT)),
                Span::raw(codes.join(", ")),
            ]))
        })
        .collect();
    let list = List::new(items).block(block(title, true)).highlight_style(highlight());
    frame.render_stateful_widget(list, area, &mut app.queue_state);
}

fn text_of(value: &Value) -> String {
    match value {
        Value::String(s) => s.clone(),
        Value::Array(items) => items.iter().map(text_of).collect::<Vec<_>>().join(", "),
        Value::Null => "—".into(),
        other => other.to_string(),
    }
}

fn glosses(card: &Value, field: &str) -> String {
    let list: Vec<String> = card[field]
        .as_array()
        .into_iter()
        .flatten()
        .filter_map(|g| g["text"].as_str().map(str::to_owned))
        .collect();
    if list.is_empty() { "—".into() } else { list.join("; ") }
}

fn card_lines(app: &App) -> Vec<Line<'static>> {
    let w = app.current();
    let card = &w.card;
    let mut head = vec![];
    if let Some(article) = card["article"].as_str() {
        head.push(Span::raw(format!("{article} ")));
    }
    head.push(Span::styled(
        w.lemma.clone(),
        Style::new().fg(ACCENT).add_modifier(Modifier::BOLD),
    ));
    head.push(Span::styled(format!("  {} · #{} · {}", w.pos, w.rank, w.id), DIM));
    if let Some(ipa) = card["ipa"].as_str() {
        head.push(Span::raw(format!("  {ipa}")));
    }
    let mut lines = vec![Line::from(head)];
    lines.push(Line::from(vec![
        Span::styled("EN ", DIM),
        Span::raw(glosses(card, "gloss_en")),
    ]));
    lines.push(Line::from(vec![
        Span::styled("DE ", DIM),
        Span::raw(glosses(card, "gloss_de")),
    ]));
    let forms: Vec<String> = card["key_forms"]
        .as_object()
        .into_iter()
        .flatten()
        .filter(|(_, v)| !v.is_null() && v.as_array().is_none_or(|a| !a.is_empty()))
        .map(|(k, v)| format!("{k}: {}", text_of(v)))
        .collect();
    let flags = text_of(&card["flags"]);
    lines.push(Line::from(vec![
        Span::styled("Forms ", DIM),
        Span::raw(if forms.is_empty() {
            "—".into()
        } else {
            forms.join(" · ")
        }),
        Span::styled("  Flags ", DIM),
        Span::raw(if flags.is_empty() { "—".into() } else { flags }),
    ]));
    for issue in &w.issues {
        lines.push(Line::from(vec![
            severity_mark(Some(issue.severity)),
            Span::raw(format!(" {}", issue.detail)),
        ]));
    }
    lines
}

fn draw_word(frame: &mut Frame, area: Rect, app: &mut App) {
    let lines = card_lines(app);
    let audio_rows = app.audio_rows();
    let card_height = lines.len() as u16 + 2;
    let audio_height = (audio_rows.len().max(1) as u16 + 2).min(10);
    let [card_area, audio_area, sentence_area] = Layout::vertical([
        Constraint::Length(card_height),
        Constraint::Length(audio_height),
        Constraint::Min(4),
    ])
    .areas(area);
    let title = format!("Card · {}", app.current().lemma);
    frame.render_widget(
        Paragraph::new(lines)
            .wrap(Wrap { trim: true })
            .block(block(title, false)),
        card_area,
    );

    let id = app.current().id.clone();
    let pin = app.overrides.audio_pin(&id);
    let candidates = app.db.audio.get(&id).cloned().unwrap_or_default();
    let audio_items: Vec<ListItem> = audio_rows
        .iter()
        .map(|row| match row {
            AudioRow::Own(path) => ListItem::new(Line::from(vec![
                Span::styled("◆ ", Style::new().fg(ACCENT)),
                Span::raw(path.file_name().unwrap_or_default().to_string_lossy().into_owned()),
                Span::styled("  own recording (wins over Commons)", DIM),
            ])),
            AudioRow::Commons(i) => {
                let c = &candidates[*i];
                let mark = if pin.as_deref() == Some(c.file.as_str()) {
                    Span::styled("★ ", Style::new().fg(ACCENT))
                } else if c.picked {
                    Span::styled("● ", Style::new().fg(Color::Green))
                } else {
                    Span::raw("  ")
                };
                let local = app.root.join("data/raw/commons/audio").join(&c.file).exists();
                let mut spans = vec![
                    mark,
                    Span::styled(format!("{:<44}", c.file), if c.usable { Style::new() } else { DIM }),
                    Span::styled(
                        format!(
                            " {} · {}{}",
                            c.author.as_deref().unwrap_or("no author"),
                            c.license.as_deref().unwrap_or("no licence"),
                            c.region.as_deref().map(|r| format!(" · {r}")).unwrap_or_default()
                        ),
                        DIM,
                    ),
                ];
                if !local {
                    spans.push(Span::styled("  (fetched on play)", DIM));
                }
                ListItem::new(Line::from(spans))
            }
        })
        .collect();
    let audio_title = format!("Audio · ● build's pick · ★ pinned · {} candidates", candidates.len());
    let audio_list = if audio_items.is_empty() {
        List::new(vec![ListItem::new(Span::styled(
            "no recording in Wiktionary; r records your own",
            DIM,
        ))])
    } else {
        List::new(audio_items)
    }
    .block(block(audio_title, app.focus == Focus::Audio))
    .highlight_style(if app.focus == Focus::Audio {
        highlight()
    } else {
        Style::new()
    });
    frame.render_stateful_widget(audio_list, audio_area, &mut app.audio_state);

    let pins = app.overrides.pins(&id);
    let bans = app.overrides.bans(&id);
    let sentences = app.db.sentences.get(&id).cloned().unwrap_or_default();
    let width = sentence_area.width.saturating_sub(8) as usize;
    let items: Vec<ListItem> = app
        .sentence_rows()
        .into_iter()
        .map(|i| {
            let s = &sentences[i];
            let mark = if pins.contains(&s.id) {
                Span::styled("★ ", Style::new().fg(ACCENT))
            } else if bans.contains(&s.id) {
                Span::styled("✗ ", Style::new().fg(Color::Red))
            } else if s.picked {
                Span::styled("● ", Style::new().fg(Color::Green))
            } else {
                Span::raw("  ")
            };
            let style = if bans.contains(&s.id) {
                DIM.add_modifier(Modifier::CROSSED_OUT)
            } else {
                Style::new()
            };
            let meta = format!(
                "    {} · {}{} · {:.1}",
                s.id,
                s.author.as_deref().unwrap_or("?"),
                if s.native { " (native)" } else { "" },
                s.score
            );
            ListItem::new(vec![
                Line::from(vec![mark, Span::styled(clip(&s.de, width), style)]),
                Line::from(Span::styled(
                    format!("  {}", clip(s.en.as_deref().unwrap_or("—"), width)),
                    DIM,
                )),
                Line::from(Span::styled(meta, DIM)),
            ])
        })
        .collect();
    let title = format!(
        "Sentences · ● in the deck · ★ pinned · ✗ banned · {} candidates",
        sentences.len()
    );
    let list = List::new(items)
        .block(block(title, app.focus == Focus::Sentences))
        .highlight_style(if app.focus == Focus::Sentences {
            highlight()
        } else {
            Style::new()
        });
    frame.render_stateful_widget(list, sentence_area, &mut app.sentence_state);
}

fn clip(text: &str, width: usize) -> String {
    if text.chars().count() <= width {
        text.to_owned()
    } else {
        let mut out: String = text.chars().take(width.saturating_sub(1)).collect();
        out.push('…');
        out
    }
}
