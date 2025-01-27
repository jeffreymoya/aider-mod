import pytest
from pathlib import Path
import json
import structlog
from rich.console import Console
from adrm.main import (
    ConfigModel,
    StandardFileHandler,
    FileSystemStandardsGenerator,
    ProjectInitializer,
    StepRunner,
    Step,
)

@pytest.fixture
def test_config():
    return ConfigModel(
        directories={
            "standards": "test_standards",
            "docs": "test_docs"
        },
        files={
            "steps": "test_steps.json"
        },
        model={
            "name": "test-model",
            "api_key": "test-key"
        },
        io={
            "auto_confirm": True
        },
        file_extensions={
            "standards": ".md"
        }
    )

@pytest.fixture
def test_logger():
    return structlog.wrap_logger(structlog.PrintLogger())

@pytest.fixture
def test_console():
    return Console()

@pytest.fixture
def temp_dir(tmp_path):
    return tmp_path

class TestStandardFileHandler:
    def test_write_and_read(self, temp_dir):
        test_content = "Test content"
        test_file = temp_dir / "test.txt"
        handler = StandardFileHandler(test_file)
        
        handler.write(test_content)
        assert handler.read() == test_content
        assert test_file.exists()

    def test_write_creates_parent_directories(self, temp_dir):
        nested_file = temp_dir / "nested" / "dir" / "test.txt"
        handler = StandardFileHandler(nested_file)
        
        handler.write("test")
        assert nested_file.exists()

class TestFileSystemStandardsGenerator:
    def test_create_implementation_standards(self, temp_dir, test_config, test_logger):
        test_config.directories["standards"] = str(temp_dir)
        generator = FileSystemStandardsGenerator(test_config, test_logger)
        
        generator.create_implementation_standards("python", "Test standards")
        expected_file = temp_dir / "python_implementation_standards.md"
        assert expected_file.exists()
        assert expected_file.read_text() == "Test standards"

    def test_create_performance_standards(self, temp_dir, test_config, test_logger):
        test_config.directories["standards"] = str(temp_dir)
        generator = FileSystemStandardsGenerator(test_config, test_logger)
        
        generator.create_performance_standards("python", "Test performance")
        expected_file = temp_dir / "python_performance_standards.md"
        assert expected_file.exists()
        assert expected_file.read_text() == "Test performance"

class TestStepRunner:
    def test_run_step_validation(self, test_config, test_logger):
        runner = StepRunner(test_config, test_logger)
        step = Step(
            prompt="Test prompt",
            files=["test.py"],
            model_name="test-model",
            api_key="test-key"
        )
        
        with pytest.raises(RuntimeError):
            runner.run_step(step)

class TestProjectInitializer:
    def test_validate_model_config(self, test_config, test_logger, test_console):
        generator = FileSystemStandardsGenerator(test_config, test_logger)
        initializer = ProjectInitializer(test_config, generator, test_logger, test_console)
        
        with pytest.raises(ValueError):
            initializer._validate_model_config(123, "key")
        
        with pytest.raises(ValueError):
            initializer._validate_model_config("model", 123)
        
        initializer._validate_model_config("valid-model", "valid-key")

    def test_setup_directories(self, temp_dir, test_config, test_logger, test_console):
        test_config.directories = {
            "test1": str(temp_dir / "test1"),
            "test2": str(temp_dir / "test2")
        }
        
        generator = FileSystemStandardsGenerator(test_config, test_logger)
        initializer = ProjectInitializer(test_config, generator, test_logger, test_console)
        
        initializer._setup_directories()
        
        assert (temp_dir / "test1").exists()
        assert (temp_dir / "test2").exists()

    def test_initialize_missing_steps_file(self, temp_dir, test_config, test_logger, test_console):
        test_config.files["steps"] = str(temp_dir / "nonexistent_steps.json")
        generator = FileSystemStandardsGenerator(test_config, test_logger)
        initializer = ProjectInitializer(test_config, generator, test_logger, test_console)
        
        with pytest.raises(RuntimeError):
            initializer.initialize("test-model", "test-key")
