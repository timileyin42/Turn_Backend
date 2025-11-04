"""Utility helpers for rendering HTML templates with Jinja2."""
from __future__ import annotations

from datetime import date, datetime
from pathlib import Path
from typing import Any, Iterable

from jinja2 import Environment, FileSystemLoader, select_autoescape


_APP_DIR = Path(__file__).resolve().parent.parent
TEMPLATE_ROOT = _APP_DIR / "templates"
TEMPLATE_ROOT.mkdir(parents=True, exist_ok=True)


def _format_date(value: Any, date_format: str = "%b %Y") -> str:
    """Format date/datetime values for display inside templates."""
    if not value:
        return ""
    if isinstance(value, datetime):
        return value.strftime(date_format)
    if isinstance(value, date):
        return value.strftime(date_format)
    return str(value)


def _join_list(value: Any, separator: str = ", ") -> str:
    """Join iterable values into a single string for cleaner rendering."""
    if not value:
        return ""
    if isinstance(value, str):
        return value
    if isinstance(value, Iterable):
        return separator.join([str(item) for item in value if item])
    return str(value)


_env = Environment(
    loader=FileSystemLoader(str(TEMPLATE_ROOT)),
    autoescape=select_autoescape(["html", "xml"]),
    trim_blocks=True,
    lstrip_blocks=True,
)

_env.filters["format_date"] = _format_date
_env.filters["join_list"] = _join_list


def render_template(template_name: str, context: dict[str, Any]) -> str:
    """Render a template with the provided context."""
    template = _env.get_template(template_name)
    return template.render(**context)
