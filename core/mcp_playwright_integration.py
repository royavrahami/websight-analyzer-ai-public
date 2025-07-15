#!/usr/bin/env python3
"""
Microsoft-Style MCP Playwright Integration
=========================================

Advanced Playwright MCP server implementation based on Microsoft's architecture.
This module provides comprehensive browser automation capabilities with MCP protocol support.

Key Features:
- Model Context Protocol (MCP) integration
- Accessibility-first approach (like Microsoft's implementation)
- Tool-based modular architecture
- Context and session management
- Support for multiple browser types
- Production-grade error handling and logging

Author: Roy Avrahami - Senior QA Automation Architect
"""

import asyncio
import json
import logging
import os
import uuid
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Optional, Union, Callable
from dataclasses import dataclass, asdict
from abc import ABC, abstractmethod
import traceback

# Core dependencies
import playwright
from playwright.async_api import (
    async_playwright, Browser, BrowserContext, Page, 
    FileChooser, Dialog, Locator, ElementHandle
)

# MCP SDK integration
try:
    from pydantic import BaseModel, Field
    from enum import Enum
except ImportError:
    print("Installing required dependencies...")
    os.system("pip install pydantic")
    from pydantic import BaseModel, Field
    from enum import Enum


class ToolCapability(str, Enum):
    """Tool capabilities following Microsoft's MCP pattern"""
    CORE = "core"
    TABS = "tabs"
    PDF = "pdf"
    HISTORY = "history"
    WAIT = "wait"
    FILES = "files"
    INSTALL = "install"
    TESTING = "testing"
    VISION = "vision"


class ToolType(str, Enum):
    """Tool types for permission management"""
    READ_ONLY = "readOnly"
    DESTRUCTIVE = "destructive"


@dataclass
class ToolSchema:
    """Schema definition for MCP tools"""
    name: str
    title: str
    description: str
    input_schema: Dict[str, Any]
    type: ToolType
    capability: ToolCapability


@dataclass
class ToolResult:
    """Result of tool execution"""
    code: List[str]
    action_result: Optional[Dict[str, Any]] = None
    capture_snapshot: bool = False
    wait_for_network: bool = False
    success: bool = True
    error_message: Optional[str] = None


class MCPBrowserContext:
    """Browser context manager following Microsoft's pattern"""
    
    def __init__(self, context: BrowserContext, close_callback: Callable):
        self.context = context
        self.close_callback = close_callback
        self.tabs: List['MCPTab'] = []
        self.current_tab_index = 0
    
    async def close(self):
        """Close browser context"""
        try:
            await self.close_callback()
        except Exception as e:
            logging.error(f"Error closing browser context: {e}")


class MCPTab:
    """Tab management following Microsoft's MCP pattern"""
    
    def __init__(self, page: Page, context: MCPBrowserContext):
        self.page = page
        self.context = context
        self.id = str(uuid.uuid4())
        self.created_at = datetime.now()
    
    async def navigate(self, url: str) -> None:
        """Navigate to URL with error handling"""
        try:
            await self.page.goto(url, wait_until='domcontentloaded')
            logging.info(f"Navigated to: {url}")
        except Exception as e:
            logging.error(f"Navigation failed to {url}: {e}")
            raise
    
    async def take_accessibility_snapshot(self) -> Dict[str, Any]:
        """Capture accessibility snapshot (Microsoft's approach)"""
        try:
            # Get accessibility tree
            accessibility_tree = await self.page.accessibility.snapshot()
            
            # Get page metadata
            title = await self.page.title()
            url = self.page.url
            
            # Get all interactive elements
            interactive_elements = await self.page.evaluate("""
                () => {
                    const elements = [];
                    const selectors = [
                        'button', 'input', 'select', 'textarea', 'a[href]',
                        '[onclick]', '[role="button"]', '[role="link"]',
                        '[tabindex]', '[contenteditable]'
                    ];
                    
                    selectors.forEach(selector => {
                        document.querySelectorAll(selector).forEach((el, index) => {
                            const rect = el.getBoundingClientRect();
                            if (rect.width > 0 && rect.height > 0) {
                                elements.push({
                                    type: el.tagName.toLowerCase(),
                                    text: el.textContent?.trim().substring(0, 100) || '',
                                    role: el.getAttribute('role') || '',
                                    ariaLabel: el.getAttribute('aria-label') || '',
                                    id: el.id || '',
                                    className: el.className || '',
                                    selector: `${el.tagName.toLowerCase()}:nth-of-type(${index + 1})`,
                                    bounds: {
                                        x: Math.round(rect.x),
                                        y: Math.round(rect.y),
                                        width: Math.round(rect.width),
                                        height: Math.round(rect.height)
                                    }
                                });
                            }
                        });
                    });
                    
                    return elements;
                }
            """)
            
            return {
                "title": title,
                "url": url,
                "timestamp": datetime.now().isoformat(),
                "accessibility_tree": accessibility_tree,
                "interactive_elements": interactive_elements,
                "element_count": len(interactive_elements)
            }
            
        except Exception as e:
            logging.error(f"Failed to capture accessibility snapshot: {e}")
            raise


