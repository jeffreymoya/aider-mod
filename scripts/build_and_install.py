#!/usr/bin/env python3
import subprocess
import sys
from pathlib import Path
import shutil

def run_command(command: str, allow_non_zero_exit: bool = False) -> bool:
    try:
        result = subprocess.run(command.split(), check=not allow_non_zero_exit)
        return result.returncode == 0 or allow_non_zero_exit
    except subprocess.CalledProcessError as e:
        print(f"Error executing '{command}': {e}")
        return False

def update_config_files(project_root: Path, site_packages: Path) -> None:
    # Create config directory if it doesn't exist
    config_dir = site_packages / "config"
    config_dir.mkdir(exist_ok=True)
    
    # Configuration files to copy
    config_files = {
        "aider.yaml": config_dir / "aider.yaml",  # config/aider.yaml -> site-packages/config/aider.yaml
        "steps.json": site_packages / "steps.json",  # steps.json -> site-packages/steps.json
        "config.json": site_packages / "config.json"  # config.json -> site-packages/config.json
    }
    
    for src_name, dst_path in config_files.items():
        # Handle files in config directory
        if src_name == "aider.yaml":
            src_path = project_root / "config" / src_name
        else:
            src_path = project_root / src_name
            
        if src_path.exists():
            shutil.copy2(src_path, dst_path)
            print(f"Updated {dst_path}")
        else:
            print(f"Warning: Source file {src_path} not found")

def main():
    # Get the project root directory
    project_root = Path(__file__).parent.parent
    
    print("\n1. Building package...")
    if not run_command("poetry build"):
        sys.exit(1)
    
    print("\n2. Installing package...")
    wheel_file = next(project_root.glob("dist/*.whl"))
    if not run_command(f"pip install {wheel_file} --force-reinstall"):
        sys.exit(1)
        
    print("\n✨ Build and installation completed successfully!")
    
    # Update configuration files
    print("\n3. Updating configuration files...")
    site_packages = Path.home() / ".local" / "lib" / "python3.10" / "site-packages"
    update_config_files(project_root, site_packages)
    
    # Test the installation
    print("\n4. Testing installation...")
    if run_command("adrm config"):
        print("\n🎉 Installation verified successfully!")
    else:
        print("\n❌ Installation verification failed!")
        sys.exit(1)

if __name__ == "__main__":
    main() 