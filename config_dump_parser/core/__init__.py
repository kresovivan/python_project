"""Ядро: парсер XML, поиск, слияние CSV. Без Tkinter."""

from .row import MetadataRow
from .parser import XmlParser
from .query import QueryCompiler, QueryMatcher
from .csv_merge import merge_csv_files

__all__ = [
    'MetadataRow', 'XmlParser',
    'QueryCompiler', 'QueryMatcher',
    'merge_csv_files',
]