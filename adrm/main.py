#!/usr/bin/env python3
import typer
import os
from pathlib import Path
from rich import print
from adrm.core.container import AppContainer
from adrm.services.initializer import ProjectInitializer

app = typer.Typer()

def get_config_locations() -> dict:
    package_dir = Path(__file__).parent.parent
    config_locations = {
        "aider_config": package_dir / "config" / "aider.yaml",
        "steps_config": package_dir / "config" / "steps.json",
    }
    return {k: str(v.absolute()) for k, v in config_locations.items()}

@app.command()
def config():
    """Show configuration file locations"""
    locations = get_config_locations()
    print("\n[bold]Configuration file locations:[/bold]")
    for name, path in locations.items():
        exists = "[green]exists[/green]" if os.path.exists(path) else "[red]not found[/red]"
        print(f"{name}: {path} ({exists})")

@app.command()
def init(model: str = typer.Option(...), api_key: str = typer.Option(...)):
    """Initialize the project with model and API key"""
    try:
        container = AppContainer()
        initializer = ProjectInitializer(
            config=container.config(),
            standards_generator=container.standards_generator(),
            logger=container.logger(),
            console=container.console()
        )
        initializer.initialize(model, api_key)
    except Exception as e:
        typer.secho(f"Error: {str(e)}", fg=typer.colors.RED)
        raise typer.Exit(code=1)

def main():
    app()

if __name__ == "__main__":
    main()
