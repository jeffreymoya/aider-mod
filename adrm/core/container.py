from pathlib import Path
import structlog
from rich.console import Console

from adrm.core.models import ConfigModel
from adrm.services.standards import FileSystemStandardsGenerator
from adrm.core.interfaces import (
    FileHandler,
    StandardsGenerator,
    StepRunnerClient
)
from adrm.integrations.aider_client import AiderClient
from adrm.infrastructure.file_handlers import LocalFileHandler

# The container setup seems excessive for current needs
# Consider removing dependency-injector package
# Replace with simple factory functions
# Current DI provides minimal benefit for the number of components

def AppContainer():
    config = ConfigModel.model_validate_json(Path.cwd() / "config.json").read_text()
    
    logger = structlog.wrap_logger(
        structlog.PrintLogger(),
        processors=[
            structlog.processors.TimeStamper(fmt="iso"),
            structlog.processors.JSONRenderer()
        ]
    )
    
    console = Console()
    
    file_handler = LocalFileHandler()
    aider_client = AiderClient(config, logger)
    standards_generator = FileSystemStandardsGenerator(config, logger, file_handler)
    
    return {
        'config': config,
        'logger': logger,
        'console': console,
        'standards_generator': standards_generator,
        'file_handler': file_handler,
        'aider_client': aider_client
    } 