"""Sinh bộ ảnh SVG mục "Support the project" cho lumentreeHA (bảng màu palette-axi neon-dark).
python make_support_svgs.py <thư mục đích>
"""
import io
import sys
from pathlib import Path

import segno
import zxingcpp
from PIL import Image

OUT = Path(sys.argv[1])
OUT.mkdir(parents=True, exist_ok=True)

# palette-axi generate --preset neon-dark (7/7 rules); nhãn dùng tông sáng do `contrast` gợi ý
C = dict(edge="#060a14", bg="#0a1122", surface="#0e182e", glow="#142443", border="#1e2b4a",
         dim="#a2b7d7", fg="#e6edf7", coffee="#f59e0b", coffee_t="#faa31a",
         pink="#f472b6", pink_t="#ff94c9", teal="#14b8a6", teal_t="#2dd4bf", cyan="#22d3ee")
FONT = "'Segoe UI', -apple-system, BlinkMacSystemFont, 'Helvetica Neue', Arial, sans-serif"
VIETQR = ("00020101021138570010A000000727012700069704220113VQRQAMTAF55920208QRIBFTTA"
          "53037045802VN62110107NPS68696304C843")

STYLE = f"""<style>
  text {{ font-family: {FONT}; }}
  .pulse {{ animation: pulse 3.2s ease-in-out infinite; }}
  @keyframes pulse {{ 0%,100% {{ opacity: .55; }} 50% {{ opacity: 1; }} }}
  @media (prefers-reduced-motion: reduce) {{ .pulse {{ animation: none; opacity: .8; }} }}
</style>"""


def defs(*accents):
    glows = "".join(
        f'<filter id="glow-{n}" x="-30%" y="-60%" width="160%" height="220%">'
        f'<feGaussianBlur stdDeviation="4" result="b"/>'
        f'<feFlood flood-color="{c}" flood-opacity=".55"/><feComposite in2="b" operator="in"/>'
        f'<feMerge><feMergeNode/><feMergeNode in="SourceGraphic"/></feMerge></filter>'
        for n, c in accents)
    return (f'<defs><radialGradient id="bgg" cx="20%" cy="0%" r="120%">'
            f'<stop offset="0" stop-color="{C["glow"]}"/><stop offset=".55" stop-color="{C["bg"]}"/>'
            f'<stop offset="1" stop-color="{C["edge"]}"/></radialGradient>{glows}</defs>')


def write(name, w, h, body, title):
    svg = (f'<svg xmlns="http://www.w3.org/2000/svg" width="{w}" height="{h}" viewBox="0 0 {w} {h}" '
           f'role="img" aria-label="{title}"><title>{title}</title>{STYLE}{body}</svg>\n')
    (OUT / name).write_text(svg, encoding="utf-8")
    print(f"{name}: {len(svg.encode())} B")


# ---------- banner ----------
W, H = 820, 170
body = defs(("c", C["cyan"]))
body += f'<rect x="1" y="1" width="{W-2}" height="{H-2}" rx="18" fill="url(#bgg)" stroke="{C["border"]}" stroke-width="2"/>'
body += f'<rect class="pulse" x="1" y="1" width="{W-2}" height="{H-2}" rx="18" fill="none" stroke="{C["cyan"]}" stroke-opacity=".35" stroke-width="1.5"/>'
body += (f'<text x="{W/2}" y="58" text-anchor="middle" font-size="27" font-weight="700" fill="{C["fg"]}">'
         f'Built &amp; maintained by one person in Việt Nam</text>')
body += (f'<text x="{W/2}" y="92" text-anchor="middle" font-size="17" fill="{C["dim"]}">'
         f'Một người Việt tự xây dựng và duy trì — miễn phí, mã nguồn mở</text>')
body += (f'<text x="{W/2}" y="134" text-anchor="middle" font-size="16" fill="{C["dim"]}">'
         f'Your support pays for: <tspan fill="{C["cyan"]}" font-weight="600">new device support</tspan>'
         f' · <tspan fill="{C["cyan"]}" font-weight="600">faster fixes</tspan>'
         f' · <tspan fill="{C["cyan"]}" font-weight="600">every Home Assistant release</tspan></text>')
write("banner.svg", W, H, body, "Built and maintained by one person in Viet Nam")


