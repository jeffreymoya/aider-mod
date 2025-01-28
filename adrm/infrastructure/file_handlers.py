from pathlib import Path
from adrm.core.interfaces import FileHandlerStrategy

class LocalFileHandler:
    def __init__(self):
        self._cache = {}

    def handle(self, filepath: Path, content: str) -> None:
        if self._cache.get(filepath) != content:
            filepath.parent.mkdir(parents=True, exist_ok=True)
            filepath.write_text(content, encoding="utf-8")
            self._cache[filepath] = content

# CloudStorageHandler is defined but unused
# class CloudStorageHandler:  # Dead code
#     def handle(self, filepath: Path, content: str):
#         self.client.upload(filepath, content)

# FileHandlerFactory adds unnecessary abstraction
# class FileHandlerFactory: ... 