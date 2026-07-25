"""Abstract page source interface."""

from __future__ import annotations

from abc import ABC, abstractmethod
from typing import Iterator

from ragfailbench.config import AppConfig
from ragfailbench.schemas.page import WikipediaPage


class PageSource(ABC):
    """Abstract source of Wikipedia pages."""

    def __init__(self, config: AppConfig) -> None:
        self.config = config

    @abstractmethod
    def fetch_pages(self) -> Iterator[WikipediaPage]:
        """Yield raw Wikipedia pages for all configured categories."""
        raise NotImplementedError
