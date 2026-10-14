"""Jinja2 templates shared by every router, with a few display filters."""

import pathlib

from fastapi.templating import Jinja2Templates

templates = Jinja2Templates(directory=str(pathlib.Path(__file__).parent / "templates"))


def money(value):
    try:
        return f"${float(value):,.2f}"
    except (TypeError, ValueError):
        return "$0.00"


def dateval(value):
    """A date (or ISO string) as YYYY-MM-DD for <input type=date>, else ''."""
    if not value:
        return ""
    return value if isinstance(value, str) else value.isoformat()


def pct(value):
    try:
        return f"{float(value):.1f}"
    except (TypeError, ValueError):
        return "0.0"


templates.env.filters.update(money=money, dateval=dateval, pct=pct)


def page(request, template, status_code=200, **context):
    return templates.TemplateResponse(request, template, context, status_code=status_code)
