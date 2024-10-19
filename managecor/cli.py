import typer
import os
import subprocess
import yaml
import requests
from typing import List
from .docker_utils import ensure_docker_image, run_docker_command

app = typer.Typer()

CONFIG_URL = (
    "https://raw.githubusercontent.com/infocornouaille/managecor/main/config.yaml"
)
CONFIG_PATH = os.path.expanduser("~/.managecor_config.yaml")


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
    shell = os.environ.get("SHELL", "").split("/")[-1]
    rc_file = f"~/.{shell}rc"
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

    typer.echo(f"Please restart your shell or run 'source {rc_file}' to apply changes.")


if __name__ == "__main__":
    app()
