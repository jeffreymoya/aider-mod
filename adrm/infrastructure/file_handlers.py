from pathlib import Path
from adrm.core.interfaces import FileHandler

class LocalFileHandler:
    def __init__(self, filepath: Path = None):
        self._cache = {}
        self.filepath = filepath

    def handle(self, filepath: Path, content: str) -> None:
        filepath = filepath or self.filepath
        if self._cache.get(filepath) != content:
            filepath.parent.mkdir(parents=True, exist_ok=True)
            filepath.write_text(content, encoding="utf-8")
            self._cache[filepath] = content

    def read(self) -> str:
        if not self.filepath:
            raise ValueError("No file path specified")
        return self.filepath.read_text(encoding="utf-8")

    def write(self, content: str) -> None:
        if not self.filepath:
            raise ValueError("No file path specified")
        self.handle(self.filepath, content)

# CloudStorageHandler is defined but unused
# class CloudStorageHandler:  # Dead code
#     def handle(self, filepath: Path, content: str):
#         self.client.upload(filepath, content)

# FileHandlerFactory adds unnecessary abstraction
# class FileHandlerFactory: ... 