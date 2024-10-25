import os
import subprocess
from typing import List

import docker
from rich.console import Console
from rich.progress import (
    BarColumn,
    DownloadColumn,
    Progress,
    SpinnerColumn,
    TextColumn,
    TimeRemainingColumn,
    TransferSpeedColumn,
)
from rich.theme import Theme

# Create a consistent console instance with the same theme as cli.py
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


def ensure_docker_image(image_name: str, force_update: bool = False):
    """
    Ensure that the specified Docker image is available locally.
    If force_update is True, pulls the latest version regardless of local availability.
    Returns a tuple (updated: bool, message: str)
    """
    client = docker.from_env()
    try:
        if not force_update:
            local_image = client.images.get(image_name)
            console.print(
                f"[info]Docker image {image_name} is already available.[/info]"
            )
            return False, "Image already present"

        # Get the current image digest if it exists
        old_digest = None
        try:
            old_image = client.images.get(image_name)
            old_digest = old_image.id
        except docker.errors.ImageNotFound:
            pass

        with Progress(
            SpinnerColumn(),
            TextColumn("[progress.description]{task.description}"),
            BarColumn(),
            DownloadColumn(),
            TransferSpeedColumn(),
            TimeRemainingColumn(),
            console=console,
        ) as progress:
            task = progress.add_task(
                f"[cyan]{'Updating' if force_update else 'Pulling'} Docker image {image_name}",
                total=1000,
            )

            for chunk in client.api.pull(image_name, stream=True, decode=True):
                if "status" in chunk:
                    status = chunk["status"]
                    if "progress" in chunk:
                        status = f"{status}: {chunk['progress']}"
                    progress.update(task, description=f"[cyan]{status}")

                    if "Downloading" in status:
                        progress.update(task, advance=5)
                    elif "Extracting" in status:
                        progress.update(task, advance=10)
                    elif "Pull complete" in status:
                        progress.update(task, advance=100)

            progress.update(task, completed=1000)

        # Check if the image was actually updated
        new_image = client.images.get(image_name)
        if old_digest and old_digest == new_image.id:
            console.print(
                f"[info]Image {image_name} is already at the latest version.[/info]"
            )
            return False, "Already at latest version"
        else:
            console.print(
                f"[success]{'Updated' if force_update else 'Pulled'} Docker image {image_name} successfully![/success]"
            )
            # Remove old image if it exists and was different
            if old_digest and old_digest != new_image.id:
                try:
                    client.images.remove(old_digest, force=True)
                    console.print("[info]Removed old image version.[/info]")
                except Exception as e:
                    console.print(f"[warning]Could not remove old image: {e}[/warning]")
            return True, "Image updated successfully"

    except docker.errors.ImageNotFound:
        # Handle initial pull
        return ensure_docker_image(image_name, force_update=False)
    except Exception as e:
        console.print(f"[error]Error managing Docker image: {str(e)}[/error]")
        raise e


def run_docker_command(command: List[str], image_name: str):
    """
    Run a command in the Docker container with enhanced output formatting.
    """
    full_command = [
        "docker",
        "run",
        "-it",
        "--rm",
        "-v",
        f"{os.getcwd()}:/data",
        image_name,
    ] + command

    console.status(f"[info]Running command in container: {' '.join(command)}[/info]")
    try:
        process = subprocess.run(full_command, text=True, capture_output=True)

        if process.returncode == 0:
            if process.stdout:
                console.print(process.stdout)
            console.print("[success]Command completed successfully![/success]")
        else:
            if process.stderr:
                console.print(f"[error]Error output:[/error]\n{process.stderr}")
            console.print(
                f"[error]Command failed with return code {process.returncode}[/error]"
            )

    except subprocess.CalledProcessError as e:
        console.print(f"[error]Failed to execute command: {str(e)}[/error]")
    except Exception as e:
        console.print(f"[error]Unexpected error: {str(e)}[/error]")


def format_size(size: int) -> str:
    """Format size in bytes to human readable format."""
    for unit in ["B", "KB", "MB", "GB"]:
        if size < 1024.0:
            return f"{size:.1f} {unit}"
        size /= 1024.0
    return f"{size:.1f} TB"


def get_image_info(image_name: str) -> dict:
    """Get detailed information about a Docker image."""
    client = docker.from_env()
    try:
        image = client.images.get(image_name)
        return {
            "id": image.short_id,
            "tags": image.tags,
            "size": format_size(image.attrs["Size"]),
            "created": image.attrs["Created"],
        }
    except docker.errors.ImageNotFound:
        return None
    except Exception as e:
        console.print(f"[error]Error getting image info: {str(e)}[/error]")
        return None
