# readme-axi

Checks that a repository's `README.md` (English) and `README.vi.md` (Vietnamese) follow the shared
ngoviet layout and stay in step with each other. One file, Python standard library only, output in
[TOON](https://toonformat.dev/) for agents; exit code 0 = pass, 1 = issues, 2 = bad usage.

```bash
python3 readme_axi.py check [dir]            # layout, switcher line, required sections, EN/VI parity, support block
python3 readme_axi.py drift [dir] [--strict] # README.md commits not yet ported to README.vi.md
python3 readme_axi.py support [dir] --write  # insert/refresh the shared "Support the project" block
python3 readme_axi.py scaffold --type ha --title "Name for Home Assistant"
python3 readme_axi.py names                  # canonical section names EN -> VI and required order
```

## The layout

Every README starts the same way:

1. `# Title` on the first line, then `<!-- readme-axi type=ha|card|esp32|tool -->`.
2. Badges, then the language switcher — `**English** · [Tiếng Việt](README.vi.md)` in README.md,
   `[English](README.md) · **Tiếng Việt**` in README.vi.md.
3. One paragraph: what it does, for which device. Optional install button, one-line support callout,
   screenshot.

and ends the same way: the shared support block, then `## License` / `## Giấy phép`
(`MIT © Ngô Đức Việt`, plus "Not affiliated with …" when the project targets a vendor's device).

Required `##` sections, in this order (others may sit in between):

| Type | Required |
|---|---|
| `ha` integration | Features · Installation · Configuration · Entities · Troubleshooting · Development |
| `card` Lovelace card / theme | Features · Installation · Usage |
| `esp32` ESPHome device | Features · Hardware · Quick start · Home Assistant |
| `tool` CLI / notes | Installation · Usage |

Both files have the same number of `##` sections, in the same order, with the canonical names
(`readme_axi.py names`). Headings carry no emoji, so anchors stay clean.

## CI

Each public repository calls the reusable workflow in this repo:

```yaml
# .github/workflows/readme.yml
name: README
on:
  push:
    paths: [README.md, README.vi.md]
  pull_request:
    paths: [README.md, README.vi.md]
jobs:
  readme:
    uses: ngoviet/.github/.github/workflows/readme.yml@main
```

---

# readme-axi (Tiếng Việt)

Kiểm tra `README.md` (tiếng Anh) và `README.vi.md` (tiếng Việt) của một repo có theo khung chung của
ngoviet và khớp nhau không. Một tệp, chỉ dùng thư viện chuẩn Python, output TOON; mã thoát 0 = đạt,
1 = có lỗi, 2 = sai cách gọi. Lệnh và khung như phần tiếng Anh ở trên; `names` in bảng tên mục Anh → Việt.
