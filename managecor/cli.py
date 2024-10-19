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
    if not os.path.exists(CONFIG_PATH):
        update_config()
    with open(CONFIG_PATH, "r") as f:
        return yaml.safe_load(f)


@app.command()
def init():
    """Initialize the managecor environment."""
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
    except requests.RequestException as e:
        typer.echo(f"Failed to update configuration: {e}")


@app.command()
def run(command: List[str] = typer.Argument(...)):
    """Run a command in the Docker container."""
    config = load_config()
    run_docker_command(command, config["docker_image"])


def create_aliases(aliases):
    """Create aliases for common commands."""
    shell = os.environ.get("SHELL", "").split("/")[-1]
    rc_file = f"~/.{shell}rc"

    with open(os.path.expanduser(rc_file), "a") as f:
        for alias, command in aliases.items():
            alias_command = f'alias {alias}="managecor run -- {command}"\n'
            f.write(alias_command)

    typer.echo(
        f"Aliases added to {rc_file}. Please restart your shell or run 'source {rc_file}' to apply changes."
    )


if __name__ == "__main__":
    app()
