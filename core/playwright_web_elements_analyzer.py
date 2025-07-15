#!/usr/bin/env python3
"""
Integrated Web Element Analyzer for Playwright

This script accepts a URL from the user, analyzes the webpage's HTML structure,
detects framework-specific elements, and creates comprehensive files with
information about elements, properties, selectors, positions, and various
automation helpers (Playwright Page Object, Cucumber steps, CSV, HTML report).

Usage:
    python playwright_web_elements_analyzer.py -u <URL> -o <output_dir> [options]

Example:
    python playwright_web_elements_analyzer.py -u https://example.com -o ./analysis_results -a -hl

Options:
    -u URL, --url URL           URL to analyze (required)
    -o OUTPUT, --output OUTPUT  Output directory (default: ./output_<timestamp>)
    -hl, --headless             Run browser in headless mode (default: True)
    -a, --all                   Enable all optional features (CSV, HTML Report, Cucumber)
    -csv, --export-csv          Export elements to CSV
    -html, --html-report        Generate HTML analysis report
    -cuc, --cucumber            Generate Cucumber-style step definitions
    # Other options like -f (file), -d (domain), -v (verbose), -m (mobile), etc. exist but main focus is URL analysis
    --scrapy                    Enable recursive crawling of the website
    --depth                     Maximum depth for recursive crawling (default: 1)
    --max-pages                 Maximum number of pages to crawl (default: 100)
    --delay                     Delay between requests in seconds (default: 0.5)
    --exclude                   URL patterns to exclude from crawling
    --include-only              Only crawl URLs matching these patterns (if specified)

Author: Roy Avrahami (Original), Gemini (Integration & Refactoring)
Date: April 2025 (Updated April 9, 2025)
"""

import os
import json
import time
import argparse
import csv
import re
import datetime
from datetime import datetime
from urllib.parse import urlparse, urljoin
from pathlib import Path
from typing import Dict, List, Any, Optional, Union
import keyword
import sys
import traceback  # Import traceback for better error logging
import io
from collections import deque
import glob
import shutil

# import anthropic  # Removed to avoid ModuleNotFoundError

# Fix encoding issues for Windows console
if os.name == 'nt':  # Windows
    try:
        sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')
        sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding='utf-8', errors='replace')
    except Exception as e:
        print(f"Warning: Could not set UTF-8 encoding: {e}")

# Attempt to import Playwright, handle if not installed
try:
    from playwright.sync_api import sync_playwright, Page, Browser, BrowserContext, Locator, expect
except ImportError:
    print("Error: Playwright library not found.")
    print("Please install it using: pip install playwright")
    print("Then install browser binaries: playwright install")
    sys.exit(1)  # Use sys.exit now that it's imported

sys.path.append(os.path.dirname(os.path.abspath(__file__)))


# from advanced_analysis import APIClient, claude_analyze, run_claude_tool  # הוסר כי לא קיים


def _clean_variable_name(name: str) -> str:
    """Clean a string to be a valid Python variable name (improved)"""
    if not name or not isinstance(name, str):
        return "invalid_name"

    # Replace non-alphanumeric chars (excluding underscore) with underscore
    cleaned = re.sub(r'[^a-zA-Z0-9_]', '_', name)

    # Remove leading digits or underscores
    cleaned = re.sub(r'^[^a-zA-Z_]+', '', cleaned)

    # Remove consecutive underscores
    cleaned = re.sub(r'_+', '_', cleaned)

    # Ensure it's not empty after cleaning
    if not cleaned:
        # Use hash for uniqueness if name was entirely invalid characters
        return f"element_{abs(hash(name)) % 10000}"

    # Check if it starts with a letter or underscore (required)
    if not cleaned[0].isalpha() and cleaned[0] != '_':
        cleaned = '_' + cleaned

    # Check if it's a Python keyword
    if keyword.iskeyword(cleaned):
        cleaned += '_'

    # Truncate overly long names
    MAX_LEN = 50
    if len(cleaned) > MAX_LEN:
        cleaned = cleaned[:MAX_LEN]

    # Ensure it doesn't end with an underscore (unless it was just '_' initially)
    if len(cleaned) > 1:
        cleaned = cleaned.rstrip('_')

    # Final check for empty string after rstrip
    if not cleaned:
        return f"element_{abs(hash(name)) % 10000}"  # Fallback

    return cleaned


def _get_element_analysis_script() -> str:
    """Get the JavaScript to run in the browser for element analysis.
       Using Python Raw String to avoid escaping issues.
    """
    # Using r""" to treat backslashes literally in Python
    return r"""
    function analyzeElements() {
      try {
        console.log("Analyzing elements via injected script...");
        const results = {
            interactive: [],
            structural: [],
            content: [],
            forms: []
        };
        const MAX_ELEMENTS_PER_CATEGORY = 500; 
        let processedCount = 0;
        const MAX_TOTAL_ELEMENTS = 2000;

        function getElementDetails(el) {
            if (processedCount >= MAX_TOTAL_ELEMENTS) return null;

            let details = null; 
            try {
                const rect = el.getBoundingClientRect();
                const isVisible = !!( el.offsetWidth || el.offsetHeight || rect.width > 0 || rect.height > 0 || el.getClientRects().length > 0);
                if (!isVisible) return null; 

                let cssSelector = el.tagName.toLowerCase();
                if (el.id) {
                    cssSelector = `#${CSS.escape(el.id)}`; 
                } else if (el.className && typeof el.className === 'string') {
                    // Use single backslash for JS regex inside raw Python string
                    const classes = el.className.trim().split(/\s+/).filter(c => c);
                    if (classes.length > 0) {
                      cssSelector += '.' + classes.map(c => CSS.escape(c)).join('.');
                    }
                } else if (el.name && el.tagName.toLowerCase() === 'input') {
                      cssSelector += `[name="${CSS.escape(el.name)}"]`;
                 }

                let xpath = `//${el.tagName.toLowerCase()}`;
                 if (el.id) {
                    xpath += `[@id='${el.id}']`;
                } else if ((el.tagName.toLowerCase() === 'button' || el.tagName.toLowerCase() === 'a') && el.textContent && el.textContent.trim()) {
                    let textContent = el.textContent.trim().substring(0, 50).replace(/'/g, ""); 
                    xpath += `[normalize-space()='${textContent}']`;
                }

                const attributes = {};
                if (el.hasAttributes()) {
                     for (const attr of el.attributes) {
                          attributes[attr.name] = attr.value;
                     }
                }

                processedCount++;
                details = {
                    tagName: el.tagName.toLowerCase(),
                    description: (el.textContent || el.value || el.alt || el.ariaLabel || el.name || el.id || el.type || '').trim().substring(0, 150),
                    name: el.id || el.name || (el.textContent || '').trim().substring(0, 50) || `element_${el.tagName.toLowerCase()}_${processedCount}`,
                    selectors: {
                        css: cssSelector,
                        xpath: xpath,
                        accessibility: el.ariaLabel || el.getAttribute('role') || null 
                    },
                    position: {
                        x: Math.round(rect.left + window.scrollX),
                        y: Math.round(rect.top + window.scrollY),
                        width: Math.round(rect.width),
                        height: Math.round(rect.height)
                    },
                    attributes: attributes,
                    text: (el.textContent || '').trim(),
                    isVisible: isVisible
                };
            } catch (err) {
                 console.warn("Error processing element:", el, err);
            }
            return details; 
        }

        function addElement(category, element) {
             if (element && results[category] && results[category].length < MAX_ELEMENTS_PER_CATEGORY) {
                 results[category].push(element);
             }
        }

        document.querySelectorAll('button, a, input, select, textarea, [role="button"], [role="link"], [onclick]').forEach(el => addElement('interactive', getElementDetails(el)));
        if (processedCount < MAX_TOTAL_ELEMENTS) {
          document.querySelectorAll('form, fieldset').forEach(el => addElement('forms', getElementDetails(el)));
        }
        if (processedCount < MAX_TOTAL_ELEMENTS) {
          document.querySelectorAll('label, legend, th, td').forEach(el => addElement('content', getElementDetails(el)));
        }
        if (processedCount < MAX_TOTAL_ELEMENTS) {
           document.querySelectorAll('h1, h2, h3, h4, h5, h6, p, span, li, dt, dd, strong, em').forEach(el => addElement('content', getElementDetails(el)));
        }
        if (processedCount < MAX_TOTAL_ELEMENTS) {
           document.querySelectorAll('div, section, article, header, footer, nav, main, aside, ul, ol, table').forEach(el => addElement('structural', getElementDetails(el)));
        }

        const uniqueKeys = new Set();
        for (const category in results) {
            results[category] = results[category].filter(el => {
                 if (!el || !el.selectors || !el.selectors.css || !el.position) return false; 
                 const key = `${el.selectors.css}_${el.position.x}_${el.position.y}`;
                if (!uniqueKeys.has(key)) {
                    uniqueKeys.add(key);
                    return true;
                }
                return false;
            });
        }

        const counts = Object.keys(results).map(k => `${results[k].length} ${k}`).join(', ');
        console.log(`Element analysis script finished. Found unique elements: ${counts}. Total processed attempts: ${processedCount}`);
        return results;
      } catch (scriptError) { 
        console.error("Error executing element analysis script:", scriptError);
        return { 
            error: `Error in element analysis script: ${scriptError.message}`,
            interactive: [], structural: [], content: [], forms: []
        }; 
      }
    }
    """


def _get_visual_map_html_template() -> str:
    """Return the HTML template for the visual map.
       Based on user-provided code.
    """
    # Note: This template is very basic and relies on external files.
    # It now uses a placeholder for the data.
    # Using regular triple-quoted string instead of f-string for safety.
    return """<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="UTF-8">
<title>Visual Element Map</title>
<style>
    body { font-family: Arial, sans-serif; margin: 0; padding: 0; position: relative; }
    #screenshot-container { position: relative; display: inline-block; border: 1px solid black; overflow: hidden; /* Hide potential overflow */ }
    #screenshot-img { display: block; max-width: 100%; height: auto; }
    .element-box {
        position: absolute;
        border: 1px solid rgba(255, 0, 0, 0.7);
        background-color: rgba(255, 0, 0, 0.1);
        box-sizing: border-box;
        cursor: pointer;
        transition: background-color 0.2s ease;
        overflow: hidden; /* Prevent content spill */
        pointer-events: auto; /* Make sure boxes are clickable */
    }
    .element-box:hover {
        background-color: rgba(255, 0, 0, 0.3);
        border-color: red;
        z-index: 10; /* Bring hovered box to front */
    }
    #tooltip {
        position: absolute;
        background-color: rgba(0, 0, 0, 0.8);
        color: white;
        padding: 5px 10px;
        border-radius: 4px;
        font-size: 12px;
        white-space: pre-wrap; /* Wrap long text */
        word-wrap: break-word; /* Break long words */
        display: none; /* Hidden by default */
        z-index: 1000;
        pointer-events: none; /* Don't block hover on element */
        max-width: 300px; /* Limit tooltip width */
    }
</style>
</head>
<body>
<h1>Visual Element Map</h1>
<p>Hover over the red boxes to see element details. Click to log details to console.</p>
<div id="screenshot-container">
    <img id="screenshot-img" src="screenshot.png" alt="Page Screenshot (if available)">
    <!-- Element boxes will be injected here by JavaScript -->
</div>
<div id="tooltip"></div>

<script>
    const elementsData = /*ELEMENT_DATA_PLACEHOLDER*/{}; // Data will be injected here
    const container = document.getElementById('screenshot-container');
    const tooltip = document.getElementById('tooltip');
    let elements = [];

    // Flatten the element data from categories
    try {
        for (const category in elementsData) {
            if (Array.isArray(elementsData[category])) {
                elements = elements.concat(elementsData[category]);
            }
        }
        console.log(`Loaded ${elements.length} elements for visual map.`);
        if (elements.length > 0) { createBoxes(); }
        else { console.warn('No element data found to create boxes.'); }
    } catch (error) {
         console.error('Error processing element data:', error);
         container.innerHTML += '<p style="color: red;">Error processing element data.</p>';
    }


    function createBoxes() {
        elements.forEach((element, index) => {
            if (!element || !element.position) return; // Skip if no element or position
            const pos = element.position;
            if (pos.width <= 0 || pos.height <= 0) return; // Skip zero-size elements

            const box = document.createElement('div');
            box.className = 'element-box';
            // Use page coordinates directly if available, otherwise fallback to viewport
            box.style.left = `${pos.x || 0}px`;
            box.style.top = `${pos.y || 0}px`;
            box.style.width = `${pos.width}px`;
            box.style.height = `${pos.height}px`;
            box.dataset.index = index; // Store index to retrieve data
            box.title = `${element.name || 'Element'} (${element.tagName})`; // Basic title attribute

            box.addEventListener('mouseover', showTooltip);
            box.addEventListener('mousemove', moveTooltip);
            box.addEventListener('mouseout', hideTooltip);
            box.addEventListener('click', logElementDetails);

            container.appendChild(box);
        });
         console.log(`Created ${container.querySelectorAll('.element-box').length} visual boxes.`);
    }

    function showTooltip(event) {
        const index = event.target.dataset.index;
        if (index === undefined) return;
        const element = elements[index];
        if (!element) return;

        const details = [
            `Name: ${element.name || 'N/A'}`, // Still using JS template literals here, which is fine inside JS
            `Tag: ${element.tagName || 'N/A'}`,
            `Text: ${(element.text || '').substring(0, 50)}${(element.text || '').length > 50 ? '...' : ''}`,
            `CSS: ${element.selectors?.css || 'N/A'}`,
            `XPath: ${element.selectors?.xpath || 'N/A'}`,
            `Pos: (${element.position?.x}, ${element.position?.y})`,
            `Size: ${element.position?.width} x ${element.position?.height}`
        ].join('\n');
        tooltip.textContent = details;
        tooltip.style.display = 'block';
        moveTooltip(event); // Position it initially
    }

    function moveTooltip(event) {
         // Position tooltip slightly offset from cursor, considering viewport edges
         const x = event.pageX + 15;
         const y = event.pageY + 15;
         const tooltipWidth = tooltip.offsetWidth;
         const tooltipHeight = tooltip.offsetHeight;
         const viewportWidth = window.innerWidth;
         const viewportHeight = window.innerHeight;

         tooltip.style.left = Math.min(x, viewportWidth - tooltipWidth - 10) + 'px';
         tooltip.style.top = Math.min(y, viewportHeight - tooltipHeight - 10) + 'px';
    }

    function hideTooltip() {
        tooltip.style.display = 'none';
    }

    function logElementDetails(event) {
        const index = event.target.dataset.index;
        if (index === undefined) return;
        const element = elements[index];
        if (element) {
            console.log('Clicked Element Details:', element);
            // Optionally display details more prominently
        }
    }

    // Adjust container size if screenshot loads
    const img = document.getElementById('screenshot-img');
    img.onload = () => {
        // Set container size based on image natural dimensions
        console.log('Screenshot loaded: ' + img.naturalWidth + 'x' + img.naturalHeight);
        container.style.width = img.naturalWidth + 'px';
        container.style.height = img.naturalHeight + 'px';
    };
    img.onerror = () => {
        console.warn('Screenshot image failed to load.');
         container.style.border = '1px dashed gray';
         container.innerHTML += '<p style="color: orange; text-align: center;">Screenshot not found or failed to load.</p>';
    };
    // Check if image is already loaded (e.g., from cache)
    if (img.complete && img.naturalHeight !== 0) {
        console.log('Screenshot already loaded from cache.');
        img.onload();
    }

</script>
</body>
</html>
"""


