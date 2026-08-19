import os
from pathlib import Path

APP_NAME = "wireg"


def get_config_dir() -> Path:
    """Returns the base configuration directory: ~/.config/wireg"""
    base = os.environ.get("XDG_CONFIG_HOME")
    if base:
        p = Path(base) / APP_NAME
    else:
        p = Path.home() / ".config" / APP_NAME
    p.mkdir(parents=True, exist_ok=True, mode=0o700)
    return p


def get_runtime_dir() -> Path:
    """Returns runtime directory for temporary wg-quick files: ~/.config/wireg/runtime"""
    p = get_config_dir() / "runtime"
    p.mkdir(parents=True, exist_ok=True, mode=0o700)
    return p


def get_configs_json_path() -> Path:
    """Returns path to ~/.config/wireg/configs.json"""
    return get_config_dir() / "configs.json"


def get_settings_json_path() -> Path:
    """Returns path to ~/.config/wireg/settings.json"""
    return get_config_dir() / "settings.json"


def ensure_directories() -> None:
    """Ensures that all application directories exist with proper 0700 permissions."""
    get_config_dir()
    get_runtime_dir()