class MCPTool(ABC):
    """Abstract base class for MCP tools"""
    
    def __init__(self, schema: ToolSchema):
        self.schema = schema
    
    @abstractmethod
    async def handle(self, context: 'MCPPlaywrightContext', params: Dict[str, Any]) -> ToolResult:
        """Handle tool execution"""
        pass


class BrowserSnapshotTool(MCPTool):
    """Browser snapshot tool - Microsoft's accessibility approach"""
    
    def __init__(self):
        schema = ToolSchema(
            name="browser_snapshot",
            title="Page snapshot",
            description="Capture accessibility snapshot of the current page, this is better than screenshot",
            input_schema={
                "type": "object",
                "properties": {},
                "required": []
            },
            type=ToolType.READ_ONLY,
            capability=ToolCapability.CORE
        )
        super().__init__(schema)
    
    async def handle(self, context: 'MCPPlaywrightContext', params: Dict[str, Any]) -> ToolResult:
        try:
            tab = await context.ensure_tab()
            snapshot = await tab.take_accessibility_snapshot()
            
            code = [
                "// Capture accessibility snapshot",
                "const snapshot = await page.accessibility.snapshot();",
                "const interactiveElements = await page.$$eval('button, input, select, a', elements => /* ... */);"
            ]
            
            return ToolResult(
                code=code,
                action_result={"snapshot": snapshot},
                capture_snapshot=True,
                success=True
            )
        except Exception as e:
            return ToolResult(
                code=[f"// Error: {str(e)}"],
                success=False,
                error_message=str(e)
            )


class BrowserNavigateTool(MCPTool):
    """Browser navigation tool"""
    
    def __init__(self):
        schema = ToolSchema(
            name="browser_navigate",
            title="Navigate to a URL",
            description="Navigate to a URL",
            input_schema={
                "type": "object",
                "properties": {
                    "url": {
                        "type": "string",
                        "description": "The URL to navigate to"
                    }
                },
                "required": ["url"]
            },
            type=ToolType.DESTRUCTIVE,
            capability=ToolCapability.CORE
        )
        super().__init__(schema)
    
    async def handle(self, context: 'MCPPlaywrightContext', params: Dict[str, Any]) -> ToolResult:
        try:
            url = params["url"]
            tab = await context.ensure_tab()
            await tab.navigate(url)
            
            code = [
                f"// Navigate to {url}",
                f"await page.goto('{url}');"
            ]
            
            return ToolResult(
                code=code,
                capture_snapshot=True,
                wait_for_network=True,
                success=True
            )
        except Exception as e:
            return ToolResult(
                code=[f"// Navigation failed: {str(e)}"],
                success=False,
                error_message=str(e)
            )


class BrowserClickTool(MCPTool):
    """Browser click tool with element reference"""
    
    def __init__(self):
        schema = ToolSchema(
            name="browser_click",
            title="Click",
            description="Perform click on a web page",
            input_schema={
                "type": "object",
                "properties": {
                    "element": {
                        "type": "string",
                        "description": "Human-readable element description"
                    },
                    "ref": {
                        "type": "string",
                        "description": "Exact target element reference from page snapshot"
                    }
                },
                "required": ["element", "ref"]
            },
            type=ToolType.DESTRUCTIVE,
            capability=ToolCapability.CORE
        )
        super().__init__(schema)
    
    async def handle(self, context: 'MCPPlaywrightContext', params: Dict[str, Any]) -> ToolResult:
        try:
            element_desc = params["element"]
            element_ref = params["ref"]
            
            tab = await context.ensure_tab()
            
            # Click using the element reference
            await tab.page.click(element_ref)
            
            code = [
                f"// Click on {element_desc}",
                f"await page.click('{element_ref}');"
            ]
            
            return ToolResult(
                code=code,
                capture_snapshot=True,
                success=True
            )
        except Exception as e:
            return ToolResult(
                code=[f"// Click failed: {str(e)}"],
                success=False,
                error_message=str(e)
            )


