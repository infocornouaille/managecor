import ctypes
import os
import platform
import subprocess
import sys
from typing import List
import time

import requests
import typer
import yaml
from rich import print as rprint
from rich.console import Console
from rich.panel import Panel
from rich.progress import (
    DownloadColumn,
    Progress,
    SpinnerColumn,
    TextColumn,
    TimeRemainingColumn,
    TransferSpeedColumn,
)
from rich.theme import Theme

from .docker_utils import run_docker_command

app = typer.Typer()
console = Console(
    theme=Theme(
        {
            "success": "green bold",
            "error": "red bold",
            "warning": "yellow bold",
            "info": "blue bold",
        }
    )
)

CONFIG_URL = (
    "https://raw.githubusercontent.com/infocornouaille/managecor/main/config.yaml"
)
CONFIG_PATH = os.path.expanduser("../managecor_config.yaml")


def get_image_info(image_name: str):
    """Get information about a Docker image."""
    try:
        result = subprocess.run(
            ["docker", "image", "inspect", image_name],
            capture_output=True,
            text=True,
        )
        if result.returncode == 0:
            image_info = yaml.safe_load(result.stdout)
            return {
                "id": image_info[0]["Id"],
                "size": image_info[0]["Size"],
                "created": image_info[0]["Created"],
            }
    except subprocess.CalledProcessError:
        pass
    return None


def load_config():
    try:
        with open(CONFIG_PATH, "r") as f:
            return yaml.safe_load(f)
    except FileNotFoundError:
        console.print(
            "[error]Configuration file not found. Run 'managecor init' first.[/error]"
        )
        raise typer.Exit(1)
    except yaml.YAMLError:
        console.print("[error]Invalid configuration file format.[/error]")
        raise typer.Exit(1)


def ensure_docker_image(
    image_name: str, force_update: bool = False
) -> tuple[bool, str]:
    """
    Ensure Docker image exists, downloading it if necessary.
    Returns a tuple of (success: bool, message: str)
    """
    try:
        # Check if image exists locally
        result = subprocess.run(
            ["docker", "image", "inspect", image_name], capture_output=True, text=True
        )

        if result.returncode == 0 and not force_update:
            message = f"Docker image {image_name} is already present."
            console.print(f"[info]{message}[/info]")
            return True, message

        console.print(f"[info]Starting pull of image {image_name}...[/info]")

        # Exécuter docker pull avec affichage en temps réel
        pull_result = subprocess.run(
            ["docker", "pull", image_name],
            capture_output=False,  # Permet l'affichage en temps réel
            text=True,
            check=False,  # Ne lève pas d'exception en cas d'erreur
        )

        if pull_result.returncode == 0:
            message = f"Successfully pulled Docker image {image_name}"
            console.print(f"[success]{message}[/success]")
            return True, message

        message = f"Failed to pull Docker image. Return code: {pull_result.returncode}"
        console.print(f"[error]{message}[/error]")
        return False, message

    except subprocess.CalledProcessError as e:
        message = f"Error with Docker: {e}"
        console.print(f"[error]{message}[/error]")
        return False, message
    except Exception as e:
        message = f"Unexpected error: {str(e)}"
        console.print(f"[error]{message}[/error]")
        return False, message


@app.command()
def init():
    """Initialize the managecor environment."""
    console.status("[bold blue]Initializing managecor environment...")
    try:
        update_config()
        config = load_config()
        ensure_docker_image(config["docker_image"])
        console.print(
            Panel.fit(
                "[success]managecor environment initialized successfully![/success]",
                title="Success",
                border_style="green",
            )
        )
    except Exception as e:
        console.print(f"[error]Initialization failed: {str(e)}[/error]")
        raise typer.Exit(1)


@app.command()
def update_config():
    """Update the configuration file from GitHub."""
    console.status("[bold blue]Updating configuration...")
    try:
        response = requests.get(CONFIG_URL)
        response.raise_for_status()
        with open(CONFIG_PATH, "w") as f:
            f.write(response.text)
        console.print("[success]Configuration updated successfully![/success]")
        config = load_config()
    except requests.RequestException as e:
        console.print(f"[error]Failed to update configuration: {e}[/error]")
        raise typer.Exit(1)


@app.command()
def update():
    """Force update the Docker image to the latest version."""
    try:
        config = load_config()
        image_name = config["docker_image"]

        console.status("[bold blue]Checking image status...")
        # Get current image info before update
        current_info = get_image_info(image_name)
        if current_info:
            console.print(f"[info]Current image details:[/info]")
            console.print(f"  ID: {current_info['id']}")
            console.print(f"  Size: {current_info['size']}")
            console.print(f"  Created: {current_info['created']}")

        # Force update the image
        updated, message = ensure_docker_image(image_name, force_update=True)

        if updated:
            # Get new image info
            new_info = get_image_info(image_name)
            if new_info:
                console.print(
                    f"\n[success]Update successful! New image details:[/success]"
                )
                console.print(f"  ID: {new_info['id']}")
                console.print(f"  Size: {new_info['size']}")
                console.print(f"  Created: {new_info['created']}")
        else:
            console.print(f"\n[info]{message}[/info]")

    except Exception as e:
        console.print(f"[error]Failed to update Docker image: {str(e)}[/error]")
        raise typer.Exit(1)


@app.command()
def run(command: List[str] = typer.Argument(...)):
    """Run a command in the Docker container."""
    try:
        config = load_config()
        console.status(f"[bold blue]Running command: {' '.join(command)}...")
        run_docker_command(command, config["docker_image"])
    except Exception as e:
        console.print(f"[error]Command execution failed: {str(e)}[/error]")
        raise typer.Exit(1)


if __name__ == "__main__":
    app()
