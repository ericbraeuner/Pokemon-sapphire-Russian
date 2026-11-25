"""Report translation and dictionary coverage for map text labels."""

import argparse
import json
import re
from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]
TEXT_LABEL = re.compile(r"^([A-Za-z_]\w*)::?[^\n]*\n(?:[ \t]*\n)*[ \t]+\.string\b", re.MULTILINE)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("prefix", nargs="+", help="Map directory name prefixes")
    parser.add_argument("--shared", action="append", default=[],
                        help="Repository-relative shared text file to scan")
    parser.add_argument("--list-fixed-only", action="store_true",
                        help="List labels that have fixed translations but no adaptive entry")
    parser.add_argument("--list-without-dictionary", action="store_true",
                        help="List translated labels without a field dictionary")
    args = parser.parse_args()

    learner = ROOT / "language_learning"
    fixed = json.loads((learner / "field_templates.json").read_text(encoding="utf-8"))
    dictionaries = json.loads((learner / "field_dictionary.json").read_text(encoding="utf-8"))
    catalog = json.loads(
        (learner / "integration/dialogue_catalog.json").read_text(encoding="utf-8")
    )
    adaptive = {entry["source"].get("base_text_symbol") for entry in catalog["dialogues"]}

    for prefix in args.prefix:
        files = (
            path
            for directory in sorted((ROOT / "data/maps").glob(f"{prefix}*"))
            for path in (directory / "text.inc", directory / "scripts.inc")
            if path.is_file()
        )
        labels = {
            label
            for path in files
            for label in TEXT_LABEL.findall(path.read_text(encoding="utf-8"))
        }
        for shared in args.shared:
            labels.update(
                label for label in TEXT_LABEL.findall((ROOT / shared).read_text(encoding="utf-8"))
                if label.startswith(prefix)
            )
        if not labels:
            print(f"{prefix}: no local map text labels")
            continue
        print(f"{prefix}: {len(labels & fixed.keys())} fixed, "
              f"{len(labels & adaptive)} adaptive, "
              f"{len(labels & dictionaries.keys())} with dictionary, {len(labels)} total")
        for label in sorted(labels - fixed.keys() - adaptive):
            print(f"  missing: {label}")
        if args.list_fixed_only:
            for label in sorted((labels & fixed.keys()) - adaptive):
                print(f"  fixed only: {label}")
        if args.list_without_dictionary:
            translated = labels & (fixed.keys() | adaptive)
            for label in sorted(translated - dictionaries.keys()):
                print(f"  no dictionary: {label}")


if __name__ == "__main__":
    main()
