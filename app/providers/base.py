from __future__ import annotations

from abc import ABC, abstractmethod
from typing import Any

from pydantic import BaseModel, Field


class ProviderResult(BaseModel):
    domain: str
    available: bool
    data: dict[str, Any] = Field(default_factory=dict)
    error: str | None = None


class Provider(ABC):
    domain: str

    @abstractmethod
    async def fetch(self) -> ProviderResult:
        """Fetch remote data and normalize into a ProviderResult."""
