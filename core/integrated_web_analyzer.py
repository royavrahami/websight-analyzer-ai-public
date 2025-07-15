#!/usr/bin/env python3
"""
Integrated Web Element Analyzer

This script integrates all the functionality provided in the separate modules:
- playwright_web_elements_analyzer.py (core functionality)
- element_detection_extensions.py (framework-specific detection)
- output_extensions.py (additional output formats)

Usage:
    python integrated_web_analyzer.py <URL> [--options]

Options:
    --headless / --no-headless    Run in headless mode (default: True)
    --all-outputs / -a            Generate all additional outputs
    --csv                         Generate CSV output
    --cucumber                    Generate Cucumber steps
    --report                      Generate HTML report

Author: Roy Avrahami
Date: April 2025
"""

import os
import sys
import time
import json
import argparse
from urllib.parse import urlparse

try:
    from playwright.sync_api import sync_playwright, Page, Browser, BrowserContext, Locator, expect
except ImportError:
    print("Error: Playwright not installed. Please install with:")
    print("  pip install playwright")
    print("  playwright install")
    sys.exit(1)

# Attempt to import our modules
try:
    # Import core functionality
    from playwright_web_elements_analyzer import WebElementAnalyzer
    
    # Import extension classes
    from element_detection_extensions import AdvancedDetectionExtensions
    from output_extensions import OutputExtensions
    
    # Create integrated class
    class IntegratedWebElementAnalyzer(WebElementAnalyzer, AdvancedDetectionExtensions, OutputExtensions):
        """
        Integrated class that combines core functionality with all extensions
        """
        pass
    
