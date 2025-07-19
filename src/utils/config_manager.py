import os
import yaml
from typing import Any, Dict
from src.utils.logger import get_logger

logger = get_logger(__name__)

_app_config: Dict[str, Any] | None = None

CONFIG_PATH: str = os.path.join(os.getcwd(), "config.yaml")

def get_config() -> Dict[str, Any]:
    if _app_config is None:
        raise RuntimeError("Configuration not loaded. Please call load_app_config() first.")
    return _app_config

def _setup_environment_variables() -> None:
    config = get_config()
    openai_config = config.get('openai', {})
    openrouter_config = config.get('openrouter', {})
    brave_config = config.get('brave', {})

    if openai_config.get('token'):
        os.environ["OPENAI_API_KEY"] = openai_config['token']
        logger.info("OPENAI_API_KEY has been set.")

    if openrouter_config.get('api_key'):
        os.environ["OPENROUTER_API_KEY"] = openrouter_config['api_key']
        logger.info("OPENROUTER_API_KEY has been set.")

    if brave_config.get('token'):
        os.environ["BRAVE_API_KEY"] = brave_config['token']
        logger.info("BRAVE_API_KEY has been set.")

def load_app_config(config_file_path: str = CONFIG_PATH) -> Dict[str, Any]:
    global _app_config
    if _app_config is None:
        try:
            with open(config_file_path, 'r', encoding='utf-8') as f:
                _app_config = yaml.safe_load(f) or {}
            _setup_environment_variables()
        except FileNotFoundError:
            logger.error(f"Error: config file not found at: {config_file_path}")
            _app_config = {} 
        except Exception as e:
            logger.error(f"Error loading config: {e}")
            _app_config = {}
    return _app_config or {}