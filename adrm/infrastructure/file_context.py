from pathlib import Path
import glob
from typing import List, Optional, Dict
import typer
import os

class FileContextHandler:
    def __init__(self):
        self.files_content: Dict[str, str] = {}
        self.working_dir = Path.cwd()

    def add_files(self, patterns: List[str]) -> None:
        for pattern in patterns:
            if '*' in pattern:
                self._handle_glob_pattern(pattern)
            else:
                self._handle_single_file(pattern)

    def _handle_glob_pattern(self, pattern: str) -> None:
        # Use os.path.join to ensure proper path handling on all platforms
        full_pattern = os.path.join(str(self.working_dir), pattern)
        matched_files = glob.glob(full_pattern, recursive=True)
        
        if not matched_files:
            typer.echo(f"Warning: No files matched pattern '{pattern}'")
            return
            
        for file_path in matched_files:
            # Convert absolute path back to relative for consistency
            relative_path = os.path.relpath(file_path, self.working_dir)
            self._handle_single_file(relative_path)

    def _handle_single_file(self, file_path: str) -> None:
        # Resolve path relative to working directory
        full_path = self.working_dir / file_path
        
        if not full_path.exists():
            content = self._prompt_for_content(file_path)
            if content:
                self.files_content[file_path] = content
                # Create the file in the correct location
                full_path.parent.mkdir(parents=True, exist_ok=True)
                full_path.write_text(content)
        else:
            self.files_content[file_path] = full_path.read_text()

    def _prompt_for_content(self, file_path: str) -> Optional[str]:
        create_file = typer.confirm(
            f"File '{file_path}' does not exist. Would you like to create it?",
            default=True
        )
        
        if create_file:
            content = typer.edit(
                suffix=f".{Path(file_path).suffix}",
                text=f"# Enter content for {file_path}\n"
            )
            if content is not None:
                return content
        return None

    def get_files_content(self) -> Dict[str, str]:
        return self.files_content 