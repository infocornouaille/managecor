import ctypes
import os
import platform
import subprocess
import sys
from typing import List

import requests
import typer
import yaml
from rich.console import Console
from rich.panel import Panel
from rich.progress import Progress, SpinnerColumn, TextColumn, DownloadColumn, TransferSpeedColumn, TimeRemainingColumn
from rich.theme import Theme
from rich import print as rprint

from .docker_utils import run_docker_command

app = typer.Typer()
console = Console(theme=Theme({
    "success": "green bold",
    "error": "red bold",
    "warning": "yellow bold",
    "info": "blue bold"
}))

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
    try:
        with open(CONFIG_PATH, "r") as f:
            return yaml.safe_load(f)
    except FileNotFoundError:
        console.print("[error]Configuration file not found. Run 'managecor init' first.[/error]")
        raise typer.Exit(1)
    except yaml.YAMLError:
        console.print("[error]Invalid configuration file format.[/error]")
        raise typer.Exit(1)

def ensure_docker_image(image_name: str):
    """Ensure Docker image exists, downloading it if necessary with progress bar."""
    try:
        # Check if image exists locally
        result = subprocess.run(
            ["docker", "image", "inspect", image_name],
            capture_output=True,
            text=True
        )
        
        if result.returncode == 0:
            console.print(f"[info]Docker image {image_name} is already present.[/info]")
            return

        with Progress(
            SpinnerColumn(),
            TextColumn("[progress.description]{task.description}"),
            DownloadColumn(),
            TransferSpeedColumn(),
            TimeRemainingColumn(),
            console=console
        ) as progress:
            task = progress.add_task(f"[cyan]Pulling Docker image {image_name}...", total=None)
            
            process = subprocess.Popen(
                ["docker", "pull", image_name],
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                universal_newlines=True
            )
            
            while True:
                output = process.stdout.readline()
                if output == '' and process.poll() is not None:
                    break
                if output:
                    progress.update(task, description=f"[cyan]{output.strip()}")
            
            if process.returncode == 0:
                progress.update(task, completed=100)
                console.print(f"[success]Successfully pulled Docker image {image_name}[/success]")
            else:
                error = process.stderr.read()
                console.print(f"[error]Failed to pull Docker image: {error}[/error]")
                raise typer.Exit(1)
    except subprocess.CalledProcessError as e:
        console.print(f"[error]Error with Docker: {e}[/error]")
        raise typer.Exit(1)

@app.command()
def init():
    """Initialize the managecor environment."""
    with console.status("[bold blue]Initializing managecor environment...") as status:
        try:
            update_config()
            config = load_config()
            ensure_docker_image(config["docker_image"])
            create_aliases(config["aliases"])
            console.print(Panel.fit(
                "[success]managecor environment initialized successfully![/success]",
                title="Success",
                border_style="green"
            ))
        except Exception as e:
            console.print(f"[error]Initialization failed: {str(e)}[/error]")
            raise typer.Exit(1)

@app.command()
def update_config():
    """Update the configuration file from GitHub."""
    with console.status("[bold blue]Updating configuration...") as status:
        try:
            response = requests.get(CONFIG_URL)
            response.raise_for_status()
            with open(CONFIG_PATH, "w") as f:
                f.write(response.text)
            console.print("[success]Configuration updated successfully![/success]")
            config = load_config()
            create_aliases(config["aliases"])
        except requests.RequestException as e:
            console.print(f"[error]Failed to update configuration: {e}[/error]")
            raise typer.Exit(1)
        
@app.command()
def update():
    """Force update the Docker image to the latest version."""
    try:
        config = load_config()
        image_name = config["docker_image"]
        
        with console.status("[bold blue]Checking image status...") as status:
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
                console.print(f"\n[success]Update successful! New image details:[/success]")
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
        with console.status(f"[bold blue]Running command: {' '.join(command)}..."):
            run_docker_command(command, config["docker_image"])
    except Exception as e:
        console.print(f"[error]Command execution failed: {str(e)}[/error]")
        raise typer.Exit(1)

def create_aliases(aliases):
    """Create aliases for common commands, avoiding duplications."""
    system = platform.system()

    with console.status("[bold blue]Creating aliases...") as status:
        if system in ("Darwin", "Linux"):
            shell = os.environ.get("SHELL", "").split("/")[-1]
            if shell == "bash":
                rc_file = "~/.bashrc"
            elif shell == "zsh":
                rc_file = "~/.zshrc"
            else:
                console.print(f"[warning]Unsupported shell: {shell}[/warning]")
                return
            
            rc_path = os.path.expanduser(rc_file)

            try:
                with open(rc_path, "r") as f:
                    current_content = f.read()
            except FileNotFoundError:
                current_content = ""

            new_aliases = []
            for alias, command in aliases.items():
                alias_command = f'alias {alias}="managecor run -- {command}"\n'
                if alias_command not in current_content:
                    new_aliases.append(alias_command)

            if new_aliases:
                with open(rc_path, "a") as f:
                    f.writelines(new_aliases)
                console.print(f"[success]Added {len(new_aliases)} new aliases to {rc_file}.[/success]")
            else:
                console.print("[info]No new aliases to add.[/info]")

            console.print(f"[warning]Please restart your shell or run 'source {rc_file}' to apply changes.[/warning]")

        elif system == "Windows":
            if not is_admin():
                console.print(
                    "[warning]This script needs to be run with administrator privileges to modify the registry.[/warning]"
                )
                console.print("[info]Attempting to restart with admin privileges...[/info]")
                run_as_admin()
                return

            alias_file = os.path.expanduser("~\\Docker_aliases.bat")
            alias_lines = []
            for alias, command in aliases.items():
                alias_lines.append(
                    f"doskey {alias}=docker run -it --rm -v %cd%:/data infocornouaille/tools:perso {command} $*\n"
                )

            with open(alias_file, "w") as f:
                f.writelines(alias_lines)

            console.print(f"[info]Created alias file: {alias_file}[/info]")

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
                console.print(
                    "[success]Successfully added aliases to Windows registry. They will be available in new command prompt windows.[/success]"
                )
            except subprocess.CalledProcessError:
                console.print(
                    "[error]Failed to add aliases to Windows registry. You may need to run this script as an administrator.[/error]"
                )

        else:
            console.print(f"[error]Unsupported operating system: {system}[/error]")

if __name__ == "__main__":
    app()