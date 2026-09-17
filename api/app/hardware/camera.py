from abc import ABC, abstractmethod
from typing import Any, Dict


class CameraInterface(ABC):
    """Contract any camera backend must satisfy. Routes and services only
    ever depend on this interface, never on a concrete implementation."""

    @abstractmethod
    async def connect(self) -> None: ...

    @abstractmethod
    async def disconnect(self) -> None: ...

    @abstractmethod
    async def capture(self) -> Dict[str, Any]: ...

    @abstractmethod
    async def get_status(self) -> Dict[str, Any]: ...
