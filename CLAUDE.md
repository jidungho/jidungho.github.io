# jidungho.github.io

Personal site. Hugo + PaperMod, deployed to GitHub Pages by `.github/workflows/hugo.yml` on push to `main`.

## Adding a reading

Each reading is one file in `content/readings/`. Create it with:

```
hugo new --kind reading readings/<slug>.md
```

Front matter:

| field        | meaning                                                      |
| ------------ | ------------------------------------------------------------ |
| `date`       | when *I* added it — controls ordering (newest first)          |
| `source`     | URL of the original article                                   |
| `author`     | article's author(s)                                           |
| `publisher`  | site/organization it was published on                         |
| `sourceDate` | the article's own publication date, as a string ("May 2026") — **not** `published`, which Hugo reserves |

Body: one paragraph summarizing the article, then `<!--more-->`. Anything after the
divider (e.g. a `## Notes` section with my own thoughts) shows on the reading's own
page but is kept off the list views.

Summaries should be checked against the source, not just a fetch tool's paraphrase —
these go on a public page.

## Layout

- `layouts/index.html` — homepage: compact profile card, then the N most recent readings (`params.homeReadings`, default 10).
- `layouts/readings/list.html` — `/readings/`, the full list.
- `layouts/readings/single.html` — one reading: title, source link, summary, notes, tags.
- `layouts/partials/reading_entry.html` — shared list-entry markup used by the two list views.
- `assets/css/extended/readings.css` — all reading-list styling; loaded after the theme CSS.

Keep the homepage sparse: one heading, one entry per article, no cards or covers.

## Leftover template content

`content/books/`, `content/courses/`, `content/papers/`, `content/data/`,
`content/location.md`, `content/officehours.md` are Lorem-ipsum placeholders from the
upstream template. They are unlinked but still build and are publicly reachable.

## Checking a change

```
hugo server -D    # http://localhost:1313
hugo --gc --minify   # must finish with no ERROR lines
```

## Brand marks

The logo is a YH ligature: the Y's stem doubles as the H's left stem, with the
crossbar meeting it at the junction. It exists in two forms.

- **Bare** (ink, no background) — inner-page header via `params.label.iconSVG` in
  `config.yml`, and `static/logo.png` for the homepage profile, where the theme
  clips it to a circle and draws the hairline ring.
- **Boxed** (white on a slate-blue `#6a7ba2` tile) — the favicons only, because a
  hairline mark disappears in a 16px browser tab.

`scripts/make-icons.py` regenerates every raster from the same geometry. The header
SVG is hand-written in `config.yml` with the same coordinates — change one, change
the other.

Note that `layouts/_default/baseof.html` hides the header on the homepage, so the
homepage mark is the profile image, not the header logo.
