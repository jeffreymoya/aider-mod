from abc import ABC, abstractmethod
from typing import Protocol, runtime_checkable
from pathlib import Path

@runtime_checkable
class FileHandler(Protocol):
    @abstractmethod
    def read(self) -> str: ...
    
    @abstractmethod
    def write(self, content: str) -> None: ...

class StepRunnerClient(Protocol):
    @abstractmethod
    async def execute_prompt(self, prompt: str, files: list[str]) -> None: ...

class StandardsGenerator(ABC):
    @abstractmethod
    def create_implementation_standards(self, technology: str, content: str) -> None: ...
    
    @abstractmethod
    def create_performance_standards(self, technology: str, content: str) -> None: ...

class ProjectInitializer(ABC):
    @abstractmethod
    def initialize(self, model_name: str | None, api_key: str | None) -> None: ... 