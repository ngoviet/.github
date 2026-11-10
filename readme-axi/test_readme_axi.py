"""Test readme-axi bằng cách chạy CLI thật trên các thư mục mẫu tạm.

Chạy: python -m unittest discover -s readme-axi -v
Chỉ dùng thư viện chuẩn (và git cho drift / tên repo từ origin).
"""
import os
import shutil
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

CLI = Path(__file__).with_name("readme_axi.py")
TYPES = ["ha", "card", "esp32", "tool", "app", "ops", "config", "docs"]


def run(*args, cwd=None):
    env = dict(os.environ, PYTHONIOENCODING="utf-8")
    r = subprocess.run([sys.executable, str(CLI), *map(str, args)], cwd=cwd, env=env,
                       capture_output=True, text=True, encoding="utf-8")
    return r.returncode, r.stdout


def git(root, *args):
    env = dict(os.environ, GIT_AUTHOR_NAME="t", GIT_AUTHOR_EMAIL="t@t", GIT_COMMITTER_NAME="t",
               GIT_COMMITTER_EMAIL="t@t")
    subprocess.run(["git", "-C", str(root), *args], check=True, capture_output=True, env=env)


def private_pair(rtype="ops", en_extra="", vi_extra=""):
    """README song ngữ hợp lệ cho repo private loại ops (không khối Ủng hộ, không License)."""
    en = ("# Demo\n\n<!-- readme-axi type=%s private -->\n\n**English** · [Tiếng Việt](README.vi.md)\n\n"
          "Runs the NAS scripts.\n\n## Usage\n\nRun it.\n\n## Project layout\n\nFiles.\n%s") % (rtype, en_extra)
    vi = ("# Demo\n\n<!-- readme-axi type=%s private -->\n\n[English](README.md) · **Tiếng Việt**\n\n"
          "Chạy script NAS.\n\n## Cách dùng\n\nChạy.\n\n## Cấu trúc dự án\n\nTệp.\n%s") % (rtype, vi_extra)
    return en, vi


class Base(unittest.TestCase):
    def setUp(self):
        self.tmp = Path(tempfile.mkdtemp())
        # git không được leo lên repo cha của thư mục tạm (nếu có) để đọc origin của nó
        os.environ["GIT_CEILING_DIRECTORIES"] = str(self.tmp.parent)
        self.root = self.tmp / "demo-repo"
        self.root.mkdir()

    def tearDown(self):
        shutil.rmtree(self.tmp, ignore_errors=True)

    def write(self, en=None, vi=None):
        if en is not None:
            (self.root / "README.md").write_bytes(en.encode("utf-8"))
        if vi is not None:
            (self.root / "README.vi.md").write_bytes(vi.encode("utf-8"))

    def rules(self, out):
        """Tập (tệp, luật) trong bảng issues của output check."""
        rows, on = set(), False
        for ln in out.splitlines():
            if ln.startswith("issues["):
                on = True
            elif on and ln.startswith("  "):
                f, rule = ln.strip().split(",")[:2]
                rows.add((f, rule))
            else:
                on = False
        return rows


class PrivateProfile(Base):
    def test_private_pair_passes_without_support_and_license(self):
        self.write(*private_pair())
        code, out = run("check", self.root)
        self.assertEqual(code, 0, out)
        self.assertIn("profile: private", out)
        self.assertIn("result: pass, 0 issues", out)

    def test_same_readme_without_private_flag_needs_support_and_license(self):
        en, vi = private_pair()
        self.write(en.replace(" private -->", " -->"), vi.replace(" private -->", " -->"))
        code, out = run("check", self.root)
        self.assertEqual(code, 1)
        self.assertIn("profile: public", out)
        got = self.rules(out)
        for f in ("README.md", "README.vi.md"):
            self.assertIn((f, "support"), got)
            self.assertIn((f, "section"), got)  # thiếu ## License / ## Giấy phép

    def test_private_still_requires_vietnamese_file(self):
        self.write(private_pair()[0])
        code, out = run("check", self.root)
        self.assertEqual(code, 1)
        self.assertIn(("README.vi.md", "missing"), self.rules(out))

    def test_private_still_requires_type_sections_switcher_and_plain_headings(self):
        en, vi = private_pair()
        en = en.replace("## Project layout", "## Layout 🚀").replace("**English** · [Tiếng Việt](README.vi.md)", "")
        self.write(en, vi)
        code, out = run("check", self.root)
        self.assertEqual(code, 1)
        got = self.rules(out)
        self.assertIn(("README.md", "section"), got)        # thiếu ## Project layout
        self.assertIn(("README.md", "switcher"), got)
        self.assertIn(("README.md", "emoji-heading"), got)

    def test_private_flag_must_match_in_both_files(self):
        en, vi = private_pair()
        self.write(en, vi.replace(" private -->", " -->"))
        code, out = run("check", self.root)
        self.assertEqual(code, 1)
        self.assertIn(("README.vi.md", "type-marker"), self.rules(out))

    def test_unknown_marker_flag_is_reported(self):
        en, vi = private_pair()
        self.write(en.replace(" private -->", " private secret -->"), vi)
        code, out = run("check", self.root)
        self.assertEqual(code, 1)
        self.assertIn("cờ lạ trong dấu: secret", out)

    def test_support_skips_private_repo_and_leaves_files(self):
        en, vi = private_pair()
        self.write(en, vi)
        code, out = run("support", self.root, "--write")
        self.assertEqual(code, 0)
        self.assertIn("result: skipped", out)
        self.assertEqual((self.root / "README.md").read_bytes().decode("utf-8"), en)

    def test_private_profile_tolerates_a_leftover_support_block(self):
        self.write(*private_pair(en_extra="\n<!-- support:start -->\nold\n<!-- support:end -->\n"))
        code, out = run("check", self.root)
        self.assertEqual(code, 0, out)


