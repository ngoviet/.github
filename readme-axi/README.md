# readme-axi

Checks that a repository's `README.md` (English) and `README.vi.md` (Vietnamese) follow the shared
ngoviet layout and stay in step with each other. One file, Python standard library only, output in
[TOON](https://toonformat.dev/) for agents; exit code 0 = pass, 1 = issues, 2 = bad usage.

```bash
python3 readme_axi.py check [dir]            # layout, switcher line, required sections, EN/VI parity, support block
python3 readme_axi.py drift [dir] [--strict] # README.md commits not yet ported to README.vi.md
python3 readme_axi.py support [dir] --write  # insert/refresh the shared "Support the project" block
python3 readme_axi.py scaffold --type ha --title "Name for Home Assistant"
python3 readme_axi.py scaffold --type ops --title "nas" --private   # private repo skeleton
python3 readme_axi.py names                  # canonical section names EN -> VI and required order
```

## The layout

Every README starts the same way:

1. `# Title` on the first line, then the marker `<!-- readme-axi type=<type> -->`
   (`<!-- readme-axi type=<type> private -->` in a private repository).
2. Badges, then the language switcher — `**English** · [Tiếng Việt](README.vi.md)` in README.md,
   `[English](README.md) · **Tiếng Việt**` in README.vi.md.
3. One paragraph: what it does, for which device. Optional install button, one-line support callout,
   screenshot.

and, in a public repository, ends the same way: the shared support block, then `## License` / `## Giấy phép`
(`[MIT](LICENSE) © Ngô Đức Việt`, plus "Not affiliated with …" when the project targets a vendor's device).

Required `##` sections, in this order (others may sit in between):

| Type | Required |
|---|---|
| `ha` integration | Features · Installation · Configuration · Entities · Troubleshooting · Development |
| `card` Lovelace card / theme | Features · Installation · Usage |
| `esp32` ESPHome device | Features · Hardware · Quick start · Home Assistant |
| `tool` CLI / library | Installation · Usage |
| `app` web app / service | Features · Development · Deployment |
| `ops` operations repo (scripts, servers) | Usage · Project layout |
| `config` configuration repo | Project layout · Deployment |
| `docs` documents, notes | Project layout |

Both files have the same number of `##` sections, in the same order, with the canonical names
(`readme_axi.py names`). Headings carry no emoji, so anchors stay clean.

The support block carries the repository name. It comes from `--repo`, then from the `origin` remote,
then from the folder name, so a worktree or a temporary clone checks against the right name.

## Private repositories

Add `private` to the marker: `<!-- readme-axi type=ops private -->`, in both files. A private repository
keeps the bilingual layout (title and marker, switcher, intro, type sections, canonical names, EN/VI
parity, no emoji, `drift`) but needs no support block and no `## License`: nobody else reads it and the
code is not MIT licensed. `support --write` leaves a private repository alone.

When the repository goes public, drop `private` from the marker; `check` then lists what is missing
(support block, License).

## CI

Each public repository calls the reusable workflow in this repo (GitHub Actions):

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

Private repositories run on the self-hosted Woodpecker at https://ci.bepmamnon.com (GitHub Actions
has no minutes left for private repositories). The repository must be enabled there and carry this file:

```yaml
# .woodpecker/readme.yaml
when:
  - event: pull_request
    path: [README.md, README.vi.md, .woodpecker/readme.yaml]
  - event: push
    branch: main
    path: [README.md, README.vi.md, .woodpecker/readme.yaml]
  - event: manual

clone:
  - name: clone
    image: woodpeckerci/plugin-git
    settings:
      partial: false # drift reads git history: full clone, not shallow
      depth: 0

steps:
  - name: readme
    image: python:3.13-bookworm # python3, git and curl included
    commands:
      - git config --global --add safe.directory "$CI_WORKSPACE"
      - curl -fsSL https://raw.githubusercontent.com/ngoviet/.github/main/readme-axi/readme_axi.py -o /tmp/readme_axi.py
      - python3 /tmp/readme_axi.py check
      - python3 /tmp/readme_axi.py drift
```

This repository (`.github`) is public, so the download needs no token.

## Tests

```bash
python3 -m unittest discover -s readme-axi -v
```

The tests run the CLI on temporary READMEs (and temporary git repositories for `drift` and the
repository name).

---

# readme-axi (Tiếng Việt)

Kiểm tra `README.md` (tiếng Anh) và `README.vi.md` (tiếng Việt) của một repo có theo khung chung của
ngoviet và khớp nhau không. Một tệp, chỉ dùng thư viện chuẩn Python, output TOON; mã thoát 0 = đạt,
1 = có lỗi, 2 = sai cách gọi. Lệnh và khung như phần tiếng Anh ở trên; `names` in bảng tên mục Anh → Việt.

Loại repo: `ha`, `card`, `esp32`, `tool` như trước, thêm `app` (web app, dịch vụ: Tính năng · Phát triển ·
Triển khai), `ops` (repo vận hành: Cách dùng · Cấu trúc dự án), `config` (repo cấu hình: Cấu trúc dự án ·
Triển khai) và `docs` (kho tài liệu: Cấu trúc dự án).

Repo private: thêm chữ `private` vào dấu ở cả hai tệp, vd `<!-- readme-axi type=ops private -->`. Vẫn song
ngữ, vẫn kiểm tiêu đề + dấu, dòng chuyển ngôn ngữ, mục theo loại, tên mục chuẩn, số mục hai bản, tiêu đề
không emoji và `drift`; không bắt khối Ủng hộ dự án và mục Giấy phép (không ai ngoài chủ đọc, mã không cấp
phép MIT). Khi chuyển repo sang public, bỏ chữ `private`: `check` sẽ báo phần còn thiếu.

Tên repo trong khối Ủng hộ lấy từ `--repo`, rồi git remote `origin`, rồi tên thư mục, nên chạy trong
worktree hay bản clone tạm vẫn đúng.

CI: repo public gọi workflow dùng chung (GitHub Actions) như trên. Repo private chạy trên Woodpecker tự
host https://ci.bepmamnon.com với tệp `.woodpecker/readme.yaml` ở phần tiếng Anh: bật repo trong
Woodpecker, clone đủ lịch sử để `drift` đọc được, tải `readme_axi.py` từ repo public này (không cần token).
