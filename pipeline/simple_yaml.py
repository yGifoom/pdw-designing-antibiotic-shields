from __future__ import annotations

import ast
from typing import Any, List, Tuple


class YamlLiteError(ValueError):
    pass


def _parse_scalar(raw: str) -> Any:
    text = raw.strip()
    if text in {"true", "True"}:
        return True
    if text in {"false", "False"}:
        return False
    if text in {"null", "None", "~"}:
        return None
    if (text.startswith('"') and text.endswith('"')) or (text.startswith("'") and text.endswith("'")):
        return text[1:-1]
    if text.startswith("[") and text.endswith("]"):
        return ast.literal_eval(text)
    try:
        if "." in text:
            return float(text)
        return int(text)
    except ValueError:
        return text


def load_yaml_lite(content: str) -> Any:
    lines = []
    for raw in content.splitlines():
        body = raw.split("#", 1)[0].rstrip("\n")
        if body.strip() == "":
            continue
        indent = len(body) - len(body.lstrip(" "))
        lines.append((indent, body.strip()))

    root: Any = None
    stack: List[Tuple[int, Any]] = []

    i = 0
    while i < len(lines):
        indent, text = lines[i]

        while stack and indent < stack[-1][0]:
            stack.pop()

        parent = stack[-1][1] if stack else None

        if text.startswith("- "):
            value_text = text[2:].strip()
            if not isinstance(parent, list):
                raise YamlLiteError("List item without list parent")
            if ":" in value_text and not value_text.startswith("["):
                key, val = [p.strip() for p in value_text.split(":", 1)]
                obj = {key: _parse_scalar(val) if val else {}}
                parent.append(obj)
                if val == "":
                    stack.append((indent + 2, obj[key]))
                stack.append((indent + 2, obj))
            else:
                parent.append(_parse_scalar(value_text))
        else:
            if ":" not in text:
                raise YamlLiteError(f"Invalid line: {text}")
            key, val = [p.strip() for p in text.split(":", 1)]

            if parent is None:
                if root is None:
                    root = {}
                    parent = root
                    stack.append((indent, root))
                else:
                    raise YamlLiteError("Multiple root elements")

            if isinstance(parent, list):
                node = {}
                parent.append(node)
                parent = node

            if val == "":
                next_is_list = i + 1 < len(lines) and lines[i + 1][0] > indent and lines[i + 1][1].startswith("- ")
                container: Any = [] if next_is_list else {}
                parent[key] = container
                stack.append((indent + 2, container))
            else:
                parent[key] = _parse_scalar(val)

        i += 1

    return root if root is not None else {}
