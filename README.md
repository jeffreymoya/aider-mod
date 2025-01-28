For development installation, clone the repository and install in editable mode:
```bash
git clone https://github.com/jeffreymoya/aider-mod.git
cd aider-mod
```

## Development Setup

1. Install Poetry (if not already installed):
```bash
curl -sSL https://install.python-poetry.org | python3 -
```

2. Install dependencies and create virtual environment:
```bash
poetry install
```

3. Activate the virtual environment:
```bash
poetry shell
```

## Common Commands

```bash
# Build the project
poetry build

# Install the project in development mode
poetry install

# Run tests
poetry run pytest

# Update dependencies
poetry update

# Add a new dependency
poetry add package_name

# Add a development dependency
poetry add --group dev package_name
```

## License

This project is licensed under the terms of the LICENSE file.

## Features
- Configuration management
- Standards generation
- Step-based workflow execution

## Configuration
| Environment Variable | Description          |
|----------------------|----------------------|
| ADRM_API_KEY         | OpenAI API key       |
| ADRM_MODEL           | Default model name   |