class Types(Base):
    def test_scaffold_then_check_passes_for_every_type_and_profile(self):
        for rtype in TYPES:
            for private in (False, True):
                with self.subTest(type=rtype, private=private):
                    for f in ("README.md", "README.vi.md"):
                        (self.root / f).unlink(missing_ok=True)
                    extra = ["--private"] if private else []
                    code, out = run("scaffold", self.root, "--type", rtype, "--title", "Demo", *extra)
                    self.assertEqual(code, 0, out)
                    code, out = run("check", self.root)
                    self.assertEqual(code, 0, out)
                    self.assertIn(f"type: {rtype}", out)
                    self.assertIn(f"profile: {'private' if private else 'public'}", out)
                    text = (self.root / "README.md").read_text(encoding="utf-8")
                    self.assertEqual("<!-- support:start -->" in text, not private)

    def test_new_types_enforce_their_sections(self):
        cases = {"app": ["Features", "Development", "Deployment"], "ops": ["Usage", "Project layout"],
                 "config": ["Project layout", "Deployment"], "docs": ["Project layout"]}
        for rtype, need in cases.items():
            with self.subTest(type=rtype):
                en = ("# Demo\n\n<!-- readme-axi type=%s private -->\n\n**English** · [Tiếng Việt](README.vi.md)\n\n"
                      "Intro.\n\n## Notes\n\nx\n") % rtype
                vi = ("# Demo\n\n<!-- readme-axi type=%s private -->\n\n[English](README.md) · **Tiếng Việt**\n\n"
                      "Giới thiệu.\n\n## Ghi chú\n\nx\n") % rtype
                self.write(en, vi)
                code, out = run("check", self.root)
                self.assertEqual(code, 1)
                for n in need:
                    self.assertIn(f"thiếu mục ## {n}", out)

    def test_deployment_has_vietnamese_name(self):
        code, out = run("names")
        self.assertEqual(code, 0)
        self.assertIn("Deployment,Triển khai", out)
        for rtype in TYPES:
            self.assertIn(f"\n  {rtype},", out)
        self.assertIn("private: none", out)

    def test_bad_type_is_usage_error(self):
        code, out = run("scaffold", self.root, "--type", "web", "--title", "x")
        self.assertEqual(code, 2)
        self.assertIn("code: USAGE", out)
        code, out = run("check", self.root, "--type", "web")
        self.assertEqual(code, 2)


class RepoName(Base):
    """Khối Ủng hộ chứa tên repo: lấy từ --repo, rồi origin, rồi tên thư mục."""

    def scaffold_for(self, repo):
        code, out = run("scaffold", self.root, "--type", "tool", "--title", "Demo", "--repo", repo, "--force")
        self.assertEqual(code, 0, out)

    def test_origin_wins_over_directory_name(self):
        git(self.root, "init", "-q")
        git(self.root, "remote", "add", "origin", "https://github.com/ngoviet/foo-bar.git")
        self.scaffold_for("foo-bar")
        code, out = run("check", self.root)
        self.assertEqual(code, 0, out)
        self.assertIn("repo: foo-bar", out)
        self.assertIn("repo_from: origin", out)

    def test_ssh_origin_without_dot_git(self):
        git(self.root, "init", "-q")
        git(self.root, "remote", "add", "origin", "git@github.com:ngoviet/foo-bar")
        self.scaffold_for("foo-bar")
        code, out = run("check", self.root)
        self.assertEqual(code, 0, out)

    def test_worktree_uses_origin_not_folder(self):
        git(self.root, "init", "-q")
        git(self.root, "remote", "add", "origin", "https://github.com/ngoviet/foo-bar.git")
        self.scaffold_for("foo-bar")
        git(self.root, "add", ".")
        git(self.root, "commit", "-qm", "init")
        wt = self.tmp / "wt-tam-123"
        git(self.root, "worktree", "add", "-q", str(wt))
        code, out = run("check", wt)
        self.assertEqual(code, 0, out)
        self.assertIn("repo: foo-bar", out)

    def test_flag_wins_over_origin(self):
        git(self.root, "init", "-q")
        git(self.root, "remote", "add", "origin", "https://github.com/ngoviet/foo-bar.git")
        self.scaffold_for("other")
        code, out = run("check", self.root)
        self.assertEqual(code, 1)
        self.assertIn(("README.md", "support"), self.rules(out))
        code, out = run("check", self.root, "--repo", "other")
        self.assertEqual(code, 0, out)
        self.assertIn("repo_from: flag", out)

    def test_directory_name_without_git(self):
        code, out = run("scaffold", self.root, "--type", "tool", "--title", "Demo")
        self.assertEqual(code, 0)
        code, out = run("check", self.root)
        self.assertEqual(code, 0, out)
        self.assertIn("repo: demo-repo", out)
        self.assertIn("repo_from: dir", out)


class Drift(Base):
    def test_drift_reports_english_commits_after_vietnamese(self):
        git(self.root, "init", "-q")
        self.write(*private_pair())
        git(self.root, "add", ".")
        git(self.root, "commit", "-qm", "both")
        code, out = run("drift", self.root)
        self.assertEqual(code, 0)
        self.assertIn("result: in sync", out)
        self.write(private_pair(en_extra="\nMore.\n")[0])
        git(self.root, "commit", "-qam", "en only")
        code, out = run("drift", self.root)
        self.assertEqual(code, 0)
        self.assertIn("result: drift", out)
        code, out = run("drift", self.root, "--strict")
        self.assertEqual(code, 1)


if __name__ == "__main__":
    unittest.main()
