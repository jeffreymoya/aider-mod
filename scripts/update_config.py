#!/usr/bin/env python3
import os
import shutil
from pathlib import Path
import typer
from rich import print

app = typer.Typer()

def get_site_packages_path() -> Path:
    import site
    user_site = site.getusersitepackages()
    return Path(user_site)

def get_config_files() -> dict:
    workspace_root = Path(__file__).parent.parent
    return {
        "config/config.yaml": "config/config.yaml",
        "steps.json": "steps.json"
    }

def update_config_files(site_packages_path: Path, force: bool = False) -> None:
    workspace_root = Path(__file__).parent.parent
    config_dir = site_packages_path / "config"
    config_dir.mkdir(parents=True, exist_ok=True)

    config_files = get_config_files()
    
    for src_rel, dest_rel in config_files.items():
        src_path = workspace_root / src_rel
        dest_path = site_packages_path / dest_rel
        
        if not src_path.exists():
            print(f"[yellow]Warning:[/yellow] Source file not found: {src_path}")
            continue
            
        if dest_path.exists() and not force:
            print(f"[yellow]Skipping:[/yellow] {dest_path} already exists. Use --force to overwrite.")
            continue
            
        # Create parent directories if they don't exist
        dest_path.parent.mkdir(parents=True, exist_ok=True)
        
        # Copy the file
        shutil.copy2(src_path, dest_path)
        print(f"[green]Updated:[/green] {dest_path}")

@app.command()
def update(
    force: bool = typer.Option(
        False,
        "--force",
        "-f",
        help="Force update even if files exist"
    )
):
    """Update ADRM configuration files in the installed package."""
    try:
        site_packages = get_site_packages_path()
        print(f"\n[bold]Updating configuration files in:[/bold] {site_packages}")
        update_config_files(site_packages, force)
        print("\n[bold green]Configuration update complete![/bold green]")
    except Exception as e:
        print(f"\n[bold red]Error:[/bold red] {str(e)}")
        raise typer.Exit(code=1)

if __name__ == "__main__":
    app() 