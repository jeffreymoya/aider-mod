from pathlib import Path
import structlog
from rich.console import Console

from adrm.core.models import ConfigModel
from adrm.services.standards import FileSystemStandardsGenerator

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
    
    standards_generator = FileSystemStandardsGenerator(
        config=config,
        logger=logger
    )
    
    return {
        'config': config,
        'logger': logger,
        'console': console,
        'standards_generator': standards_generator
    } 