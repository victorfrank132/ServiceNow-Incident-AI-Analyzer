"""Utility functions for the incident agent."""

import yaml
import json
from pathlib import Path
from typing import Dict, Any, Optional


def load_config(config_path: str = "config/config.yaml") -> Dict[str, Any]:
    """
    Load configuration from YAML file.

    Args:
        config_path: Path to config.yaml file

    Returns:
        Configuration dictionary
    """
    try:
        with open(config_path, "r") as f:
            config = yaml.safe_load(f)
        return config or {}
    except FileNotFoundError:
        print(f"Config file not found: {config_path}")
        return {}
    except yaml.YAMLError as e:
        print(f"Error parsing config: {str(e)}")
        return {}


def load_team_mappings(mapping_path: str = "config/team_mappings.json") -> Dict[str, str]:
    """
    Load team mappings from JSON file.

    Args:
        mapping_path: Path to team_mappings.json file

    Returns:
        Team mapping dictionary
    """
    try:
        with open(mapping_path, "r") as f:
            mappings = json.load(f)
        return mappings
    except FileNotFoundError:
        print(f"Team mappings file not found: {mapping_path}")
        return {"default": "General-Support"}
    except json.JSONDecodeError as e:
        print(f"Error parsing team mappings: {str(e)}")
        return {"default": "General-Support"}


def validate_config(config: Dict[str, Any]) -> bool:
    """
    Validate configuration has required fields.

    Args:
        config: Configuration dictionary

    Returns:
        True if valid, False otherwise
    """
    required_fields = ["servicenow", "incident_processing"]
    for field in required_fields:
        if field not in config:
            print(f"Missing required config field: {field}")
            return False
    return True


def ensure_directories_exist(directories: list) -> None:
    """
    Ensure required directories exist.

    Args:
        directories: List of directory paths to create
    """
    for directory in directories:
        Path(directory).mkdir(parents=True, exist_ok=True)
