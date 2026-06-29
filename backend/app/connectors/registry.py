from __future__ import annotations
from typing import Optional
from .base import BaseConnector
from .adzuna import AdzunaConnector
from .aps import APSConnector
from .council import CouncilConnector
from .jora import JoraConnector


def create_connector_registry(
    adzuna_app_id: Optional[str] = None,
    adzuna_app_key: Optional[str] = None,
) -> dict[str, BaseConnector]:
    """Create and return a registry of all available connectors."""
    return {
        "adzuna": AdzunaConnector(app_id=adzuna_app_id, app_key=adzuna_app_key),
        "jora": JoraConnector(),
        "aps": APSConnector(),
        "council": CouncilConnector(),
    }


def get_active_connectors(
    registry: dict[str, BaseConnector],
    source_filter: str = "all",
) -> list[BaseConnector]:
    """
    Return the list of connectors to use based on source_filter.
    - "government" → only aps
    - "council"    → only council
    - "all"        → all connectors
    """
    if source_filter == "government":
        return [registry["aps"]]
    elif source_filter == "council":
        return [registry["council"]]
    else:
        return list(registry.values())
