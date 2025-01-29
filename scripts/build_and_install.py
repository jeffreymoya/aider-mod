#!/usr/bin/env python3
import subprocess
import sys
from pathlib import Path
import shutil
import hashlib
import json
from pkg_resources import get_distribution

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

def get_source_files_hash(project_root: Path) -> str:
    source_files = []
    for ext in ('*.py', '*.yaml', '*.json'):
        source_files.extend(project_root.rglob(ext))
    
    hasher = hashlib.md5()
    for file in sorted(source_files):
        if 'dist' not in str(file) and 'build' not in str(file):
            hasher.update(file.read_bytes())
    return hasher.hexdigest()

def get_package_dependencies(project_root: Path) -> dict:
    pyproject_file = project_root / "pyproject.toml"
    if not pyproject_file.exists():
        return {}
    
    try:
        result = subprocess.run(["poetry", "export", "--format", "requirements.txt"], 
                              capture_output=True, text=True, check=True)
        deps = {}
        for line in result.stdout.splitlines():
            if "==" in line:
                name, version = line.split("==", 1)
                deps[name] = version.split(";")[0]  # Remove any platform specifiers
        return deps
    except subprocess.CalledProcessError:
        return {}

def check_dependencies_changed(project_root: Path, cache_file: Path) -> bool:
    current_deps = get_package_dependencies(project_root)
    deps_cache_file = cache_file.with_suffix('.deps')
    
    if not deps_cache_file.exists():
        deps_cache_file.write_text(json.dumps(current_deps))
        return True
        
    cached_deps = json.loads(deps_cache_file.read_text())
    if current_deps != cached_deps:
        deps_cache_file.write_text(json.dumps(current_deps))
        return True
        
    return False

def main():
    project_root = Path(__file__).parent.parent
    cache_file = project_root / '.build_cache'
    
    print("\n1. Checking build cache...")
    current_hash = get_source_files_hash(project_root)
    
    should_build = True
    if cache_file.exists():
        cached_hash = cache_file.read_text().strip()
        if cached_hash == current_hash:
            print("No changes detected, skipping build...")
            should_build = False
    
    if should_build:
        print("\n2. Building package...")
        if not run_command("poetry build"):
            sys.exit(1)
        cache_file.write_text(current_hash)
    
    print("\n3. Installing package...")
    wheel_file = next(project_root.glob("dist/*.whl"))
    
    # Check if dependencies have changed
    deps_changed = check_dependencies_changed(project_root, cache_file)
    install_cmd = f"pip install {wheel_file}"
    if deps_changed:
        print("Dependencies have changed, forcing reinstall...")
        install_cmd += " --force-reinstall"
    else:
        print("Dependencies unchanged, performing minimal install...")
    
    if not run_command(install_cmd):
        sys.exit(1)
        
    print("\n✨ Build and installation completed successfully!")
    
    # Update configuration files
    print("\n4. Updating configuration files...")
    site_packages = Path.home() / ".local" / "lib" / "python3.10" / "site-packages"
    update_config_files(project_root, site_packages)
    
    # Test the installation
    print("\n5. Testing installation...")
    if run_command("adrm config"):
        print("\n🎉 Installation verified successfully!")
    else:
        print("\n❌ Installation verification failed!")
        sys.exit(1)

if __name__ == "__main__":
    main() 