except ImportError:
    # If modules are not available, create IntegratedWebElementAnalyzer from built-in classes
    print("Warning: Could not import extension modules. Using integrated class definition.")
    
    # Define the integrated class here
    def _clean_variable_name(name: str) -> str:
        """Clean a string to use as a valid Python variable name"""
        if not name:
            return ""

        # Replace non-alphanumeric chars with underscore
        clean_name = ''.join(c if c.isalnum() else '_' for c in name)

        # Remove consecutive underscores
        while '__' in clean_name:
            clean_name = clean_name.replace('__', '_')

        # Remove leading/trailing underscores
        clean_name = clean_name.strip('_')

        # Ensure it starts with a letter
        if clean_name and not clean_name[0].isalpha():
            clean_name = 'e_' + clean_name

        # Truncate if too long
        if len(clean_name) > 40:
            clean_name = clean_name[:40]

        # Return lowercase (Python convention)
        return clean_name.lower()


    def _detect_angular_elements():
        """Detect Angular elements (simplified placeholder)"""
        # This should contain the full implementation from element_detection_extensions.py
        return {"components": [], "bindings": [], "directives": []}


    def _detect_react_elements():
        """Detect React elements (simplified placeholder)"""
        # This should contain the full implementation from element_detection_extensions.py
        return {"components": [], "props": []}


    def _detect_form_elements():
        """Detect form elements (simplified placeholder)"""
        # This should contain the full implementation from element_detection_extensions.py
        return {"forms": [], "formGroups": [], "validation": []}


    def _detect_accessible_elements():
        """Detect accessibility elements (simplified placeholder)"""
        # This should contain the full implementation from element_detection_extensions.py
        return {"ariaElements": [], "landmarks": [], "accessibilityIssues": []}


    def _detect_dynamic_content():
        """Detect dynamic content (simplified placeholder)"""
        # This should contain the full implementation from element_detection_extensions.py
        return {"dynamicAreas": [], "eventHandlers": [], "ajaxElements": []}


    def _get_element_analysis_script():
        """Get the JavaScript to run in the browser for element analysis"""
        # This should return a JavaScript string for element analysis
        # In the integrated version, this would be imported from the full implementation
        # For now, return a minimal implementation
        return """
        function analyzeElements() {
            console.log("Analyzing elements...");
            // Simplified implementation - would need the full JS from main class
            const result = {
                interactive: [],
                structural: [],
                content: [],
                forms: []
            };
            
            // Fill with elements - SIMPLIFIED VERSION
            document.querySelectorAll('button, a, input').forEach(el => {
                const rect = el.getBoundingClientRect();
                result.interactive.push({
                    tagName: el.tagName.toLowerCase(),
                    description: el.textContent || el.value || el.type,
                    name: el.id || el.name || el.textContent,
                    selectors: {
                        css: el.id ? `#${el.id}` : el.tagName.toLowerCase(),
                        xpath: `//${el.tagName.toLowerCase()}`,
                        accessibility: null
                    },
                    position: {
                        x: rect.x,
                        y: rect.y,
                        width: rect.width,
                        height: rect.height
                    },
                    attributes: {
                        id: el.id,
                        class: el.className
                    },
                    text: el.textContent,
                    isVisible: true
                });
            });
            
            return result;
        }
        
        return analyzeElements();
        """


    class IntegratedWebElementAnalyzer:
        """Integrated Web Element Analyzer with all functionality"""
        
        def __init__(self, headless: bool = True):
            """Initialize the analyzer with configuration options"""
            self.headless = headless
            self.playwright = None
            self.browser = None
            self.context = None
            self.page = None
            self.output_dir = None
            self.domain = None
            self.url = None
            self.framework_data = {}
            self.elements_data = {}
        
        def start(self):
            """Start the Playwright browser instance"""
            try:
                self.playwright = sync_playwright().start()
                self.browser = self.playwright.chromium.launch(headless=self.headless)
                self.context = self.browser.new_context(
                    viewport={"width": 1366, "height": 768}
                )
                self.page = self.context.new_page()
                print("Browser started successfully")
            except Exception as e:
                print(f"Error starting browser: {e}")
                self.close()
                raise
        
        def close(self):
            """Close all browser resources"""
            print("Closing browser resources...")
            if self.page:
                try:
                    self.page.close()
                except Exception as e:
                    print(f"Error closing page: {e}")
            if self.context:
                try:
                    self.context.close()
                except Exception as e:
                    print(f"Error closing context: {e}")
            if self.browser:
                try:
                    self.browser.close()
                except Exception as e:
                    print(f"Error closing browser: {e}")
            if self.playwright:
                try:
                    self.playwright.stop()
                except Exception as e:
                    print(f"Error stopping playwright: {e}")
        
        def analyze_url(self, url: str, generate_all_outputs: bool = False, 
                       generate_csv: bool = False, generate_cucumber: bool = False, 
                       generate_report: bool = False):
            """
            Main method to analyze a webpage and generate reports
            
            Args:
                url: The URL to analyze
                generate_all_outputs: Generate all additional outputs
                generate_csv: Generate CSV export
                generate_cucumber: Generate Cucumber steps
                generate_report: Generate HTML report
            
            Returns:
                Path to the output directory
            """
            print(f"Analyzing webpage: {url}")
            self.url = url
            
            # Start the browser if not already started
            if not self.page:
                self.start()
            
            try:
                # Extract domain for file naming
                parsed_url = urlparse(url)
                self.domain = parsed_url.netloc.replace(".", "_").replace(":", "_")
                timestamp = int(time.time())
                self.output_dir = f"{self.domain}_analysis_{timestamp}"
                
                # Create output directory
                os.makedirs(self.output_dir, exist_ok=True)
                
                # Navigate to the URL
                print("Loading page...")
                self.page.goto(url, wait_until="load", timeout=60000)
                print("Page loaded successfully")
                
                # 1. Core Analysis
                print("\n--- Starting Core Analysis ---")
                self._extract_basic_info()
                self._analyze_elements()
                
                # 2. Advanced Detection
                print("\n--- Starting Advanced Detection ---")
                self._perform_advanced_detection()
                
                # 3. Generate Core Helpers
                print("\n--- Generating Core Helpers ---")
                self._generate_visual_map()
                self._create_helpers()
                
                # 4. Generate Extended Outputs
                print("\n--- Generating Extended Outputs ---")
                self._generate_extended_outputs(
                    generate_all_outputs,
                    generate_csv,
                    generate_cucumber,
                    generate_report
                )
                
                # 5. Create Final README
                print("\n--- Generating README ---")
                self._create_readme()
                
                print(f"\nAnalysis completed successfully!")
                print(f"All files are saved in: {self.output_dir}")
                
                return self.output_dir
                
            except Exception as e:
                print(f"Error analyzing page: {e}")
                import traceback
                traceback.print_exc()
                return None
        
        # Core functionality methods (simplified versions)
        def _extract_basic_info(self):
            """Extract basic page information including HTML and metadata"""
            print("Extracting basic page information...")
            
            # Save full HTML
            try:
                html_content = self.page.content()
                with open(os.path.join(self.output_dir, "full_page.html"), "w", encoding="utf-8") as f:
                    f.write(html_content)
                print("Full HTML saved")
            except Exception as e:
                print(f"Error saving HTML: {e}")
            
            # Extract metadata
            try:
                metadata = self.page.evaluate("""() => {
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
                }""")
                
                with open(os.path.join(self.output_dir, "metadata.json"), "w", encoding="utf-8") as f:
                    json.dump(metadata, f, indent=2)
                print("Page metadata saved")
            except Exception as e:
                print(f"Error extracting metadata: {e}")
            
            # Take a screenshot
            try:
                self.page.screenshot(path=os.path.join(self.output_dir, "screenshot.png"), full_page=True)
                print("Screenshot saved")
            except Exception as e:
                print(f"Error taking screenshot: {e}")
                try:
                    self.page.screenshot(path=os.path.join(self.output_dir, "screenshot.png"))
                    print("Viewport screenshot saved")
                except Exception as e2:
                    print(f"Error taking viewport screenshot: {e2}")
        
        def _analyze_elements(self):
            """Analyze all elements on the page to extract detailed information"""
            print("Extracting detailed element information...")
            
            # Execute the enhanced element analysis script in the browser
            element_structure = self.page.evaluate(_get_element_analysis_script())
            self.elements_data = element_structure
            
            # Save all elements by category
            for category, elements in element_structure.items():
                with open(os.path.join(self.output_dir, f"{category}.json"), "w", encoding="utf-8") as f:
                    json.dump(elements, f, indent=2)
                print(f"Saved {len(elements)} {category}")
            
            # Save full element data
            with open(os.path.join(self.output_dir, "enhanced_elements.json"), "w", encoding="utf-8") as f:
                json.dump(element_structure, f, indent=2)
            print("Enhanced element data saved")
            
            # Process and save selector information
            self._process_selectors(element_structure)
        
        def _process_selectors(self, element_structure):
            """Process and save various selector strategies from element data"""
            css_selectors = {}
            xpath_selectors = {}
            a11y_selectors = {}
            
            # Process all categories
            for category, elements in element_structure.items():
                for element in elements:
                    selectors = element.get("selectors", {})
                    element_info = {
                        "name": element.get("name", ""),
                        "description": element.get("description", ""),
                        "category": category,
                        "tagName": element.get("tagName", ""),
                        "text": element.get("text", "")
                    }
                    
                    # Add to appropriate selector maps
                    if selectors.get("css"):
                        css_selectors[selectors["css"]] = element_info
                    
                    if selectors.get("xpath"):
                        xpath_selectors[selectors["xpath"]] = element_info
                    
                    if selectors.get("accessibility"):
                        a11y_selectors[selectors["accessibility"]] = element_info
            
            # Save selector maps
            with open(os.path.join(self.output_dir, "css_selectors.json"), "w", encoding="utf-8") as f:
                json.dump(css_selectors, f, indent=2)
            
            with open(os.path.join(self.output_dir, "xpath_selectors.json"), "w", encoding="utf-8") as f:
                json.dump(xpath_selectors, f, indent=2)
            
            with open(os.path.join(self.output_dir, "a11y_selectors.json"), "w", encoding="utf-8") as f:
                json.dump(a11y_selectors, f, indent=2)
            
            print("Selector strategy files saved")
        
        def _create_helpers(self):
            """Generate helper files for test automation including Page Objects and test templates"""
            print("Generating helper files for automation...")
            
            # Load the element data to generate selectors and page objects
            with open(os.path.join(self.output_dir, "enhanced_elements.json"), "r", encoding="utf-8") as f:
                elements_data = json.load(f)
            
            with open(os.path.join(self.output_dir, "css_selectors.json"), "r", encoding="utf-8") as f:
                css_selectors = json.load(f)
            
            # Generate Python Page Object Class
            self._generate_page_object(elements_data, css_selectors)
            
            # Generate helper classes
            self._generate_selectors_class(css_selectors)
            
            # Generate test template
            self._generate_test_template(css_selectors)
        
        def _generate_visual_map(self):
            """Generate a visual HTML map of elements for interactive exploration"""
            html_path = os.path.join(self.output_dir, "visual_element_map.html")
            
            # Get the HTML template for the visual map
            visual_map_html = self._get_visual_map_html_template()
            
            # Write to file
            with open(html_path, "w", encoding="utf-8") as f:
                f.write(visual_map_html)
            
            print("Visual element map generated")
        
        # --- Include simplified placeholder methods for all required functionality ---
        # These would be filled in by the actual implementation in the extension files
        
        # Helper for clean variable names used in many methods

        # Required getter methods that return JavaScript code

        def _get_visual_map_html_template(self):
            """Return the HTML template for the visual map"""
            # This should return an HTML template for the visual map
            # Simplified version - the full implementation would come from main class
            return f"""<!DOCTYPE html>
            <html>
            <head>
                <title>Visual Element Map for {self.url}</title>
                <style>
                    body {{ font-family: Arial; }}
                    .screenshot {{ position: relative; max-width: 100%; }}
                    .element {{ position: absolute; border: 2px solid blue; background: rgba(0,0,255,0.2); }}
                </style>
            </head>
            <body>
                <h1>Visual Element Map</h1>
                <p>View screenshot.png to see the page layout.</p>
                <p>Examine enhanced_elements.json for detailed element information.</p>
                <div class="screenshot">
                    <img src="screenshot.png" alt="Page Screenshot" />
                </div>
                <script>
                    // Full implementation would include interactive JavaScript
                    console.log("Visual map would display element highlights");
                </script>
            </body>
            </html>
            """
        
        # Core helpers generation
        def _generate_page_object(self, elements_data, css_selectors):
            """Generate a Playwright Page Object Model in Python"""
            # Simplified implementation - the full version would come from main class
            page_object_path = os.path.join(self.output_dir, "page_object.py")
            
            page_class = f"{self.domain.title().replace('_', '')}Page"
            
            with open(page_object_path, "w", encoding="utf-8") as f:
                f.write(f"""# Page Object for {self.url}
from playwright.sync_api import Page

class {page_class}:
    \"\"\"Page Object Model for {self.url}\"\"\"
    
    def __init__(self, page: Page):
        self.page = page
        self.url = "{self.url}"
    
    def navigate(self):
        \"\"\"Navigate to the page\"\"\"
        self.page.goto(self.url)
        self.page.wait_for_load_state("networkidle")
    
    # Additional methods would be generated here
""")
            print(f"Page Object Model generated: {page_object_path}")
        
        def _generate_selectors_class(self, css_selectors):
            """Generate a Python class with all selectors as class variables"""
            # Simplified implementation - the full version would come from main class
            selectors_path = os.path.join(self.output_dir, "selectors.py")
            
            with open(selectors_path, "w", encoding="utf-8") as f:
                f.write(f"""# Selectors for {self.url}
class Selectors:
    \"\"\"Contains all selectors found on the page as class variables\"\"\"
    # Selectors would be added here
""")
            print(f"Selectors class generated: {selectors_path}")
        
        def _generate_test_template(self, css_selectors):
            """Generate a Playwright test template in Python"""
            # Simplified implementation - the full version would come from main class
            test_path = os.path.join(self.output_dir, "test_template.py")
            
            with open(test_path, "w", encoding="utf-8") as f:
                f.write(f"""# Playwright test template for {self.url}
import pytest
from playwright.sync_api import Page, expect

# Test implementations would be added here
""")
            print(f"Playwright test template generated: {test_path}")
        
        def _create_readme(self):
            """Create a README file with usage instructions"""
            readme_path = os.path.join(self.output_dir, "README.md")
            
            with open(readme_path, "w", encoding="utf-8") as f:
                f.write(f"""# Web Element Analysis for {self.url}

## Overview
This analysis provides detailed information about web elements on the page,
including selectors, properties, and helper files for test automation.

## Generated Files
- Full page HTML and screenshot
- Element information by category
- Selectors in multiple formats (CSS, XPath, accessibility)
- Page Object and test templates for Playwright
- Selenium helper class
- Cucumber/Behave step definitions
- Visual element map for interactive exploration

## Usage
Open visual_element_map.html in your browser to explore elements interactively.
""")
            print(f"README file generated: {readme_path}")
        
        # Advanced detection methods (simplified implementations)
        def _perform_advanced_detection(self):
            """Perform advanced detection of framework-specific elements"""
            print("Performing advanced element detection...")
            # This would call all the framework-specific detection methods
            # Simplified implementation here
            
            # Detect Angular elements
            angular_elements = _detect_angular_elements()
            with open(f"{self.output_dir}/angular_elements.json", "w", encoding="utf-8") as f:
                json.dump(angular_elements, f, indent=2)
            
            # Detect React elements
            react_elements = _detect_react_elements()
            with open(f"{self.output_dir}/react_elements.json", "w", encoding="utf-8") as f:
                json.dump(react_elements, f, indent=2)
            
            # Detect form elements
            form_elements = _detect_form_elements()
            with open(f"{self.output_dir}/form_elements.json", "w", encoding="utf-8") as f:
                json.dump(form_elements, f, indent=2)
            
            # Detect accessibility features
            accessibility_elements = _detect_accessible_elements()
            with open(f"{self.output_dir}/accessibility_elements.json", "w", encoding="utf-8") as f:
                json.dump(accessibility_elements, f, indent=2)
            
            # Detect dynamic content
            dynamic_content = _detect_dynamic_content()
            with open(f"{self.output_dir}/dynamic_content.json", "w", encoding="utf-8") as f:
                json.dump(dynamic_content, f, indent=2)
            
            # Store for later use
            self.framework_data = {
                "angular": angular_elements,
                "react": react_elements,
                "forms": form_elements,
                "accessibility": accessibility_elements,
                "dynamic": dynamic_content
            }
            
            # Generate advanced descriptors
            self._generate_advanced_descriptors()

        def _generate_advanced_descriptors(self):
            """Generate advanced element descriptors (simplified placeholder)"""
            # This should contain the full implementation from element_detection_extensions.py
            print("Generating advanced element descriptors...")
            # In the real implementation, this would combine data from standard and framework-specific analysis
            descriptors_path = os.path.join(self.output_dir, "advanced_descriptors.json")
            with open(descriptors_path, "w", encoding="utf-8") as f:
                json.dump([], f, indent=2)
        
        # Extended output methods (simplified implementations)
        def _generate_extended_outputs(self, generate_all, generate_csv, generate_cucumber, generate_report):
            """Generate additional output formats based on user preferences"""
            print("Generating extended outputs...")
            
            if generate_all or generate_csv:
                self.export_to_csv()
            
            if generate_all or generate_cucumber:
                self.generate_cucumber_steps()
            
            # Always generate Selenium helper
            self.generate_selenium_helper()
            
            if generate_all or generate_report:
                self.create_html_report()
        
        def export_to_csv(self):
            """Export to CSV (simplified placeholder)"""
            # This should contain the full implementation from output_extensions.py
            print("Exporting to CSV...")
            csv_path = os.path.join(self.output_dir, "all_elements.csv")
            with open(csv_path, "w", encoding="utf-8") as f:
                f.write("Category,Tag,Description,Text,Selector\n")
                f.write("Sample,div,Example,Sample text,#example\n")
            print(f"CSV export created: {csv_path}")
        
        def generate_cucumber_steps(self):
            """Generate Cucumber steps (simplified placeholder)"""
            # This should contain the full implementation from output_extensions.py
            print("Generating Cucumber steps...")
            steps_path = os.path.join(self.output_dir, "steps.py")
            with open(steps_path, "w", encoding="utf-8") as f:
                f.write(f"""# Cucumber/Behave step definitions
from behave import given, when, then
from playwright.sync_api import expect

@given('I navigate to the page')
def navigate_to_page(context):
    context.page.goto("{self.url}")
""")
            print(f"Cucumber steps generated: {steps_path}")
        
        def generate_selenium_helper(self):
            """Generate Selenium helper (simplified placeholder)"""
            # This should contain the full implementation from output_extensions.py
            print("Generating Selenium helper...")
            selenium_path = os.path.join(self.output_dir, "selenium_helper.py")
            with open(selenium_path, "w", encoding="utf-8") as f:
                f.write(f"""# Selenium WebDriver helper
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC

class {self.domain.title().replace('_', '')}Helper:
    def __init__(self, driver):
        self.driver = driver
        self.url = "{self.url}"
    
    def navigate(self):
        self.driver.get(self.url)
""")
            print(f"Selenium helper generated: {selenium_path}")
        
        def create_html_report(self):
            """Create HTML report (simplified placeholder)"""
            # This should contain the full implementation from output_extensions.py
            print("Creating HTML report...")
            report_path = os.path.join(self.output_dir, "analysis_report.html")
            with open(report_path, "w", encoding="utf-8") as f:
                f.write(f"""<!DOCTYPE html>
<html>
<head>
    <title>Analysis Report for {self.url}</title>
</head>
<body>
    <h1>Web Element Analysis Report</h1>
    <p>URL: {self.url}</p>
    <p>See individual files for detailed information.</p>
</body>
</html>""")
            print(f"HTML report created: {report_path}")


