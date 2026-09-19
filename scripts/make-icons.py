#!/usr/bin/env python3
"""Regenerate the site's icon set from the YH monogram.

The monogram is a ligature: the Y's stem doubles as the H's left stem, and the
crossbar meets it at the junction. The header uses an inline SVG of the same
geometry (params.label.iconSVG in config.yml) - keep the two in sync if you
change the coordinates below.

    python3 scripts/make-icons.py

Writes static/logo.png, static/favicon{.ico,-16x16.png,-32x32.png} and
static/apple-touch-icon.png. Requires Pillow.
"""
from PIL import Image, ImageDraw

SS = 12                      # supersample factor, downsampled with LANCZOS
ACCENT = (106, 123, 162, 255)  # --darkcolor #6a7ba2
INK = (30, 30, 30, 255)        # --primary
WHITE = (255, 255, 255, 255)
STATIC = "static/"

# Paths on a 24-unit grid. The bare mark occupies x 2.6-18.4, the boxed one is
# inset to leave room for the tile edge.
BARE = [[(2.6, 3.2), (8.2, 11.2), (13.8, 3.2)],
        [(8.2, 11.2), (8.2, 20.8)],
        [(18.4, 3.2), (18.4, 20.8)],
        [(8.2, 11.2), (18.4, 11.2)]]
BOXED = [[(4.2, 5.4), (8.6, 11.4), (13.0, 5.4)],
         [(8.6, 11.4), (8.6, 18.6)],
         [(19.0, 5.4), (19.0, 18.6)],
         [(8.6, 11.4), (19.0, 11.4)]]
STROKE = 2.9


def _draw(d, strokes, scale, offset, width, color):
    ox, oy = offset
    for path in strokes:
        pts = [(ox + x * scale, oy + y * scale) for x, y in path]
        d.line(pts, fill=color, width=int(round(width)), joint="curve")
        for x, y in pts:  # round caps
            d.ellipse([x - width / 2, y - width / 2,
                       x + width / 2, y + width / 2], fill=color)


def tile(size, radius=6.0, pad=0.0, bg=ACCENT):
    """Boxed monogram: white mark on an accent tile. pad insets the glyph."""
    n = size * SS
    k = n / 24.0
    im = Image.new("RGBA", (n, n), (0, 0, 0, 0))
    d = ImageDraw.Draw(im)
    if radius > 0:
        d.rounded_rectangle([0, 0, n - 1, n - 1], radius=radius * k, fill=bg)
    else:
        d.rectangle([0, 0, n - 1, n - 1], fill=bg)
    shrunk = [[(((x - 12) * (1 - pad) + 12), ((y - 12) * (1 - pad) + 12))
               for x, y in path] for path in BOXED]
    _draw(d, shrunk, k, (0, 0), STROKE * (1 - pad) * k, WHITE)
    return im.resize((size, size), Image.LANCZOS)


def bare(size, glyph_frac=0.43, color=INK):
    """Transparent square holding just the mark; the theme adds the ring."""
    n = size * SS
    k = (n * glyph_frac) / 24.0
    im = Image.new("RGBA", (n, n), (0, 0, 0, 0))
    _draw(ImageDraw.Draw(im), BARE, k,
          ((n - 21 * k) / 2, (n - 24 * k) / 2), STROKE * k, color)
    return im.resize((size, size), Image.LANCZOS)


if __name__ == "__main__":
    bare(320).save(STATIC + "logo.png")                  # homepage profile
    tile(16).save(STATIC + "favicon-16x16.png")
    tile(32).save(STATIC + "favicon-32x32.png")
    tile(180, radius=0, pad=0.18).save(STATIC + "apple-touch-icon.png")  # iOS rounds it itself
    tile(64).save(STATIC + "favicon.ico", format="ICO",
                  sizes=[(16, 16), (32, 32), (48, 48), (64, 64)])
    print("wrote logo.png, favicon.ico, favicon-16x16.png, "
          "favicon-32x32.png, apple-touch-icon.png")
