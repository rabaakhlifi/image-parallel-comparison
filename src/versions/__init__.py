# src/versions/__init__.py
"""Module contenant toutes les versions de parallélisme"""

from . import mono
from . import threading_version
from . import multiprocessing_version
from . import threadpool_executor
from . import processpool_executor

__all__ = [
    'mono',
    'threading_version',
    'multiprocessing_version',
    'threadpool_executor',
    'processpool_executor'
]

