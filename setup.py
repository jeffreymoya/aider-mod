from setuptools import setup, find_packages

setup(
    name="adrm",
    version="0.1.0",
    packages=find_packages(),
    install_requires=[
        "aider-chat",
        "pydantic>=2.0.0",
        "dependency-injector>=4.41.0",
        "structlog>=23.1.0",
        "rich>=13.3.5",
        "tenacity>=8.2.2",
    ],
    entry_points={
        "console_scripts": [
            "adrm=adrm.main:main",
        ],
    },
    python_requires=">=3.8",
) 