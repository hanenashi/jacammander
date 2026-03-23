# jacammander/app/core/protocol.py

from app.common import constants

def build_request(command, payload=None):
    """Builds a standard dictionary for a client request."""
    if payload is None:
        payload = {}
        
    return {
        constants.KEY_CMD: command,
        constants.KEY_PAYLOAD: payload
    }

def build_response(status, message="", payload=None):
    """Builds a standard dictionary for a server response."""
    if payload is None:
        payload = {}
        
    return {
        constants.KEY_STATUS: status,
        constants.KEY_MESSAGE: message,
        constants.KEY_PAYLOAD: payload
    }

def build_auth_request(password):
    """Helper for the AUTH command."""
    return build_request(constants.CMD_AUTH, {"password": password})

def build_error(error_msg):
    """Helper for quick error responses."""
    return build_response(constants.CMD_ERROR, error_msg)

def build_ping():
    """Helper for connection testing."""
    return build_request(constants.CMD_PING)