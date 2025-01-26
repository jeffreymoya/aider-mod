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

    def create_implementation_standards(self, technology: str, content: str) -> None:
        filename = Path(self.config.directories["standards"]) / f"{technology}_implementation_standards{self.config.file_extensions['standards']}"
        handler = StandardFileHandler(filename)
        handler.write(content)
        self.logger.info("created_implementation_standards", technology=technology)

    def create_performance_standards(self, technology: str, content: str) -> None:
        filename = Path(self.config.directories["standards"]) / f"{technology}_performance_standards{self.config.file_extensions['standards']}"
        handler = StandardFileHandler(filename)
        handler.write(content)
        self.logger.info("created_performance_standards", technology=technology)

class Container(containers.DeclarativeContainer):
    config = providers.Singleton(
        lambda: ConfigModel.model_validate_json(Path("config.json").read_text())
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
    handler: str
    params: Dict[str, str] = Field(default_factory=dict)

class StepRunner:
    def __init__(self, coder: Coder, standards_generator: StandardsGenerator, config: ConfigModel):
        self.coder = coder
        self.standards_generator = standards_generator
        self.config = config
        self.handlers = {
            "create_implementation_standards": self._handle_implementation_standards,
            "create_performance_standards": self._handle_performance_standards,
            "create_task_file": self._handle_task_file,
            "create_subtask_spec": self._handle_subtask_spec,
        }

    def run_step(self, step: Step) -> Any:
        response = self.coder.run(step.prompt)
        handler = self.handlers.get(step.handler)
        if not handler:
            raise ValueError(f"Unknown handler: {step.handler}")
        return handler(response, **step.params)

    def _handle_implementation_standards(self, response: str, technology: str, **kwargs) -> None:
        self.standards_generator.create_implementation_standards(technology, response)

    def _handle_performance_standards(self, response: str, technology: str, **kwargs) -> None:
        self.standards_generator.create_performance_standards(technology, response)

    def _handle_task_file(self, response: str, **kwargs) -> None:
        tasks = json.loads(response)
        for task in tasks:
            filename = Path(self.config.directories["tasks"]) / f"{task['task_number']}_{task['task_name']}{self.config.file_extensions['tasks']}"
            content = f"# Task {task['task_number']}: {task['task_name']}\n\n## Subtasks\n"
            StandardFileHandler(filename).write(content)

    def _handle_subtask_spec(self, response: str, task_number: str, **kwargs) -> None:
        subtasks = json.loads(response)
        for subtask in subtasks:
            filename = Path(self.config.directories["specs"]) / f"{task_number}_{subtask['subtask_number']}_{subtask['subtask_name']}{self.config.file_extensions['specs']}"
            spec = {
                "tasks": [
                    {
                        "performance_standard": f"{tech}_performance_standards{self.config.file_extensions['standards']}",
                        "implementation_standard": f"{tech}_implementation_standards{self.config.file_extensions['standards']}",
                        "task_description": f"Implement {subtask['subtask_name']}",
                        "done": False
                    } for tech in self._get_tech_stack()
                ]
            }
            StandardFileHandler(filename).write(json.dumps(spec, indent=2))

    def _get_tech_stack(self) -> List[str]:
        standards_dir = Path(self.config.directories["standards"])
        tech_files = standards_dir.glob(f"*_implementation_standards{self.config.file_extensions['standards']}")
        return [f.stem.replace("_implementation_standards", "") for f in tech_files]

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
        model_config = self.config.model.copy()
        if model_name:
            model_config["name"] = model_name
        if api_key:
            model_config["api_key"] = api_key

        try:
            model = Model(model_config["name"])
            if model_config["api_key"]:
                model.api_key = model_config["api_key"]
            io = InputOutput(yes=self.config.io["auto_confirm"])
            
            fnames = [self.config.files["requirements"], self.config.files["standards"]]
            coder = Coder.create(main_model=model, fnames=fnames, io=io)
            
            step_runner = StepRunner(coder, self.standards_generator, self.config)
            self._run_steps(step_runner)
            
        except Exception as e:
            self.logger.error("aider_initialization_failed", error=str(e))
            raise RuntimeError(f"Failed to initialize Aider: {str(e)}")

    def _run_steps(self, step_runner: StepRunner) -> None:
        steps_file = Path(self.config.files.get("steps", "steps.json"))
        if not steps_file.exists():
            raise FileNotFoundError(f"Steps file not found: {steps_file}")

        try:
            steps_data = json.loads(steps_file.read_text())
            steps = [Step(**step) for step in steps_data]
            
            for step in steps:
                step_runner.run_step(step)
                
        except Exception as e:
            self.logger.error("steps_execution_failed", error=str(e))
            raise RuntimeError(f"Failed to execute steps: {str(e)}")

    def initialize(self, model_name: Optional[str] = None, api_key: Optional[str] = None) -> None:
        try:
            self._validate_model_config(model_name, api_key)
            self._setup_directories()
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
