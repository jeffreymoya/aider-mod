from abc import ABC, abstractmethod
from typing import Protocol
from pathlib import Path

class FileHandlerStrategy(Protocol):
    def handle(self, filepath: Path, content: str) -> None: ...

class StandardsGenerator(ABC):
    @abstractmethod
    def create_implementation_standards(self, technology: str, content: str) -> None: ...
    
    @abstractmethod
    def create_performance_standards(self, technology: str, content: str) -> None: ... 