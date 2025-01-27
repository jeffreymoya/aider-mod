For development installation, clone the repository and install in editable mode:
```bash
git clone https://github.com/jeffreymoya/aider-mod.git
cd aider-mod
pip install -e .
```

## Updating

To update to the latest version:

```bash
pip install --upgrade adrm
```

## Development Setup

1. Create a virtual environment:
```bash
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
```

2. Install development dependencies:
```bash
pip install -r requirements.txt
```

## Running Tests

```bash
pytest tests/
```

## License

This project is licensed under the terms of the LICENSE file.
