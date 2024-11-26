import os
import tomli

path = os.path.abspath("../pyproject.toml")
with open(path, "rb") as f:
    info = tomli.load(f)

project = info["project"]["name"]
release = info["project"]["version"]
author = info["project"]["authors"][0]["name"]
copyright = f"2024, {author}"

extensions = ["myst_parser", "sphinx.ext.autodoc"]

templates_path = ["_templates"]
exclude_patterns = ["_build", "Thumbs.db", ".DS_Store"]

html_theme = "sphinx_rtd_theme"
html_static_path = ["_static"]
