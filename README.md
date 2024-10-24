# ManageCor

![PyPI Version](https://img.shields.io/pypi/v/managecor)
![Python Version](https://img.shields.io/pypi/pyversions/managecor)
![License](https://img.shields.io/github/license/infocornouaille/managecor)
![Docker Pulls](https://img.shields.io/docker/pulls/infocornouaille/tools)
![Docker Image Size](https://img.shields.io/docker/image-size/infocornouaille/tools)
![PyPI Downloads](https://img.shields.io/pypi/dm/managecor)
![GitHub last commit](https://img.shields.io/github/last-commit/infocornouaille/managecor)

A command-line tool for managing and using a customized Docker development environment based on Texlive. It includes Python, Pandoc, along with LaTeX packages and Pandoc templates, including eisvogel.latex.

## Features

- 🐳 Docker-based isolated environment
- 📦 Pre-configured TeXLive installation
- 🐍 Python with essential development tools
- 📄 Pandoc with custom templates
- 🎨 ImageMagick support
- 🔄 Automatic updates and configuration
- ⚡ Convenient command aliases

## Prerequisites

- Docker installed on your system
- Python 3.8 or higher
- pip package manager

## Installation

Install `managecor` using pip:

```bash
pip install managecor
```

## Quick Start

1. Initialize the environment:
```bash
managecor init
```

This will:
- Update configuration from GitHub
- Pull required Docker images
- Set up command aliases

2. Use the provided aliases:
```bash
pythoncor script.py    # Run Python
pandoccor input.md -o output.pdf    # Convert documents
```

## Commands

| Command | Description |
|---------|-------------|
| `managecor init` | Initialize the environment |
| `managecor update` | Force update Docker images to latest version |
| `managecor update-config` | Update configuration from GitHub |
| `managecor run -- <command>` | Run a command in the Docker container |

## Available Aliases

After initialization, the following aliases will be available in your shell:

| Alias | Description |
|-------|-------------|
| `pythoncor` | Python environment |
| `xelatexcor` | XeLaTeX compiler |
| `pandoccor` | Pandoc document converter |
| `latexcor` | Custom LaTeX environment |
| `latextomd` | Convert LaTeX to Markdown |
| `pdfcor` | PDF manipulation tools |
| `jupytercor` | Custom Jupyter environment |
| `black` | Python code formatter |
| `magick` | ImageMagick |

## Usage Examples

Run Python script:
```bash
pythoncor script.py
```

Convert Markdown to PDF:
```bash
pandoccor input.md -o output.pdf
```

Format Python code:
```bash
black script.py
```

## Configuration

The configuration file is stored at `~/.managecor_config.yaml`. It's automatically updated during initialization or via the `update-config` command.

## Docker Images

ManageCor uses two Docker images:

- Base image (`infocornouaille/tools:base`): Contains core tools and dependencies
- Custom image (`infocornouaille/tools:perso`): Includes additional templates and configurations

To force update the Docker images to their latest versions:
```bash
managecor update
```

## Development

To contribute to ManageCor:

1. Fork the repository
2. Create a feature branch
3. Submit a Pull Request

## Troubleshooting

Common issues and solutions:

- If aliases aren't working, try restarting your terminal or running:
  ```bash
  source ~/.bashrc  # for bash
  source ~/.zshrc   # for zsh
  ```
- For Docker-related issues, ensure Docker daemon is running
- For permission issues on Linux, ensure your user is in the docker group

## License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## Acknowledgements

- TeXLive team for the base Docker image
- Pandoc team for document conversion tools
- All contributors to the project