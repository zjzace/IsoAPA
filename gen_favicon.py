from PIL import Image, ImageDraw

TEAL   = (13, 115, 119, 255)
WHITE  = (255, 255, 255, 255)
TRANSP = (0, 0, 0, 0)
VIEWBOX = 24

SPINE    = ((4, 5), (4, 19))
ISOFORMS = [
    ((4, 8),  (20, 8),  20, 8,  2),
    ((4, 12), (14, 12), 14, 12, 2),
    ((4, 16), (9,  16), 9,  16, 2),
]


def draw_icon(size):
    pad   = size * 0.08
    inner = size - 2 * pad
    img   = Image.new("RGBA", (size, size), TRANSP)
    draw  = ImageDraw.Draw(img)
    draw.rounded_rectangle([0, 0, size - 1, size - 1], radius=size * 0.22, fill=TEAL)

    sw = max(1.0, (size / VIEWBOX) * 2)

    def tx(x): return pad + (x / VIEWBOX) * inner
    def ty(y): return pad + (y / VIEWBOX) * inner
    def rr(r): return r * (inner / VIEWBOX)

    draw.line([(tx(4), ty(5)), (tx(4), ty(19))], fill=WHITE, width=max(1, round(sw)))
    for (lx0, ly0), (lx1, ly1), cx, cy, cr in ISOFORMS:
        draw.line([(tx(lx0), ty(ly0)), (tx(lx1), ty(ly1))], fill=WHITE, width=max(1, round(sw)))
        pcx, pcy, pcr = tx(cx), ty(cy), rr(cr)
        draw.ellipse([pcx - pcr, pcy - pcr, pcx + pcr, pcy + pcr], fill=WHITE)

    return img


sizes  = [256, 128, 64, 48, 32, 16]
frames = [draw_icon(s) for s in sizes]

out = "frontend/public/favicon.ico"
frames[0].save(out, format="ICO", sizes=[(s, s) for s in sizes], append_images=frames[1:])
print(f"Saved {out}  ({', '.join(str(s) for s in reversed(sizes))} px)")
