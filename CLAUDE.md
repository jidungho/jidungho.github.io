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
