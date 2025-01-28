import argparse
import subprocess
import sys
from pathlib import Path

def run_command(command):
    try:
        subprocess.run(command, check=True, shell=True)
    except subprocess.CalledProcessError as e:
        print(f"Error executing command: {command}")
        sys.exit(1)

def clean():
    run_command("python setup.py clean --all")

def build():
    clean()
    run_command("python setup.py build")

def install():
    run_command("python setup.py install")

def test():
    run_command("pytest tests/")

def main():
    parser = argparse.ArgumentParser(description="Build script for ADRM")
    parser.add_argument("action", choices=["build", "install", "test", "all"],
                       help="Action to perform")

    args = parser.parse_args()

    if args.action == "build":
        build()
    elif args.action == "install":
        install()
    elif args.action == "test":
        test()
    elif args.action == "all":
        build()
        install()
        test()

if __name__ == "__main__":
    main() 