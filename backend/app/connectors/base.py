from __future__ import annotations
from abc import ABC, abstractmethod
from typing import Any
from ..models import SourceStatus


class BaseConnector(ABC):
    name: str = "base"

    @abstractmethod
    async def search(
        self,
        query: str,
        location: str,
        radius_km: int = 50,
        work_type: str = "any",
        results_per_page: int = 20,
    ) -> tuple[list[dict], SourceStatus]:
        """
        Search for jobs.
        Returns (list of raw job dicts, SourceStatus).
        Must never raise — return empty list + unavailable status on error.
        """
        pass

    def get_status(self) -> SourceStatus:
        return SourceStatus(name=self.name, status="available")