class BrowserTypeTool(MCPTool):
    """Browser type tool for text input"""
    
    def __init__(self):
        schema = ToolSchema(
            name="browser_type",
            title="Type text",
            description="Type text into editable element",
            input_schema={
                "type": "object",
                "properties": {
                    "element": {
                        "type": "string",
                        "description": "Human-readable element description"
                    },
                    "ref": {
                        "type": "string",
                        "description": "Exact target element reference from page snapshot"
                    },
                    "text": {
                        "type": "string",
                        "description": "Text to type into the element"
                    },
                    "submit": {
                        "type": "boolean",
                        "description": "Whether to submit entered text (press Enter after)",
                        "default": False
                    },
                    "slowly": {
                        "type": "boolean",
                        "description": "Whether to type one character at a time",
                        "default": False
                    }
                },
                "required": ["element", "ref", "text"]
            },
            type=ToolType.DESTRUCTIVE,
            capability=ToolCapability.CORE
        )
        super().__init__(schema)
    
    async def handle(self, context: 'MCPPlaywrightContext', params: Dict[str, Any]) -> ToolResult:
        try:
            element_desc = params["element"]
            element_ref = params["ref"]
            text = params["text"]
            submit = params.get("submit", False)
            slowly = params.get("slowly", False)
            
            tab = await context.ensure_tab()
            
            if slowly:
                await tab.page.type(element_ref, text, delay=100)
            else:
                await tab.page.fill(element_ref, text)
            
            if submit:
                await tab.page.press(element_ref, "Enter")
            
            code = [
                f"// Type '{text}' into {element_desc}",
                f"await page.fill('{element_ref}', '{text}');"
            ]
            
            if submit:
                code.append(f"await page.press('{element_ref}', 'Enter');")
            
            return ToolResult(
                code=code,
                capture_snapshot=True,
                success=True
            )
        except Exception as e:
            return ToolResult(
                code=[f"// Type failed: {str(e)}"],
                success=False,
                error_message=str(e)
            )


class MCPPlaywrightContext:
    """Main context manager for MCP Playwright integration"""
    
    def __init__(self, config: Optional[Dict[str, Any]] = None):
        self.config = config or {}
        self.playwright_instance = None
        self.browser: Optional[Browser] = None
        self.browser_context: Optional[MCPBrowserContext] = None
        self.current_tab: Optional[MCPTab] = None
        self.tools: Dict[str, MCPTool] = {}
        self.session_id = str(uuid.uuid4())
        
        # Initialize tools
        self._register_tools()
        
        # Setup logging
        self._setup_logging()
    
    def _setup_logging(self):
        """Setup logging configuration"""
        logging.basicConfig(
            level=logging.INFO,
            format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
            handlers=[
                logging.FileHandler(f'mcp_playwright_{self.session_id}.log'),
                logging.StreamHandler()
            ]
        )
    
    def _register_tools(self):
        """Register all available tools"""
        tools = [
            BrowserSnapshotTool(),
            BrowserNavigateTool(),
            BrowserClickTool(),
            BrowserTypeTool()
        ]
        
        for tool in tools:
            self.tools[tool.schema.name] = tool
    
    async def initialize(self):
        """Initialize Playwright and browser"""
        try:
            self.playwright_instance = await async_playwright().start()
            
            # Browser configuration
            browser_type = self.config.get('browser', 'chromium')
            headless = self.config.get('headless', False)
            
            if browser_type == 'chromium':
                self.browser = await self.playwright_instance.chromium.launch(headless=headless)
            elif browser_type == 'firefox':
                self.browser = await self.playwright_instance.firefox.launch(headless=headless)
            elif browser_type == 'webkit':
                self.browser = await self.playwright_instance.webkit.launch(headless=headless)
            else:
                raise ValueError(f"Unsupported browser type: {browser_type}")
            
            # Create browser context
            context = await self.browser.new_context()
            self.browser_context = MCPBrowserContext(context, context.close)
            
            logging.info(f"MCP Playwright context initialized with {browser_type}")
            
        except Exception as e:
            logging.error(f"Failed to initialize MCP Playwright context: {e}")
            raise
    
    async def ensure_tab(self) -> MCPTab:
        """Ensure we have an active tab"""
        if not self.current_tab:
            if not self.browser_context:
                await self.initialize()
            
            page = await self.browser_context.context.new_page()
            self.current_tab = MCPTab(page, self.browser_context)
            self.browser_context.tabs.append(self.current_tab)
        
        return self.current_tab
    
    async def execute_tool(self, tool_name: str, params: Dict[str, Any]) -> ToolResult:
        """Execute a tool by name"""
        if tool_name not in self.tools:
            return ToolResult(
                code=[f"// Error: Tool '{tool_name}' not found"],
                success=False,
                error_message=f"Tool '{tool_name}' not found"
            )
        
        tool = self.tools[tool_name]
        try:
            return await tool.handle(self, params)
        except Exception as e:
            logging.error(f"Tool execution failed for {tool_name}: {e}")
            return ToolResult(
                code=[f"// Tool execution failed: {str(e)}"],
                success=False,
                error_message=str(e)
            )
    
    def get_tool_schemas(self) -> List[Dict[str, Any]]:
        """Get all tool schemas for MCP client"""
        return [asdict(tool.schema) for tool in self.tools.values()]
    
    async def close(self):
        """Clean up resources"""
        try:
            if self.browser_context:
                await self.browser_context.close()
            if self.browser:
                await self.browser.close()
            if self.playwright_instance:
                await self.playwright_instance.stop()
            logging.info("MCP Playwright context closed successfully")
        except Exception as e:
            logging.error(f"Error closing MCP Playwright context: {e}")


