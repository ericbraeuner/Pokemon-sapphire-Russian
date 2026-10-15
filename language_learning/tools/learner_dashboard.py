#!/usr/bin/env python3
"""Render a self-contained learner progress dashboard from an external profile."""

from __future__ import annotations

import argparse
import html
import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

import review_queue


TEXT = {
    "ru": {
        "title": "Прогресс в языке", "level": "Уровень", "exposures": "Встречи",
        "dictionary": "Словарь", "due": "К повторению", "reviews": "Повторение слов",
        "mastery": "Освоение", "context": "Контекст", "empty": "Сейчас нет слов для повторения.",
        "upcoming": "Позже", "gloss": "Значение",
    },
    "de": {
        "title": "Sprachfortschritt", "level": "Niveau", "exposures": "Begegnungen",
        "dictionary": "Wörterbuch", "due": "Jetzt fällig", "reviews": "Wörter wiederholen",
        "mastery": "Gelernt", "context": "Kontext", "empty": "Zurzeit sind keine Wörter fällig.",
        "upcoming": "Später", "gloss": "Bedeutung",
    },
}


def _e(value: Any) -> str:
    return html.escape(str(value), quote=True)


def render(profile: dict[str, Any], *, now: datetime | None = None, limit: int = 20) -> str:
    language = profile.get("selected_language")
    if language not in TEXT:
        raise ValueError("profile selected_language must be ru or de")
    now = now or datetime.now(timezone.utc)
    queue = review_queue.build(profile, now=now, limit=limit, include_upcoming=True)
    labels = TEXT[language]
    learning = profile.get("rom_learning", {})
    cards = []
    for card in queue["cards"]:
        status = labels["due"] if card["is_due"] else labels["upcoming"]
        percent = max(0, min(100, round(card["mastery"] * 100)))
        cards.append(f"""
        <article class="word-card{' due' if card['is_due'] else ''}">
          <div class="word-row"><h3>{_e(card['lemma'])}</h3><span class="status">{_e(status)}</span></div>
          <p><strong>{_e(labels['gloss'])}:</strong> {_e(card['english_gloss'])}</p>
          <p><strong>{_e(labels['context'])}:</strong> {_e(card['source_id'])}</p>
          <div class="meter" role="meter" aria-valuemin="0" aria-valuemax="100" aria-valuenow="{percent}"><span style="width:{percent}%"></span></div>
          <small>{_e(labels['mastery'])}: {percent}% · {_e(card['due_at'])}</small>
        </article>""")
    card_html = "\n".join(cards) if cards else f'<p class="empty">{_e(labels["empty"])}</p>'
    return f"""<!doctype html>
<html lang="{_e(language)}">
<head>
  <meta charset="utf-8">
  <meta name="viewport" content="width=device-width,initial-scale=1">
  <title>{_e(labels['title'])}</title>
  <style>
    :root {{ color-scheme: light dark; font-family: system-ui, sans-serif; --accent:#3567d6; --panel:#ffffff12; }}
    body {{ margin:0; background:#15213a; color:#f7f8fc; }}
    main {{ max-width:760px; margin:auto; padding:24px 16px 48px; }}
    header {{ display:flex; justify-content:space-between; gap:16px; align-items:end; flex-wrap:wrap; }}
    h1 {{ margin:0; font-size:clamp(1.75rem,6vw,2.6rem); }}
    .profile {{ opacity:.75; }}
    .stats {{ display:grid; grid-template-columns:repeat(4,minmax(0,1fr)); gap:10px; margin:24px 0; }}
    .stat,.word-card {{ background:var(--panel); border:1px solid #ffffff20; border-radius:14px; padding:14px; }}
    .stat strong {{ display:block; font-size:1.45rem; }} .stat span,small {{ opacity:.75; }}
    .words {{ display:grid; gap:12px; }} .word-row {{ display:flex; justify-content:space-between; gap:12px; align-items:center; }}
    h2,h3,p {{ margin-top:0; }} h3 {{ margin-bottom:0; font-size:1.35rem; }}
    .status {{ background:#ffffff16; padding:4px 9px; border-radius:99px; white-space:nowrap; }}
    .due {{ border-color:#f4bd50; }} .due .status {{ background:#9b641f; }}
    .meter {{ height:8px; margin:12px 0 7px; border-radius:8px; overflow:hidden; background:#ffffff20; }}
    .meter span {{ display:block; height:100%; background:#65b982; }} .empty {{ opacity:.8; }}
    @media (max-width:560px) {{ .stats {{ grid-template-columns:repeat(2,minmax(0,1fr)); }} }}
  </style>
</head>
<body><main>
  <header><div><h1>{_e(labels['title'])}</h1><div class="profile">{_e(profile.get('profile_id', ''))}</div></div></header>
  <section class="stats" aria-label="{_e(labels['title'])}">
    <div class="stat"><strong>{_e(profile['current_learner_difficulty']['cefr'])}</strong><span>{_e(labels['level'])}</span></div>
    <div class="stat"><strong>{_e(learning.get('exposure_count', 0))}</strong><span>{_e(labels['exposures'])}</span></div>
    <div class="stat"><strong>{_e(learning.get('dictionary_count', 0))}</strong><span>{_e(labels['dictionary'])}</span></div>
    <div class="stat"><strong>{_e(queue['due_count'])}</strong><span>{_e(labels['due'])}</span></div>
  </section>
  <h2>{_e(labels['reviews'])}</h2>
  <section class="words">{card_html}</section>
</main></body></html>\n"""


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("profile", type=Path)
    parser.add_argument("output", type=Path)
    parser.add_argument("--limit", type=int, default=20)
    parser.add_argument("--now", help="fixed UTC timestamp for reproducible output")
    args = parser.parse_args()
    profile = json.loads(args.profile.read_text(encoding="utf-8"))
    now = review_queue._timestamp(args.now) if args.now else None
    rendered = render(profile, now=now, limit=args.limit)
    temporary = args.output.with_suffix(args.output.suffix + ".tmp")
    temporary.write_text(rendered, encoding="utf-8")
    temporary.replace(args.output)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
