"""
MCP Client for Playwright MCP Server
===================================

Production-grade, modular client for interacting with Playwright MCP Server.
Supports all major MCP commands (navigate, click, snapshot, etc.).
Includes input validation, error handling, and logging best practices.

Author: Senior QA Automation Architect
Date: June 2024
"""

import aiohttp
import asyncio
import logging
from typing import Any, Dict, Optional, List, Union

class MCPClient:
    """
    Modular client for Playwright MCP Server.
    Supports sending commands and receiving results via HTTP (REST/SSE).
    """
    def __init__(self, host: str = "localhost", port: int = 8931, use_https: bool = False, timeout: int = 30):
        """
        Initialize MCPClient.
        Args:
            host (str): MCP server host
            port (int): MCP server port
            use_https (bool): Use HTTPS (default: False)
            timeout (int): Request timeout in seconds
        """
        self.host = host
        self.port = port
        self.use_https = use_https
        self.timeout = timeout
        self.base_url = f"{'https' if use_https else 'http'}://{host}:{port}"
        self.session: Optional[aiohttp.ClientSession] = None
        self.logger = logging.getLogger("MCPClient")

    async def __aenter__(self):
        self.session = aiohttp.ClientSession()
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        if self.session:
            await self.session.close()

    async def connect(self):
        if not self.session:
            self.session = aiohttp.ClientSession()

    async def close(self):
        if self.session:
            await self.session.close()
            self.session = None

    async def send_command(self, command: str, params: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """
        Send a command to the MCP server and return the response.
        Args:
            command (str): MCP command name (e.g., 'browser_navigate')
            params (dict): Parameters for the command
        Returns:
            dict: Response from the server
        Raises:
            Exception: On network or protocol error
        """
        await self.connect()
        url = f"{self.base_url}/command"
        payload = {
            "command": command,
            "params": params or {}
        }
        self.logger.debug(f"Sending MCP command: {command} | Params: {params}")
        try:
            async with self.session.post(url, json=payload, timeout=self.timeout) as resp:
                if resp.status == 200:
                    data = await resp.json()
                    self.logger.info(f"MCP command '{command}' succeeded.")
                    return data
                else:
                    text = await resp.text()
                    self.logger.error(f"MCP command '{command}' failed: {resp.status} {text}")
                    raise Exception(f"MCP command failed: {resp.status} {text}")
        except Exception as e:
            self.logger.error(f"Error sending MCP command '{command}': {e}")
            raise

    # --- High-level API methods ---

    async def navigate(self, url: str) -> Dict[str, Any]:
        """Navigate to a URL."""
        if not url:
            raise ValueError("URL must not be empty.")
        return await self.send_command("browser_navigate", {"url": url})

    async def click(self, element: str, ref: str) -> Dict[str, Any]:
        """Click an element by description and ref."""
        return await self.send_command("browser_click", {"element": element, "ref": ref})

    async def type_text(self, element: str, ref: str, text: str, submit: bool = False, slowly: bool = False) -> Dict[str, Any]:
        """Type text into an element."""
        return await self.send_command("browser_type", {"element": element, "ref": ref, "text": text, "submit": submit, "slowly": slowly})

    async def snapshot(self) -> Dict[str, Any]:
        """Get accessibility snapshot of the current page."""
        return await self.send_command("browser_snapshot")

    async def take_screenshot(self, filename: Optional[str] = None) -> Dict[str, Any]:
        """Take a screenshot of the current page."""
        params = {"filename": filename} if filename else {}
        return await self.send_command("browser_take_screenshot", params)

    async def get_console_messages(self) -> Dict[str, Any]:
        """Get all console messages from the page."""
        return await self.send_command("browser_console_messages")

    async def wait_for(self, time_sec: Optional[float] = None, text: Optional[str] = None, text_gone: Optional[str] = None) -> Dict[str, Any]:
        """Wait for text or time on the page."""
        params = {}
        if time_sec:
            params["time"] = time_sec
        if text:
            params["text"] = text
        if text_gone:
            params["textGone"] = text_gone
        return await self.send_command("browser_wait_for", params)

    async def upload_files(self, paths: List[str]) -> Dict[str, Any]:
        """Upload files to the page."""
        return await self.send_command("browser_file_upload", {"paths": paths})

    async def close_browser(self) -> Dict[str, Any]:
        """Close the browser session."""
        return await self.send_command("browser_close")

    async def generate_playwright_test(self, name: str, description: str, steps: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Generate a Playwright test for a scenario."""
        return await self.send_command("browser_generate_playwright_test", {"name": name, "description": description, "steps": steps})

    # Add more methods as needed for all MCP commands

    # --- Utility ---
    def set_config(self, host: str, port: int, use_https: bool = False, timeout: int = 30):
        """Update MCP server configuration at runtime."""
        self.host = host
        self.port = port
        self.use_https = use_https
        self.timeout = timeout
        self.base_url = f"{'https' if use_https else 'http'}://{host}:{port}"
        self.logger.info(f"MCPClient config updated: {self.base_url}") 