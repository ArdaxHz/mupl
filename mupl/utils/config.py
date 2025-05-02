import json
import logging
import os
import sys
from pathlib import Path
import tempfile
from typing import Optional


logger = logging.getLogger("mupl")


def open_defaults_file(defaults_path: "Path") -> "dict":
    """Load default configuration values from a file."""
    try:
        with open(
            defaults_path,
            "r",
            encoding="utf-8",
        ) as json_file:
            return json.load(json_file)
    except (FileNotFoundError, json.JSONDecodeError):
        return {}


def load_config(config_path, cli=False):
    """Load configuration from file."""
    try:
        with open(config_path, "r", encoding="utf-8") as f:
            return json.load(f)
    except FileNotFoundError:
        logger.error(f"Configuration file not found: {config_path}")
        if cli:
            print(f"Error: Configuration file not found at {config_path}")
            sys.exit(1)
        else:
            raise
    except json.JSONDecodeError as e:
        logger.error(f"Invalid JSON in configuration file: {config_path}: {e}")
        if cli:
            print(f"Error: Invalid JSON in configuration file: {config_path}: {e}")
            sys.exit(1)
        else:
            raise
    except Exception as e:
        logger.error(f"Error loading configuration: {e}")
        if cli:
            print(f"Error loading configuration: {e}")
            sys.exit(1)
        else:
            raise


def validate_path(path):
    try:
        os.makedirs(path, exist_ok=True)
        with tempfile.TemporaryDirectory(dir=path):
            return True
    except OSError:
        return False
