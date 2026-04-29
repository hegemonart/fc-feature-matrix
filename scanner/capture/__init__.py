"""Capture-layer public surface.

Re-exports the helpers that downstream phases (crawler, login-gated
capture) will import via the package path rather than the module path.
"""
from scanner.capture.credentials import MissingCredentialError, get_credential

__all__ = ["get_credential", "MissingCredentialError"]
