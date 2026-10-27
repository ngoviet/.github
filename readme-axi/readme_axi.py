#!/usr/bin/env python3
"""readme-axi — kiểm tra README song ngữ Anh – Việt theo khung chung của ngoviet.

Lệnh:
  readme_axi.py [check] [dir] [--type ha|card|esp32|tool]   kiểm tra README.md + README.vi.md
  readme_axi.py drift [dir] [--strict]                      README.md đổi mà README.vi.md chưa theo
  readme_axi.py support [dir] [--repo name] [--write]       chèn/thay khối Ủng hộ chung (mặc định chỉ xem)
  readme_axi.py scaffold [dir] --type T --title "..." [--repo name] [--force]
Mã thoát: 0 = đạt, 1 = có lỗi, 2 = sai cách gọi. Output dạng TOON.
Chỉ dùng thư viện chuẩn để workflow tải về một tệp là chạy được.
"""
import os
import re
import subprocess
import sys
from pathlib import Path

VERSION = "0.1.0"
EN, VI = "README.md", "README.vi.md"
SWITCH_EN = "**English** · [Tiếng Việt](README.vi.md)"
SWITCH_VI = "[English](README.md) · **Tiếng Việt**"
TYPE_RE = re.compile(r"<!--\s*readme-axi\s+type=(\w+)\s*-->")
START, END = "<!-- support:start -->", "<!-- support:end -->"
ASSET = "https://raw.githubusercontent.com/ngoviet/.github/main/assets/support"
BEP20 = "0xcbf0402b232cb24b4d998f09a4884f87b5f74750"

# tên mục chuẩn: EN -> VI
NAMES = {
    "Contents": "Mục lục", "Features": "Tính năng", "Supported devices": "Thiết bị hỗ trợ",
    "Requirements": "Yêu cầu", "Installation": "Cài đặt", "Configuration": "Cấu hình",
    "Entities": "Thực thể", "Services": "Dịch vụ", "Troubleshooting": "Xử lý sự cố",
    "How it works": "Cách hoạt động", "Development": "Phát triển", "Usage": "Cách dùng",
    "Options": "Tuỳ chọn", "Hardware": "Phần cứng", "Quick start": "Bắt đầu nhanh",
    "Home Assistant": "Home Assistant", "Project layout": "Cấu trúc dự án", "Commands": "Lệnh",
    "Support the project": "Ủng hộ dự án", "License": "Giấy phép",
}
# mục bắt buộc theo loại repo, đúng thứ tự (mục khác được chen vào giữa)
REQUIRED = {
    "ha": ["Features", "Installation", "Configuration", "Entities", "Troubleshooting", "Development"],
    "card": ["Features", "Installation", "Usage"],
    "esp32": ["Features", "Hardware", "Quick start", "Home Assistant"],
    "tool": ["Installation", "Usage"],
}
EMOJI = re.compile("[\U0001F000-\U0001FAFF☀-➿⬀-⯿⌀-⏿️‍�]")


def toon(v):
    s = str(v)
    return '"' + s.replace('"', "'") + '"' if re.search(r'[,:"\n]|^\s|\s$', s) or s == "" else s


def table(name, fields, rows):
    out = [f"{name}[{len(rows)}]{{{','.join(fields)}}}:"]
    out += ["  " + ",".join(toon(r[f]) for f in fields) for r in rows]
    return out


def die(msg, code=2, hint=None):
    print(f"error: {msg}")
    print(f"code: {'USAGE' if code == 2 else 'FAILED'}")
    if hint:
        print(f"help[1]:\n  {hint}")
    sys.exit(code)


def read(p):
    return p.read_bytes().decode("utf-8-sig").replace("\r\n", "\n")


def headings(text):
    """(cấp, chữ, số dòng) của các tiêu đề, bỏ qua dòng trong code block."""
    out, fence = [], None
    for i, ln in enumerate(text.split("\n"), 1):
        m = re.match(r"^\s*(```+|~~~+)", ln)
        if m:
            tok = m.group(1)[0] * 3
            fence = None if fence == tok else (fence or tok)
            continue
        if fence:
            continue
        m = re.match(r"^(#{1,6})\s+(.*?)\s*#*\s*$", ln)
        if m:
            out.append((len(m.group(1)), m.group(2), i))
    return out


