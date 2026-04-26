#!/usr/bin/env python3
"""
Unified Project Code Collector

Steps:
1. Indexing – add relative path comments to files
2. Collecting – create a single project code dump file
3. Cleanup – remove added comments, restoring original files
"""

import argparse
import sys
from pathlib import Path
from typing import Set, Dict, List

# ============================================================
# CONFIG
# ============================================================

DEFAULT_IGNORE_DIRS = {
    ".git", ".svn", ".hg", "__pycache__", "node_modules",
    ".idea", ".vscode", ".vs", "build", "dist", "target",
    "venv", "env", ".env", "coverage", ".mypy_cache",
    "bin", "obj", "public", ".next", # ,"test", "tests",
}

DEFAULT_IGNORE_FILES = {
    "package-lock.json", "yarn.lock", "pnpm-lock.yaml", "bun.lockb",
    "cargo.lock", "Gemfile.lock", "composer.lock", "mix.lock",
    "poetry.lock", "Pipfile.lock", "go.sum", "migration_lock.toml",
    ".DS_Store", "Thumbs.db", "LICENSE", "LICENSE.txt",
    "tsconfig.json", "tsconfig.app.json", "tsconfig.node.json",
    "eslint.config.js", ".eslintrc.js", ".prettierrc",
    "postcss.config.js", "tailwind.config.js",
    "vite.config.ts", "vite.config.js",
    "jest.config.js", "jest-e2e.json",
    "index.html", "favicon.ico", "merger.py",
}

DEFAULT_EXTENSIONS = {
    ".py", ".js", ".ts", ".jsx", ".tsx", ".java", ".c", ".cpp",
    ".h", ".hpp", ".cs", ".go", ".rs", ".php", ".rb",
    ".css", ".scss", ".html", ".xml", ".json", ".yaml",
    ".yml", ".sql", ".graphql", ".env", ".toml",
    ".ini", ".cfg", ".conf", "dockerfile",
}

COMMENT_SYNTAX = {
    "default": "# {}",
    ".js": "// {}",
    ".ts": "// {}",
    ".jsx": "// {}",
    ".tsx": "// {}",
    ".java": "// {}",
    ".c": "// {}",
    ".cpp": "// {}",
    ".cs": "// {}",
    ".go": "// {}",
    ".rs": "// {}",
    ".php": "// {}",
    ".css": "/* {} */",
    ".scss": "/* {} */",
    ".html": "<!-- {} -->",
    ".xml": "<!-- {} -->",
    ".md": "<!-- {} -->",
    ".sql": "-- {}",
    ".json": "# {}",
}

# ============================================================
# UTILITIES
# ============================================================

def comment_for(ext: str, path: str) -> str:
    return COMMENT_SYNTAX.get(ext, COMMENT_SYNTAX["default"]).format(path)


def is_valid_file(path: Path) -> bool:
    ext = path.suffix.lower()
    if ext == "" and path.name.lower() == "dockerfile":
        ext = "dockerfile"
    return ext in DEFAULT_EXTENSIONS


# ============================================================
# STEP 1 – INDEXING
# ============================================================

def add_comment(file: Path, rel: str, dry: bool) -> bool:
    try:
        content = file.read_text(encoding="utf-8")
    except:
        return False

    ext = file.suffix.lower()
    comment = comment_for(ext, rel)

    if any(comment in line for line in content.splitlines()[:5]):
        return False

    if not dry:
        file.write_text(f"{comment}\n{content}", encoding="utf-8")
    return True


def index_files(root: Path, base: Path, dry: bool, verbose: bool):
    for item in root.iterdir():
        if item.name in DEFAULT_IGNORE_FILES:
            continue
        if item.is_dir():
            if item.name not in DEFAULT_IGNORE_DIRS:
                index_files(item, base, dry, verbose)
            continue

        if not is_valid_file(item):
            continue

        rel = str(item.relative_to(base)).replace("\\", "/")
        if add_comment(item, rel, dry) and verbose:
            print(f"Indexed: {rel}")


# ============================================================
# STEP 2 – COLLECTING
# ============================================================

def has_comment(file: Path, rel: str) -> bool:
    try:
        for line in file.read_text(encoding="utf-8").splitlines()[:10]:
            if rel in line:
                return True
    except:
        pass
    return False


def collect_files(root: Path, base: Path) -> List[Dict]:
    collected = []
    for item in root.rglob("*"):
        if item.is_dir():
            continue
        if item.name in DEFAULT_IGNORE_FILES:
            continue
        if not is_valid_file(item):
            continue

        rel = str(item.relative_to(base)).replace("\\", "/")
        if has_comment(item, rel):
            collected.append({
                "path": rel,
                "full": item,
                "size": item.stat().st_size,
            })
    return sorted(collected, key=lambda x: x["path"])


def create_dump(output: Path, files: List[Dict]):
    with output.open("w", encoding="utf-8") as f:
        f.write(f"PROJECT CODE DUMP\nFILES: {len(files)}\n{'='*80}\n\n")
        f.write("INDEX:\n")
        for file in files:
            f.write(f"{file['path']}\n")
        f.write(f"\n{'='*80}\n")

        for file in files:
            f.write(f"\nFILE: {file['path']}\n{'='*80}\n")
            try:
                f.write(file["full"].read_text(encoding="utf-8"))
            except:
                f.write("[Unreadable file]")
            f.write("\n")


# ============================================================
# STEP 3 – CLEANUP
# ============================================================

def clean_file(file: Path, rel: str, dry: bool) -> bool:
    try:
        lines = file.read_text(encoding="utf-8").splitlines(True)
    except:
        return False

    ext = file.suffix.lower()
    expected = comment_for(ext, rel)

    if lines and lines[0].strip() == expected:
        if not dry:
            file.write_text("".join(lines[1:]), encoding="utf-8")
        return True
    return False


def cleanup(root: Path, base: Path, dry: bool, verbose: bool):
    for item in root.iterdir():
        if item.name in DEFAULT_IGNORE_FILES:
            continue
        if item.is_dir():
            if item.name not in DEFAULT_IGNORE_DIRS:
                cleanup(item, base, dry, verbose)
            continue

        rel = str(item.relative_to(base)).replace("\\", "/")
        if clean_file(item, rel, dry) and verbose:
            print(f"Cleaned: {rel}")


# ============================================================
# MAIN
# ============================================================

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("directory", nargs="?", default=".")
    parser.add_argument("--output", "-o", default="project_code.txt")
    parser.add_argument("--dry-run", action="store_true")
    parser.add_argument("--verbose", "-v", action="store_true")
    args = parser.parse_args()

    base = Path(args.directory).resolve()
    output = Path(args.output).resolve()
    DEFAULT_IGNORE_FILES.add(output.name)

    print("STEP 1: Indexing files...")
    index_files(base, base, args.dry_run, args.verbose)

    print("STEP 2: Collecting files...")
    files = collect_files(base, base)
    if not files:
        print("No files collected.")
        sys.exit(0)

    create_dump(output, files)
    print(f"Created dump: {output}")

    print("STEP 3: Cleanup...")
    cleanup(base, base, args.dry_run, args.verbose)

    print("Done ✔")


if __name__ == "__main__":
    main()
