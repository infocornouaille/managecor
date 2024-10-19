import docker
import typer
import subprocess
import os


def ensure_docker_image(image_name: str):
    """Ensure that the specified Docker image is available locally."""
    client = docker.from_env()
    try:
        client.images.get(image_name)
        typer.echo(f"Docker image {image_name} is already available.")
    except docker.errors.ImageNotFound:
        typer.echo(f"Pulling Docker image {image_name}...")
        client.images.pull(image_name)
        typer.echo(f"Docker image {image_name} pulled successfully.")


def run_docker_command(command: list, image_name: str):
    """Run a command in the Docker container."""
    full_command = [
        "docker",
        "run",
        "-it",
        "--rm",
        "-v",
        f"{os.getcwd()}:/data",
        image_name,
    ] + command

    subprocess.run(full_command)