def detect_type(text):
    m = TYPE_RE.search(text)
    return m.group(1) if m else None


# ---------- check ----------

def check(root, forced_type=None):
    issues = []

    def add(f, rule, detail):
        issues.append({"file": f, "rule": rule, "detail": detail})

    files = {}
    for f in (EN, VI):
        p = root / f
        if p.exists():
            files[f] = read(p)
        else:
            add(f, "missing", "tệp không có")
    rtype = forced_type
    for f, text in files.items():
        t = detect_type(text)
        if not t:
            add(f, "type-marker", "thiếu dòng <!-- readme-axi type=ha|card|esp32|tool -->")
        elif t not in REQUIRED:
            add(f, "type-marker", f"loại lạ: {t}")
        rtype = rtype or t
    if EN in files and VI in files and detect_type(files[EN]) != detect_type(files[VI]):
        add(VI, "type-marker", "loại khác với README.md")

    heads = {}
    for f, text in files.items():
        vi = f == VI
        hs = headings(text)
        h1 = [h for h in hs if h[0] == 1]
        if len(h1) != 1 or not text.lstrip().startswith("# "):
            add(f, "h1", f"cần đúng 1 tiêu đề # ở dòng đầu (đang có {len(h1)})")
        top = "\n".join(text.split("\n")[:15])
        if (SWITCH_VI if vi else SWITCH_EN) not in top:
            add(f, "switcher", f"thiếu dòng chuyển ngôn ngữ trong 15 dòng đầu: {SWITCH_VI if vi else SWITCH_EN}")
        h2 = [h for h in hs if h[0] == 2]
        heads[f] = h2
        for _, t, ln in hs:
            if EMOJI.search(t):
                add(f, "emoji-heading", f"dòng {ln}: {t}")
        names = [t for _, t, _ in h2]
        want = [NAMES[n] if vi else n for n in REQUIRED.get(rtype, [])]
        pos = -1
        for w in want:
            if w not in names:
                add(f, "section", f"thiếu mục ## {w}")
            elif names.index(w) < pos:
                add(f, "order", f"## {w} sai thứ tự")
            else:
                pos = names.index(w)
        lic = NAMES["License"] if vi else "License"
        sup = NAMES["Support the project"] if vi else "Support the project"
        if lic not in names:
            add(f, "section", f"thiếu mục ## {lic}")
        elif names[-1] != lic:
            add(f, "order", f"## {lic} phải là mục cuối")
        if text.count(START) != 1 or text.count(END) != 1:
            add(f, "support", f"cần đúng một khối {START} … {END}")
        else:
            blk = text[text.index(START):text.index(END) + len(END)]
            if blk != support_block(root.resolve().name, vi):
                add(f, "support", f"khối ## {sup} khác mẫu chung")
            if lic in names and text.index(START) > text.index(f"## {lic}"):
                add(f, "order", f"khối Ủng hộ phải đứng trước ## {lic}")
    if EN in heads and VI in heads and len(heads[EN]) != len(heads[VI]):
        add(VI, "parity", f"số mục ## khác nhau: EN {len(heads[EN])}, VI {len(heads[VI])}")
    return rtype, heads, issues


def cmd_check(root, forced_type):
    rtype, heads, issues = check(root, forced_type)
    print(f"repo: {toon(root.resolve().name)}")
    print(f"type: {rtype or 'unknown'}")
    en, vi = heads.get(EN, []), heads.get(VI, [])
    rows = [{"n": i + 1, "en": en[i][1] if i < len(en) else "-", "vi": vi[i][1] if i < len(vi) else "-"}
            for i in range(max(len(en), len(vi)))]
    print("\n".join(table("sections", ["n", "en", "vi"], rows)) if rows else "sections: 0 results")
    print(f"result: {'pass' if not issues else 'fail'}, {len(issues)} issues")
    if issues:
        print("\n".join(table("issues", ["file", "rule", "detail"], issues)))
        hints = []
        if any(i["rule"] == "support" for i in issues):
            hints.append("Run `readme_axi.py support --write` to insert the shared support block")
        if any(i["rule"] == "missing" for i in issues):
            hints.append("Run `readme_axi.py scaffold --type <ha|card|esp32|tool> --title \"<name>\"` for a skeleton")
        hints.append("Section names (EN -> VI) are listed by `readme_axi.py names`")
        print(f"help[{len(hints)}]:")
        for h in hints:
            print(f"  {h}")
    else:
        print("help[1]:\n  Run `readme_axi.py drift` to see whether README.vi.md lags behind README.md")
    return 1 if issues else 0


