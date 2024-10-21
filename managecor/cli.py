import ctypes
import os
import platform
import subprocess
import sys
from typing import List

import requests
import typer
import yaml

from .docker_utils import ensure_docker_image, run_docker_command

app = typer.Typer()

CONFIG_URL = (
    "https://raw.githubusercontent.com/infocornouaille/managecor/main/config.yaml"
)
CONFIG_PATH = os.path.expanduser("~/.managecor_config.yaml")


def is_admin():
    """Check if the script is running with administrative privileges."""
    try:
        return ctypes.windll.shell32.IsUserAnAdmin()
    except:
        return False


def run_as_admin():
    """Restart the script with administrative privileges."""
    ctypes.windll.shell32.ShellExecuteW(
        None, "runas", sys.executable, " ".join(sys.argv), None, 1
    )


def load_config():
    with open(CONFIG_PATH, "r") as f:
        return yaml.safe_load(f)


@app.command()
def init():
    """Initialize the managecor environment."""
    update_config()
    config = load_config()
    ensure_docker_image(config["docker_image"])
    create_aliases(config["aliases"])
    typer.echo("managecor environment initialized successfully!")


@app.command()
def update_config():
    """Update the configuration file from GitHub."""
    try:
        response = requests.get(CONFIG_URL)
        response.raise_for_status()
        with open(CONFIG_PATH, "w") as f:
            f.write(response.text)
        typer.echo("Configuration updated successfully!")
        config = load_config()
        create_aliases(config["aliases"])
    except requests.RequestException as e:
        typer.echo(f"Failed to update configuration: {e}")


@app.command()
def run(command: List[str] = typer.Argument(...)):
    """Run a command in the Docker container."""
    config = load_config()
    run_docker_command(command, config["docker_image"])


def create_aliases(aliases):
    """Create aliases for common commands, avoiding duplications."""

    system = platform.system()

    if system == "Darwin" or system == "Linux":
        shell = os.environ.get("SHELL", "").split("/")[-1]
        if shell == "bash":
            rc_file = "~/.bashrc"
        elif shell == "zsh":
            rc_file = "~/.zshrc"
        else:
            print(f"Unsupported shell: {shell}")
            return
        rc_path = os.path.expanduser(rc_file)

        # Lire le contenu actuel du fichier
        try:
            with open(rc_path, "r") as f:
                current_content = f.read()
        except FileNotFoundError:
            current_content = ""

        # Préparer les nouvelles lignes d'alias
        new_aliases = []
        for alias, command in aliases.items():
            alias_command = f'alias {alias}="managecor run -- {command}"\n'
            if alias_command not in current_content:
                new_aliases.append(alias_command)

        # Ajouter uniquement les nouveaux alias
        if new_aliases:
            with open(rc_path, "a") as f:
                f.writelines(new_aliases)
            typer.echo(f"Added {len(new_aliases)} new aliases to {rc_file}.")
        else:
            typer.echo("No new aliases to add.")

        typer.echo(
            f"Please restart your shell or run 'source {rc_file}' to apply changes."
        )

    elif system == "Windows":
        if not is_admin():
            print(
                "This script needs to be run with administrator privileges to modify the registry."
            )
            print("Attempting to restart with admin privileges...")
            run_as_admin()
            return

        # Pour Windows, nous allons créer un fichier batch avec les alias
        alias_file = os.path.expanduser("~\\Docker_aliases.bat")

        # Préparer les lignes d'alias pour Windows
        alias_lines = []
        for alias, command in aliases.items():
            alias_lines.append(
                f"doskey {alias}=docker run -it --rm -v %cd%:/data infocornouaille/tools:perso {command} $*\n"
            )

        # Écrire les alias dans le fichier batch
        with open(alias_file, "w") as f:
            f.writelines(alias_lines)

        print(f"Created alias file: {alias_file}")

        # Ajouter le fichier batch à l'AutoRun du registre Windows
        try:
            subprocess.run(
                [
                    "reg",
                    "add",
                    "HKCU\\Software\\Microsoft\\Command Processor",
                    "/v",
                    "AutoRun",
                    "/t",
                    "REG_EXPAND_SZ",
                    "/d",
                    f"%UserProfile%\\Docker_aliases.bat",
                    "/f",
                ],
                check=True,
            )
            print(
                "Successfully added aliases to Windows registry. They will be available in new command prompt windows."
            )
        except subprocess.CalledProcessError:
            print(
                "Failed to add aliases to Windows registry. You may need to run this script as an administrator."
            )

    else:
        print(f"Unsupported operating system: {system}")


if __name__ == "__main__":
    app()
