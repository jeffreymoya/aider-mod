import os
import json
from pathlib import Path
import structlog
from rich.console import Console
from typing import Optional

from adrm.core.models import ConfigModel, Step
from adrm.core.interfaces import StandardsGenerator
from adrm.services.step_runner import StepRunner

class ProjectInitializer:
    def __init__(
        self,
        config: ConfigModel,
        standards_generator: StandardsGenerator,
        logger: structlog.BoundLogger,
        console: Console,
        step_runner: StepRunner
    ):
        self.config = config
        self.standards_generator = standards_generator
        self.logger = logger
        self.console = console
        self.step_runner = step_runner

    def _validate_model_config(self, model_name: Optional[str], api_key: Optional[str]) -> None:
        if model_name and not isinstance(model_name, str):
            raise ValueError("Model name must be a string")
        if api_key and not isinstance(api_key, str):
            raise ValueError("API key must be a string")
        if api_key and len(api_key) < 20:  # Basic validation
            raise ValueError("Invalid API key format")

    def _setup_directories(self) -> None:
        for directory in self.config.directories.values():
            Path(directory).mkdir(parents=True, exist_ok=True)

    def _initialize_aider(self, model_name: Optional[str], api_key: Optional[str]) -> None:
        try:
            self._setup_directories()
            self._run_steps(model_name, api_key)
            
        except Exception as e:
            self.logger.error("aider_initialization_failed", error=str(e))
            raise RuntimeError(f"Failed to initialize Aider: {str(e)}")

    def _run_steps(self, model_name: Optional[str], api_key: Optional[str]) -> None:
        steps_file = Path.cwd() / self.config.files.get("steps", "steps.json")
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
                step.files = [str(Path.cwd() / f) for f in step.files]
                self.step_runner.run_step(step)
                
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