class MCPPlaywrightServer:
    """MCP Playwright Server - Microsoft-style implementation"""
    
    def __init__(self, config: Optional[Dict[str, Any]] = None):
        self.config = config or {}
        self.context = MCPPlaywrightContext(config)
        self.is_running = False
    
    async def start(self):
        """Start the MCP server"""
        try:
            await self.context.initialize()
            self.is_running = True
            logging.info("MCP Playwright Server started successfully")
        except Exception as e:
            logging.error(f"Failed to start MCP Playwright Server: {e}")
            raise
    
    async def handle_tool_call(self, tool_name: str, params: Dict[str, Any]) -> Dict[str, Any]:
        """Handle incoming tool calls"""
        if not self.is_running:
            return {
                "success": False,
                "error": "Server not running"
            }
        
        try:
            result = await self.context.execute_tool(tool_name, params)
            
            return {
                "success": result.success,
                "code": result.code,
                "action_result": result.action_result,
                "error_message": result.error_message
            }
        except Exception as e:
            logging.error(f"Error handling tool call {tool_name}: {e}")
            return {
                "success": False,
                "error": str(e)
            }
    
    def get_available_tools(self) -> List[Dict[str, Any]]:
        """Get list of available tools"""
        return self.context.get_tool_schemas()
    
    async def stop(self):
        """Stop the MCP server"""
        try:
            await self.context.close()
            self.is_running = False
            logging.info("MCP Playwright Server stopped")
        except Exception as e:
            logging.error(f"Error stopping server: {e}")


# Example usage and integration
async def example_usage():
    """Example of how to use the MCP Playwright Server"""
    
    # Configuration
    config = {
        'browser': 'chromium',
        'headless': False,
        'viewport': {'width': 1280, 'height': 720}
    }
    
    # Create and start server
    server = MCPPlaywrightServer(config)
    await server.start()
    
    try:
        # Example tool calls
        
        # 1. Navigate to a URL
        nav_result = await server.handle_tool_call(
            "browser_navigate", 
            {"url": "https://example.com"}
        )
        print("Navigation result:", nav_result)
        
        # 2. Take accessibility snapshot
        snapshot_result = await server.handle_tool_call(
            "browser_snapshot", 
            {}
        )
        print("Snapshot result:", snapshot_result["success"])
        
        # 3. Click on an element (would need actual element reference)
        # click_result = await server.handle_tool_call(
        #     "browser_click",
        #     {
        #         "element": "Search button",
        #         "ref": "button:nth-of-type(1)"
        #     }
        # )
        
    finally:
        await server.stop()


if __name__ == "__main__":
    # Run example
    asyncio.run(example_usage()) 