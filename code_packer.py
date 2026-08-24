import sys
from pathlib import Path

ROOT_DIR = Path.cwd()
OUTPUT_FILE = Path("codebase_payload.md")

def collect_files(targets: list[Path]) -> list[Path]:
    files = []
    for target in targets:
        if not target.exists():
            print(f"⚠️  Skipping non-existent path: {target.name}")
            continue
        if target.is_file():
            files.append(target)
        elif target.is_dir():
            files.extend(target.rglob("*"))

    return files

def pack_codebase(targets: list[Path]):
    payload_lines = ["# Codebase Context Payload\n"]
    file_count = 0
    processed = set()

    for file_path in collect_files(targets):
        resolved = file_path.resolve()

        if resolved in processed or resolved == OUTPUT_FILE.resolve():
            continue

        if not file_path.is_file():
            continue

        try:
            content = file_path.read_text(encoding="utf-8")
            try:
                rel_path = file_path.relative_to(ROOT_DIR)
            except ValueError:
                rel_path = file_path

            ext = file_path.suffix.lstrip(".") or "text"
            payload_lines.append(f"## File: `{rel_path}`\n````{ext}\n{content}\n````\n")
            file_count += 1
            processed.add(resolved)

        except UnicodeDecodeError:
            continue
    if file_count == 0:
        print(f"❌ No readable text files found.")
        return

    OUTPUT_FILE.write_text("\n".join(payload_lines), encoding="utf-8")
    print(f"✅ Successfully packed {file_count} file(s) into '{OUTPUT_FILE.name}'!")

if __name__ == "__main__":
    raw_args = sys.argv[1:]

    if not raw_args:
        print("❌ Error: At least one file or directory target is required.")
        print("Usage: python3 pack_code.py <path1> [path2 ...]")
        sys.exit(1)

    targets = [ROOT_DIR / arg for arg in raw_args] if raw_args else [ROOT_DIR]
    pack_codebase(targets)