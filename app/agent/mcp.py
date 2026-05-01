from __future__ import annotations

from typing import Optional

from app.agent.toolcall import ToolCallAgent
from app.config import Config
from app.logger import logger
from app.mcp.client import MCPClient
from app.tool.base import ToolCollection
from app.tool.terminate import Terminate


MCP_PROMPT = """\
You are an MCP agent with access to tools provided by remote MCP servers. \
Use them to accomplish the user's task, then call terminate.
"""


class MCPAgent(ToolCallAgent):
    name = "mcp"
    system_prompt = MCP_PROMPT

    def __init__(self, server_url: Optional[str] = None, connection: str = "stdio") -> None:
        tools = ToolCollection(Terminate())
        super().__init__(tools=tools)
        self._server_url = server_url
        self._connection = connection
        self._mcp_clients: list[MCPClient] = []

    async def _setup_mcp(self) -> None:
        cfg = Config.get()
        servers = cfg.mcp_servers

        if self._server_url:
            client = MCPClient(
                name="remote",
                transport=self._connection,
                url=self._server_url if self._connection == "sse" else None,
                command=self._server_url if self._connection == "stdio" else None,
            )
            try:
                remote_tools = await client.connect()
                self._mcp_clients.append(client)
                for tool in remote_tools:
                    self.tools.add(tool)
                logger.info(f"[mcp] Loaded {len(remote_tools)} tools from remote server.")
            except Exception as e:
                logger.warning(f"[mcp] Could not connect to remote server: {e}")

        for srv in servers:
            client = MCPClient(
                name=srv.name,
                transport=srv.transport,
                command=srv.command,
                args=srv.args,
                url=srv.url,
            )
            try:
                srv_tools = await client.connect()
                self._mcp_clients.append(client)
                for tool in srv_tools:
                    self.tools.add(tool)
            except Exception as e:
                logger.warning(f"[mcp] Could not connect to server '{srv.name}': {e}")

    async def run(self, prompt: str) -> str:
        await self._setup_mcp()
        return await super().run(prompt)

    async def cleanup(self) -> None:
        await super().cleanup()
        for client in self._mcp_clients:
            await client.disconnect()
