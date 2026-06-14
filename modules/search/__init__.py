# modules/search/__init__.py
from .controller import SearchController
from .view import SearchView
from .widgets import SearchBarWidget

__all__ = [
    'SearchController',
    'SearchView',
    'SearchBarWidget',
]