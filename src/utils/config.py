"""Configuration loader"""

import os
from pathlib import Path
from typing import Dict, Any
import tomli


def load_config() -> Dict[str, Any]:
    """Load configuration from TOML file"""
    # Try multiple config paths
    config_paths = [
        "/etc/autobuilder/config.toml",
        os.path.expanduser("~/.config/autobuilder/config.toml"),
        Path(__file__).parent.parent.parent / "config" / "config.toml",
    ]
    
    project_root = Path(__file__).parent.parent.parent
    
    for config_path in config_paths:
        config_file = Path(config_path)
        if config_file.exists():
            with open(config_file, "rb") as f:
                config = tomli.load(f)
                # Set base_dir if not set
                if 'paths' not in config:
                    config['paths'] = {}
                if 'base_dir' not in config['paths']:
                    # Use /opt/autobuilder for production, project root for dev
                    if str(config_file).startswith('/etc'):
                        config['paths']['base_dir'] = "/opt/autobuilder"
                    else:
                        config['paths']['base_dir'] = str(project_root)
                
                # Set other paths if not set
                base_dir = config['paths']['base_dir']
                if 'reports_dir' not in config['paths']:
                    config['paths']['reports_dir'] = os.path.join(base_dir, 'reports')
                if 'workspaces_dir' not in config['paths']:
                    config['paths']['workspaces_dir'] = os.path.join(base_dir, 'workspaces')
                if 'logs_dir' not in config['paths']:
                    config['paths']['logs_dir'] = '/var/log/autobuilder'
                
                return config
    
    raise FileNotFoundError(
        f"Configuration file not found. Tried: {', '.join(str(p) for p in config_paths)}"
    )

