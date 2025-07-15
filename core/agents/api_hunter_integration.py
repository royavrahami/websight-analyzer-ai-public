#!/usr/bin/env python3
"""
API Hunter GUI Integration
==========================

Integration module for API Hunter Agent with GUI applications.
Provides GUI extensions and helper functions for web analyzer interfaces.

Author: Roy Avrahami - Senior QA Automation Architect
"""

import tkinter as tk
from tkinter import ttk
from pathlib import Path
from typing import Optional, Callable, Any
import threading
import asyncio
from datetime import datetime

from .api_hunter_agent import APIHunterAgent, APIHunterConfig


class APIHunterGUIExtension:
    """GUI extension for API Hunter integration"""
    
    def __init__(self, parent_gui):
        self.parent_gui = parent_gui
        self.api_hunter_enabled = tk.BooleanVar(value=True)
        self.capture_xhr_only = tk.BooleanVar(value=True)
        self.max_response_size = tk.StringVar(value="1024")  # KB
        
    def add_api_hunter_section(self, parent_frame):
        """Add API Hunter configuration section to GUI"""
        # API Hunter Section
        api_frame = tk.LabelFrame(parent_frame, text="🕵️ API Hunter",
                                  font=('Arial', 10, 'bold'), 
                                  bg='white', fg='#059669')
        api_frame.pack(fill='x', pady=(0, 5))
        
        # Main enable checkbox
        tk.Checkbutton(api_frame, text="🌐 Enable Network Traffic Analysis",
                       variable=self.api_hunter_enabled, bg='white',
                       font=('Arial', 10), fg='#059669').pack(anchor='w', padx=5, pady=2)
        
        # Configuration options
        config_frame = tk.LabelFrame(api_frame, text="📊 Capture Settings",
                                     font=('Arial', 9, 'bold'), bg='white',
                                     fg='#374151')
        config_frame.pack(fill='x', padx=10, pady=(5, 0))
        
        # XHR only option
        tk.Checkbutton(config_frame, text="📡 Capture XHR/Fetch only (recommended)",
                       variable=self.capture_xhr_only, bg='white',
                       font=('Arial', 9)).pack(anchor='w', padx=5, pady=2)
        
        # Max response size
        size_frame = tk.Frame(config_frame, bg='white')
        size_frame.pack(fill='x', padx=5, pady=2)
        
        tk.Label(size_frame, text="💾 Max Response Size (KB):",
                 font=('Arial', 9), bg='white', fg='#374151').pack(side='left')
        tk.Spinbox(size_frame, from_=128, to=10240, width=8,
                   textvariable=self.max_response_size,
                   font=('Arial', 9)).pack(side='left', padx=(5, 0))
        
        # Info labels
        info_frame = tk.Frame(api_frame, bg='white')
        info_frame.pack(fill='x', padx=10, pady=(5, 10))
        
        info_labels = [
            "• Captures API calls, generates automated tests",
            "• Creates performance analysis and documentation",
            "• Integrates with pytest for continuous testing"
        ]
        
        for label in info_labels:
            tk.Label(info_frame, text=label,
                     font=('Arial', 8, 'italic'), fg='#059669', bg='white').pack(anchor='w')
    
    def get_config(self) -> APIHunterConfig:
        """Get API Hunter configuration from GUI settings"""
        return APIHunterConfig(
            capture_xhr_only=self.capture_xhr_only.get(),
            capture_static_assets=False,
            capture_images=False,
            max_response_size=int(self.max_response_size.get()) * 1024,  # Convert KB to bytes
            output_dir="./api_analysis"
        )
    
    def is_enabled(self) -> bool:
        """Check if API Hunter is enabled in GUI"""
        return self.api_hunter_enabled.get()


class APIHunterIntegration:
    """Main integration class for API Hunter with analysis workflows"""
    
    def __init__(self, log_callback: Optional[Callable[[str], None]] = None):
        self.log_callback = log_callback or print
        self.agent: Optional[APIHunterAgent] = None
        
    def log_message(self, message: str):
        """Log message using callback or print"""
        self.log_callback(f"[API-HUNTER] {message}")
        
    async def run_analysis(self, url: str, output_dir: str, config: APIHunterConfig) -> bool:
        """Run API Hunter analysis on a URL"""
        try:
            self.log_message("🚀 Starting API Hunter network analysis...")
            
            # Create agent with config
            config.output_dir = output_dir
            self.agent = APIHunterAgent(config)
            
            # Use Playwright to capture network traffic
            from playwright.async_api import async_playwright
            
            async with async_playwright() as p:
                browser = await p.chromium.launch(headless=True)
                context = await browser.new_context()
                page = await context.new_page()
                
                # Attach API Hunter to page
                await self.agent.attach_to_page(page)
                
                self.log_message(f"🌐 Navigating to: {url}")
                await page.goto(url, wait_until="networkidle", timeout=30000)
                
                # Wait for API calls to complete
                await asyncio.sleep(3)
                
                # Perform some interactions to trigger more API calls
                await self._perform_interactions(page)
                
                # Save results
                await self.agent.save_session_data()
                
                await browser.close()
                
            # Get statistics
            stats = self.agent.get_statistics()
            self.log_message(f"✅ Analysis complete - Captured {stats['total_captured']} API calls")
            
            return True
            
        except Exception as e:
            self.log_message(f"❌ Error during analysis: {e}")
            return False
    
    async def _perform_interactions(self, page):
        """Perform interactions to trigger API calls"""
        try:
            self.log_message("🖱️ Performing interactions to trigger API calls...")
            
            # Click buttons
            buttons = await page.query_selector_all('button, [role="button"]')
            for i, button in enumerate(buttons[:3]):  # Limit to first 3 buttons
                try:
                    if await button.is_visible():
                        await button.click(timeout=2000)
                        await asyncio.sleep(1)
                        self.log_message(f"   🔘 Clicked button {i+1}")
                except:
                    pass
            
            # Scroll to trigger lazy loading
            for _ in range(2):
                await page.evaluate('window.scrollBy(0, window.innerHeight)')
                await asyncio.sleep(1)
                
            self.log_message("✅ Interactions completed")
            
        except Exception as e:
            self.log_message(f"⚠️ Error during interactions: {e}")
    
    def run_analysis_sync(self, url: str, output_dir: str, config: APIHunterConfig) -> bool:
        """Synchronous wrapper for async analysis"""
        try:
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)
            result = loop.run_until_complete(self.run_analysis(url, output_dir, config))
            loop.close()
            return result
        except Exception as e:
            self.log_message(f"❌ Sync analysis error: {e}")
            return False
    
    def run_analysis_threaded(self, url: str, output_dir: str, config: APIHunterConfig, 
                            callback: Optional[Callable[[bool], None]] = None):
        """Run analysis in a separate thread"""
        def thread_worker():
            result = self.run_analysis_sync(url, output_dir, config)
            if callback:
                callback(result)
                
        thread = threading.Thread(target=thread_worker, daemon=True)
        thread.start()
        return thread 