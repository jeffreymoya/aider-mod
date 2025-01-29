from typing import Dict, List, Optional, Literal
from pydantic import BaseModel, Field, validator, field_validator
import os

class AiderCoderConfig(BaseModel):
    type: Literal["editblock", "wholefile", "udiff", "architect"] = "editblock"
    allow_edits: bool = True
    auto_confirm: bool = True
    include_patterns: List[str] = Field(default_factory=list)
    exclude_patterns: List[str] = Field(default_factory=list)

class AiderConfig(BaseModel):
    model_name: str = Field(..., min_length=1)
    api_key: Optional[str] = None
    default_files: List[str] = Field(default_factory=list)
    coder: AiderCoderConfig = Field(default_factory=AiderCoderConfig)
    chat_history_file: Optional[str] = ".aider.chat.history.md"
    git_enabled: bool = True
    stream_output: bool = True
    pretty: bool = True

class ConfigModel(BaseModel):
    directories: Dict[str, str] = Field(default_factory=dict)
    files: Dict[str, str] = Field(default_factory=dict)
    model: Dict[str, str] = Field(default_factory=dict)
    io: Dict[str, str] = Field(default_factory=dict)
    file_extensions: Dict[str, List[str]] = Field(default_factory=dict)
    openai_api_key: Optional[str] = Field(default=None)
    openai_model: str = Field(default="gpt-4")
    temperature: float = Field(default=0.7)
    aider_config: Optional[dict] = Field(default_factory=dict)

    @field_validator("directories")
    @classmethod
    def validate_directories(cls, v: Dict[str, str]) -> Dict[str, str]:
        if not v:
            raise ValueError("At least one directory must be specified")
        return v

    @field_validator("files")
    @classmethod
    def validate_files(cls, v: Dict[str, str]) -> Dict[str, str]:
        if not v:
            raise ValueError("At least one file must be specified")
        return v

    @field_validator("aider_config")
    @classmethod
    def validate_aider_config(cls, v: Optional[dict]) -> dict:
        if v is None:
            return {}
        return v

class Step(BaseModel):
    prompt: str
    files: List[str] = Field(default_factory=list, description="List of file patterns to include")
    allow_edits: bool = True
    model_name: Optional[str] = None
    api_key: Optional[str] = None

    @field_validator("files")
    @classmethod
    def validate_files(cls, v):
        if not v:
            return []
        return [str(path) for path in v]  # Convert all paths to strings 