# ---------- drift ----------

def git(root, *a):
    r = subprocess.run(["git", "-C", str(root), *a], capture_output=True, text=True, encoding="utf-8")
    if r.returncode:
        die(f"git {' '.join(a[:2])}: {r.stderr.strip()[:200]}", 1)
    return r.stdout.strip()


def cmd_drift(root, strict):
    last_vi = git(root, "log", "-1", "--format=%H", "--", VI)
    if not last_vi:
        die("README.vi.md chưa có trong lịch sử git", 1, "Commit README.vi.md first")
    behind = git(root, "log", "--format=%h %s", f"{last_vi}..HEAD", "--", EN).splitlines()
    print(f"repo: {toon(root.resolve().name)}")
    print(f"last_vi_commit: {last_vi[:8]}")
    if behind:
        rows = [{"commit": b.split(" ", 1)[0], "subject": (b.split(" ", 1) + [""])[1][:80]} for b in behind]
        print("\n".join(table("en_commits_since", ["commit", "subject"], rows)))
        print(f"result: drift, README.md changed in {len(behind)} commits after README.vi.md")
        print("help[1]:\n  Port these README.md changes into README.vi.md, then commit both")
        return 1 if strict else 0
    print("en_commits_since: 0 results")
    print("result: in sync")
    return 0


# ---------- support ----------

def support_block(repo, vi):
    if vi:
        title, note = "## Ủng hộ dự án", (f"🇻🇳 VietQR: quét bằng app ngân hàng bất kỳ, nội dung <code>Ung ho {repo}</code>. "
                                          "Cảm ơn bạn đã giúp dự án tiếp tục phát triển!")
        crypto = "Ví tiền mã hoá, chỉ gửi qua mạng BNB Smart Chain (BEP20)"
    else:
        title, note = "## Support the project", (f"🇻🇳 VietQR: scan with any Vietnamese banking app, transfer note "
                                                 f"<code>Ung ho {repo}</code>. Thank you for keeping this project alive!")
        crypto = "Crypto wallet, BNB Smart Chain (BEP20) only"
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
  &nbsp;
  <img src="{ASSET}/crypto-card.svg" width="300" alt="Crypto — BNB Smart Chain (BEP20) — {BEP20}">
</p>

<p align="center"><b>{crypto}:</b><br><code>{BEP20}</code></p>

