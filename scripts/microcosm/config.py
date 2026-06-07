import json
from pathlib import Path

DEFAULT_INVARIANTS = [{"operator": "no-cycle", "relation": ["imports", "depends-on"]}]


def _strip_comment(line):
    if "#" not in line:
        return line
    return line.split("#", 1)[0]


def _parse_scalar(value):
    value = value.strip()
    if not value:
        return ""
    if value.startswith("[") and value.endswith("]"):
        inner = value[1:-1].strip()
        if not inner:
            return []
        return [_parse_scalar(part.strip()) for part in inner.split(",")]
    if value.lower() in {"true", "false"}:
        return value.lower() == "true"
    try:
        return int(value)
    except ValueError:
        pass
    try:
        return float(value)
    except ValueError:
        pass
    return value.strip('"\'')


def _looks_like_scalar(text):
    if not text:
        return True
    if text[0] in {"[", "{", '"', "'"} or text.lower() in {"true", "false"}:
        return True
    try:
        int(text); return True
    except ValueError:
        pass
    try:
        float(text); return True
    except ValueError:
        pass
    return False


def parse_simple_yaml(text):
    """Tiny YAML parser sufficient for V0.1 templates."""
    lines = []
    for raw in text.splitlines():
        stripped_comment = _strip_comment(raw).rstrip()
        if not stripped_comment.strip():
            continue
        indent = len(stripped_comment) - len(stripped_comment.lstrip(" "))
        lines.append((indent, stripped_comment.strip()))
    result, _ = _parse_block(lines, 0, 0, expect="map")
    return result


def _parse_block(lines, index, indent, expect):
    if expect == "map":
        return _parse_map(lines, index, indent)
    if expect == "list":
        return _parse_list(lines, index, indent)
    raise ValueError("unknown expect value: " + expect)


def _parse_map(lines, index, indent):
    mapping = {}
    while index < len(lines):
        cur_indent, cur_text = lines[index]
        if cur_indent < indent:
            return mapping, index
        if cur_indent > indent:
            index += 1
            continue
        if cur_text.startswith("- "):
            return mapping, index
        if ":" not in cur_text:
            index += 1
            continue
        key, _, value = cur_text.partition(":")
        key = key.strip(); value = value.strip()
        index += 1
        if value == "":
            if index < len(lines) and lines[index][0] > indent and lines[index][1].startswith("- "):
                sub, index = _parse_list(lines, index, lines[index][0])
                mapping[key] = sub
            elif index < len(lines) and lines[index][0] > indent:
                sub, index = _parse_map(lines, index, lines[index][0])
                mapping[key] = sub
            else:
                mapping[key] = {}
        else:
            mapping[key] = _parse_scalar(value)
    return mapping, index


def _parse_list(lines, index, indent):
    items = []
    while index < len(lines):
        cur_indent, cur_text = lines[index]
        if cur_indent < indent:
            return items, index
        if cur_indent > indent:
            index += 1
            continue
        if not cur_text.startswith("- "):
            return items, index
        item_text = cur_text[2:].strip()
        if not item_text:
            sub, index = _parse_map(lines, index + 1, cur_indent + 2)
            items.append(sub)
            continue
        if ":" in item_text and not _looks_like_scalar(item_text.split(":", 1)[1]):
            key, _, value = item_text.partition(":")
            key = key.strip(); value = value.strip()
            item = {}
            index += 1
            if value == "":
                if index < len(lines) and lines[index][0] > cur_indent and lines[index][1].startswith("- "):
                    sub, index = _parse_list(lines, index, lines[index][0])
                    item[key] = sub
                elif index < len(lines) and lines[index][0] > cur_indent:
                    sub, index = _parse_map(lines, index, lines[index][0])
                    item[key] = sub
                else:
                    item[key] = {}
            else:
                item[key] = _parse_scalar(value)
            while index < len(lines) and lines[index][0] == cur_indent + 2 and not lines[index][1].startswith("- "):
                child_indent, child_text = lines[index]
                if ":" not in child_text:
                    index += 1
                    continue
                ck, _, cv = child_text.partition(":")
                ck = ck.strip(); cv = cv.strip()
                if cv == "":
                    if index + 1 < len(lines) and lines[index + 1][0] > child_indent and lines[index + 1][1].startswith("- "):
                        sub, index = _parse_list(lines, index + 1, lines[index + 1][0])
                        item[ck] = sub
                    elif index + 1 < len(lines) and lines[index + 1][0] > child_indent:
                        sub, index = _parse_map(lines, index + 1, lines[index + 1][0])
                        item[ck] = sub
                    else:
                        item[ck] = {}
                        index += 1
                else:
                    item[ck] = _parse_scalar(cv)
                    index += 1
            items.append(item)
            continue
        items.append(_parse_scalar(item_text))
        index += 1
    return items, index


def _load_json_or_yaml(path):
    if not path.exists():
        return None
    suffix = path.suffix.lower()
    text = path.read_text(encoding="utf-8")
    if suffix == ".json":
        return json.loads(text)
    return parse_simple_yaml(text)


def _ensure_list(value):
    if value is None:
        return []
    if isinstance(value, list):
        return value
    return [value]


def load_invariants(project_root):
    config_dir = Path(project_root) / ".microcosm" / "config"
    json_path = config_dir / "invariants.json"
    yaml_path = config_dir / "invariants.yaml"
    yml_path = config_dir / "invariants.yml"
    if json_path.exists():
        data = json.loads(json_path.read_text(encoding="utf-8"))
        if isinstance(data, list):
            return data
        return data.get("invariants", DEFAULT_INVARIANTS)
    for path in [yaml_path, yml_path]:
        if path.exists():
            parsed = parse_simple_yaml(path.read_text(encoding="utf-8"))
            items = parsed.get("invariants", []) if isinstance(parsed, dict) else []
            return items or DEFAULT_INVARIANTS
    return DEFAULT_INVARIANTS


def load_assertions(project_root):
    config_dir = Path(project_root) / ".microcosm" / "config"
    for name in ("assertions.json", "assertions.yaml", "assertions.yml"):
        path = config_dir / name
        if path.exists():
            data = _load_json_or_yaml(path)
            if isinstance(data, list):
                return data
            if isinstance(data, dict):
                return _ensure_list(data.get("assertions"))
    return []


def load_policies(project_root):
    config_dir = Path(project_root) / ".microcosm" / "config"
    for name in ("policies.json", "policies.yaml", "policies.yml"):
        path = config_dir / name
        if path.exists():
            data = _load_json_or_yaml(path)
            if isinstance(data, list):
                return data
            if isinstance(data, dict):
                return _ensure_list(data.get("policies"))
    return []


def load_change_plan(plan_path):
    path = Path(plan_path)
    if not path.exists():
        raise FileNotFoundError("change plan not found: " + str(path))
    suffix = path.suffix.lower()
    text = path.read_text(encoding="utf-8")
    if suffix == ".json":
        data = json.loads(text)
        if isinstance(data, dict) and "change" in data:
            return data["change"]
        return data if isinstance(data, dict) else {}
    parsed = parse_simple_yaml(text)
    if isinstance(parsed, dict):
        return parsed.get("change", {}) or {}
    return {}


def parse_simple_invariants_yaml(text):
    parsed = parse_simple_yaml(text)
    if not isinstance(parsed, dict):
        return []
    return parsed.get("invariants", []) or []


def parse_change_plan_yaml(text):
    parsed = parse_simple_yaml(text)
    if not isinstance(parsed, dict):
        return {}
    return parsed.get("change", {}) or {}
