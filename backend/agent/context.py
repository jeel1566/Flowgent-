"""Context storage for agent tools to access user credentials."""
import logging
from typing import Optional, Dict, Any

logger = logging.getLogger(__name__)

# Thread-local storage for n8n credentials
_n8n_credentials: Optional[Dict[str, str]] = None


def set_n8n_credentials(instance_url: str, api_key: str) -> None:
    """Store n8n credentials for current request context."""
    global _n8n_credentials
    _n8n_credentials = {
        "instance_url": instance_url,
        "api_key": api_key
    }
    logger.debug("Stored n8n credentials for agent context")


def get_n8n_credentials() -> Optional[Dict[str, str]]:
    """Get n8n credentials for current request context."""
    global _n8n_credentials
    return _n8n_credentials


def clear_n8n_credentials() -> None:
    """Clear stored n8n credentials."""
    global _n8n_credentials
    _n8n_credentials = None
    logger.debug("Cleared n8n credentials from agent context")
