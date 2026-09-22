# jidungho.github.io

Personal site. Hugo + PaperMod, deployed to GitHub Pages by `.github/workflows/hugo.yml` on push to `main`.

## Two sections

- **Readings** (`content/readings/`) — someone else's article: source link + one-paragraph summary.
- **Learning** (`content/learning/`) — something I built or worked through myself: a write-up with
  code, results, and the scripts attached. Each entry is a page bundle (a folder with `index.md`).

The homepage shows Learning first, then Readings.

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

## Adding a learning entry

```
hugo new --kind learning learning/<slug>/index.md
```

Put the summary paragraph before `<!--more-->` and the write-up after it. Copy any scripts into
the bundle folder and link them relatively (`[step1.py](step1.py)`); Hugo publishes them next to
the page. Published copies are for readers: strip debug prints, fix stale paths, and say so.

Numbers in a write-up get re-run before publishing, not copied from a README, and any "X beats Y"
claim states what exactly was compared.

## Layout

- `layouts/index.html` — homepage: compact profile card, then Learning and Readings, N most recent each (`params.homeEntries`, default 10).
- `layouts/{learning,readings}/list.html` — `/learning/` and `/readings/`, the full lists.
- `layouts/readings/single.html` — one reading: title, source link, summary, notes, tags.
  Learning entries use the default `layouts/_default/single.html`.
- `layouts/partials/entry.html` — shared list-entry markup. With `source` set it shows
  author · source date · link; without, the date it was written.
- `assets/css/extended/readings.css` — all list styling (the `.reading*` classes serve both sections).

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