class WebElementAnalyzer:
    """Main class for analyzing web elements on a page with integrated features"""

    def __init__(self, headless: bool = True):
        """Initialize the analyzer with configuration options"""
        print(f"Initializing WebElementAnalyzer (Headless: {headless})")
        self.headless = headless
        self.playwright = None
        self.browser = None
        self.context = None
        self.page: Optional[Page] = None  # Type hint for page
        self.output_dir: Optional[Path] = None  # Use Path object
        self.domain: Optional[str] = None
        self.url: Optional[str] = None
        self.page_title: Optional[str] = None
        self.framework_data: Dict[str, Any] = {}  # Store framework results (if implemented)
        self.elements_data: Dict[str, List[Dict[str, Any]]] = {}  # Store results from _analyze_elements
        self.css_selectors: Dict[str, Dict[str, Any]] = {}
        self.xpath_selectors: Dict[str, Dict[str, Any]] = {}
        self.a11y_selectors: Dict[str, Dict[str, Any]] = {}
        self.ml_classifier = None  # Initialize ML classifier as None

    def start(self):
        """Start the Playwright browser instance"""
        if self.playwright:
            print("Playwright already started.")
            return
        print("Starting Playwright...")
        try:
            self.playwright = sync_playwright().start()
            print("Launching Chromium browser...")
            self.browser = self.playwright.chromium.launch(headless=self.headless)
            print("Creating new browser context...")
            self.context = self.browser.new_context(
                viewport={"width": 1366, "height": 768},  # Standard viewport size
                # user_agent="Mozilla/5.0 ..." # Consider adding user agent override if needed
                java_script_enabled=True  # JS is enabled by default, but explicit can be good
            )
            print("Creating new page...")
            self.page = self.context.new_page()
            print("Browser started successfully.")
        except Exception as e:
            print(f"Error starting Playwright browser: {e}")
            traceback.print_exc()
            self.close()  # Attempt cleanup
            raise  # Re-raise the exception to signal failure

    def close(self):
        """Close all browser resources gracefully"""
        print("Closing browser resources...")
        # Close in reverse order of creation
        if self.page:
            try:
                self.page.close()
                print("- Page closed.")
            except Exception as e:
                print(f"- Error closing page: {e}")
            finally:
                self.page = None
        if self.context:
            try:
                self.context.close()
                print("- Context closed.")
            except Exception as e:
                print(f"- Error closing context: {e}")
            finally:
                self.context = None
        if self.browser:
            try:
                self.browser.close()
                print("- Browser closed.")
            except Exception as e:
                print(f"- Error closing browser: {e}")
            finally:
                self.browser = None
        if self.playwright:
            try:
                self.playwright.stop()
                print("- Playwright stopped.")
            except Exception as e:
                print(f"- Error stopping Playwright: {e}")
            finally:
                self.playwright = None
        print("Browser resources closed process finished.")

    def analyze_url(self, url: str, base_output_path: str,
                    generate_all_outputs: bool = False,
                    generate_csv: bool = False,
                    generate_cucumber: bool = False,
                    generate_report: bool = False,
                    detect_frameworks: bool = False,
                    visualize: bool = False,
                    json_only: bool = False) -> Optional[Path]:
        """Analyze a URL and generate outputs"""
        try:
            # Create output directory
            output_path = Path(base_output_path)
            output_path.mkdir(parents=True, exist_ok=True)

            # Start browser
            self.start()

            # Navigate to URL with retry logic
            max_retries = 3
            retry_delay = 2  # seconds

            for attempt in range(max_retries):
                try:
                    if not self.page:
                        raise RuntimeError("Playwright page is not initialized.")
                    self.page.goto(url, wait_until='load', timeout=30000)  # 30 second timeout
                    break
                except Exception as e:
                    if attempt < max_retries - 1:
                        print(f"Connection attempt {attempt + 1} failed: {e}")
                        print(f"Retrying in {retry_delay} seconds...")
                        time.sleep(retry_delay)
                        retry_delay *= 2  # Exponential backoff
                    else:
                        print(f"Failed to connect after {max_retries} attempts")
                        raise

            # Continue with analysis...
            print(f"\n--- Starting Analysis for: {url} ---")
            self.url = url
            self.framework_data = {}  # Reset
            self.elements_data = {}  # Reset
            self.css_selectors = {}
            self.xpath_selectors = {}
            self.a11y_selectors = {}
            self.page_title = None  # Reset

            # 1. Setup: Parse URL, Create Output Directory
            print("--- Step 1: Setup ---")
            try:
                parsed_url = urlparse(url)
                if not parsed_url.scheme or not parsed_url.netloc:
                    raise ValueError("Invalid URL format. Please include scheme (e.g., http:// or https://)")
                # Use provided domain if available, otherwise extract
                if not self.domain:  # Check if domain was passed via main args
                    self.domain = parsed_url.netloc.replace(".", "_").replace(":", "_")
                print(f"Domain identified/set as: {self.domain}")

                timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
                # Clean URL for directory name
                url_clean = re.sub(r'[^\w\-_]', '_', parsed_url.netloc)
                url_clean = re.sub(r'_+', '_', url_clean).strip('_')
                # Ensure base path is a Path object
                base_path = Path(base_output_path)
                self.output_dir = base_path / f"analysis_{url_clean}_{timestamp}"
                print(f"Output directory target: {self.output_dir}")

                self.output_dir.mkdir(parents=True, exist_ok=True)
                print(f"Output directory created/verified: {self.output_dir}")

            except ValueError as e:
                print(f"Error processing URL/Domain: {e}")
                return None
            except OSError as e:
                print(f"Error creating output directory '{self.output_dir}': {e}")
                return None
            except Exception as e:
                print(f"Unexpected setup error: {e}")
                traceback.print_exc()
                return None

            # 2. Browser Start & Navigation
            print("--- Step 2: Browser Interaction ---")
            try:
                if not self.page:
                    self.start()  # Start browser if not already running

                if not self.page:
                    raise RuntimeError("Playwright page could not be initialized.")

                print(f"Navigating to page: {url}...")
                # Use 'load' state which is generally safer than 'networkidle'
                self.page.goto(url, wait_until="load", timeout=90000)  # 90 seconds timeout
                print("Page navigation successful (load event fired).")

                # Safely get page title with error handling
                try:
                    self.page_title = self.page.title()
                    print(f"Page Title: {self.page_title}")
                except Exception as title_error:
                    self.page_title = f"Unknown (Error: {str(title_error).split(':')[-1].strip()})"
                    print(f"Warning: Could not retrieve page title: {title_error}")
                    # Continue with analysis despite title error

            except Exception as e:
                print(f"\n--- ERROR DURING BROWSER START/NAVIGATION --- ")
                print(f"Failed to load URL: {e}")
                traceback.print_exc()
                self.close()  # Ensure cleanup
                return None

            # 3. Core Analysis & Output Generation
            analysis_succeeded = False
            try:
                print("--- Step 3: Core Analysis & Generation ---")

                # 3a. Basic Info Extraction
                self._extract_basic_info()

                # 3b. Element Analysis (JS Execution)
                self._analyze_elements()  # Creates self.elements_data, self.css_selectors etc.

                # Check if core analysis produced results
                if not self.elements_data or not any(self.elements_data.values()):
                    print("Warning: No elements data generated by analysis script. Subsequent outputs might be empty.")
                    # Continue but expect potential issues in generation steps

                # --- Generate core files needed by optional outputs ---
                # (PO, Selectors, Test Template are considered core helpers here)
                self._create_helpers()

                # Generate basic visual map (even if visualize flag is off for now)
                self._generate_visual_map()

                # --- Generate Optional Outputs ---
                if not json_only:
                    print("--- Generating Optional Outputs --- ")
                    if generate_csv or generate_all_outputs:
                        self.export_csv()
                    if generate_report or generate_all_outputs:
                        self.generate_html_report()
                    if generate_cucumber or generate_all_outputs:
                        self.generate_cucumber_steps()

                    # Placeholder calls for unimplemented features
                    if detect_frameworks or generate_all_outputs:
                        print("Note: Framework detection is not fully implemented.")
                        # self.detect_frameworks() # Call if/when implemented
                    # if visualize or generate_all_outputs:
                    #      print("Note: Advanced visualization is not fully implemented (basic visual map is generated)." )
                    #      # self.generate_visualizations() # Call if/when implemented
                else:
                    print("Skipping optional outputs as --json-only was specified.")

                # --- Generate AI Summary ---
                print("--- Generating AI Summary ---")
                self._generate_ai_summary_for_single_page()

                # --- Generate README Last ---
                self._create_readme()  # Summarizes generated files

                # Save run info for MCP
                self._save_run_info()

                print("\n--- Analysis and Generation Steps Completed --- ")
                analysis_succeeded = True  # Mark as succeeded if we got here

            except Exception as e:
                print(f"\n--- ERROR DURING ANALYSIS/GENERATION --- ")
                print(f"An unexpected error occurred: {e}")
                traceback.print_exc()  # Print full traceback for debugging
                analysis_succeeded = False  # Ensure failure
            finally:
                # 4. Cleanup
                print("--- Step 4: Cleanup --- ")
                self.close()

            if analysis_succeeded:
                print(f"--- Analysis Successfully Finished for {url} ---")
                return self.output_dir  # Return the path on success
            else:
                print(f"--- Analysis Failed for {url} --- ")
                return None  # Indicate failure

        except Exception as e:
            print(f"Error analyzing URL: {e}")
            traceback.print_exc()
            return None

    # --- Core Methods ---
    def _extract_basic_info(self):
        """Extract basic page information including HTML and metadata"""
        print("Extracting basic page information...")
        if not self.page or not self.output_dir:
            print("Error: Page or output directory not initialized for basic info extraction.")
            return  # הסרתי את ה-None המיותר

        # Save full HTML
        try:
            html_content = self.page.content()
            html_path = self.output_dir / "full_page.html"
            with open(html_path, "w", encoding="utf-8") as f:
                f.write(html_content)
            print(f"Full HTML saved to {html_path}")
        except Exception as e:
            print(f"Error saving HTML content: {e}")

        # Extract metadata
        try:
            # Use a more reliable approach to extract metadata with proper error handling
            metadata = {}

            try:
                metadata = self.page.evaluate("""() => {
                    try {
                        return {
                            title: document.title,
                            url: window.location.href,
                            metaTags: Array.from(document.querySelectorAll('meta')).map(meta => {
                                const attributes = {};
                                for (const attr of meta.attributes) {
                                    attributes[attr.name] = attr.value;
                                }
                                return attributes;
                            }),
                            scripts: Array.from(document.querySelectorAll('script[src]')).map(script => script.src),
                            stylesheets: Array.from(document.querySelectorAll('link[rel="stylesheet"]')).map(link => link.href)
                        };
                    } catch (err) {
                        return { error: `Error extracting metadata in browser: ${err.message}` };
                    }
                }""")
            except Exception as eval_error:
                print(f"Error during metadata evaluation: {eval_error}")
                # Create a fallback metadata object
                metadata = {
                    "title": self.page_title or "Unknown",
                    "url": self.url or "Unknown",  # תיקנתי - השתמשתי ב-self.url במקום url
                    "metaTags": [],
                    "scripts": [],
                    "stylesheets": [],
                    "extraction_error": str(eval_error)
                }

            # Store page title if extracted and not already set
            if isinstance(metadata, dict) and metadata.get('title') and not self.page_title:
                self.page_title = metadata.get('title')

            metadata_path = self.output_dir / "metadata.json"
            with open(metadata_path, "w", encoding="utf-8") as f:
                json.dump(metadata, f, indent=2)
            print(f"Page metadata saved to {metadata_path}")
            if isinstance(metadata, dict) and metadata.get("error"):
                print(f"Warning: {metadata.get('error')}")

        except Exception as e:
            print(f"Error extracting page metadata: {e}")

        # Take a screenshot with improved error handling
        screenshot_path = self.output_dir / "screenshot.png"
        try:
            print("Taking full page screenshot...")
            self.page.screenshot(path=screenshot_path, full_page=True, timeout=30000)  # 30s timeout for screenshot
            print(f"Full page screenshot saved to {screenshot_path}")
        except Exception as e:
            print(f"Could not take full page screenshot: {e}. Trying viewport screenshot.")
            try:
                self.page.screenshot(path=screenshot_path, full_page=False)
                print(f"Viewport screenshot saved to {screenshot_path}")
            except Exception as e2:
                print(f"Could not take viewport screenshot either: {e2}")
                # Create a placeholder image to indicate failure
                try:
                    with open(screenshot_path, "w") as f:
                        f.write("Screenshot failed")
                    print(f"Created placeholder file for failed screenshot at {screenshot_path}")
                except Exception:
                    pass

    # --- ADDED from user code ---

    def _analyze_elements(self):
        """Analyze page elements and extract information"""
        try:
            print("Extracting detailed element information using Playwright...")
            start_time = time.time()

            # Execute element analysis script
            try:
                if not self.page:
                    print("Error: Playwright page is not initialized.")
                    return False
                element_data = self.page.evaluate(_get_element_analysis_script())
            except Exception as e:
                print(f"Error executing element analysis script: {e}")
                return False

            # Process and save element data
            try:
                if not self.output_dir:
                    print("Error: Output directory not set for element data.")
                    return False
                # Save interactive elements
                if 'interactive' in element_data:
                    with open(self.output_dir / 'interactive.json', 'w', encoding='utf-8') as f:
                        json.dump(element_data['interactive'], f, indent=2, ensure_ascii=False)
                    print(f"Saved {len(element_data['interactive'])} 'interactive' elements")
                # Save structural elements
                if 'structural' in element_data:
                    with open(self.output_dir / 'structural.json', 'w', encoding='utf-8') as f:
                        json.dump(element_data['structural'], f, indent=2, ensure_ascii=False)
                    print(f"Saved {len(element_data['structural'])} 'structural' elements")
                # Save content elements
                if 'content' in element_data:
                    with open(self.output_dir / 'content.json', 'w', encoding='utf-8') as f:
                        json.dump(element_data['content'], f, indent=2, ensure_ascii=False)
                    print(f"Saved {len(element_data['content'])} 'content' elements")
                # Save form elements
                if 'forms' in element_data:
                    with open(self.output_dir / 'forms.json', 'w', encoding='utf-8') as f:
                        json.dump(element_data['forms'], f, indent=2, ensure_ascii=False)
                    print(f"Saved {len(element_data['forms'])} 'forms' elements")
                # Always save enhanced_elements.json, even if element_data is empty or invalid
                enhanced_path = self.output_dir / 'enhanced_elements.json'
                enhanced_data = element_data if isinstance(element_data, dict) else {}
                try:
                    with open(enhanced_path, 'w', encoding='utf-8') as f:
                        json.dump(enhanced_data, f, indent=2, ensure_ascii=False)
                        f.write('\n')  # POSIX best practice: end with newline
                    print(f"Enhanced elements saved to {enhanced_path}")
                except Exception as e:
                    print(f"Error writing enhanced_elements.json: {e}")

                # Store the element data for use in other methods
                self.elements_data = enhanced_data

                # Also process selectors from the data
                self._process_selectors(enhanced_data)

                # שימוש במודל ML לשיפור הזיהוי
                if hasattr(self, 'ml_classifier') and self.ml_classifier:
                    for category, elements in enhanced_data.items():
                        for element in elements:
                            predicted_type = self.ml_classifier.predict_element_type(element)
                            element['ml_predicted_type'] = predicted_type

                return True
            except Exception as e:
                print(f"Error saving element data: {e}")
                return False
        except Exception as e:
            print(f"Error in element analysis: {e}")
            return False

    def _process_selectors(self, element_structure):
        """Process and save various selector strategies from element data"""
        if not isinstance(element_structure, dict) or not self.output_dir:
            print("Warning: Invalid element structure data or output directory not set for processing selectors.")
            return

        self.css_selectors = {}
        self.xpath_selectors = {}
        self.a11y_selectors = {}

        print("Processing selectors...")
        processed_count = 0
        skipped_count = 0
        # Process all categories
        for category, elements in element_structure.items():
            if not isinstance(elements, list):
                print(f"Skipping selector processing for category '{category}': data is not a list.")
                continue

            for element in elements:
                if not isinstance(element, dict):
                    skipped_count += 1
                    continue

                selectors = element.get("selectors", {})
                if not isinstance(selectors, dict):
                    skipped_count += 1
                    continue

                # Basic info to associate with the selector
                element_info = {
                    "name": element.get("name", ""),
                    "description": element.get("description", ""),
                    "category": category,
                    "tagName": element.get("tagName", ""),
                    "text": (element.get("text", "") or "")[:100],  # Limit text length
                    "attributes": element.get("attributes", {}),  # Include attributes for context
                    "isVisible": element.get("isVisible", None)  # Include visibility info
                }

                # Add to appropriate selector maps if selector exists and is unique
                css_sel = selectors.get("css")
                if css_sel and isinstance(css_sel, str) and css_sel not in self.css_selectors:
                    self.css_selectors[css_sel] = element_info
                    processed_count += 1
                elif css_sel in self.css_selectors:
                    skipped_count += 1  # Duplicate CSS selector

                xpath_sel = selectors.get("xpath")
                if xpath_sel and isinstance(xpath_sel, str) and xpath_sel not in self.xpath_selectors:
                    self.xpath_selectors[xpath_sel] = element_info
                    # Don't double count if both exist: processed_count += 1
                elif xpath_sel in self.xpath_selectors:
                    skipped_count += 1  # Duplicate XPath selector

                a11y_sel = selectors.get("accessibility")
                if a11y_sel and isinstance(a11y_sel, str) and a11y_sel not in self.a11y_selectors:
                    self.a11y_selectors[a11y_sel] = element_info
                    # processed_count += 1
                elif a11y_sel in self.a11y_selectors:
                    skipped_count += 1

        print(f"Processed {processed_count} unique selectors. Skipped {skipped_count} invalid/duplicate entries.")

        # Save selector maps
        try:
            css_path = self.output_dir / "css_selectors.json"
            with open(css_path, "w", encoding="utf-8") as f:
                json.dump(self.css_selectors, f, indent=2)

            xpath_path = self.output_dir / "xpath_selectors.json"
            with open(xpath_path, "w", encoding="utf-8") as f:
                json.dump(self.xpath_selectors, f, indent=2)

            a11y_path = self.output_dir / "a11y_selectors.json"
            with open(a11y_path, "w", encoding="utf-8") as f:
                json.dump(self.a11y_selectors, f, indent=2)

            print(f"Selector strategy files saved: css_selectors.json, xpath_selectors.json, a11y_selectors.json")
        except Exception as e:
            print(f"Error saving selector files: {e}")

    # --- ADDED from user code ---

    def _generate_visual_map(self):
        """Generate a visual HTML map of elements for interactive exploration"""
        print("Generating visual element map...")
        if not self.output_dir:
            print("Error: Output directory not set for visual map.")
            return

        html_path = self.output_dir / "visual_element_map.html"
        elements_json_path = self.output_dir / "enhanced_elements.json"
        screenshot_exists = (self.output_dir / "screenshot.png").exists()
        elements_to_inject = {}

        # Load element data to inject into the map
        if elements_json_path.exists():
            try:
                with open(elements_json_path, "r", encoding="utf-8") as f:
                    elements_to_inject = json.load(f)
                print(f"Loaded data from {elements_json_path} for visual map.")
            except Exception as e:
                print(f"Error loading {elements_json_path} for visual map: {e}. Map will be empty.")
                elements_to_inject = {}
        else:
            print(f"Warning: Cannot find {elements_json_path}. Visual map will have no element data.")
            elements_to_inject = {}

        if not screenshot_exists:
            print("Warning: screenshot.png not found. Visual map may not display correctly.")

        # Get the HTML template
        visual_map_html_template = _get_visual_map_html_template()

        # Inject the elements data into the template
        placeholder = '/*ELEMENT_DATA_PLACEHOLDER*/'
        if placeholder in visual_map_html_template:
            # Use compact JSON for JS injection
            elements_json_string = json.dumps(elements_to_inject, indent=None, separators=(',', ':'))
            visual_map_html = visual_map_html_template.replace(placeholder, elements_json_string)
        else:
            print("Warning: Placeholder not found in visual map template. Map may not function.")
            visual_map_html = visual_map_html_template  # Use template as-is

        # Write to file
        try:
            with open(html_path, "w", encoding="utf-8") as f:
                f.write(visual_map_html)
            print(f"Visual element map generated: {html_path}")
        except Exception as e:
            print(f"Error writing visual element map HTML file: {e}")

    # --- Helper File Generation ---
    def _create_helpers(self):
        """Generate helper files (PO, Selectors, Test Template) based on analysis"""
        print("Generating Playwright helper files...")
        if not self.output_dir:
            print("Error: Output directory not set for helpers.")
            return

        # Ensure elements_data and css_selectors are populated
        # _analyze_elements should have populated these
        if not self.elements_data:
            print("Warning: No elements data available. Helper files might be basic templates.")
        if not self.css_selectors:
            print("Warning: No CSS selectors processed. Helper files might be basic templates.")

        # Generate Python Page Object Class
        self._generate_page_object()

        # Generate Selectors class
        self._generate_selectors_class()

        # Generate test template
        self._generate_test_template()

    def _generate_page_object(self):
        """Generate a Playwright Page Object Model in Python"""
        if not self.output_dir:
            print("Error: Output directory not set for page object.")
            return
        page_object_path = self.output_dir / "page_object.py"
        domain_part = self.domain or "MyWebsite"
        class_name = domain_part.title().replace('_', '').replace('-', '') + 'Page'

        print(f"Generating Page Object: {class_name}...")

        # Get interactive elements for methods
        # Combine interactive and form elements for processing
        interactive_elements = self.elements_data.get("interactive", []) if isinstance(self.elements_data, dict) else []
        form_elements = self.elements_data.get("forms", []) if isinstance(self.elements_data, dict) else []
        elements_to_process = interactive_elements + form_elements

        # Get current timestamp
        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        
        # Initialize Page Object content
        page_object = f"""# Page Object for {self.url or 'the analyzed page'} - Generated: {timestamp}
# Analysis Date: {timestamp}

import re
from playwright.sync_api import Page, expect, Locator

class {class_name}:
    \"\"
    Page Object Model for {self.url or 'the analyzed page'}
    Contains element locators and methods for interacting with the page.
    Generated by Web Element Analyzer. Review and adapt as needed.
    \"\"

    def __init__(self, page: Page):
        \"\"Initialize with a Playwright page\"\"
        self.page = page
        self.url = "{self.url or ''}"
        # Store title if available
        self.TITLE = "{self.page_title or ''}".replace("'", "\\'")

        # --- Element Locators ---
        # Add locators for important elements found on the page.
        # Descriptions are based on element analysis.
        print(f"Initializing {class_name}...")
"""

        # --- Locator Definitions ---
        locators_code = "    # --- Locators ---\n"
        generated_locators_count = 0
        # Ensure self.locator_names is initialized as a set here
        self.locator_names = set()
        # Iterate through elements to create locators
        # Use the combined list elements_to_process
        for element in elements_to_process:
            try:
                if not isinstance(element, dict): continue
                # Use the cleaned name from _process_selectors if available
                potential_name = element.get("cleaned_name") or element.get("name")
                if not potential_name: continue

                var_name = _clean_variable_name(potential_name)
                selector = element.get("selectors", {}).get("css", None)
                # If no CSS selector, try XPath as fallback for locator generation
                if not selector:
                    selector = element.get("selectors", {}).get("xpath", None)

                desc = (element.get('description', '') or "").replace("'", "\'")
                tag = element.get('tagName', '')

                # Ensure uniqueness and validity AND add to self.locator_names
                # Only proceed if we have a valid selector (CSS or XPath)
                if var_name and selector and var_name not in self.locator_names and var_name.isidentifier() and not keyword.iskeyword(
                        var_name):
                    self.locator_names.add(var_name)  # Add the valid name to the set
                    escaped_selector = selector.replace("'", "\'")
                    locators_code += f"        self.{var_name}_locator = self.page.locator('{escaped_selector}') # Description: '{desc}', Tag: {tag}\n"
                    generated_locators_count += 1
            except Exception as e:  # Add the except block to handle potential errors
                print(f"Error processing element for locator: {element.get('name', '(no name)')} - {e}")

        if generated_locators_count == 0:
            locators_code += "        # No unique interactive/form elements found to generate locators.\n"
            locators_code += "        # Add locators manually, e.g.:\n"
            # Corrected selector class usage if available
            locators_code += '        # self.search_input_locator = self.page.locator(self.selectors.SEARCH_INPUT)\n'
            locators_code += '        # self.submit_button_locator = self.page.locator(self.selectors.SUBMIT_BUTTON)\n'

        print(f"Generated {generated_locators_count} locators.")
        page_object += locators_code

        # --- Basic Page Actions ---
        page_object += f"""
    # --- Basic Page Actions ---

    def navigate(self):
        \"\"Navigate to the page URL.\"\"
        print(f"Navigating to {{self.url}}...")
        if not self.url:
            print("Warning: URL is not defined in Page Object.")
            return
        try:
             self.page.goto(self.url)
             print("Navigation successful.")
        except Exception as e:
             print(f"Error navigating to {{self.url}}: {{e}}")
             raise # Re-raise the exception to fail the test

    def is_loaded(self, timeout: int = 15000) -> bool:
        \"\"Basic check if the page is loaded, e.g., by checking title or a key element.\"\"
        print("Performing basic page load check...")
        if self.TITLE:
            try:
                print(f"Checking for title: '{{self.TITLE}}'...")
                expect(self.page).to_have_title(self.TITLE, timeout=timeout)
                print("Page title matches.")
                return True
            except Exception as e:
                print(f"Page load check failed: Title '{{self.TITLE}}' not found within {{timeout}}ms. Error: {{e}}")
                return False
        else:
            # Fallback: Check if the URL is correct (less reliable)
            print("No title stored, checking current URL...")
            try:
                 expect(self.page).to_have_url(re.compile(self.url), timeout=timeout)
                 print("Page URL matches.")
                 return True
            except Exception as e:
                 print(f"Page load check failed: URL did not match '{{self.url}}' within {{timeout}}ms. Error: {{e}}")
                 return False

"""
        # --- Element Interaction Methods ---
        page_object += "    # --- Element Interaction Methods ---\n"
        generated_methods_count = 0
        method_signatures = set()  # Keep track of generated method signatures

        # Use self.locator_names (populated above) to check if method should be added
        method_vars_added = self.locator_names.copy()  # Use the correctly populated set

        # Use the combined list elements_to_process
        for element in elements_to_process:
            try:
                if not isinstance(element, dict): continue
                potential_name = element.get("cleaned_name") or element.get("name")
                if not potential_name: continue

                var_name = _clean_variable_name(potential_name)
                # Check against the correctly populated self.locator_names
                if var_name not in self.locator_names: continue

                tag_name = element.get('tagName', '').lower()
                element_type = element.get('attributes', {}).get('type', '').lower()
                desc = (element.get('description', '') or "Element").replace("'", "\\'")
                locator_name = f"self.{var_name}_locator"

                method_code = ""
                # Generate methods based on element type...
                # (Code for generating specific methods like click_*, fill_*, select_* goes here)
                # ... (Placeholder for the method generation logic based on element type)

                # Append generated code for this element type if unique
                if method_code:
                    page_object += method_code
                    generated_methods_count += 1  # Increment count correctly

            except Exception as e:  # Close the try block for the current element iteration
                print(f"Error generating method for element {element.get('name', '(no name)')}: {e}")

        print(f"Generated {generated_methods_count} interaction methods.")

        # --- Verification Methods ---
        page_object += f"""
    # --- Verification Methods ---

    def verify_element_visible(self, locator: Locator, description: str, timeout: int = 10000):
        \"\"Verify a specific element is visible\"\"
        # Ensure double curly braces for placeholders in f-string templates
        print(f"Verifying '{{description}}' is visible...")
        try:
            expect(locator).to_be_visible(timeout=timeout)
            print(f"'{{description}}' is visible.")
        except Exception as e:
            print(f"Verification failed: '{{description}}' is not visible within {{timeout}}ms. Error: {{e}}")
            raise AssertionError(f"Element '{{description}}' not visible.") from e

    def verify_element_contains_text(self, locator: Locator, expected_text: Union[str, re.Pattern], description: str, timeout: int = 10000):
        \"\"Verify a specific element contains the expected text (can be regex pattern)\"\"
        # Ensure double curly braces for placeholders
        print(f"Verifying '{{description}}' contains text '{{str(expected_text)[:50]}}...'") 
        try:
            expect(locator).to_contain_text(expected_text, timeout=timeout)
            print(f"'{{description}}' contains expected text.")
        except Exception as e:
            print(f"Verification failed: '{{description}}' does not contain text '{{str(expected_text)[:50]}}...' within {{timeout}}ms. Error: {{e}}")
            raise AssertionError(f"Element '{{description}}' did not contain expected text.") from e

    # Add more specific verification methods as needed, e.g.,
    # def verify_cart_item_count(self, expected_count: int): ...
    # def verify_success_message_displayed(self, text='Success!'): ...

"""

        # Write to file
        try:
            with open(page_object_path, "w", encoding="utf-8") as f:
                f.write(page_object)
            print(f"Playwright Page Object Model generated: {page_object_path}")
        except Exception as e:
            print(f"Error writing Page Object file: {e}")

    def _generate_selectors_class(self):
        """Generate a Python class with all CSS selectors as class variables"""
        if not self.output_dir:
            print("Error: Output directory not set for selectors class.")
            return
        selectors_path = self.output_dir / "selectors.py"
        domain_part = self.domain or "MyWebsite"
        class_name = domain_part.title().replace('_', '').replace('-', '') + 'Selectors'

        print(f"Generating Selectors Class: {class_name}...")

        # Use self.css_selectors populated by _process_selectors
        css_selectors = self.css_selectors

        # Get current timestamp
        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        
        selectors_class = f"""# Selectors for {self.url or 'the analyzed page'} - Generated: {timestamp}
# Analysis Date: {timestamp}

class {class_name}:
    \"\"
    Contains CSS selectors found on the page as class variables.
    These can be used directly in Playwright tests.
    Generated by Web Element Analyzer. Review and adapt as needed.
    Selector descriptions are based on element analysis.
    \"\"
"""

        # Add selector constants
        added_vars = set()
        generated_selectors_count = 0
        if isinstance(css_selectors, dict):
            for selector, info in css_selectors.items():
                if not isinstance(info, dict) or not isinstance(selector, str): continue

                potential_name = info.get("description", "") or info.get("name",
                                                                         "") or f"element_{info.get('tagName', 'tag')}_{abs(hash(selector)) % 1000}"

                if potential_name and isinstance(potential_name, str):
                    var_name = _clean_variable_name(potential_name).upper()
                    # Ensure uniqueness and validity
                    if var_name and var_name not in added_vars and var_name.isidentifier() and not keyword.iskeyword(
                            var_name) and var_name not in ['SELECT', 'INPUT', 'CLASS']:
                        added_vars.add(var_name)
                        desc = (info.get('description', '') or "").replace("'", "\'")
                        tag = info.get('tagName', '')
                        text = (info.get('text', '') or "").replace("'", "\'").strip()[:50]
                        escaped_selector = selector.replace("'", "\'")
                        selectors_class += f"    {var_name} = '{escaped_selector}' # Description: '{desc}', Tag: {tag}, Text: '{text}...\'\n"
                        generated_selectors_count += 1

        if generated_selectors_count == 0:
            selectors_class += "    # No unique CSS selectors found or processed.\n"
            selectors_class += "    # Add selectors manually, e.g.:\n"
            selectors_class += "    # SEARCH_INPUT = '#search-input'\n"
            # Use single quotes for the outer string to avoid conflict with inner double quotes
            selectors_class += '    # SUBMIT_BUTTON = \'//button[contains(text(), "Submit")]\' # Can use XPath too\n'

        print(f"Generated {generated_selectors_count} selector constants.")

        # Write to file
        try:
            with open(selectors_path, "w", encoding="utf-8") as f:
                f.write(selectors_class)
            print(f"Selectors class generated: {selectors_path}")
        except Exception as e:
            print(f"Error writing Selectors class file: {e}")

    def _generate_test_template(self):
        """Generate a Playwright test template in Python using pytest"""
        if not self.output_dir:
            print("Error: Output directory not set for test template.")
            return
        test_path = self.output_dir / "test_template.py"

        # Format domain name for class names
        base_name = (self.domain or "MyWebsite").title().replace('_', '').replace('-', '')
        page_class_name = base_name + 'Page'
        selectors_class_name = base_name + 'Selectors'
        test_class_name = 'Test' + base_name

        print(f"Generating Test Template: {test_class_name}...")

        # Use self.css_selectors populated earlier
        css_selectors = self.css_selectors

        test_template = f"""# Playwright test template for {self.url or 'the analyzed page'} using pytest
# Generated: {datetime.now().isoformat()}

import pytest
import re # For potential regex use in assertions
from playwright.sync_api import Page, expect

# --- Test Setup ---
# Ensure you have a 'page_object.py' and 'selectors.py' file
# generated in the same directory or adjust the import paths.
try:
    from .page_object import {page_class_name}
    from .selectors import {selectors_class_name}
except ImportError:
    # Fallback if running script directly
    try:
        from page_object import {page_class_name}
        from selectors import {selectors_class_name}
    except ImportError as e:
        print(f"Error importing Page Object or Selectors: {{e}}")
        print("Please ensure page_object.py and selectors.py are in the Python path.")
        # Define dummy classes to prevent immediate script failure if imports fail
        class {page_class_name}:
             def __init__(self, page): self.page = page; self.url = "{self.url or ''}"
             def navigate(self): print("Dummy navigate: Imports failed.")
             def is_loaded(self): print("Dummy is_loaded: Imports failed."); return False
        class {selectors_class_name}: pass # Empty class

# --- Pytest Fixture ---
# Creates an instance of the Page Object for each test function
@pytest.fixture(scope="function")
def page_object(page: Page) -> {page_class_name}:
    \"\"Fixture to initialize the Page Object for each test function.\"\"
    print("\\nInitializing Page Object for test...")
    po = {page_class_name}(page)
    yield po # Provide the instance to the test
    print("Test function finished.")

# --- Test Class ---
# Group related tests for the page
# Test function names should start with 'test_'
@pytest.mark.usefixtures("page_object") # Apply fixture to all methods in class
class {test_class_name}:
    \"\"Example test suite for {self.url or 'the analyzed page'}.\"\"

    def test_page_loads_successfully(self, page_object: {page_class_name}, page: Page):
        \"\"
        Test Case ID: TC-LOAD-001
        Description: Verify the page loads correctly and the title is as expected.
        \"\"
        print("\\n--- Test: Page Loads Successfully ---")
        page_object.navigate()
        assert page_object.is_loaded(timeout=20000), "Page failed basic load check (title missing or navigation failed)"

        # Example: More specific title check using stored title
        # Use double braces {{}} for variables that should be part of the generated code
        expected_title = "{{self.page_title or ''}}".replace("'", "\\'") # Use title extracted earlier
        if expected_title:
             print(f"Checking page title matches: '{{expected_title}}'...") # Fixed: Use double braces
             expect(page).to_have_title(expected_title, timeout=5000)
             print("Page title matches expected title.") # Fixed: This print is OK as it's within the generated code's logic
        else:
             print("Page title not extracted during analysis, skipping specific title check.")

        print("Test Passed: Page loaded successfully.")


    def test_example_interaction(self, page_object: {page_class_name}, page: Page):
        \"\"
        Test Case ID: TC-INTERACT-001
        Description: Perform a sample interaction using Page Object methods.
                     (Adapt this test to your specific scenario)
        \"\"
        print("\\n--- Test: Example Interaction ---")
        # Prerequisite: Page should load
        page_object.navigate()
        assert page_object.is_loaded(), "Prerequisite failed: Page did not load before interaction test"

        print("Starting example interactions (modify as needed)...")

        # --- Add example test steps below using page_object --- 
        # This logic needs to be in Python to determine which block to add
        # example_steps_added = False # Removed from template

        # Python logic to check for common patterns using self.locator_names
        example_steps_added_py = False
        has_login_related = any(name.startswith('login') or name.startswith('submit') or name.startswith('sign_in') for name in self.locator_names)
        has_username_related = any(name.startswith('username') or name.startswith('email') for name in self.locator_names)
        has_password_related = any(name.startswith('password') for name in self.locator_names)
        has_search_related = any(name.startswith('search') or name.startswith('query') for name in self.locator_names)

        if has_username_related and has_login_related:
            example_steps_added_py = True
        elif has_search_related:
            example_steps_added_py = True

        # Template still finds methods, but Python decides which block to add
        login_method = next((m for m in dir(page_object) if m.startswith('click_login')), None)
        username_method = next((m for m in dir(page_object) if m.startswith('fill_username')), None)
        search_method = next((m for m in dir(page_object) if m.startswith('fill_search')), None)
        submit_method = next((m for m in dir(page_object) if m.startswith('click_submit')), None)

        if username_method and login_method:
             print(f"Example: Using {{username_method}} and {{login_method}}...") 
             # getattr(page_object, username_method)("test_user")
             # getattr(page_object, login_method)()
             # example_steps_added = True # Removed from template
        elif search_method and submit_method:
             print(f"Example: Using {{search_method}} and {{submit_method}}...") 
             # getattr(page_object, search_method)("playwright test")
             # getattr(page_object, submit_method)()
             # example_steps_added = True # Removed from template
        elif search_method: # Just search if no submit found
             print(f"Example: Using {{search_method}}...") 
             # getattr(page_object, search_method)("example query")
             # example_steps_added = True # Removed from template
"""
        example_steps_added_py = False
        if not example_steps_added_py:
            test_template += """
        # --- Placeholder Steps --- 
        # No standard interaction patterns (login, search, submit) found in generated methods/locators.
        # Replace these placeholders with actual interactions based on your page.

        # Example: Find the first available 'fill' method and use it
        fill_method = next((m for m in dir(page_object) if m.startswith('fill_')), None)
        if fill_method:
            print(f"Example: Calling first fill method found: {{fill_method}}")
            # getattr(page_object, fill_method)("Sample Data") # Uncomment with caution

        # Example: Find the first available 'click' method and use it
        click_method = next((m for m in dir(page_object) if m.startswith('click_')), None)
        if click_method:
             print(f"Example: Calling first click method found: {{click_method}}")
             # getattr(page_object, click_method)() # Uncomment with caution

        # Example: Use a selector directly from the Selectors class if available
        if hasattr({selectors_class_name}, 'SOME_SELECTOR_NAME'): # Replace with actual generated name
             print("Example: Interacting using a selector constant...")
             # expect(page.locator({selectors_class_name}.SOME_SELECTOR_NAME)).to_be_visible()
             # page.locator({selectors_class_name}.SOME_SELECTOR_NAME).click()
        else:
             print(f"No example selector constant found in {selectors_class_name}. Add selectors or use page.locator directly.")

        print("Add your specific test steps and assertions here.")
        pytest.skip("Test skipped: Add specific interaction steps and assertions.") # Skip placeholder test
"""
        else:  # example_steps_added_py is True
            test_template += """
        # --- Verification --- 
        # Add assertions here to verify the outcome of the interactions.
        # Example: Check if the URL changed to an expected pattern
        # print("Verifying URL change after interaction...")
        # expect(page).to_have_url(re.compile(r"/expected-path"), timeout=10000)
        # print("URL changed as expected.")

        # Example: Check if a specific element is now visible
        # result_element_locator = getattr(page_object, 'search_results_container', None) # Example locator
        # if result_element_locator:
        #     print("Verifying results container visibility...")
        #     expect(result_element_locator).to_be_visible(timeout=10000)
        #     print("Results container is visible.")

        print("Add relevant assertions for your test case.")
        pass # Remove pass when adding real assertions

        print("Test Passed: Example interaction finished (verification depends on added assertions).")
"""

        test_template += f"""
    # --- Add More Test Functions ---
    # Follow the pattern: def test_feature_or_scenario(self, page_object, page): ...
    # Example:
    # def test_invalid_login_shows_error(self, page_object: {page_class_name}, page: Page):
    #     \"\"
    #     Test Case ID: TC-LOGIN-002
    #     Description: Verify error message is shown on invalid login attempt.
    #     \"\"
    #     print("\\n--- Test: Invalid Login Shows Error ---")
    #     page_object.navigate()
    #     assert page_object.is_loaded(), "Prerequisite failed: Page did not load"
    #
    #     # Assuming page object has methods like fill_username, fill_password, click_login
    #     username_method = next((m for m in dir(page_object) if m.startswith('fill_username')), None)
    #     password_method = next((m for m in dir(page_object) if m.startswith('fill_password')), None)
    #     login_method = next((m for m in dir(page_object) if m.startswith('click_login')), None)
    #     error_message_locator = getattr(page_object, 'error_message', None) # Assuming locator exists
    #
    #     if not (username_method and password_method and login_method and error_message_locator):
    #         pytest.skip("Skipping test: Required methods/locators for invalid login not found.")
    #
    #     getattr(page_object, username_method)("invalid_user")
    #     getattr(page_object, password_method)("wrong_password")
    #     getattr(page_object, login_method)()
    #
    #     print("Verifying error message...")
    #     expect(error_message_locator).to_be_visible(timeout=5000)
    #     expect(error_message_locator).to_contain_text("Invalid credentials") # Adjust expected error text
    #     print("Error message verified.")
    #
    #     print("Test Passed: Invalid login showed error message.")
    #

# --- How to Run ---
# 1. Make sure you have pytest and playwright installed:
#    pip install pytest pytest-playwright
# 2. Navigate to the directory containing this test file, page_object.py, and selectors.py
# 3. Run pytest from your terminal:
#    pytest {test_path.name}       (Run all tests)
#    pytest {test_path.name} -s    (Show print statements)
#    pytest {test_path.name} --headed (Run in non-headless mode)
#    pytest {test_path.name} -k test_page_loads_successfully (Run specific test)

"""

        # Write to file
        try:
            with open(test_path, "w", encoding="utf-8") as f:
                f.write(test_template)
            print(f"Playwright test template generated: {test_path}")
        except Exception as e:
            print(f"Error writing test template file: {e}")

    # --- Optional Output Generation Methods ---
    def export_csv(self):
        """Export combined element data to a single CSV file"""
        print("Exporting element data to CSV...")
        if not self.output_dir:
            print("Error: Output directory not set for CSV export.")
            return
        if not self.elements_data:
            print("Warning: No element data available for CSV export. Skipping.")
            return

        csv_path = self.output_dir / "all_elements.csv"
        print(f"Generating CSV file: {csv_path}...")

        header = [
            "Category", "Variable Name", "Tag", "Description", "Text Content",
            "Selector (CSS)", "Selector (XPath)", "Selector (A11y)",
            "Position (X)", "Position (Y)", "Size (Width)", "Size (Height)",
            "Is Visible", "All Attributes"
            # Add framework info headers if framework_data is populated
        ]

        rows_written = 0
        try:
            with open(csv_path, "w", newline='', encoding='utf-8-sig') as f:  # Use utf-8-sig for Excel compatibility
                writer = csv.writer(f)
                writer.writerow(header)

                # Write element data from all categories
                for category, elements in self.elements_data.items():
                    if isinstance(elements, list):
                        for element in elements:
                            if isinstance(element, dict):
                                selectors = element.get('selectors', {})
                                pos = element.get('position', {})
                                attrs = element.get('attributes', {})

                                # Prepare data for row
                                var_name = _clean_variable_name(element.get("description") or element.get(
                                    "name") or f"element_{element.get('tagName', 'tag')}_{abs(hash(selectors.get('css') or str(pos))) % 1000}")
                                row = [
                                    category,
                                    var_name,
                                    element.get('tagName', 'N/A'),
                                    element.get('description', ''),
                                    element.get('text', ''),
                                    selectors.get('css', 'N/A'),
                                    selectors.get('xpath', 'N/A'),
                                    selectors.get('accessibility', 'N/A'),
                                    pos.get('x', 'N/A'),
                                    pos.get('y', 'N/A'),
                                    pos.get('width', 'N/A'),
                                    pos.get('height', 'N/A'),
                                    element.get('isVisible', 'N/A'),
                                    json.dumps(attrs)  # Store all attributes as JSON string
                                ]
                                writer.writerow(row)
                                rows_written += 1

            print(f"CSV file generated successfully with {rows_written} rows: {csv_path}")
        except Exception as e:
            print(f"Error writing CSV file: {e}")
            traceback.print_exc()

    def generate_html_report(self):
        """Generate a basic HTML report summarizing the analysis"""
        print("Generating HTML report...")
        if not self.output_dir:
            print("Error: Output directory not set for HTML report.")
            return
        if not self.elements_data:
            print("Warning: No element data available for HTML report. Skipping.")
            return

        report_path = self.output_dir / "analysis_report.html"
        print(f"Generating HTML report: {report_path}...")

        total_elements = sum(len(v) for v in self.elements_data.values() if isinstance(v, list))

        # Basic HTML structure
        html = f"""<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Web Element Analysis Report - {self.domain or 'Analysis'}</title>
    <style>
        body {{ font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, Helvetica, Arial, sans-serif; margin: 20px; line-height: 1.6; }}
        h1, h2 {{ color: #333; border-bottom: 1px solid #eee; padding-bottom: 5px; }}
        table {{ border-collapse: collapse; width: 100%; margin-bottom: 20px; font-size: 0.9em; }}
        th, td {{ border: 1px solid #ddd; padding: 8px 10px; text-align: left; vertical-align: top; }}
        th {{ background-color: #f7f7f7; font-weight: bold; }}
        pre {{ background-color: #f0f0f0; padding: 10px; border: 1px solid #ccc; overflow-x: auto; font-size: 0.85em; white-space: pre-wrap; word-wrap: break-word; }}
        .element-details {{ margin-bottom: 15px; border: 1px solid #ccc; padding: 10px; background-color: #fdfdfd; border-radius: 4px; }}
        .element-name {{ font-weight: bold; color: #0056b3; font-size: 1.1em; margin-bottom: 5px; display: block; }}
        code {{ background-color: #e8e8e8; padding: 2px 4px; border-radius: 3px; font-family: Consolas, Monaco, 'Andale Mono', 'Ubuntu Mono', monospace; }}
        a {{ color: #0066cc; text-decoration: none; }}
        a:hover {{ text-decoration: underline; }}
        .category-title {{ font-size: 1.2em; margin-top: 20px; color: #555; }}
    </style>
</head>
<body>
    <h1>Web Element Analysis Report</h1>
    <p><strong>URL:</strong> <a href="{self.url or '#'}" target="_blank">{self.url or 'N/A'}</a></p>
    <p><strong>Analysis Timestamp:</strong> {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}</p>
    <p><strong>Page Title:</strong> {self.page_title or 'N/A'}</p>
    <p><strong>Total Unique Elements Processed:</strong> {total_elements}</p>
    <p>Links: <a href="enhanced_elements.json">Enhanced Elements JSON</a> | <a href="visual_element_map.html">Visual Map</a> | <a href="screenshot.png">Screenshot</a></p>

"""

        # Add details table for each category
        for category, elements in self.elements_data.items():
            if isinstance(elements, list) and elements:
                html += f'<h2 class="category-title">Category: {category.capitalize()} ({len(elements)} elements)</h2>\n'
                html += '<table>\n'
                html += '<thead><tr><th>Name</th><th>Tag</th><th>Text</th><th>Selector (CSS)</th><th>Position & Size</th><th>Attributes</th></tr></thead>\n'
                html += '<tbody>\n'
                for i, element in enumerate(elements):
                    if not isinstance(element, dict): continue
                    if i >= 20:  # Limit rows per category shown in report for brevity
                        html += f'<tr><td colspan="6"><i>... ({len(elements) - i} more elements not shown)</i></td></tr>\n'
                        break

                    name = _clean_variable_name(element.get("description") or element.get("name") or f"element_{i}")
                    tag = element.get('tagName', 'N/A')
                    text = (element.get('text', '') or '')[:100]
                    text += '...' if len(element.get('text', '') or '') > 100 else ''
                    css = element.get('selectors', {}).get('css', 'N/A')
                    pos = element.get('position', {})
                    pos_size = f"({pos.get('x', '?')},{pos.get('y', '?')}) - {pos.get('width', '?')}x{pos.get('height', '?')}"
                    attrs = json.dumps(element.get('attributes', {}), indent=None)  # Compact JSON for table

                    html += f'<tr><td><code>{name}</code></td><td>{tag}</td><td>{text}</td><td><code>{css}</code></td><td>{pos_size}</td><td><pre style="max-height: 5em; overflow-y: auto;">{attrs}</pre></td></tr>\n'
                html += '</tbody></table>\n'

        html += """
</body>
</html>
"""

        # Write to file
        try:
            with open(report_path, "w", encoding="utf-8") as f:
                f.write(html)
            print(f"HTML report generated successfully: {report_path}")
        except Exception as e:
            print(f"Error writing HTML report: {e}")
            traceback.print_exc()

    def generate_cucumber_steps(self):
        """Generate basic Cucumber/Behave step definitions"""
        print("Generating Cucumber/Behave steps...")
        if not self.output_dir:
            print("Error: Output directory not set for Cucumber steps.")
            return
        if not self.elements_data:
            print("Warning: No element data available for Cucumber steps. Skipping.")
            return

        steps_path = self.output_dir / "steps.py"
        print(f"Generating Cucumber steps file: {steps_path}...")

        # Get interactive elements for steps
        interactive_elements = self.elements_data.get("interactive", []) if isinstance(self.elements_data, dict) else []

        steps_code = (
            "# Basic Cucumber/Behave step definitions for {url}\n"
            "# Generated: {date}\n"
            "from behave import given, when, then\n"
            "from playwright.sync_api import expect, Page\n"
            "import re\n\n"
            "@given('I navigate to the page')\n"
            "def step_impl_navigate(context):\n"
            "    '''Navigate to the main URL'''\n"
            "    if not hasattr(context, 'page') or not isinstance(context.page, Page):\n"
            "        raise AttributeError('context.page is not initialized. Ensure Playwright Page is set in Behave environment.')\n"
            "    print('Navigating to: {url}')\n"
            "    context.page.goto('{url}', wait_until='load')\n"
            "    expect(context.page).to_have_title(re.compile(r'.+'))\n\n"
            "@then('the page title should contain \"{{expected_part}}\"')\n"
            "def step_impl_check_title(context, expected_part):\n"
            "    '''Verify the page title contains specific text'''\n"
            "    print(f'Checking if title contains: {{expected_part}}')\n"
            "    expect(context.page).to_have_title(re.compile(re.escape(expected_part), re.IGNORECASE))\n\n"
        ).format(
            url=self.url or 'about:blank',
            date=datetime.now().isoformat()
        )

        generated_steps_count = 0
        step_phrases = set()  # Avoid duplicate step phrases

        if isinstance(interactive_elements, list):
            for element in interactive_elements:
                if not isinstance(element, dict): continue
                selector = element.get("selectors", {}).get("css")
                if not selector:
                    selector = element.get("selectors", {}).get("xpath")

                potential_name = element.get("description") or element.get("name")
                if selector and potential_name and isinstance(potential_name, str):
                    # Create a user-friendly phrase for the step
                    clean_desc = re.sub(r'[^a-zA-Z0-9\s]', '', potential_name).strip()
                    if not clean_desc: continue

                    tag_name = element.get("tagName", "").lower()
                    attrs = element.get("attributes", {})
                    element_type = (attrs.get("type", "") or "").lower() if tag_name == "input" else ""
                    role = (attrs.get("role", "") or "").lower()
                    escaped_selector = selector.replace("'", "\\'")  # Escape for Python string

                    # Generate CLICK step for clickable elements
                    if tag_name in ["button", "a"] or role == "button" or role == "link" or (
                            tag_name == "input" and element_type in ["button", "submit", "reset", "image"]):
                        step_phrase = f'I click the "{clean_desc}"'
                        if step_phrase not in step_phrases:
                            steps_code += f"""
@when('{step_phrase}')
def step_impl_click_{_clean_variable_name(clean_desc)}(context):
    locator = context.page.locator('{escaped_selector}')
    print(f"Clicking: {clean_desc} using selector '{escaped_selector}'")
    expect(locator).to_be_enabled()
    locator.click()

"""
                            step_phrases.add(step_phrase)
                            generated_steps_count += 1

                    # Generate FILL step for input/textarea
                    elif tag_name == "input" and element_type not in ["button", "submit", "checkbox", "radio", "reset",
                                                                      "file", "image"] or tag_name == "textarea":
                        step_phrase = f'I fill the "{clean_desc}" with "{{{{text_value}}}}"'
                        step_signature = f'I fill the "{clean_desc}" with "{{{{text_value:.+}}}}"'  # Use regex capture
                        if step_phrase not in step_phrases:
                            steps_code += f"""
@when('{step_signature}')
def step_impl_fill_{_clean_variable_name(clean_desc)}(context, text_value):
    locator = context.page.locator('{escaped_selector}')
    print(f"Filling: {clean_desc} with '{{text_value}}' using selector '{escaped_selector}'")
    expect(locator).to_be_visible()
    locator.fill(text_value)

"""
                            step_phrases.add(step_phrase)
                            generated_steps_count += 1

                    # Generate SELECT step for dropdowns
                    elif tag_name == "select":
                        step_phrase = f'I select "{{{{option_text}}}}" from the "{clean_desc}" dropdown'
                        step_signature = f'I select "{{{{option_text:.+}}}}" from the "{clean_desc}" dropdown'
                        if step_phrase not in step_phrases:
                            steps_code += f"""
@when('{step_signature}')
def step_impl_select_{_clean_variable_name(clean_desc)}(context, option_text):
    locator = context.page.locator('{escaped_selector}')
    print(f"Selecting: '{{option_text}}' in {clean_desc} using selector '{escaped_selector}'")
    expect(locator).to_be_visible()
    locator.select_option(label=option_text)

"""
                            step_phrases.add(step_phrase)
                            generated_steps_count += 1

                    # Generate VERIFY VISIBLE step
                    verify_step_phrase = f'I should see the "{clean_desc}"'
                    if verify_step_phrase not in step_phrases:
                        steps_code += f"""
@then('{verify_step_phrase}')
def step_impl_verify_{_clean_variable_name(clean_desc)}_visible(context):
    locator = context.page.locator('{escaped_selector}')
    print(f"Verifying visible: {clean_desc} using selector '{escaped_selector}'")
    expect(locator).to_be_visible()

"""
                        step_phrases.add(verify_step_phrase)
                        generated_steps_count += 1

        if generated_steps_count == 0:
            steps_code += "# No interactive elements found to generate specific steps.\n"

        print(f"Generated {generated_steps_count} Cucumber/Behave steps.")

        # Write to file
        try:
            with open(steps_path, "w", encoding="utf-8") as f:
                f.write(steps_code)
            print(f"Cucumber steps file generated: {steps_path}")
        except Exception as e:
            print(f"Error writing Cucumber steps file: {e}")
            traceback.print_exc()

    # --- README Generation ---
    def _create_readme(self):
        """Create a README file summarizing the analysis and generated files"""
        print("Generating README file...")
        if not self.output_dir:
            print("Error: Output directory not set for README.")
            return

        readme_path = self.output_dir / "README.md"

        # Generate element counts
        element_counts_list = []
        total_elements = 0
        if isinstance(self.elements_data, dict):
            for category, elements in self.elements_data.items():
                if isinstance(elements, list):
                    count = len(elements)
                    element_counts_list.append(f"- `{category}`: {count}")
                    total_elements += count
        element_counts = "\n".join(
            element_counts_list) if element_counts_list else "*No element data available or loaded.*"

        # Check which optional files were actually generated
        csv_exists = (self.output_dir / "all_elements.csv").exists()
        cucumber_exists = (self.output_dir / "steps.py").exists()
        report_exists = (self.output_dir / "analysis_report.html").exists()
        visual_map_exists = (self.output_dir / "visual_element_map.html").exists()
        # framework_exists = (self.output_dir / "framework_data.json").exists() and os.path.getsize(self.output_dir / "framework_data.json") > 2

        # Get current timestamp for the README
        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        
        # README template
        readme_content = f"""# Playwright Web Element Analysis - {self.url or 'Unknown URL'} ({timestamp})

## Overview
This directory contains the results of a web element analysis performed on `{self.url or 'the analyzed page'}`.
The analysis was generated on {timestamp} using the Integrated Web Element Analyzer tool.

## URL Information
- **Analyzed URL**: `{self.url or 'N/A'}`
- **Domain**: `{self.domain or 'N/A'}`
- **Page Title**: `{self.page_title or 'N/A'}`

## Element Statistics
Total unique elements processed: {total_elements}

Element categories:
{element_counts}

## Generated Files
This directory contains the following files:

### Core Analysis Files
- `enhanced_elements.json`: Detailed JSON with all elements and their properties.
- `metadata.json`: Page metadata (title, scripts, stylesheets, etc.).
- `full_page.html`: Saved HTML content of the page.
- `screenshot.png`: Full page screenshot (or viewport if full failed).
- `css_selectors.json`: Map of unique CSS selectors to element info.
- `xpath_selectors.json`: Map of unique XPath selectors to element info.
- `a11y_selectors.json`: Map of unique accessibility selectors to element info.
- `interactive.json`, `content.json`, etc.: Elements grouped by category.

### Playwright Helper Files
- `page_object.py`: Playwright Page Object Model with locators and interaction methods.
- `selectors.py`: Python class containing CSS selectors as constants.
- `test_template.py`: Example pytest test file using the Page Object and Selectors.

### Additional Optional Files
{f"- `all_elements.csv`: CSV export of all elements and properties." if csv_exists else "- `all_elements.csv`: *Not generated (use --csv or --all)*"}
{f"- `analysis_report.html`: Visual HTML report summarizing the analysis." if report_exists else "- `analysis_report.html`: *Not generated (use --html or --all)*"}
{f"- `steps.py`: Cucumber/Behave step definitions based on interactive elements." if cucumber_exists else "- `steps.py`: *Not generated (use --cucumber or --all)*"}
{f"- `visual_element_map.html`: Interactive HTML map overlaying screenshot." if visual_map_exists else "- `visual_element_map.html`: *Generation failed or skipped*"}
{f"- `framework_data.json`: Framework detection results." if False else "- `framework_data.json`: *Not generated (framework detection not implemented)*"}

## How to Use

1.  **Explore Visually**: Open `visual_element_map.html` in your browser to interactively see elements overlaid on the screenshot.
2.  **Review Data**: Examine `enhanced_elements.json` for the raw detailed data on all elements.
3.  **Use for Automation**: 
    *   Integrate the `page_object.py` and `selectors.py` files into your Playwright test framework.
    *   Use `test_template.py` as a starting point for writing tests using `pytest`.
    *   Refer to `all_elements.csv` for a tabular overview or quick reference.
    *   Use `steps.py` if you are using Behave for BDD testing.

## Running the Example Tests
```bash
# Ensure you have the necessary libraries installed
pip install pytest pytest-playwright behave

# Navigate to this directory
cd {self.output_dir.name}

# Run the pytest example tests
pytest test_template.py -s --headed

# (Optional) If using Behave, create a features/ directory and a .feature file,
# then run behave (requires environment.py setup for context.page)
# behave features/
```

## Notes
- The selectors and Page Object Model are auto-generated and might require review and refinement based on the specific application and test needs.
- Dynamic elements loaded after the initial page load might not be fully captured.
- Complex CSS/XPath selectors might be generated; consider simplifying them for robustness.

"""

        # Write to file
        try:
            with open(readme_path, "w", encoding="utf-8") as f:
                f.write(readme_content)
            print(f"README file generated: {readme_path}")
        except Exception as e:
            print(f"Error writing README file: {e}")
            traceback.print_exc()

    def _save_run_info(self):
        """Save run information for MCP to find the results"""
        try:
            # בדיקה שיש תיקיית פלט
            if not self.output_dir:
                print("Warning: No output directory set, cannot save run info for MCP")
                return

            # מחשב את הנתיב של MCP
            script_dir = Path(__file__).parent
            mcp_dir = script_dir / "mcp"
            mcp_dir.mkdir(exist_ok=True)

            run_info_path = mcp_dir / "run_info.json"

            # מכין את המידע על הריצה
            run_info = {
                "timestamp": datetime.now().isoformat(),
                "output_dir": str(self.output_dir.absolute()),
                "url": self.url,
                "domain": self.domain,
                "page_title": self.page_title,
                "urls": [self.url] if self.url else [],
                "dates": [datetime.now().strftime("%Y/%m/%d")],
                "analysis_type": "single_page"
            }

            # שומר את המידע
            with open(run_info_path, "w", encoding="utf-8") as f:
                json.dump(run_info, f, indent=2)

            print(f"Run info saved for MCP: {run_info_path}")

        except Exception as e:
            print(f"Warning: Could not save run info for MCP: {e}")

    def _generate_ai_summary_for_single_page(self):
        """Generate AI summary for single page analysis"""
        try:
            if not self.output_dir:
                print("Warning: No output directory set for AI summary")
                return

            # Create summary directory
            summary_dir = self.output_dir / "ai_summary"
            summary_dir.mkdir(exist_ok=True)

            # Call the main AI summary function
            _generate_ai_summary(
                raw_dir=str(self.output_dir),
                analysis_dir=str(self.output_dir),
                summary_dir=str(summary_dir)
            )

            print(f"✅ AI Summary generated: {summary_dir}")

        except Exception as e:
            print(f"⚠️ Error generating AI summary: {e}")

    @staticmethod
    def _create_fallback_summary(page_title: str, element_stats: Dict, element_insights: List, metadata: Dict) -> str:
        """Create intelligent fallback summary when AI is not available"""
        total_elements = element_stats.get('total', 0)
        interactive_count = element_stats.get('interactive', 0)
        forms_count = element_stats.get('forms', 0)

        summary_parts = []

        # Page purpose analysis
        if "login" in page_title.lower():
            summary_parts.append("This appears to be a login/authentication page")
        elif "home" in page_title.lower() or "main" in page_title.lower():
            summary_parts.append("This is the main homepage or landing page")
        elif "search" in page_title.lower():
            summary_parts.append("This is a search-focused page")
        else:
            summary_parts.append(f"Analysis of '{page_title}' page")

        # Element analysis
        if total_elements > 100:
            summary_parts.append(f"containing {total_elements} elements indicating a complex interface")
        elif total_elements > 50:
            summary_parts.append(f"with {total_elements} elements showing moderate complexity")
        else:
            summary_parts.append(f"featuring {total_elements} elements in a streamlined design")

        # Interactive features
        if interactive_count > 10:
            summary_parts.append(f"The page offers rich interactivity with {interactive_count} interactive elements")
        elif interactive_count > 0:
            summary_parts.append(f"It includes {interactive_count} interactive components")

        # Forms analysis
        if forms_count > 0:
            summary_parts.append(f"and contains {forms_count} form(s) for user input")

        # Technical assessment
        scripts_count = len(metadata.get('scripts', []))
        if scripts_count > 5:
            summary_parts.append(f"The page uses {scripts_count} scripts suggesting dynamic functionality")

        return ". ".join(summary_parts) + "."

    @staticmethod
    def _extract_topics(content: str) -> List[str]:
        """Extract main topics from page content"""
        if not content or len(content) < 50:
            return []

        # Simple keyword extraction (in a real implementation, you might use NLP)
        common_words = {
            'the', 'and', 'or', 'but', 'in', 'on', 'at', 'to', 'for', 'of', 'with', 'by', 'from',
            'up', 'about', 'into', 'through', 'during', 'before', 'after', 'above', 'below',
            'this', 'that', 'these', 'those', 'a', 'an', 'is', 'are', 'was', 'were', 'be',
            'been', 'being', 'have', 'has', 'had', 'do', 'does', 'did', 'will', 'would',
            'could', 'should', 'may', 'might', 'must', 'can', 'your', 'you', 'we', 'our', 'us'
        }

        words = re.findall(r'\b[a-zA-Z]{3,}\b', content.lower())
        word_freq = {}

        for word in words:
            if word not in common_words:
                word_freq[word] = word_freq.get(word, 0) + 1

        # Get top topics
        top_words = sorted(word_freq.items(), key=lambda x: x[1], reverse=True)[:8]
        return [word for word, freq in top_words if freq > 2]


