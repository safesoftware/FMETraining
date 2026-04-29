"""Jinja2 templates singleton.

Defining `templates` once here keeps every route from re-instantiating the
`Jinja2Templates` object and makes it trivial to override in tests.
"""
from __future__ import annotations

from pathlib import Path

from fastapi.templating import Jinja2Templates

TEMPLATES_DIR = Path(__file__).resolve().parent

templates = Jinja2Templates(directory=str(TEMPLATES_DIR))