<p align="center"><sub>{note}</sub></p>
{END}"""


def place_support(text, repo, vi):
    new = support_block(repo, vi)
    if START in text and END in text:
        return re.sub(re.escape(START) + r".*?" + re.escape(END), lambda _: new, text, flags=re.S), "replaced"
    lines = text.rstrip("\n").split("\n")
    lic = "## " + (NAMES["License"] if vi else "License")
    for i, ln in enumerate(lines):
        if ln.strip() == lic:
            return "\n".join(lines[:i] + new.split("\n") + [""] + lines[i:]) + "\n", "inserted"
    return "\n".join(lines) + "\n\n" + new + "\n", "appended"


def cmd_support(root, repo, write):
    rows = []
    for f, vi in ((EN, False), (VI, True)):
        p = root / f
        if not p.exists():
            rows.append({"file": f, "action": "skipped (missing)"})
            continue
        raw = p.read_bytes()
        text = read(p)
        out, how = place_support(text, repo, vi)
        changed = out != text
        if write and changed:
            p.write_bytes((out.replace("\n", "\r\n") if b"\r\n" in raw else out).encode("utf-8"))
        rows.append({"file": f, "action": how if changed else "unchanged"})
    print(f"repo: {toon(repo)}")
    print("\n".join(table("support", ["file", "action"], rows)))
    print(f"mode: {'written' if write else 'dry run'}")
    if not write:
        print("help[1]:\n  Add --write to apply")
    return 0


# ---------- scaffold ----------

SCAFFOLD_BODY = {
    "ha": ["Features", "Supported devices", "Requirements", "Installation", "Configuration", "Entities",
           "Troubleshooting", "Development"],
    "card": ["Features", "Installation", "Usage", "Options", "Development"],
    "esp32": ["Features", "Hardware", "Quick start", "Home Assistant", "Configuration", "Troubleshooting",
              "Project layout"],
    "tool": ["Installation", "Usage", "Commands", "Development"],
}


def cmd_scaffold(root, rtype, title, repo, force):
    if rtype not in SCAFFOLD_BODY:
        die("--type phải là ha, card, esp32 hoặc tool")
    if not title:
        die("thiếu --title")
    made = []
    for f, vi in ((EN, False), (VI, True)):
        p = root / f
        if p.exists() and not force:
            made.append({"file": f, "action": "exists (use --force)"})
            continue
        body = [f"# {title}", "", f"<!-- readme-axi type={rtype} -->", "", SWITCH_VI if vi else SWITCH_EN, "",
                "Một câu: làm gì, cho thiết bị nào." if vi else "One sentence: what it does, for which device.", ""]
        for n in SCAFFOLD_BODY[rtype]:
            body += [f"## {NAMES[n] if vi else n}", "", "TODO", ""]
        body += [support_block(repo, vi), "", f"## {NAMES['License'] if vi else 'License'}", "",
                 "[MIT](LICENSE) © Ngô Đức Việt", ""]
        p.write_text("\n".join(body), encoding="utf-8")
        made.append({"file": f, "action": "written"})
    print("\n".join(table("scaffold", ["file", "action"], made)))
    print("help[1]:\n  Fill the TODO sections, then run `readme_axi.py check`")
    return 0


def cmd_names():
    rows = [{"en": k, "vi": v} for k, v in NAMES.items()]
    print("\n".join(table("names", ["en", "vi"], rows)))
    req = [{"type": t, "required": " > ".join(r) + " > Support the project > License"} for t, r in REQUIRED.items()]
    print("\n".join(table("required", ["type", "required"], req)))
    return 0


def main(argv):
    if "--version" in argv:
        print(f"readme-axi {VERSION}")
        return 0
    if "--help" in argv or "-h" in argv:
        print(__doc__.strip())
        return 0
    cmds = {"check", "drift", "support", "scaffold", "names"}
    cmd = argv[0] if argv and argv[0] in cmds else "check"
    rest = argv[1:] if argv and argv[0] in cmds else argv
    opts, pos, i = {}, [], 0
    flags = {"--type", "--title", "--repo"}
    bools = {"--write", "--force", "--strict"}
    while i < len(rest):
        a = rest[i]
        if a in flags:
            if i + 1 >= len(rest):
                die(f"{a} cần giá trị")
            opts[a] = rest[i + 1]
            i += 2
        elif a in bools:
            opts[a] = True
            i += 1
        elif a.startswith("-"):
            die(f"cờ lạ: {a}", 2, "Run `readme_axi.py --help`")
        else:
            pos.append(a)
            i += 1
    root = Path(pos[0]) if pos else Path(".")
    if not root.is_dir():
        die(f"không phải thư mục: {root}")
    repo = opts.get("--repo") or root.resolve().name
    if cmd == "check":
        return cmd_check(root, opts.get("--type"))
    if cmd == "drift":
        return cmd_drift(root, opts.get("--strict", False))
    if cmd == "support":
        return cmd_support(root, repo, opts.get("--write", False))
    if cmd == "scaffold":
        return cmd_scaffold(root, opts.get("--type"), opts.get("--title"), repo, opts.get("--force", False))
    return cmd_names()


if __name__ == "__main__":
    try:
        sys.stdout.reconfigure(encoding="utf-8")
    except AttributeError:
        pass
    sys.exit(main(sys.argv[1:]))