def extract_links(page_url, html_content):
    """Extract links from HTML content and normalize them"""
    # Use simple regex to extract links from href attributes
    # In a real implementation, you might want to use a proper HTML parser
    links = []
    href_pattern = re.compile(r'href=[\'"]?([^\'" >]+)')
    matches = href_pattern.finditer(html_content)

    # Keep track of unique links to avoid duplicates
    unique_links = set()

    for match in matches:
        link = match.group(1)

        # Skip fragment-only links, javascript, mailto, etc.
        if (not link) or link.startswith('#') or link.startswith('javascript:') or link.startswith('mailto:'):
            continue

        # Skip print links and other common navigation actions
        if link.startswith('print=') or '/print/' in link or 'javascript:void(0)' in link:
            continue

        # Normalize the URL (handle relative URLs)
        normalized_url = urljoin(page_url, link)

        # Remove fragments
        normalized_url = normalized_url.split('#')[0]

        # Skip data URLs and other non-HTTP/HTTPS protocols
        if not normalized_url.startswith(('http://', 'https://')):
            continue

        # Skip duplicates
        if normalized_url in unique_links:
            continue

        unique_links.add(normalized_url)
        links.append(normalized_url)

    # For debugging, print the number of links found
    print(f"Found {len(links)} unique links on page: {page_url}")
    return links