# ---------- buttons ----------
def button(name, label, sub, accent, accent_t, icon, title):
    w, h = 300, 64
    b = defs(("a", accent))
    b += f'<rect x="1.5" y="1.5" width="{w-3}" height="{h-3}" rx="14" fill="{C["surface"]}" stroke="{accent}" stroke-width="2" filter="url(#glow-a)"/>'
    b += f'<g transform="translate(22 16)" fill="none" stroke="{accent_t}" stroke-width="2.2" stroke-linecap="round" stroke-linejoin="round">{icon}</g>'
    b += f'<text x="70" y="30" font-size="19" font-weight="700" fill="{accent_t}">{label}</text>'
    b += f'<text x="70" y="49" font-size="13" fill="{C["dim"]}">{sub}</text>'
    write(name, w, h, b, title)


CUP = ('<path d="M2 8h20v9a7 7 0 0 1-7 7H9a7 7 0 0 1-7-7z"/><path d="M22 11h3a3 3 0 0 1 0 6h-3"/>'
       '<path class="pulse" d="M8 1c-1 2 1 3 0 5M13 1c-1 2 1 3 0 5M18 1c-1 2 1 3 0 5"/>')
HEART = ('<path d="M14 26S2 18.5 2 10.5A6 6 0 0 1 14 7a6 6 0 0 1 12 3.5C26 18.5 14 26 14 26z"/>')
button("btn-coffee.svg", "Buy me a coffee", "Card · one-time or monthly", C["coffee"], C["coffee_t"], CUP, "Buy me a coffee")
button("btn-sponsors.svg", "GitHub Sponsors", "Monthly or one-time · 0% fees", C["pink"], C["pink_t"], HEART, "GitHub Sponsors")


# ---------- VietQR card ----------
qr = segno.make(VIETQR, error="m")
# Kiểm tra vòng: render PNG từ đúng ma trận này rồi giải mã lại
buf = io.BytesIO()
qr.save(buf, kind="png", scale=8, border=4)
decoded = zxingcpp.read_barcodes(Image.open(io.BytesIO(buf.getvalue())))
assert decoded and decoded[0].text == VIETQR, "QR vẽ lại không giải mã ra đúng payload"
print("QR round-trip OK, version", qr.version, qr.designator)

n = qr.symbol_size(border=0)[0]
mod = 7
qsize = n * mod
pad = 18                      # quiet zone (>= 2.5 module) trên nền trắng
W = qsize + 2 * pad + 56
H = 120 + qsize + 2 * pad + 118
qx, qy = (W - qsize) / 2, 108 + pad
rects = "".join(f'<rect x="{qx + c*mod}" y="{qy + r*mod}" width="{mod}" height="{mod}"/>'
                for r, row in enumerate(qr.matrix) for c, v in enumerate(row) if v)
body = defs(("t", C["teal"]))
body += f'<rect x="1.5" y="1.5" width="{W-3}" height="{H-3}" rx="20" fill="url(#bgg)" stroke="{C["teal"]}" stroke-width="2" filter="url(#glow-t)"/>'
body += f'<text x="{W/2}" y="46" text-anchor="middle" font-size="24" font-weight="700" fill="{C["teal_t"]}">VietQR</text>'
body += f'<text x="{W/2}" y="74" text-anchor="middle" font-size="15" fill="{C["dim"]}">Chuyển khoản trong nước · miễn phí</text>'
body += f'<rect x="{qx-pad}" y="{qy-pad}" width="{qsize+2*pad}" height="{qsize+2*pad}" rx="12" fill="#ffffff"/>'
body += f'<g fill="{C["bg"]}" shape-rendering="crispEdges">{rects}</g>'
ty = qy + qsize + pad + 36
body += f'<text x="{W/2}" y="{ty}" text-anchor="middle" font-size="17" font-weight="600" fill="{C["fg"]}">MB Bank · NGO DUC VIET</text>'
body += f'<text x="{W/2}" y="{ty+26}" text-anchor="middle" font-size="16" fill="{C["dim"]}">STK <tspan fill="{C["teal_t"]}" font-weight="600">911051212</tspan></text>'
body += f'<text x="{W/2}" y="{ty+54}" text-anchor="middle" font-size="14" fill="{C["dim"]}">Nội dung: <tspan fill="{C["fg"]}">Ung ho + tên dự án</tspan></text>'
write("vietqr-card.svg", W, H, body, "VietQR MB Bank NGO DUC VIET 911051212")
