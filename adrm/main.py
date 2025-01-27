#!/usr/bin/env python3
from aider.coders import Coder
from aider.models import Model
from aider.io import InputOutput
import os
import json
import argparse
from typing import Dict, List, Optional, Protocol, Any
from pathlib import Path
from pydantic import BaseModel, Field
from dependency_injector import containers, providers
from abc import ABC, abstractmethod
import structlog
from rich.console import Console
from tenacity import retry, stop_after_attempt, wait_exponential

class ConfigModel(BaseModel):
    directories: Dict[str, str] = Field(...)
    files: Dict[str, str] = Field(...)
    model: Dict[str, Optional[str]] = Field(...)
    io: Dict[str, bool] = Field(...)
    file_extensions: Dict[str, str] = Field(...)

class FileHandler(Protocol):
    def write(self, content: str) -> None: ...
    def read(self) -> str: ...

class StandardFileHandler:
    def __init__(self, filepath: Path):
        self.filepath = filepath

    @retry(stop=stop_after_attempt(3), wait=wait_exponential(multiplier=1, min=4, max=10))
    def write(self, content: str) -> None:
        self.filepath.parent.mkdir(parents=True, exist_ok=True)
        self.filepath.write_text(content, encoding="utf-8")

    def read(self) -> str:
        return self.filepath.read_text(encoding="utf-8")

class StandardsGenerator(ABC):
    @abstractmethod
    def create_implementation_standards(self, technology: str, content: str) -> None: ...
    @abstractmethod
    def create_performance_standards(self, technology: str, content: str) -> None: ...

class FileSystemStandardsGenerator(StandardsGenerator):
    def __init__(self, config: ConfigModel, logger: structlog.BoundLogger):
        self.config = config
        self.logger = logger
        self.base_path = Path(os.getcwd())

    def create_implementation_standards(self, technology: str, content: str) -> None:
        filename = self.base_path / self.config.directories["standards"] / f"{technology}_implementation_standards{self.config.file_extensions['standards']}"
        handler = StandardFileHandler(filename)
        handler.write(content)
        self.logger.info("created_implementation_standards", technology=technology)

    def create_performance_standards(self, technology: str, content: str) -> None:
        filename = self.base_path / self.config.directories["standards"] / f"{technology}_performance_standards{self.config.file_extensions['standards']}"
        handler = StandardFileHandler(filename)
        handler.write(content)
        self.logger.info("created_performance_standards", technology=technology)

class Container(containers.DeclarativeContainer):
    config = providers.Singleton(
        lambda: ConfigModel.model_validate_json(Path(os.getcwd()) / "config.json").read_text()
    )
    logger = providers.Singleton(
        structlog.wrap_logger,
        structlog.PrintLogger(),
        processors=[
            structlog.processors.TimeStamper(fmt="iso"),
            structlog.processors.JSONRenderer()
        ]
    )
    console = providers.Singleton(Console)
    standards_generator = providers.Singleton(
        FileSystemStandardsGenerator,
        config=config,
        logger=logger
    )

class Step(BaseModel):
    prompt: str
    files: List[str] = Field(default_factory=list)  # Files to include for context and editing
    allow_edits: bool = True
    model_name: Optional[str] = None
    api_key: Optional[str] = None

class StepRunner:
    def __init__(self, config: ConfigModel, logger: structlog.BoundLogger):
        self.config = config
        self.logger = logger

    def run_step(self, step: Step) -> None:
        try:
            model_config = self.config.model.copy()
            if step.model_name:
                model_config["name"] = step.model_name
            if step.api_key:
                model_config["api_key"] = step.api_key

            model = Model(model_config["name"])
            if model_config["api_key"]:
                model.api_key = model_config["api_key"]

            io = InputOutput(yes=self.config.io["auto_confirm"])
            
            # Get list of files for context
            context_files = []
            if step.files:
                context_files.extend(step.files)
            
            # Create coder with context files
            coder = Coder.create(
                main_model=model,
                fnames=context_files,  # Pass context files to Coder
                io=io,
                allow_edits=step.allow_edits
            )
            
            coder.run(step.prompt)
            
        except Exception as e:
            self.logger.error("step_execution_failed", error=str(e))
            raise RuntimeError(f"Failed to execute step: {str(e)}")

class ProjectInitializer:
    def __init__(
        self,
        config: ConfigModel,
        standards_generator: StandardsGenerator,
        logger: structlog.BoundLogger,
        console: Console
    ):
        self.config = config
        self.standards_generator = standards_generator
        self.logger = logger
        self.console = console

    def _validate_model_config(self, model_name: Optional[str], api_key: Optional[str]) -> None:
        if model_name and not isinstance(model_name, str):
            raise ValueError("Model name must be a string")
        if api_key and not isinstance(api_key, str):
            raise ValueError("API key must be a string")

    def _setup_directories(self) -> None:
        for directory in self.config.directories.values():
            Path(directory).mkdir(parents=True, exist_ok=True)

    def _initialize_aider(self, model_name: Optional[str], api_key: Optional[str]) -> None:
        try:
            self._setup_directories()
            step_runner = StepRunner(self.config, self.logger)
            self._run_steps(step_runner, model_name, api_key)
            
        except Exception as e:
            self.logger.error("aider_initialization_failed", error=str(e))
            raise RuntimeError(f"Failed to initialize Aider: {str(e)}")

    def _run_steps(self, step_runner: StepRunner, model_name: Optional[str], api_key: Optional[str]) -> None:
        steps_file = Path(os.getcwd()) / self.config.files.get("steps", "steps.json")
        if not steps_file.exists():
            raise FileNotFoundError(f"Steps file not found: {steps_file}")

        try:
            steps_data = json.loads(steps_file.read_text())
            steps = [Step(**step) for step in steps_data]
            
            for step in steps:
                if not step.model_name:
                    step.model_name = model_name
                if not step.api_key:
                    step.api_key = api_key
                # Convert file paths to be relative to current working directory
                step.files = [str(Path(os.getcwd()) / f) for f in step.files]
                step_runner.run_step(step)
                
        except Exception as e:
            self.logger.error("steps_execution_failed", error=str(e))
            raise RuntimeError(f"Failed to execute steps: {str(e)}")

    def initialize(self, model_name: Optional[str] = None, api_key: Optional[str] = None) -> None:
        try:
            self._validate_model_config(model_name, api_key)
            self._initialize_aider(model_name, api_key)
        except Exception as e:
            self.logger.error("initialization_failed", error=str(e))
            raise RuntimeError(f"Project initialization failed: {str(e)}")

def main() -> None:
    container = Container()
    parser = argparse.ArgumentParser(description="Initialize project with specified LLM model")
    parser.add_argument("--model", help="Name of the LLM model to use")
    parser.add_argument("--api-key", help="API key for the LLM model")
    args = parser.parse_args()

    try:
        initializer = ProjectInitializer(
            config=container.config(),
            standards_generator=container.standards_generator(),
            logger=container.logger(),
            console=container.console()
        )
        initializer.initialize(args.model, args.api_key)
    except Exception as e:
        container.console().print(f"[red]Error: {str(e)}[/red]")
        exit(1)

if __name__ == "__main__":
    main()