def _get_page_content(result_dir):
    """Get the HTML content of a page from the saved results"""
    # Try to find the full HTML file in the result directory
    for root, dirs, files in os.walk(result_dir):
        for file in files:
            if file == "full_page.html":
                html_file_path = os.path.join(root, file)
                try:
                    with open(html_file_path, 'r', encoding='utf-8') as f:
                        return f.read()
                except Exception as e:
                    print(f"Error reading HTML file {html_file_path}: {e}")
    return None


def _update_progress(progress_file, message):
    """Update progress file with timestamp and message"""
    try:
        with open(progress_file, 'a', encoding='utf-8') as f:
            timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            f.write(f"[{timestamp}] {message}\n")
    except Exception as e:
        print(f"Failed to write progress: {e}")


def _process_raw_data(raw_dir, analysis_dir):
    """Process raw data to create enriched analysis"""
    try:
        # Copy metadata.json if it exists
        metadata_file = os.path.join(raw_dir, "metadata.json")
        if os.path.exists(metadata_file):
            # Read the metadata
            with open(metadata_file, "r", encoding="utf-8") as f:
                metadata = json.load(f)

            # Create an enriched version with additional analysis
            enriched_metadata = {
                "original_metadata": metadata,
                "analysis_timestamp": datetime.now().isoformat(),
                "page_structure_analysis": {
                    "has_header": False,
                    "has_footer": False,
                    "has_navigation": False,
                    "has_forms": False,
                    "has_images": False,
                    "has_tables": False
                }
            }

            # Check for various elements in the raw data
            html_file = os.path.join(raw_dir, "full_page.html")
            if os.path.exists(html_file):
                with open(html_file, "r", encoding="utf-8") as f:
                    html_content = f.read()

                    # Simple heuristic checks
                    enriched_metadata["page_structure_analysis"]["has_header"] = "<header" in html_content.lower()
                    enriched_metadata["page_structure_analysis"]["has_footer"] = "<footer" in html_content.lower()
                    enriched_metadata["page_structure_analysis"]["has_navigation"] = "<nav" in html_content.lower()
                    enriched_metadata["page_structure_analysis"]["has_forms"] = "<form" in html_content.lower()
                    enriched_metadata["page_structure_analysis"]["has_images"] = "<img" in html_content.lower()
                    enriched_metadata["page_structure_analysis"]["has_tables"] = "<table" in html_content.lower()

            # Save the enriched metadata
            with open(os.path.join(analysis_dir, "enriched_metadata.json"), "w", encoding="utf-8") as f:
                json.dump(enriched_metadata, f, indent=2)

    except Exception as e:
        print(f"Error processing raw data: {e}")


