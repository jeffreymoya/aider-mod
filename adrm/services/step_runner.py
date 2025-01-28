from typing import Optional
import structlog
from pathlib import Path
from aider.coders import Coder
from aider.models import Model
from aider.io import InputOutput
from adrm.core.models import ConfigModel, Step
from adrm.integrations.aider_client import AiderClient
from adrm.infrastructure.file_context import FileContextHandler

class StepRunner:
    def __init__(self, config: ConfigModel, logger: structlog.BoundLogger) -> None:
        self.config = config
        self.logger = logger
        self._client: Optional[AiderClient] = None
        self.file_context = FileContextHandler()
        self.working_dir = Path.cwd()

    def _get_client(self, model_name: str, api_key: str) -> AiderClient:
        if not self._client:
            self._client = AiderClient(model_name, api_key)
        return self._client

    def run_step(self, step: Step) -> None:
        try:
            model_name = step.model_name or self.config.model_name
            api_key = step.api_key or self.config.api_key
            
            if not model_name or not api_key:
                raise ValueError("Missing model configuration")

            # Log the working directory for debugging
            self.logger.debug("executing_step", working_dir=str(self.working_dir))

            # Handle file patterns and non-existent files
            self.file_context.add_files(step.files)
            files_content = self.file_context.get_files_content()

            if not files_content:
                self.logger.warning("no_files_found", patterns=step.files)
                return

            client = self._get_client(model_name, api_key)
            client.execute_prompt(step.prompt, files_content)
            
        except ValueError as e:
            self.logger.error("configuration_error", error=str(e))
            raise
        except Exception as e:
            self.logger.error("step_execution_failed", error=str(e))
            raise RuntimeError(f"Failed to execute step: {str(e)}") from e 