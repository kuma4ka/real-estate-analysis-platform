from flask import Blueprint

bp = Blueprint('api', __name__)

# ruff: noqa: E402
from . import properties, stats

__all__ = ['properties', 'stats']