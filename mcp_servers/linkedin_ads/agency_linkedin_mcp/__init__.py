"""LinkedIn Ads MCP server.

Talks HTTP to the agency_ads FastAPI app's `/linkedin/mcp/*` endpoints,
authenticating with a static bearer token. Token refresh, OAuth state,
and credential storage all live in the app — this process is stateless.
"""

__version__ = "0.1.0"