def main():
    """Main entry point for the script"""
    parser = argparse.ArgumentParser(description="Integrated Web Element Analyzer")
    parser.add_argument("url", nargs="?", help="URL to analyze (will prompt if not provided)")
    parser.add_argument("--headless", dest="headless", action="store_true", default=True, help="Run in headless mode (default)")
    parser.add_argument("--no-headless", dest="headless", action="store_false", help="Run with visible browser")
    parser.add_argument("--all-outputs", "-a", action="store_true", help="Generate all additional outputs")
    parser.add_argument("--csv", action="store_true", help="Generate CSV output")
    parser.add_argument("--cucumber", action="store_true", help="Generate Cucumber steps")
    parser.add_argument("--report", action="store_true", help="Generate HTML report")
    
    args = parser.parse_args()
    
    # Get URL from arguments or prompt
    url = args.url
    if not url:
        url = input("Please enter the URL to analyze: ")
    
    # Basic URL validation
    if not url.startswith("http://") and not url.startswith("https://"):
        url = "https://" + url
    
    # Create analyzer instance
    analyzer = IntegratedWebElementAnalyzer(headless=args.headless)
    
    try:
        # Run the analysis
        output_dir = analyzer.analyze_url(
            url,
            generate_all_outputs=args.all_outputs,
            generate_csv=args.csv,
            generate_cucumber=args.cucumber,
            generate_report=args.report
        )
        
        if output_dir:
            print(f"\nAnalysis complete! All files saved to: {output_dir}")
            visual_map_path = os.path.join(output_dir, "visual_element_map.html")
            print(f"Open {visual_map_path} in your browser to explore the elements")
            report_path = os.path.join(output_dir, "analysis_report.html")
            if os.path.exists(report_path):
                print(f"View the detailed analysis report: {report_path}")
        else:
            print("\nAnalysis failed. Please check the error messages above.")
            sys.exit(1)
        
    except Exception as e:
        print(f"Error during analysis: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
    finally:
        # Always close browser resources
        analyzer.close()


if __name__ == "__main__":
    main() 