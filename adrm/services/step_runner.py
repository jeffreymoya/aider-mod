from typing import Optional
import structlog
from pathlib import Path
from aider.coders import Coder
from aider.models import Model
from aider.io import InputOutput
from adrm.core.models import ConfigModel, Step
from adrm.integrations.aider_client import AiderClient
from adrm.infrastructure.file_context import FileContextHandler
from adrm.core.interfaces import FileHandler, StepRunnerClient

class StepRunner:
    def __init__(
        self, 
        config: ConfigModel,
        logger: structlog.BoundLogger,
        file_handler: FileHandler,
        client: StepRunnerClient
    ) -> None:
        self.config = config
        self.logger = logger
        self.file_handler = file_handler
        self.client = client
        self.working_dir = Path.cwd()

    def run_step(self, step: Step) -> None:
        try:
            model_name = step.model_name or self.config.model_name
            api_key = step.api_key or self.config.api_key
            
            if not model_name or not api_key:
                raise ValueError("Missing model configuration")

            # Log the working directory for debugging
            self.logger.debug("executing_step", working_dir=str(self.working_dir))

            # Handle file patterns and non-existent files
            self.file_handler.add_files(step.files)
            files_content = self.file_handler.get_files_content()

            if not files_content:
                self.logger.warning("no_files_found", patterns=step.files)
                return

            self.client.execute_prompt(step.prompt, files_content)
            
        except ValueError as e:
            self.logger.error("configuration_error", error=str(e))
            raise
        except Exception as e:
            self.logger.error("step_execution_failed", error=str(e))
            raise RuntimeError(f"Failed to execute step: {str(e)}") from e 