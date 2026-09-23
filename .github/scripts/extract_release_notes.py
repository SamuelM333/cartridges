"""Extract release notes from AppStream metainfo for GitHub Releases."""

import re
import sys
import textwrap
from pathlib import Path


def extract_release_notes(metainfo_path: Path) -> str:
    """Parse the latest release description from an AppStream metainfo file."""
    if not metainfo_path.exists():
        return "Release notes not found."

    content = metainfo_path.read_text(encoding="utf-8")
    pattern = (
        r"<release[^>]*>\s*<description[^>]*>\n([\s\S]*?)\s*</description>\s*</release>"
    )
    match = re.search(pattern, content)
    if match:
        return textwrap.dedent(match.group(1)).strip()

    version_match = re.search(r'<release[^>]*version="([^"]+)"', content)
    if version_match:
        version = version_match.group(1)
        return f"Cartridges release {version}"

    return "Release notes not found."


def main() -> None:
    """CLI entry point to extract release notes to output file."""
    metainfo_file = Path("data/page.samuelm333.Cartridges.metainfo.xml.in")
    output_file = Path("release_notes.md")

    if len(sys.argv) > 1:
        metainfo_file = Path(sys.argv[1])
    if len(sys.argv) > 2:
        output_file = Path(sys.argv[2])

    notes = extract_release_notes(metainfo_file)
    output_file.write_text(notes + "\n", encoding="utf-8")
    sys.stdout.write(f"Release notes written to {output_file}\n")


if __name__ == "__main__":
    main()
