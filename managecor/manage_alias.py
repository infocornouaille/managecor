import os
import winreg
from pathlib import Path
from rich.console import Console

console = Console()

def create_batch_file(alias_name, command):
    """Crée un fichier batch pour l'alias"""
    scripts_dir = Path.home() / "Scripts"
    scripts_dir.mkdir(exist_ok=True)
    
    batch_path = scripts_dir / f"{alias_name}.bat"
    
    try:
        with open(batch_path, "w") as f:
            f.write("@echo off\n")
            f.write(f"{command} %*")
        console.print(f"[green]✓[/green] Fichier batch créé: {batch_path}")
        return batch_path
    except Exception as e:
        console.print(f"[red]✗[/red] Erreur lors de la création du fichier batch: {e}")
        return None

def add_to_path(directory):
    """Ajoute un répertoire au PATH utilisateur"""
    try:
        key = winreg.OpenKey(winreg.HKEY_CURRENT_USER, 
                            "Environment", 
                            0, 
                            winreg.KEY_ALL_ACCESS)
        
        try:
            path_value, _ = winreg.QueryValueEx(key, "PATH")
        except WindowsError:
            path_value = ""
        
        if str(directory) not in path_value:
            new_path = f"{path_value};{directory}" if path_value else str(directory)
            winreg.SetValueEx(key, "PATH", 0, winreg.REG_EXPAND_SZ, new_path)
            console.print(f"[green]✓[/green] Répertoire ajouté au PATH: {directory}")
        else:
            console.print(f"[blue]ℹ[/blue] Le répertoire est déjà dans le PATH: {directory}")
            
        winreg.CloseKey(key)
        return True
    except WindowsError as e:
        console.print(f"[red]✗[/red] Erreur lors de la modification du PATH: {e}")
        return False

def create_alias(alias_name, command):
    """Crée un alias en créant un fichier batch et l'ajoute au PATH"""
    console.print(f"\n[yellow]Création de l'alias[/yellow] '{alias_name}'...")
    console.print(f"[dim]Commande:[/dim] {command}")
    
    try:
        batch_path = create_batch_file(alias_name, command)
        if not batch_path:
            return False
        
        scripts_dir = str(Path.home() / "Scripts")
        if add_to_path(scripts_dir):
            console.print(f"[green]✓[/green] Alias '{alias_name}' créé avec succès!")
            return True
        return False
    except Exception as e:
        console.print(f"[red]✗[/red] Erreur lors de la création de l'alias: {e}")
        return False

def main():
    console.print("[bold blue]Création des alias Windows[/bold blue]")
    console.print("=" * 50)

    # Définition des alias
    aliases = {
        "docker-pandoc": "docker run -it --rm -v %cd%:/data infocornouaille/tools:perso pandoc",
        # Ajoutez d'autres alias ici
    }
    
    success_count = 0
    for alias_name, command in aliases.items():
        if create_alias(alias_name, command):
            success_count += 1
    
    console.print("\n[bold]Résumé:[/bold]")
    console.print(f"✓ {success_count} alias créés sur {len(aliases)} demandés")
    if success_count > 0:
        console.print("\n[yellow]ℹ Vous devrez peut-être redémarrer votre terminal pour utiliser les nouveaux alias.[/yellow]")

if __name__ == "__main__":
    main()