def _generate_ai_summary(raw_dir, analysis_dir, summary_dir):
    """Generate an AI summary of the webpage content using comprehensive data analysis"""
    try:
        print("🤖 Starting AI-powered analysis of webpage data...")

        # Try to import AI libraries
        has_ai_support = False
        ai_client = None
        ai_provider = None

        # Check for Anthropic Claude API
        anthropic_api_key = os.environ.get("ANTHROPIC_API_KEY")
        claude_key_path = os.path.join(os.path.dirname(__file__), "anthropic_key.txt")
        if not anthropic_api_key and os.path.exists(claude_key_path):
            with open(claude_key_path, "r", encoding="utf-8") as f:
                anthropic_api_key = f.read().strip()

        if anthropic_api_key:
            try:
                import anthropic
                ai_client = anthropic.Anthropic(api_key=anthropic_api_key)
                ai_provider = "claude"
                has_ai_support = True
                print("✅ Using Claude AI for advanced summary generation.")
            except ImportError:
                print("⚠️ Anthropic library not available. Trying OpenAI...")

        # Check for OpenAI if Claude not available
        if not has_ai_support:
            openai_api_key = os.environ.get("OPENAI_API_KEY")
            key_path = os.path.join(os.path.dirname(__file__), "openai_key.txt")
            if not openai_api_key and os.path.exists(key_path):
                with open(key_path, "r", encoding="utf-8") as f:
                    openai_api_key = f.read().strip()

            if openai_api_key:
                try:
                    import openai
                    ai_client = openai.OpenAI(api_key=openai_api_key)
                    ai_provider = "openai"
                    has_ai_support = True
                    print("✅ Using OpenAI for advanced summary generation.")
                except ImportError:
                    print("⚠️ OpenAI library not available. Using fallback summary.")

        # Comprehensive data extraction from all raw_data files
        print("📊 Extracting comprehensive data from raw_data...")

        metadata_file = os.path.join(raw_dir, "metadata.json")
        html_file = os.path.join(raw_dir, "full_page.html")
        enhanced_elements_file = os.path.join(raw_dir, "enhanced_elements.json")
        css_selectors_file = os.path.join(raw_dir, "css_selectors.json")
        interactive_file = os.path.join(raw_dir, "interactive.json")
        content_file = os.path.join(raw_dir, "content.json")
        forms_file = os.path.join(raw_dir, "forms.json")

        # Initialize data containers
        page_title = "Unknown Page"
        page_content = ""
        page_url = ""
        metadata = {}
        elements_data = {}
        css_selectors = {}

        # Load metadata
        if os.path.exists(metadata_file):
            with open(metadata_file, "r", encoding="utf-8") as f:
                metadata = json.load(f)
                if isinstance(metadata, dict):
                    page_title = metadata.get("title", "Unknown Page")
                    page_url = metadata.get("url", "")
                    print(f"📄 Loaded metadata: {page_title}")

        # Extract clean page content
        if os.path.exists(html_file):
            with open(html_file, "r", encoding="utf-8") as f:
                html_content = f.read()
                try:
                    from bs4 import BeautifulSoup
                    soup = BeautifulSoup(html_content, "html.parser")

                    # Remove scripts, styles, and other non-content elements
                    for element in soup(["script", "style", "nav", "header", "footer", "aside"]):
                        element.decompose()

                    # Get main content
                    main_content = soup.find("main") or soup.find("article") or soup.body or soup
                    page_content = main_content.get_text(separator=" ", strip=True)
                    print(f"📝 Extracted {len(page_content)} characters of content")

                except Exception as e:
                    # Fallback: simple regex cleaning
                    page_content = re.sub(r'<[^>]+>', ' ', html_content)
                    page_content = re.sub(r'\s+', ' ', page_content).strip()
                    print(f"📝 Extracted content using fallback method: {len(page_content)} characters")

        # Load comprehensive element analysis data
        element_insights = []
        element_stats = {"interactive": 0, "content": 0, "forms": 0, "structural": 0, "total": 0}

        # Load enhanced elements (main analysis file)
        if os.path.exists(enhanced_elements_file):
            try:
                with open(enhanced_elements_file, "r", encoding="utf-8") as f:
                    elements_data = json.load(f)

                    # Handle different data structures
                    if isinstance(elements_data, dict):
                        # Count elements by category
                        for category, elements in elements_data.items():
                            if isinstance(elements, list):
                                count = len(elements)
                                element_stats[category] = count
                                element_stats["total"] += count

                                # Extract insights from top elements
                                for element in elements[:5]:  # Top 5 per category
                                    if isinstance(element, dict) and element.get("description"):
                                        element_insights.append({
                                            "category": category,
                                            "description": element.get("description", ""),
                                            "tag": element.get("tagName", ""),
                                            "text": element.get("text", "")[:100]
                                        })

                    print(f"🔍 Analyzed {element_stats['total']} total elements:")
                    for category, count in element_stats.items():
                        if category != "total" and count > 0:
                            print(f"   - {category}: {count}")

            except Exception as e:
                print(f"⚠️ Error loading enhanced elements: {e}")

        # Load CSS selectors for technical insights
        if os.path.exists(css_selectors_file):
            try:
                with open(css_selectors_file, "r", encoding="utf-8") as f:
                    css_selectors = json.load(f)
                    print(f"🎨 Loaded {len(css_selectors)} CSS selectors")
            except Exception as e:
                print(f"⚠️ Error loading CSS selectors: {e}")

        # Additional files analysis
        additional_data = {}
        for file_name, file_path in [
            ("interactive", interactive_file),
            ("content", content_file),
            ("forms", forms_file)
        ]:
            if os.path.exists(file_path):
                try:
                    with open(file_path, "r", encoding="utf-8") as f:
                        data = json.load(f)
                        additional_data[file_name] = data
                        if isinstance(data, list):
                            print(f"📁 Loaded {len(data)} {file_name} elements")
                except Exception as e:
                    print(f"⚠️ Error loading {file_name} data: {e}")

        # Generate comprehensive AI summary if available
        ai_summary = None
        if has_ai_support and ai_client:
            try:
                print("🤖 Generating AI-powered comprehensive analysis...")

                # Prepare comprehensive content for AI analysis
                analysis_content = page_content[:2000] if len(page_content) > 2000 else page_content

                # Create detailed analysis prompt with all collected data
                prompt = f"""
As a QA Automation Architect, analyze this webpage comprehensively based on the following data:

## PAGE INFORMATION
Title: {page_title}
URL: {page_url}

## CONTENT ANALYSIS  
Main Content ({len(page_content)} chars): {analysis_content}

## ELEMENT ANALYSIS SUMMARY
Total Elements Analyzed: {element_stats.get('total', 0)}
- Interactive Elements: {element_stats.get('interactive', 0)}
- Content Elements: {element_stats.get('content', 0)}
- Forms: {element_stats.get('forms', 0)}
- Structural Elements: {element_stats.get('structural', 0)}

## KEY INSIGHTS FROM ELEMENTS
{json.dumps(element_insights[:10], indent=2) if element_insights else "No element insights available"}

## TECHNICAL DETAILS
CSS Selectors Found: {len(css_selectors)}
Scripts Detected: {len(metadata.get('scripts', []))}
Stylesheets: {len(metadata.get('stylesheets', []))}

## ADDITIONAL ELEMENT DATA
{json.dumps({k: len(v) if isinstance(v, list) else "N/A" for k, v in additional_data.items()}, indent=2) if additional_data else "No additional data"}

Please provide a comprehensive QA analysis including:

1. **Page Purpose & Functionality**: What is this page designed to do?
2. **User Experience Assessment**: How user-friendly is the interface?
3. **Technical Architecture**: What technologies and patterns are used?
4. **Testing Recommendations**: What QA testing strategies would be most effective?
5. **Automation Opportunities**: Which elements are best suited for automated testing?
6. **Potential Issues**: Any UX or technical concerns identified?

Focus on actionable insights for QA automation and testing strategy.
"""

                # Call appropriate AI service
                if ai_provider == "claude":
                    # ודא ש-ai_client הוא Anthropic
                    response = ai_client.messages.create(
                        model="claude-sonnet-4-20250514",
                        max_tokens=20000,
                        temperature=1,
                        messages=[{"role": "user", "content": prompt}]
                    )
                    ai_summary = response.content[0].text
                elif ai_provider == "openai":
                    # ודא ש-ai_client הוא openai.OpenAI
                    response = ai_client.chat.completions.create(
                        model="gpt-3.5-turbo",
                        messages=[{"role": "user", "content": prompt}],
                        max_tokens=800
                    )
                    ai_summary = response.choices[0].message.content

                print("✅ Comprehensive AI analysis generated successfully")

            except Exception as e:
                print(f"⚠️ AI analysis generation failed: {e}")
                print(f"   Provider: {ai_provider}, Error: {str(e)[:200]}...")
                ai_summary = None

        # Create comprehensive summary object with all collected data
        summary = {
            "page_title": page_title,
            "page_url": page_url,
            "generation_time": datetime.now().isoformat(),
            "ai_powered": has_ai_support and ai_summary is not None,
            "ai_provider": ai_provider if has_ai_support and ai_summary else None,
            "summary": ai_summary if ai_summary else f"Comprehensive analysis of '{page_title}' revealing {element_stats.get('total', 0)} total elements including {element_stats.get('interactive', 0)} interactive components, {element_stats.get('content', 0)} content elements, and {element_stats.get('forms', 0)} forms. The page structure indicates {'high' if element_stats.get('total', 0) > 100 else 'moderate' if element_stats.get('total', 0) > 50 else 'simple'} complexity with comprehensive functionality for user interaction.",
            "comprehensive_analysis": {
                "total_data_sources": len(
                    [f for f in [metadata_file, html_file, enhanced_elements_file, css_selectors_file] if
                     os.path.exists(f)]),
                "content_analysis": {
                    "content_length": len(page_content),
                    "word_count": len(page_content.split()) if page_content else 0,
                    "main_topics": []
                },
                "technical_analysis": {
                    "total_css_selectors": len(css_selectors),
                    "scripts_count": len(metadata.get('scripts', [])),
                    "stylesheets_count": len(metadata.get('stylesheets', [])),
                    "meta_tags_count": len(metadata.get('metaTags', []))
                },
                "element_categories": element_stats
            },
            "key_elements": element_insights[:8],  # Top 8 elements
            "page_stats": {
                "content_length": len(page_content) if page_content else 0,
                "elements_analyzed": element_stats.get('total', 0),
                "has_forms": element_stats.get('forms', 0) > 0,
                "has_navigation": any(
                    e.get("category") == "navigation" for e in element_insights) if element_insights else False,
                "interactive_elements": element_stats.get('interactive', 0),
                "content_elements": element_stats.get('content', 0),
                "structural_elements": element_stats.get('structural', 0)
            },
            "raw_data_summary": {
                "files_processed": {
                    "metadata": os.path.exists(metadata_file),
                    "html_content": os.path.exists(html_file),
                    "enhanced_elements": os.path.exists(enhanced_elements_file),
                    "css_selectors": os.path.exists(css_selectors_file),
                    "interactive_elements": os.path.exists(interactive_file),
                    "content_elements": os.path.exists(content_file),
                    "forms": os.path.exists(forms_file)
                },
                "data_completeness": round(
                    len([f for f in [metadata_file, html_file, enhanced_elements_file] if os.path.exists(f)]) / 3 * 100,
                    1)
            }
        }
        elements_files = glob.glob(os.path.join(raw_dir, "*.json"))
        for file in elements_files:
            if os.path.basename(file) not in ["metadata.json"]:
                try:
                    with open(file, "r", encoding="utf-8") as f:
                        elements_data = json.load(f)
                        if isinstance(elements_data, list):
                            for element in elements_data[:5]:
                                if isinstance(element, dict) and "description" in element and element["description"]:
                                    summary["key_elements"].append({
                                        "type": os.path.basename(file).replace(".json", ""),
                                        "description": element["description"]
                                    })
                except Exception as e:
                    print(f"Error processing elements file {file}: {e}")
        with open(os.path.join(summary_dir, "ai_summary.json"), "w", encoding="utf-8") as f:
            json.dump(summary, f, indent=2)
        # Generate enhanced HTML report with comprehensive data
        with open(os.path.join(summary_dir, "summary.html"), "w", encoding="utf-8") as f:
            ai_badge = f"🤖 AI-Powered ({summary.get('ai_provider', 'Unknown').title()})" if summary[
                "ai_powered"] else "📊 Intelligent Analysis"
            comprehensive = summary.get("comprehensive_analysis", {})
            raw_data_summary = summary.get("raw_data_summary", {})

            f.write(f"""<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Comprehensive AI Analysis: {page_title}</title>
    <style>
        body {{ 
            font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif; 
            margin: 0; 
            padding: 20px; 
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            min-height: 100vh;
        }}
        .container {{
            max-width: 1200px;
            margin: 0 auto;
            background: white;
            border-radius: 12px;
            box-shadow: 0 10px 30px rgba(0,0,0,0.2);
            overflow: hidden;
        }}
        .header {{
            background: linear-gradient(135deg, #2c3e50, #34495e);
            color: white;
            padding: 30px;
            text-align: center;
        }}
        .header h1 {{ 
            margin: 0; 
            font-size: 2.4em; 
            font-weight: 300;
        }}
        .ai-badge {{
            display: inline-block;
            background: {('#27ae60' if summary["ai_powered"] else '#f39c12')};
            color: white;
            padding: 8px 18px;
            border-radius: 25px;
            font-size: 0.9em;
            margin-top: 15px;
            font-weight: 600;
            box-shadow: 0 2px 10px rgba(0,0,0,0.2);
        }}
        .content {{
            padding: 30px;
        }}
        .summary-section {{ 
            background: #f8f9fa; 
            padding: 25px; 
            border-radius: 12px; 
            margin-bottom: 30px;
            border-left: 5px solid #3498db;
            box-shadow: 0 2px 10px rgba(0,0,0,0.1);
        }}
        .summary-section h2 {{
            color: #2c3e50;
            margin-top: 0;
            font-size: 1.6em;
            display: flex;
            align-items: center;
            gap: 10px;
        }}
        .summary-text {{
            line-height: 1.8;
            font-size: 1.1em;
            color: #34495e;
            white-space: pre-line;
        }}
        .stats-grid {{
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(200px, 1fr));
            gap: 20px;
            margin: 30px 0;
        }}
        .stat-card {{
            background: linear-gradient(145deg, #f1f3f4, #e8eaed);
            padding: 20px;
            border-radius: 12px;
            text-align: center;
            border: 1px solid #dadce0;
            transition: all 0.3s ease;
        }}
        .stat-card:hover {{
            transform: translateY(-5px);
            box-shadow: 0 10px 25px rgba(0,0,0,0.15);
        }}
        .stat-number {{
            font-size: 2.2em;
            font-weight: bold;
            color: #3498db;
            display: block;
        }}
        .stat-label {{
            color: #5f6368;
            font-size: 0.9em;
            margin-top: 8px;
            font-weight: 500;
        }}
        .comprehensive-grid {{
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(300px, 1fr));
            gap: 25px;
            margin: 30px 0;
        }}
        .analysis-section {{
            background: white;
            border: 1px solid #e1e8ed;
            border-radius: 12px;
            padding: 20px;
            box-shadow: 0 2px 8px rgba(0,0,0,0.1);
        }}
        .analysis-section h3 {{
            margin-top: 0;
            color: #2c3e50;
            font-size: 1.3em;
            display: flex;
            align-items: center;
            gap: 8px;
        }}
        .key-elements {{
            margin-top: 30px;
        }}
        .key-element {{ 
            background: white;
            border: 1px solid #e1e8ed;
            border-radius: 10px;
            padding: 18px; 
            margin: 12px 0;
            border-left: 5px solid #e74c3c;
            transition: all 0.3s ease;
        }}
        .key-element:hover {{
            box-shadow: 0 8px 20px rgba(0,0,0,0.15);
            transform: translateY(-3px);
        }}
        .element-category {{
            background: #3498db;
            color: white;
            padding: 4px 12px;
            border-radius: 15px;
            font-size: 0.8em;
            font-weight: 600;
            text-transform: uppercase;
        }}
        .element-description {{
            margin-top: 10px;
            color: #2c3e50;
            line-height: 1.5;
        }}
        .element-tag {{
            background: #ecf0f1;
            color: #7f8c8d;
            padding: 2px 8px;
            border-radius: 10px;
            font-size: 0.8em;
            margin-left: 10px;
        }}
        .data-sources {{
            background: #e8f5e8;
            padding: 15px;
            border-radius: 8px;
            margin: 20px 0;
        }}
        .data-sources h4 {{
            margin-top: 0;
            color: #27ae60;
        }}
        .source-list {{
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(200px, 1fr));
            gap: 10px;
        }}
        .source-item {{
            display: flex;
            align-items: center;
            gap: 8px;
            font-size: 0.9em;
        }}
        .source-status {{
            width: 12px;
            height: 12px;
            border-radius: 50%;
        }}
        .status-success {{ background: #27ae60; }}
        .status-missing {{ background: #e74c3c; }}
        .generation-info {{
            background: #34495e;
            color: white;
            padding: 20px;
            text-align: center;
            font-size: 0.9em;
        }}
        .url-info {{
            background: #ecf0f1;
            padding: 15px 20px;
            border-radius: 8px;
            margin: 20px 0;
            font-family: monospace;
            color: #2c3e50;
            word-break: break-all;
            border-left: 4px solid #3498db;
        }}
        .completeness-bar {{
            width: 100%;
            height: 20px;
            background: #ecf0f1;
            border-radius: 10px;
            overflow: hidden;
            margin: 10px 0;
        }}
        .completeness-fill {{
            height: 100%;
            background: linear-gradient(90deg, #27ae60, #2ecc71);
            transition: width 0.5s ease;
        }}
    </style>
</head>
<body>
    <div class="container">
        <div class="header">
            <h1>🔍 Comprehensive Webpage Analysis</h1>
            <div class="ai-badge">{ai_badge}</div>
            <h2 style="margin: 15px 0 0 0; font-weight: 300; font-size: 1.3em;">{page_title}</h2>
        </div>

        <div class="content">
            <div class="url-info">
                <strong>🌐 Analyzed URL:</strong> {summary["page_url"] or "N/A"}
            </div>

            <div class="data-sources">
                <h4>📊 Data Sources Processed ({raw_data_summary.get('data_completeness', 0)}% Complete)</h4>
                <div class="completeness-bar">
                    <div class="completeness-fill" style="width: {raw_data_summary.get('data_completeness', 0)}%"></div>
                </div>
                <div class="source-list">""")

            # Add data sources status
            sources = raw_data_summary.get('files_processed', {})
            source_names = {
                'metadata': '📄 Page Metadata',
                'html_content': '🌐 HTML Content',
                'enhanced_elements': '🔍 Element Analysis',
                'css_selectors': '🎨 CSS Selectors',
                'interactive_elements': '⚡ Interactive Elements',
                'content_elements': '📝 Content Elements',
                'forms': '📋 Forms Data'
            }

            for key, name in source_names.items():
                status = sources.get(key, False)
                status_class = 'status-success' if status else 'status-missing'
                f.write(f"""
                    <div class="source-item">
                        <div class="source-status {status_class}"></div>
                        <span>{name}</span>
                    </div>""")

            f.write(f"""
                </div>
            </div>

            <div class="summary-section">
                <h2>🤖 AI Analysis Summary</h2>
                <div class="summary-text">{summary["summary"]}</div>
            </div>

            <div class="stats-grid">
                <div class="stat-card">
                    <span class="stat-number">{summary["page_stats"]["elements_analyzed"]}</span>
                    <div class="stat-label">Total Elements</div>
                </div>
                <div class="stat-card">
                    <span class="stat-number">{summary["page_stats"]["interactive_elements"]}</span>
                    <div class="stat-label">Interactive</div>
                </div>
                <div class="stat-card">
                    <span class="stat-number">{summary["page_stats"]["content_elements"]}</span>
                    <div class="stat-label">Content</div>
                </div>
                <div class="stat-card">
                    <span class="stat-number">{summary["page_stats"]["structural_elements"]}</span>
                    <div class="stat-label">Structural</div>
                </div>
                <div class="stat-card">
                    <span class="stat-number">{"Yes" if summary["page_stats"]["has_forms"] else "No"}</span>
                    <div class="stat-label">Forms</div>
                </div>
                <div class="stat-card">
                    <span class="stat-number">{(summary["page_stats"]["content_length"] // 1000) if summary["page_stats"]["content_length"] > 0 else 0}K</span>
                    <div class="stat-label">Content Size</div>
                </div>
            </div>

            <div class="comprehensive-grid">
                <div class="analysis-section">
                    <h3>📊 Content Analysis</h3>
                    <p><strong>Word Count:</strong> {comprehensive.get('content_analysis', {}).get('word_count', 0):,}</p>
                    <p><strong>Content Length:</strong> {comprehensive.get('content_analysis', {}).get('content_length', 0):,} characters</p>
                    <p><strong>Main Topics:</strong> {', '.join(comprehensive.get('content_analysis', {}).get('main_topics', [])[:5]) or 'None detected'}</p>
                </div>

                <div class="analysis-section">
                    <h3>⚙️ Technical Analysis</h3>
                    <p><strong>CSS Selectors:</strong> {comprehensive.get('technical_analysis', {}).get('total_css_selectors', 0)}</p>
                    <p><strong>Scripts:</strong> {comprehensive.get('technical_analysis', {}).get('scripts_count', 0)}</p>
                    <p><strong>Stylesheets:</strong> {comprehensive.get('technical_analysis', {}).get('stylesheets_count', 0)}</p>
                    <p><strong>Meta Tags:</strong> {comprehensive.get('technical_analysis', {}).get('meta_tags_count', 0)}</p>
                </div>
            </div>

            <div class="key-elements">
                <h2>🎯 Key Elements Identified</h2>""")

            if summary["key_elements"]:
                for element in summary["key_elements"]:
                    # Safe category access with fallback
                    category = element.get("category", "general")
                    description = element.get("description", "No description available")
                    
                    category_color = {
                        "interactive": "#3498db",
                        "form": "#e74c3c",
                        "navigation": "#f39c12",
                        "content": "#27ae60",
                        "structural": "#9b59b6",
                        "general": "#95a5a6"
                    }.get(category, "#95a5a6")

                    f.write(f"""
                <div class="key-element">
                    <span class="element-category" style="background-color: {category_color};">
                        {category.title()}
                    </span>
                    <div class="element-description">{description}</div>
                </div>""")
            else:
                f.write("""
                <div class="key-element">
                    <div class="element-description">No specific elements were highlighted in this analysis.</div>
                </div>""")

            f.write("""
            </div>
        </div>

        <div class="generation-info">
            <strong>Generated:</strong> """ + summary["generation_time"] + """ | 
            <strong>Analysis Type:</strong> """ + (
                "AI-Powered Summary" if summary["ai_powered"] else "Intelligent Fallback Analysis") + """
        </div>
    </div>
</body>
</html>""")
    except Exception as e:
        print(f"Error generating AI summary: {e}")
        with open(os.path.join(summary_dir, "summary_error.txt"), "w", encoding="utf-8") as f:
            f.write(f"Failed to generate AI summary: {str(e)}")


