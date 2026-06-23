import json
import sys
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]

RULE_FILES = [
    "AGENTS.md",
    "SKILL.md",
    "README.md",
    "docs/README.md",
    "docs/EXPERTS.md",
    "references/temporal-engine.md",
]

REQUIRED_PHRASES = [
    "smallest",
    "fastest",
    "structural",
    "deep decision",
    "verify",
]


def check_rule_copies(root=ROOT):
    issues = []
    for rel in RULE_FILES:
        path = Path(root) / rel
        if not path.exists():
            issues.append({
                "file": rel,
                "code": "rule-file-missing",
                "message": "Expected rule surface is missing.",
            })
            continue
        text = path.read_text(encoding="utf-8").lower()
        for phrase in REQUIRED_PHRASES:
            if phrase not in text:
                issues.append({
                    "file": rel,
                    "code": "required-phrase-missing",
                    "phrase": phrase,
                    "message": "Rule surface drifted from the compact time-compression contract.",
                })
    return {
        "ok": not issues,
        "checked_files": RULE_FILES,
        "required_phrases": REQUIRED_PHRASES,
        "issues": issues,
    }


def main(argv=None):
    root = Path(argv[0]).resolve() if argv else ROOT
    payload = check_rule_copies(root)
    print(json.dumps(payload, indent=2, ensure_ascii=False))
    return 0 if payload["ok"] else 1


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))
