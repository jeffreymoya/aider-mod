from pathlib import Path
import structlog
from adrm.core.interfaces import StandardsGenerator
from adrm.core.models import ConfigModel
from adrm.infrastructure.file_handlers import LocalFileHandler

def create_standard_file(standard_type: str, technology: str, content: str):
    path = f"{technology}_{standard_type}.md"
    Path(path).write_text(content)

class FileSystemStandardsGenerator(StandardsGenerator):
    def __init__(self, config: ConfigModel, logger: structlog.BoundLogger):
        self.config = config
        self.logger = logger
        self.base_path = Path.cwd()
        self.file_handler = LocalFileHandler()

    def create_implementation_standards(self, technology: str, content: str) -> None:
        filename = self.base_path / self.config.directories["standards"] / f"{technology}_implementation_standards{self.config.file_extensions['standards']}"
        self.file_handler.handle(filename, content)
        self.logger.info("created_implementation_standards", technology=technology)

    def create_performance_standards(self, technology: str, content: str) -> None:
        filename = self.base_path / self.config.directories["standards"] / f"{technology}_performance_standards{self.config.file_extensions['standards']}"
        self.file_handler.handle(filename, content)
        self.logger.info("created_performance_standards", technology=technology) 