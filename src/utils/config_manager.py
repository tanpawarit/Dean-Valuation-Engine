import os
import yaml
from src.utils import logger
from typing import Any

_APP_CONFIG = None 

CONFIG_PATH: str = os.path.join(os.getcwd(), "config.yaml")

def get_config() -> dict[str, Any]:
    if _APP_CONFIG is None:
        raise RuntimeError("Configuration not loaded. Please call load_app_config() first.")
    return _APP_CONFIG

def _setup_environment_variables() -> None:
    config = get_config()
    openai_config = config.get('openai', {})
    serper_config = config.get('serper', {})

    if openai_config.get('token'):
        os.environ["OPENAI_API_KEY"] = openai_config['token']
        logger.info("OPENAI_API_KEY has been set.")

    if serper_config.get('token'):
        os.environ["SERPER_API_KEY"] = serper_config['token']
        logger.info("SERPER_API_KEY has been set.")

def load_app_config(config_file_path: str = CONFIG_PATH) -> dict[str, Any]:
    global _APP_CONFIG
    if _APP_CONFIG is None:
        try:
            with open(config_file_path, 'r', encoding='utf-8') as f:
                _APP_CONFIG = yaml.safe_load(f)
            _setup_environment_variables()
        except FileNotFoundError:
            logger.error(f"Error: config file not found at: {config_file_path}")
            _APP_CONFIG = {} 
        except Exception as e:
            logger.error(f"Error loading config: {e}")
            _APP_CONFIG = {}
    return _APP_CONFIG