import sys
import os
from . import cli


def main():
    """
    Point d'entrée pour l'alias jupytercor.
    Cette fonction prend les arguments de ligne de commande et les transmet
    à la commande Docker appropriée.
    """

    command = ["jupytercor"] + sys.argv[1:]

    # Exécuter la commande via Docker
    try:
        cli.console.print(f"Excécution dans le docker")
        cli.run_docker_command(command, "infocornouaille/tools:perso")
    except Exception as e:
        cli.console.print(
            f"[error]Erreur lors de l'exécution de jupytercor : {str(e)}[/error]"
        )
        sys.exit(1)
