"""Chèn / thay mục Support chuẩn vào README của một repo.
python support_block.py <thư mục repo> <tên repo> [--dry]

- Nếu đã có khối <!-- support:start --> ... <!-- support:end --> thì thay khối đó.
- Nếu có mục cũ (tiêu đề ## chứa Support/Donate/Ủng hộ/Sponsor) thì thay cả mục đó
  (tới tiêu đề ## kế tiếp, hoặc tới dòng '---' cuối / hết file).
- Không có thì thêm vào cuối file, trước dòng chân trang 'MIT licensed…' nếu có.
README.vi.md (nếu có) nhận cùng khối với tiêu đề tiếng Việt.
"""
import re
import sys
from pathlib import Path

ASSET = "https://raw.githubusercontent.com/ngoviet/.github/main/assets/support"
START, END = "<!-- support:start -->", "<!-- support:end -->"


def block(repo, vi=False):
    title = "## Ủng hộ dự án" if vi else "## Support the project"
    return f"""{START}
{title}

<p align="center">
  <img src="{ASSET}/banner.svg" width="720" alt="Built and maintained by one person in Việt Nam">
</p>

<p align="center">
  <a href="https://buymeacoffee.com/ngoviet"><img src="{ASSET}/btn-coffee.svg" height="56" alt="Buy me a coffee"></a>
  &nbsp;
  <a href="https://github.com/sponsors/ngoviet"><img src="{ASSET}/btn-sponsors.svg" height="56" alt="GitHub Sponsors"></a>
</p>

<p align="center">
  <img src="{ASSET}/vietqr-card.svg" width="300" alt="VietQR — MB Bank — NGO DUC VIET — 911051212">
</p>

<p align="center"><sub>🇻🇳 VietQR: quét bằng app ngân hàng bất kỳ, nội dung <code>Ung ho {repo}</code>. Cảm ơn bạn! · Thank you for keeping this project alive.</sub></p>
{END}"""


HEAD = re.compile(r"^##\s+.*(support|donat|ủng hộ|ung ho|sponsor|buy me)", re.I)


def apply(text, repo, vi):
    new = block(repo, vi)
    if START in text and END in text:
        return re.sub(re.escape(START) + r".*?" + re.escape(END), lambda _: new, text, flags=re.S), "thay khối cũ"
    lines = text.split("\n")
    for i, ln in enumerate(lines):
        if HEAD.match(ln):
            j = i + 1
            while j < len(lines) and not lines[j].startswith("## "):
                j += 1
            # giữ lại '---' + chân trang nếu mục cũ là mục cuối
            k = j
            if j == len(lines):
                for t in range(i + 1, len(lines)):
                    if lines[t].strip() == "---":
                        k = t
            out = lines[:i] + new.split("\n") + [""] + lines[k:]
            return "\n".join(out), f"thay mục '{ln.strip()}'"
    # thêm cuối, trước chân trang license nếu có
    for t in range(len(lines) - 1, max(len(lines) - 6, -1), -1):
        if re.match(r"^(MIT|Apache|Licen[cs]ed|License)", lines[t].strip(), re.I) and t > 0:
            sep = t - 1 if lines[t - 1].strip() == "---" else t
            out = lines[:sep] + new.split("\n") + [""] + lines[sep:]
            return "\n".join(out), "thêm trước chân trang"
    return text.rstrip("\n") + "\n\n---\n\n" + new + "\n", "thêm cuối file"


root, repo = Path(sys.argv[1]), sys.argv[2]
dry = "--dry" in sys.argv
for name, vi in (("README.md", False), ("README.vi.md", True)):
    p = root / name
    if not p.exists():
        continue
    raw = p.read_bytes()
    crlf = b"\r\n" in raw
    text = raw.decode("utf-8-sig").replace("\r\n", "\n")
    out, how = apply(text, repo, vi)
    if not out.endswith("\n"):
        out += "\n"
    print(f"{repo}/{name}: {how}")
    if not dry and out != text:
        p.write_bytes((out.replace("\n", "\r\n") if crlf else out).encode("utf-8"))
