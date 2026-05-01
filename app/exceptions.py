class ManusClawError(Exception):
    """Base exception for ManusClaw."""

class TokenLimitExceeded(ManusClawError):
    """Raised when the token limit is exceeded and retrying won't help."""

class ToolError(ManusClawError):
    """Raised when a tool encounters an unrecoverable error."""

class ConfigError(ManusClawError):
    """Raised for configuration problems."""

class SandboxError(ManusClawError):
    """Raised for sandbox-related errors."""

class MCPError(ManusClawError):
    """Raised for MCP integration errors."""
