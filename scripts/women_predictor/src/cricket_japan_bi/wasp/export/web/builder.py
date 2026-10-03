"""Compose the standalone WASP UI into one self-contained HTML document.

The source files in this package deliberately remain split so they are easy to
review.  :func:`render_standalone_html` is the only composition step: it embeds
the payload, predictor and UI assets without making network references.
"""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any, Mapping


_ROOT = Path(__file__).resolve().parent
_PLACEHOLDERS = {
    "style": "<!--__WASP_STYLE__-->",
    "payload": "<!--__WASP_PAYLOAD__-->",
    "predictor": "<!--__WASP_PREDICTOR__-->",
    "app": "<!--__WASP_APP__-->",
}


class PlaceholderError(ValueError):
    """Raised when an asset cannot be embedded safely or completely."""


def _json_for_script(value: Mapping[str, Any]) -> str:
    """Serialize JSON so untrusted labels cannot terminate the script node."""

    rendered = json.dumps(value, ensure_ascii=False, separators=(",", ":"), allow_nan=False)
    return (
        rendered.replace("&", "\\u0026")
        .replace("<", "\\u003c")
        .replace(">", "\\u003e")
        .replace("\u2028", "\\u2028")
        .replace("\u2029", "\\u2029")
    )


def _safe_javascript(source: str, *, label: str) -> str:
    if "</script" in source.lower():
        raise PlaceholderError(f"{label} contains a closing script tag")
    return source


def render_standalone_html(
    payload: Mapping[str, Any],
    predictor_javascript: str,
    *,
    title: str = "Japan T20 WASP-style Lab",
) -> str:
    """Return one HTML file that works when opened directly with ``file://``.

    ``predictor_javascript`` must assign an object to
    ``globalThis.WASPStandalonePredictor``.  The object contract is documented
    in ``CONTRACT.md`` next to this module.
    """

    if not isinstance(payload, Mapping):
        raise TypeError("payload must be a mapping")
    if not isinstance(predictor_javascript, str) or not predictor_javascript.strip():
        raise PlaceholderError("predictor_javascript must be a non-empty string")

    template = (_ROOT / "template.html").read_text(encoding="utf-8")
    assets = {
        _PLACEHOLDERS["style"]: (_ROOT / "standalone.css").read_text(encoding="utf-8"),
        _PLACEHOLDERS["payload"]: _json_for_script(payload),
        _PLACEHOLDERS["predictor"]: _safe_javascript(
            predictor_javascript, label="predictor_javascript"
        ),
        _PLACEHOLDERS["app"]: _safe_javascript(
            (_ROOT / "standalone.js").read_text(encoding="utf-8"), label="standalone.js"
        ),
    }
    html = template.replace("__WASP_DOCUMENT_TITLE__", _escape_title(title))
    for placeholder, content in assets.items():
        if html.count(placeholder) != 1:
            raise PlaceholderError(f"expected exactly one {placeholder} placeholder")
        html = html.replace(placeholder, content)
    leftovers = [value for value in _PLACEHOLDERS.values() if value in html]
    if leftovers:
        raise PlaceholderError(f"unresolved placeholders: {', '.join(leftovers)}")
    return html


def _escape_title(value: str) -> str:
    return (
        str(value)
        .replace("&", "&amp;")
        .replace("<", "&lt;")
        .replace(">", "&gt;")
        .replace('"', "&quot;")
        .replace("'", "&#39;")
    )