def _get_progress_bar(percent, width=50):
    """Generate a text-based progress bar"""
    filled = int(width * percent / 100)
    bar = '█' * filled + '░' * (width - filled)
    return f"[{bar}]"


class WebCrawler:
    """Class to handle recursive website crawling"""

    def __init__(self, analyzer, start_url, output_dir, options):
        """Initialize the web crawler

        Args:
            analyzer: The WebElementAnalyzer instance
            start_url: The starting URL
            output_dir: Base directory for output
            options: Dictionary of options including:
                - depth: Maximum crawl depth
                - max_pages: Maximum number of pages to crawl
                - delay: Delay between requests
                - exclude: List of regex patterns to exclude
                - include_only: List of regex patterns to include (if specified)
        """
        self.analyzer = analyzer
        self.start_url = start_url
        self.base_output_dir = output_dir

        # Extract options
        self.max_depth = options.get('depth', 1)
        self.max_pages = options.get('max_pages', 100)
        self.delay = options.get('delay', 0.5)

        # Convert exclude and include patterns to compiled regex
        self.exclude_patterns = [re.compile(pattern) for pattern in options.get('exclude', [])]
        self.include_patterns = [re.compile(pattern) for pattern in options.get('include_only', [])]

        # Parse the base domain for same-domain check
        parsed_url = urlparse(start_url)
        self.base_domain = parsed_url.netloc

        # Crawling stats
        self.pages_crawled = 0
        self.start_time = None
        self.end_time = None

        # Setup tracking structures
        self.visited_urls = set()
        self.failed_urls = set()  # Track URLs that failed during crawling
        self.urls_to_visit = deque()  # Using deque for efficient queue operations
        self.url_to_depth = {}  # Track depth of each URL

        # Initialize the queue with the start URL
        self.urls_to_visit.append(start_url)
        self.url_to_depth[start_url] = 0

        # Results storage
        self.results = {}

    def should_crawl_url(self, url):
        """Determine if a URL should be crawled based on filters"""
        # Skip if already visited or failed
        if url in self.visited_urls or url in self.failed_urls:
            return False

        # Check if URL is from the same domain or a subdomain
        parsed_url = urlparse(url)
        parsed_base = urlparse(self.start_url)

        # Allow same domain or subdomains (like www.domain.com, news.domain.com for domain.com)
        if parsed_url.netloc != self.base_domain:
            base_domain_parts = self.base_domain.split('.')
            url_domain_parts = parsed_url.netloc.split('.')

            # Check if it's a subdomain or related domain
            is_related = False

            # Check if domain ends with the same TLD and domain (e.g., .co.il, .com)
            if len(base_domain_parts) >= 2 and len(url_domain_parts) >= 2:
                base_main_domain = '.'.join(base_domain_parts[-2:])  # Get last two parts (e.g., co.il)
                url_main_domain = '.'.join(url_domain_parts[-2:])  # Same for URL

                # Consider related if they have the same main domain
                if base_main_domain == url_main_domain:
                    is_related = True

                    # For debugging
                    print(f"Allowing related domain: {parsed_url.netloc} (base: {self.base_domain})")

            if not is_related:
                return False

        # Common API/Media file extensions to skip
        excluded_extensions = [
            # API and data formats
            '.oembed', '.json', '.xml', '.rss', '.csv', '.zip', '.pdf', '.atom',
            # Web assets
            '.js', '.css', '.ico', '.map',
            # Images
            '.png', '.jpeg', '.jpg', '.gif', '.svg', '.webp', '.bmp', '.tiff',
            # Videos
            '.mp4', '.avi', '.mov', '.webm', '.mkv', '.flv', '.wmv',
            # Audio
            '.mp3', '.wav', '.ogg', '.aac', '.flac',
            # Fonts
            '.woff', '.woff2', '.ttf', '.eot', '.otf',
            # Document formats
            '.doc', '.docx', '.xls', '.xlsx', '.ppt', '.pptx',
            # Archive formats
            '.tar', '.gz', '.rar', '.7z'
        ]

        # Check if URL ends with any excluded extension
        lower_url = url.lower()
        for ext in excluded_extensions:
            if lower_url.endswith(ext):
                return False

        # Check for common API patterns in URL path
        api_patterns = [
            '/api/', '/oembed/', '/feed/', '/rss/', '/json/', '/xml/',
            '/download/', '/static/', '/assets/', '/wp-json/',
            '/wp-content/', '/wp-includes/'
        ]

        for pattern in api_patterns:
            if pattern in lower_url:
                return False

        # Check exclude patterns
        for pattern in self.exclude_patterns:
            if pattern.search(url):
                return False

        # Check include patterns (if specified)
        if self.include_patterns:
            match_found = False
            for pattern in self.include_patterns:
                if pattern.search(url):
                    match_found = True
                    break
            if not match_found:
                return False

        # Check for URL fragments (which typically refer to the same page)
        if '#' in url:
            base_url = url.split('#')[0]
            if base_url in self.visited_urls:
                return False

        # Avoid URLs with too many query parameters (likely pagination or filters)
        if '?' in url:
            query_part = urlparse(url).query
            if len(query_part) > 150 or query_part.count('&') > 8:  # Increased threshold
                return False

        # Avoid excessively long URLs
        if len(url) > 750:  # Increased from 500
            return False

        # Special handling for news sites like ynet
        lower_url = url.lower()
        if "ynet" in lower_url:
            # Allow category pages and article pages in news sites
            allowed_patterns = ['/category/', '/article/', '/articles/', '/news/',
                                '/home/', '/health/', '/sport/', '/economy/', '/tech/']
            for pattern in allowed_patterns:
                if pattern in lower_url:
                    return True

        return True

    def crawl(self):
        """Main crawl method that orchestrates the crawling process"""
        print(f"\n--- Starting Web Crawler with depth {self.max_depth} and max {self.max_pages} pages ---")

        self.start_time = time.time()

        # Calculate total work for progress indication
        total_work = min(self.max_pages, len(self.urls_to_visit) if self.urls_to_visit else 1)
        completed_work = 0

        # Continue until queue is empty or we hit the page limit
        while self.urls_to_visit and self.pages_crawled < self.max_pages:
            # Get the next URL and its depth
            current_url = self.urls_to_visit.popleft()
            current_depth = self.url_to_depth[current_url]

            # Skip if we've already visited this URL
            if current_url in self.visited_urls:
                continue

            # Mark as visited
            self.visited_urls.add(current_url)

            # Update progress indicator
            completed_work += 1
            progress = (completed_work / total_work) * 100
            progress_bar = _get_progress_bar(progress)
            print(f"\n{progress_bar} {progress:.1f}% complete")

            print(
                f"\n--- Crawling page {self.pages_crawled + 1}/{self.max_pages} at depth {current_depth}/{self.max_depth}: {current_url} ---")

            try:
                # Analyze the page (this should reuse your existing analysis logic)
                result_dir = self._analyze_page(current_url, current_depth)

                # Store result directory in our results
                self.results[current_url] = {
                    'depth': current_depth,
                    'result_dir': result_dir,
                    'page_number': self.pages_crawled + 1
                }

                # Increment pages crawled counter
                self.pages_crawled += 1

                # If we've reached the maximum depth, don't extract more links
                if current_depth >= self.max_depth:
                    continue

                # Extract links from the page if not at max depth
                page_content = _get_page_content(result_dir)
                if page_content:
                    links = extract_links(current_url, page_content)

                    # Add new links to the queue if they pass our filters
                    for link in links:
                        if self.should_crawl_url(link):
                            self.urls_to_visit.append(link)
                            self.url_to_depth[link] = current_depth + 1
                            # Update total work estimate for progress bar
                            total_work = min(self.max_pages, len(self.visited_urls) + len(self.urls_to_visit))

                # Respect the delay setting
                if self.delay > 0:
                    time.sleep(self.delay)

            except Exception as e:
                # Record the failed URL
                self.failed_urls.add(current_url)
                print(f"Error crawling {current_url}: {e}")

        self.end_time = time.time()
        self._generate_crawl_report()

    def _generate_crawl_report(self):
        """Generate a report of the crawling activity"""
        if self.start_time is None or self.end_time is None:
            print("Error: start_time or end_time is None. Cannot generate crawl report.")
            return
        duration = self.end_time - self.start_time

        # Create report
        report = {
            'start_url': self.start_url,
            'pages_crawled': self.pages_crawled,
            'max_depth': self.max_depth,
            'duration_seconds': duration,
            'visited_urls': len(self.visited_urls),
            'failed_urls': len(self.failed_urls),
            'pages': self.results,
            'failed': list(self.failed_urls)[:100]  # Include up to 100 failed URLs
        }

        # Save report to JSON
        report_path = os.path.join(self.base_output_dir, "crawl_report.json")
        try:
            with open(report_path, 'w', encoding='utf-8') as f:
                json.dump(report, f, indent=2)
            print(f"Crawl report saved to: {report_path}")
        except Exception as e:
            print(f"Error saving crawl report: {e}")

        # Save run info for MCP
        try:
            script_dir = Path(__file__).parent
            mcp_dir = script_dir / "mcp"
            mcp_dir.mkdir(exist_ok=True)

            run_info_path = mcp_dir / "run_info.json"

            # Collect all URLs and output directories
            urls = []
            output_dirs = []
            for url, info in self.results.items():
                urls.append(url)
                if info.get('result_dir'):
                    output_dirs.append(info['result_dir'])

            run_info = {
                "timestamp": datetime.now().isoformat(),
                "output_dirs": output_dirs,
                "base_output_dir": str(self.base_output_dir),
                "urls": urls,
                "dates": [datetime.now().strftime("%Y/%m/%d")],
                "analysis_type": "crawl",
                "pages_crawled": self.pages_crawled,
                "start_url": self.start_url
            }

            with open(run_info_path, "w", encoding="utf-8") as f:
                json.dump(run_info, f, indent=2)

            print(f"Run info saved for MCP (crawl mode): {run_info_path}")

        except Exception as e:
            print(f"Warning: Could not save run info for MCP: {e}")

        # Also generate an HTML report
        self._generate_html_report(report)

        # Print summary
        print("\n--- Web Crawling Summary ---")
        print(f"Starting URL: {self.start_url}")
        print(f"Total pages crawled: {self.pages_crawled}")
        print(f"Total URLs visited: {len(self.visited_urls)}")
        print(f"Failed URLs: {len(self.failed_urls)}")
        print(f"Maximum depth reached: {max([info['depth'] for info in self.results.values()] or [0])}")
        print(f"Total duration: {duration:.2f} seconds")
        print(f"Pages per second: {(self.pages_crawled / duration if duration > 0 else 0):.2f}")
        print(f"Crawl report saved to: {report_path}")

    def _analyze_page(self, url, depth):
        """Analyze a single page and return the result directory"""
        # Create directory structure based on URL and date
        result_dir = self._create_url_based_directory(url)

        # Create screen processing subdirectories
        screen_dirs = {
            'raw': os.path.join(result_dir, "1_raw_data"),
            'analysis': os.path.join(result_dir, "2_analysis"),
            'summary': os.path.join(result_dir, "3_summary")
        }

        # Create subdirectories
        for dir_name, dir_path in screen_dirs.items():
            os.makedirs(dir_path, exist_ok=True)

        # Create an error log file in case analysis fails
        error_log_path = os.path.join(result_dir, "analysis_error.log")

        # Create progress file to track processing steps
        progress_file = os.path.join(result_dir, "progress.log")
        _update_progress(progress_file, "Started analysis")

        try:
            # Run the analyzer on this URL with a timeout protection
            _update_progress(progress_file, "Running web page analysis")

            result = self.analyzer.analyze_url(
                url=url,
                base_output_path=screen_dirs['raw'],
                json_only=True  # For faster crawling, only generate core JSON data
            )

            # Process raw data to create enriched analysis
            if result is not None:
                _update_progress(progress_file, "Processing raw data")
                _process_raw_data(screen_dirs['raw'], screen_dirs['analysis'])

                # Generate AI summary
                _update_progress(progress_file, "Generating AI summary")
                _generate_ai_summary(screen_dirs['raw'], screen_dirs['analysis'], screen_dirs['summary'])

                _update_progress(progress_file, "Analysis completed successfully")
            else:
                # If analysis fails, create minimal content for extraction
                _update_progress(progress_file, "Analysis failed, creating minimal content")
                with open(os.path.join(screen_dirs['raw'], "full_page.html"), "w", encoding="utf-8") as f:
                    f.write(
                        f"<html><head><title>Failed to analyze: {url}</title></head><body><p>Analysis failed for this URL</p></body></html>")

                # Record the failure reason
                from datetime import datetime as dt
                with open(error_log_path, "w", encoding="utf-8") as f:
                    f.write(f"Analysis failed for URL: {url}\nTime: {dt.now()}\n")

            return result_dir

        except Exception as e:
            _update_progress(progress_file, f"Error: {str(e)}")
            print(f"Exception during page analysis of {url}: {e}")
            # Log the error
            try:
                from datetime import datetime as dt
                with open(error_log_path, "w", encoding="utf-8") as f:
                    f.write(f"Error analyzing URL: {url}\n")
                    f.write(f"Time: {dt.now()}\n")
                    f.write(f"Exception: {str(e)}\n")
                    f.write("Traceback:\n")
                    traceback.print_exc(file=f)
            except Exception as log_error:
                print(f"Failed to write error log: {log_error}")

            # Create minimal content for link extraction to continue
            try:
                with open(os.path.join(screen_dirs['raw'], "full_page.html"), "w", encoding="utf-8") as f:
                    f.write(
                        f"<html><head><title>Error analyzing: {url}</title></head><body><p>Error during analysis: {str(e)}</p></body></html>")
            except Exception:
                pass

            return result_dir

    def _create_url_based_directory(self, url):
        """Create a directory structure based on the URL and date

        Args:
            url: The URL to create a directory for

        Returns:
            Path to the created directory
        """
        # Parse the URL to extract components
        parsed_url = urlparse(url)

        # Extract domain and path
        domain = parsed_url.netloc.replace(".", "_").replace(":", "_")
        path = parsed_url.path.replace("/", "_").strip("_")
        if not path:
            path = "homepage"

        # Create date-based directory structure
        today = datetime.now()
        date_path = today.strftime("%Y/%m/%d")  # Year/Month/Day format

        # Create a unique timestamp for this analysis
        timestamp = today.strftime("%H%M%S")

        # Create the full path
        full_path = os.path.join(
            self.base_output_dir,
            date_path,
            domain,
            f"{path}_{timestamp}"
        )

        # Ensure the directory exists
        os.makedirs(full_path, exist_ok=True)

        return full_path

    def _generate_html_report(self, report):
        """Generate an HTML report for better visualization"""
        report_path = os.path.join(self.base_output_dir, "crawl_report.html")

        # Simple HTML template
        html = f"""<!DOCTYPE html>
<html>
<head>
    <title>Web Crawler Report</title>
    <style>
        body {{ font-family: Arial, sans-serif; margin: 20px; }}
        h1, h2 {{ color: #333; }}
        .summary {{ background-color: #f5f5f5; padding: 15px; border-radius: 5px; margin-bottom: 20px; }}
        .pages {{ display: flex; flex-wrap: wrap; }}
        .page-card {{ border: 1px solid #ddd; margin: 10px; padding: 15px; border-radius: 5px; width: 300px; }}
        .page-card h3 {{ margin-top: 0; }}
        .page-card a {{ color: #0066cc; }}
        .depth-0 {{ background-color: #e6f7ff; }}
        .depth-1 {{ background-color: #e6ffe6; }}
        .depth-2 {{ background-color: #fff2e6; }}
        .depth-3 {{ background-color: #f2e6ff; }}
        .depth-4 {{ background-color: #e6ffff; }}
        .depth-5 {{ background-color: #ffe6e6; }}
        .progress-bar {{ 
            background-color: #f1f1f1; 
            width: 100%; 
            border-radius: 5px; 
            margin: 10px 0;
        }}
        .progress {{ 
            background-color: #4CAF50; 
            height: 30px; 
            border-radius: 5px; 
            text-align: center;
            line-height: 30px;
            color: white;
            transition: width 0.5s;
        }}
    </style>
</head>
<body>
    <h1>Web Crawler Report</h1>

    <div class="summary">
        <h2>Summary</h2>
        <p><strong>Starting URL:</strong> {report['start_url']}</p>
        <p><strong>Pages Crawled:</strong> {report['pages_crawled']}</p>
        <p><strong>Maximum Depth:</strong> {report['max_depth']}</p>
        <p><strong>Duration:</strong> {report['duration_seconds']:.2f} seconds</p>
        <p><strong>Pages per Second:</strong> {report['pages_crawled'] / max(report['duration_seconds'], 0.001):.2f}</p>
        <p><strong>Total URLs Visited:</strong> {report['visited_urls']}</p>
        <p><strong>Failed URLs:</strong> {report['failed_urls']}</p>
    </div>

    <h2>Crawled Pages</h2>
    <div class="pages">
"""

        # Sort pages by page number
        sorted_pages = sorted(report['pages'].items(), key=lambda x: x[1]['page_number'])

        # Add page cards
        for url, info in sorted_pages:
            depth = info['depth']
            result_dir = info['result_dir']
            page_number = info['page_number']

            # Get relative path for better links
            rel_path = os.path.relpath(result_dir, self.base_output_dir)

            # Check if AI summary exists
            summary_path = os.path.join(result_dir, "3_summary", "summary.html")
            summary_link = f'<a href="{os.path.join(rel_path, "3_summary", "summary.html")}" target="_blank">AI Summary</a>' if os.path.exists(
                summary_path) else 'No Summary'

            html += f"""
        <div class="page-card depth-{min(depth, 5)}">
            <h3>Page {page_number}</h3>
            <p><strong>URL:</strong> <a href="{url}" target="_blank">{url[:50]}{'...' if len(url) > 50 else ''}</a></p>
            <p><strong>Depth:</strong> {depth}</p>
            <p><strong>Results:</strong> <a href="{os.path.join(rel_path, "1_raw_data")}" target="_blank">Raw Data</a> | {summary_link}</p>
        </div>
"""

        # Add failed URLs section if any
        if report['failed_urls'] > 0:
            html += """
    </div>

    <h2>Failed URLs</h2>
    <div class="failed-urls">
        <ul>
"""
            for failed_url in report.get('failed', []):
                html += f"""        <li><a href="{failed_url}" target="_blank">{failed_url}</a></li>
"""
            html += """        </ul>
    </div>
"""
        else:
            html += """
    </div>
"""

        # Close the HTML
        html += """
</body>
</html>
"""

        # Save the HTML report
        try:
            with open(report_path, 'w', encoding='utf-8') as f:
                f.write(html)
            print(f"HTML crawl report saved to: {report_path}")
        except Exception as e:
            print(f"Error saving HTML crawl report: {e}")


