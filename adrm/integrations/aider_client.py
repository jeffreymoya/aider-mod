from typing import List, Optional, Type
from pathlib import Path
import structlog
from aider.coders import (
    Coder,
    EditBlockCoder,
    WholeFileCoder,
    ArchitectCoder
)
from aider.models import Model
from aider.io import InputOutput
from adrm.core.models import AiderConfig, AiderCoderConfig
import os
from rich.console import Console

class AiderClient:
    CODER_TYPES = {
        "editblock": EditBlockCoder,
        "wholefile": WholeFileCoder,
        "architect": ArchitectCoder
    }

    def __init__(self, config: AiderConfig, logger: structlog.BoundLogger, console: Optional[Console] = None):
        self.config = config
        self.logger = logger
        self.model = Model(config.model_name)
        api_key = config.api_key or os.getenv("ADRM_API_KEY")
        if not api_key:
            error_message = """
API key not found. Please set your API key using one of these methods:

1. Environment variable:
   export ADRM_API_KEY='your-api-key'

2. Configuration file:
   Update config/config.yaml with your API key

3. Command line:
   adrm init --model gpt-4 --api-key your-api-key

You can get your API key from: https://platform.openai.com/api-keys
"""
            self.logger.error("api_key_not_found")
            raise ValueError(error_message)
            
        self.model.api_key = api_key
        self.console = console or Console()
        self.io = InputOutput(
            yes=config.coder.auto_confirm,
            pretty=config.pretty,
            stream=config.stream_output
        )

    def _get_coder_class(self) -> Type[Coder]:
        coder_type = self.config.coder.type
        if coder_type not in self.CODER_TYPES:
            raise ValueError(f"Unsupported coder type: {coder_type}")
        return self.CODER_TYPES[coder_type]

    def create_coder(self, files: List[str]) -> Coder:
        coder_class = self._get_coder_class()
        
        # Filter files based on include/exclude patterns
        filtered_files = self._filter_files(files)
        
        return coder_class.create(
            main_model=self.model,
            fnames=filtered_files,
            io=self.io,
            allow_edits=self.config.coder.allow_edits,
            git_enabled=self.config.git_enabled,
            chat_history_file=self.config.chat_history_file
        )

    def _filter_files(self, files: List[str]) -> List[str]:
        if not (self.config.coder.include_patterns or self.config.coder.exclude_patterns):
            return files

        import fnmatch
        filtered = []
        for file in files:
            # Check include patterns
            if self.config.coder.include_patterns:
                if not any(fnmatch.fnmatch(file, p) for p in self.config.coder.include_patterns):
                    continue
            
            # Check exclude patterns
            if self.config.coder.exclude_patterns:
                if any(fnmatch.fnmatch(file, p) for p in self.config.coder.exclude_patterns):
                    continue
                    
            filtered.append(file)
        return filtered

    async def execute_prompt(self, prompt: str, files: List[str]) -> None:
        try:
            coder = self.create_coder(files)
            await coder.run(prompt)
        except Exception as e:
            self.logger.error("aider_execution_failed", error=str(e))
            raise 