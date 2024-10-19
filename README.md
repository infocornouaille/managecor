# managecor

`managecor` est un outil en ligne de commande pour gérer et utiliser un environnement de développement Docker personnalisé basé sur Ubuntu Noble. Il inclut TeXLive 2023 (version complète sans documentation), Anaconda 2024.06, Git, Pandoc, FastAPI, ainsi que des packages LaTeX et des modèles Pandoc, dont eisvogel.latex.

## Installation

1. Assurez-vous d'avoir Docker installé sur votre système.
2. Installez `managecor` via pip :

   ```
   pip install managecor
   ```

## Initialisation

Pour initialiser l'environnement `managecor`, exécutez :

```
managecor init
```

Cette commande va :
- Mettre à jour la configuration depuis GitHub
- S'assurer que l'image Docker est disponible localement
- Créer des alias pour les commandes courantes

## Utilisation

### Exécuter une commande dans le conteneur Docker

```
managecor run -- <commande>
```

Par exemple :
```
managecor run -- python script.py
```

### Alias disponibles

Après l'initialisation, les alias suivants seront disponibles dans votre shell :

- `pythoncor` : Python
- `xelatexcor` : XeLaTeX
- `pandoccor` : Pandoc
- `latexcor` : LaTeX personnalisé
- `latextomd` : Conversion LaTeX vers Markdown
- `pdfcor` : Manipulation PDF
- `jupytercor` : Manipulation Jupyter personnalisée
- `black` : Formateur de code Python
- `magick` : ImageMagick

Utilisez ces alias comme des commandes normales, par exemple :

```
pythoncor script.py
```

### Mise à jour de la configuration

Pour mettre à jour la configuration depuis GitHub :

```
managecor update-config
```

## Configuration

La configuration est stockée dans `~/.managecor_config.yaml`. Elle est automatiquement mise à jour lors de l'initialisation ou via la commande `update-config`.

## Licence

Ce projet est sous licence MIT. Voir le fichier `LICENSE` pour plus de détails.