# --- Main Execution Block ---
if __name__ == "__main__":
    start_time = time.time()
    print("--- Web Element Analyzer Script Started ---")

    # Parse arguments
    parser = argparse.ArgumentParser(description="Integrated Web Element Analyzer for Playwright",
                                     formatter_class=argparse.ArgumentDefaultsHelpFormatter)

    # Required arguments (URL or File)
    group = parser.add_mutually_exclusive_group(required=True)
    group.add_argument("-u", "--url", type=str, help="URL to analyze")
    group.add_argument("-f", "--file", type=str, help="HTML file path to analyze")

    # Optional arguments
    parser.add_argument("-o", "--output", type=str, help="Base output directory")
    parser.add_argument("-d", "--domain", type=str,
                        help="Override domain name for generated classes (default: extracted from URL/filename)")
    parser.add_argument("-hl", "--headless", action=argparse.BooleanOptionalAction, default=True,
                        help="Run browser in headless mode")
    parser.add_argument("-v", "--verbose", action="store_true",
                        help="Verbose output (Currently adds more print statements)")  # Basic verbose flag
    # parser.add_argument("-m", "--mobile", action="store_true", help="Enable mobile emulation (Not implemented)")
    # parser.add_argument("-w", "--width", type=int, default=1366, help="Browser viewport width (Not fully implemented)")
    # parser.add_argument("-ht", "--height", type=int, default=768, help="Browser viewport height (Not fully implemented)")

    # Output format flags
    parser.add_argument("-csv", "--export-csv", action="store_true", help="Export elements to CSV")
    parser.add_argument("-html", "--html-report", action="store_true", help="Generate HTML analysis report")
    parser.add_argument("-cuc", "--cucumber", action="store_true", help="Generate Cucumber/Behave step definitions")
    parser.add_argument("-a", "--all", action="store_true",
                        help="Enable all optional output features (CSV, HTML Report, Cucumber)")
    parser.add_argument("-j", "--json-only", action="store_true",
                        help="Only generate core JSON data (faster, skips helpers and optional outputs)")

    # Web crawler arguments
    parser.add_argument("--scrapy", action="store_true", help="Enable recursive crawling of the website")
    parser.add_argument("--depth", type=int, default=1, help="Maximum depth for recursive crawling")
    parser.add_argument("--max-pages", type=int, default=100, help="Maximum number of pages to crawl")
    parser.add_argument("--delay", type=float, default=0.5, help="Delay between requests in seconds")
    parser.add_argument("--exclude", type=str, nargs="*", default=[], help="URL patterns to exclude from crawling")
    parser.add_argument("--include-only", type=str, nargs="*", default=[],
                        help="Only crawl URLs matching these patterns (if specified)")

    # Advanced/Experimental flags (Not fully implemented)
    # parser.add_argument("-fw", "--detect-frameworks", action="store_true", help="Detect frontend frameworks")
    # parser.add_argument("-vis", "--visualize", action="store_true", help="Generate advanced visualization")

    # Parse the arguments
    args = parser.parse_args()

    # --- Prepare for Analysis ---

    # Determine base output directory
    base_output_dir = args.output
    if not base_output_dir:
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        # Create default in the script's directory if -o not specified
        script_dir = Path(__file__).parent
        base_output_dir = script_dir / f"output_{timestamp}"
        print(f"Warning: No output directory specified (-o). Using default: {base_output_dir}")
    else:
        # Ensure the provided path is absolute or resolve relative to current dir
        base_output_dir = Path(base_output_dir).resolve()
        print(f"Using specified base output directory: {base_output_dir}")

    # Ensure base output directory exists before passing to analyzer
    try:
        base_output_dir.mkdir(parents=True, exist_ok=True)
    except OSError as e:
        print(f"Error: Cannot create base output directory '{base_output_dir}': {e}")
        sys.exit(1)

    # --- Create and Run Analyzer ---
    analyzer = None  # Initialize analyzer variable
    final_output_path = None
    try:
        # Create analyzer instance, passing necessary args
        analyzer = WebElementAnalyzer(headless=args.headless)
        # Pass domain if provided
        if args.domain:
            analyzer.domain = args.domain

        # Run analysis (either URL or File)
        if args.url:
            # Check if we should run in crawler mode
            if args.scrapy:
                print(f"\n--- Scrapy mode enabled with depth {args.depth} ---")

                # Create options dictionary for the crawler
                options = {
                    'depth': args.depth,
                    'max_pages': args.max_pages,
                    'delay': args.delay,
                    'exclude': args.exclude,
                    'include_only': args.include_only
                }

                # Create and run the crawler
                crawler = WebCrawler(analyzer, args.url, str(base_output_dir), options)
                crawler.crawl()

                final_output_path = base_output_dir
            else:
                # Regular single-page analysis
                final_output_path = analyzer.analyze_url(
                    url=args.url,
                    base_output_path=str(base_output_dir),
                    generate_all_outputs=args.all,
                    generate_csv=args.export_csv,
                    generate_cucumber=args.cucumber,
                    generate_report=args.html_report,
                    # detect_frameworks=args.detect_frameworks, # Pass if implemented
                    # visualize=args.visualize, # Pass if implemented
                    json_only=args.json_only
                )
        elif args.file:
            print("Error: Analyzing local HTML files (-f) is not fully implemented in this version.")
            # Implement analyze_file(file_path, ...) method if needed
            sys.exit(1)

        # --- Report Outcome ---
        if final_output_path:
            print(f"\n✅ Analysis complete. Final results saved to: {final_output_path}")
            if args.scrapy:
                print(f"   View the crawl report: {final_output_path / 'crawl_report.html'}")
            else:
                print(f"   View the visual map: {final_output_path / 'visual_element_map.html'}")
                if (final_output_path / 'analysis_report.html').exists():
                    print(f"   View the HTML report: {final_output_path / 'analysis_report.html'}")
            end_time = time.time()
            print(f"Total execution time: {end_time - start_time:.2f} seconds")
            sys.exit(0)  # Exit with success code
        else:
            print("\n❌ Analysis failed. Check logs above for errors.")
            end_time = time.time()
            print(f"Total execution time: {end_time - start_time:.2f} seconds")
            sys.exit(1)  # Exit with failure code

    except Exception as main_err:
        print(f"\n--- CRITICAL ERROR in main execution --- ")
        print(f"Error: {main_err}")
        traceback.print_exc()
        if analyzer:  # Attempt cleanup if analyzer was created
            analyzer.close()
        sys.exit(2)  # Different error code for critical failure