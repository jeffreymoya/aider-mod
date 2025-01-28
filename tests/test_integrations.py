import pytest
from unittest.mock import Mock, patch
from pathlib import Path
from adrm.integrations.aider_client import AiderClient
from adrm.core.models import AiderConfig, AiderCoderConfig

@pytest.fixture
def mock_logger():
    return Mock()

@pytest.fixture
def test_config():
    return AiderConfig(
        model_name="test-model",
        api_key="test-key",
        coder=AiderCoderConfig(
            type="editblock",
            include_patterns=["*.py"],
            exclude_patterns=["tests/*"]
        )
    )

class TestAiderClient:
    @pytest.mark.asyncio
    async def test_execute_prompt(self, test_config, mock_logger):
        with patch("aider.coders.EditBlockCoder.create") as mock_create:
            mock_coder = Mock()
            mock_create.return_value = mock_coder
            
            client = AiderClient(test_config, mock_logger)
            await client.execute_prompt("test prompt", ["test.py", "tests/test.py"])
            
            # Should only include test.py after filtering
            mock_create.assert_called_once()
            assert mock_create.call_args[1]["fnames"] == ["test.py"]
            mock_coder.run.assert_called_once_with("test prompt")

    def test_invalid_coder_type(self, mock_logger):
        config = AiderConfig(
            model_name="test-model",
            api_key="test-key",
            coder=AiderCoderConfig(type="invalid")  # type: ignore
        )
        with pytest.raises(ValueError, match="Unsupported coder type"):
            AiderClient(config, mock_logger)

    def test_file_filtering(self, test_config, mock_logger):
        client = AiderClient(test_config, mock_logger)
        files = [
            "src/main.py",
            "tests/test_main.py",
            "README.md"
        ]
        filtered = client._filter_files(files)
        assert filtered == ["src/main.py"] 