from abc import ABC, abstractmethod


class GPIOInterface(ABC):
    """Contract for future Raspberry Pi GPIO interactions (status LEDs,
    trigger buttons, sensors). Not implemented yet — no hardware to target."""

    @abstractmethod
    def set_output(self, pin: int, value: bool) -> None: ...

    @abstractmethod
    def read_input(self, pin: int) -> bool: ...
