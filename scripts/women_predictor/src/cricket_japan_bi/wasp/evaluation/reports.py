"""Deterministic JSON and Markdown evaluation/audit reports."""

from __future__ import annotations

import json
import math
from pathlib import Path
from typing import Any, List, Mapping


def _json_default(value: Any) -> Any:
    if hasattr(value, "item"):
        return value.item()
    if hasattr(value, "as_dict"):
        return value.as_dict()
    raise TypeError("cannot serialize {!r}".format(type(value)))


def _clean(value: Any) -> Any:
    if isinstance(value, float) and not math.isfinite(value):
        return None
    if isinstance(value, Mapping):
        return {str(key): _clean(item) for key, item in value.items()}
    if isinstance(value, (list, tuple)):
        return [_clean(item) for item in value]
    if hasattr(value, "item"):
        return _clean(value.item())
    return value


def render_markdown(report: Mapping[str, Any], title: str = "WASP-style model evaluation") -> str:
    lines: List[str] = ["# {}".format(title), ""]

    def walk(value: Any, depth: int, name: str) -> None:
        prefix = "#" * min(6, depth + 2)
        if isinstance(value, Mapping):
            lines.extend(["{} {}".format(prefix, name), ""])
            scalars = {key: item for key, item in value.items() if not isinstance(item, (Mapping, list, tuple))}
            for key, item in scalars.items():
                lines.append("- {}: {}".format(key, item))
            if scalars:
                lines.append("")
            for key, item in value.items():
                if isinstance(item, (Mapping, list, tuple)):
                    walk(item, depth + 1, str(key))
        elif isinstance(value, (list, tuple)):
            lines.extend(["{} {}".format(prefix, name), ""])
            for item in value:
                if isinstance(item, Mapping):
                    lines.append("- `{}`".format(json.dumps(_clean(item), ensure_ascii=False, sort_keys=True)))
                else:
                    lines.append("- {}".format(item))
            lines.append("")

    for key, value in report.items():
        walk(value, 0, str(key)) if isinstance(value, (Mapping, list, tuple)) else lines.append("- {}: {}".format(key, value))
    return "\n".join(lines).rstrip() + "\n"


def write_report(
    report: Mapping[str, Any],
    output_dir: Any,
    *,
    stem: str = "evaluation",
    title: str = "WASP-style model evaluation",
) -> Mapping[str, str]:
    target = Path(output_dir)
    target.mkdir(parents=True, exist_ok=True)
    cleaned = _clean(report)
    json_path = target / "{}.json".format(stem)
    markdown_path = target / "{}.md".format(stem)
    json_path.write_text(
        json.dumps(cleaned, ensure_ascii=False, indent=2, sort_keys=True, default=_json_default) + "\n",
        encoding="utf-8",
    )
    markdown_path.write_text(render_markdown(cleaned, title), encoding="utf-8")
    return {"json": str(json_path), "markdown": str(markdown_path)}
