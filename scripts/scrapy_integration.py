#!/usr/bin/env python3
"""
Scrapy Integration for Web Element Analyzer

This module integrates Scrapy crawling capabilities with the Playwright Web Element Analyzer.
It crawls websites respecting robots.txt and creates separate analysis folders for each page.

Usage:
    python scrapy_integration.py -u <start_url> -o <output_dir> [options]

Options:
    -u, --url URL           Start URL to crawl (required)
    -o, --output OUTPUT     Base output directory (default: ./output_<timestamp>)
    -d, --depth INT         Maximum crawl depth (default: 2)
    -p, --max-pages INT     Maximum number of pages to crawl (default: 10)
    -r, --respect-robots    Respect robots.txt (default: True)
    -a, --analyze-all       Analyze all crawled pages with Playwright (default: True)
    -hl, --headless         Run browser in headless mode (default: True)
    --csv                   Generate CSV output for each page
    --html                  Generate HTML report for each page
    --cucumber              Generate Cucumber steps for each page
    --all                   Enable all optional outputs (CSV, HTML, Cucumber)

Author: Roy Avrahami
Date: April 2025
"""

import os
import sys
import time
import json
import shutil
import argparse
import logging
from urllib.parse import urlparse, urljoin
from pathlib import Path
from datetime import datetime
import io
import re

# Fix encoding issues for Windows console
if os.name == 'nt':  # Windows
    try:
        sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')
        sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding='utf-8', errors='replace')
    except Exception as e:
        print(f"Warning: Could not set UTF-8 encoding: {e}")

# Try importing required modules
try:
    import scrapy
    from scrapy.crawler import CrawlerProcess
    from scrapy.utils.project import get_project_settings
    from scrapy.spiders import CrawlSpider, Rule
    from scrapy.linkextractors import LinkExtractor
    from scrapy.exceptions import CloseSpider
except ImportError:
    print("Error: Scrapy not installed. Please install with:")
    print("  pip install scrapy")
    sys.exit(1)

# Try to import the Playwright analyzer
WebElementAnalyzer = None

def import_analyzer():
    """Import the WebElementAnalyzer from the appropriate location"""
    global WebElementAnalyzer
    
    try:
        # First try to import from core directory
        import sys
        import os
        core_path = os.path.join(os.path.dirname(os.path.dirname(__file__)), 'core')
        if core_path not in sys.path:
            sys.path.insert(0, core_path)
        
        from playwright_web_elements_analyzer import WebElementAnalyzer
        logger.info("✅ Successfully imported Playwright Web Element Analyzer from core/")
        return WebElementAnalyzer
    except ImportError:
        try:
            # Fallback to current directory
            from playwright_web_elements_analyzer_fixed_v2 import WebElementAnalyzer
            logger.info("✅ Successfully imported Playwright Web Element Analyzer from current directory")
            return WebElementAnalyzer
        except ImportError:
            logger.error("Error: Playwright Web Element Analyzer not found.")
            logger.error("Looking for:")
            logger.error("  1. core/playwright_web_elements_analyzer.py")
            logger.error("  2. playwright_web_elements_analyzer_fixed_v2.py")
            logger.error("Please ensure one of these files exists.")
            sys.exit(1)

# Set up logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s [%(levelname)s] %(message)s',
    handlers=[
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)


def sanitize_filename(url):
    """Convert URL to a safe directory/file name"""
    # Parse the URL
    parsed = urlparse(url)

    # Extract hostname and path
    hostname = parsed.netloc
    path = parsed.path

    # Remove trailing slash from path if it exists
    if path.endswith('/'):
        path = path[:-1]

    # If path is empty, use 'home' instead
    if not path:
        path = 'home'

    # Replace slashes with underscores and remove special characters
    path = re.sub(r'[^a-zA-Z0-9_-]', '_', path)

    # Combine hostname and path
    result = f"{hostname}{path}"

    # Truncate if too long
    if len(result) > 100:
        result = result[:100]

    return result


class WebElementCrawlSpider(CrawlSpider):
    """Scrapy spider to crawl websites and analyze pages using Playwright Web Element Analyzer"""

    name = 'web_element_crawler'

    def __init__(self, start_url=None, max_depth=2, max_pages=10, respect_robots=True,
                 output_dir=None, analyze_all=True, playwright_options=None, *args, **kwargs):
        super(WebElementCrawlSpider, self).__init__(*args, **kwargs)

        if not start_url:
            raise ValueError("start_url is required")

        # Initialize the spider
        self.start_urls = [start_url]
        parsed_url = urlparse(start_url)
        self.allowed_domains = [parsed_url.netloc]

        # Set crawl configurations
        self.max_depth = int(max_depth)
        self.max_pages = int(max_pages)
        self.respect_robots = respect_robots
        self.output_dir = output_dir or Path("./output_" + datetime.now().strftime("%Y%m%d_%H%M%S"))
        self.analyze_all = analyze_all
        self.playwright_options = playwright_options or {}

        # Initialize counters
        self.pages_crawled = 0

        # Define crawl rules
        self.rules = (
            Rule(
                LinkExtractor(allow=(), deny=(), allow_domains=self.allowed_domains,
                              deny_domains=(), restrict_xpaths=(), tags=('a', 'area'),
                              attrs=('href',), unique=True),
                callback='parse_item',
                follow=True
            ),
        )

        # Finalize initialization
        self._compile_rules()

        # Create results directory
        self.results_dir = Path(self.output_dir) / "results"
        self.results_dir.mkdir(parents=True, exist_ok=True)

        # Create a log file for the crawl
        self.log_file = Path(self.output_dir) / "crawl_log.txt"
        self.log_handler = logging.FileHandler(self.log_file)
        self.log_handler.setFormatter(logging.Formatter('%(asctime)s [%(levelname)s] %(message)s'))
        logger.addHandler(self.log_handler)

        # Log start of crawl
        logger.info(f"Starting crawl from: {start_url}")
        logger.info(f"Max depth: {max_depth}, Max pages: {max_pages}")
        logger.info(f"Respect robots.txt: {respect_robots}")
        logger.info(f"Output directory: {self.output_dir}")

    def parse_item(self, response):
        """Process each page, create a folder, and analyze it if required"""
        # Check if max pages limit reached
        self.pages_crawled += 1
        if self.pages_crawled > self.max_pages:
            logger.info(f"Reached maximum pages limit ({self.max_pages}). Stopping crawl.")
            raise CloseSpider(f"Reached maximum {self.max_pages} pages")

        # Extract page information
        url = response.url
        page_title = response.css('title::text').get() or sanitize_filename(url)
        page_name = sanitize_filename(url)

        # Log the found page
        logger.info(f"Crawled page {self.pages_crawled}/{self.max_pages}: {url}")
        logger.info(f"Page title: {page_title}")

        # Create a directory for this page
        page_dir = self.results_dir / page_name
        page_dir.mkdir(parents=True, exist_ok=True)

        # Save basic page information
        page_info = {
            "url": url,
            "title": page_title,
            "crawl_time": datetime.now().isoformat(),
            "status_code": response.status
        }

        with open(page_dir / "page_info.json", "w", encoding="utf-8") as f:
            json.dump(page_info, f, indent=2)

        # Save HTML content
        with open(page_dir / "raw_page.html", "w", encoding="utf-8") as f:
            f.write(response.text)

        # Analyze with Playwright if required
        if self.analyze_all:
            self._analyze_with_playwright(url, page_dir)

        # Extract depth from request meta, default to 0 if not present
        depth = response.meta.get('depth', 0)
        logger.info(f"Current page depth: {depth}")

        # Yield nothing as we're using Rules for link extraction
        yield {
            "url": url,
            "title": page_title,
            "depth": depth
        }

    def _analyze_with_playwright(self, url, page_dir):
        """Analyze the page using the Playwright Web Element Analyzer"""
        logger.info(f"Analyzing page with Playwright: {url}")

        try:
            # Import analyzer dynamically if not already imported
            if WebElementAnalyzer is None:
                analyzer_class = import_analyzer()
            else:
                analyzer_class = WebElementAnalyzer
                
            # Create a new analyzer instance
            analyzer = analyzer_class(headless=self.playwright_options.get('headless', True))

            # Run the analysis
            try:
                analyzer.analyze_url(
                    url=url,
                    base_output_path=str(page_dir),
                    generate_all_outputs=self.playwright_options.get('all', False),
                    generate_csv=self.playwright_options.get('csv', False),
                    generate_cucumber=self.playwright_options.get('cucumber', False),
                    generate_report=self.playwright_options.get('html', False),
                    json_only=self.playwright_options.get('json_only', False)
                )
                logger.info(f"Playwright analysis completed for: {url}")

            except Exception as e:
                logger.error(f"Error during Playwright analysis of {url}: {e}")
            finally:
                # Always close the analyzer to release resources
                analyzer.close()

        except Exception as e:
            logger.error(f"Failed to initialize Playwright for {url}: {e}")


def run_scrapy_crawler(start_url, output_dir, max_depth=2, max_pages=10, respect_robots=True,
                       analyze_all=True, headless=True, generate_csv=False, generate_html=False,
                       generate_cucumber=False, generate_all=False):
    """Run the Scrapy crawler with the given parameters"""

    # Ensure output directory exists
    output_path = Path(output_dir)
    output_path.mkdir(parents=True, exist_ok=True)

    # Configure Playwright options
    playwright_options = {
        'headless': headless,
        'csv': generate_csv,
        'html': generate_html,
        'cucumber': generate_cucumber,
        'all': generate_all,
        'json_only': False
    }

    # Configure Scrapy settings
    settings = {
        'BOT_NAME': 'web_element_crawler',
        'ROBOTSTXT_OBEY': respect_robots,
        'CONCURRENT_REQUESTS': 8,  # Adjust concurrency
        'DOWNLOAD_DELAY': 1,  # Add delay between requests
        'COOKIES_ENABLED': True,
        'USER_AGENT': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
        'DEPTH_LIMIT': max_depth,
        'DEPTH_PRIORITY': 1,
        'SCHEDULER_DISK_QUEUE': 'scrapy.squeues.PickleFifoDiskQueue',
        'SCHEDULER_MEMORY_QUEUE': 'scrapy.squeues.FifoMemoryQueue',
        'LOG_LEVEL': 'INFO',
        'LOG_FILE': os.path.join(output_dir, 'scrapy_log.txt')
    }

    # Create the crawler process
    process = CrawlerProcess(settings)

    # Add our spider
    process.crawl(
        WebElementCrawlSpider,
        start_url=start_url,
        max_depth=max_depth,
        max_pages=max_pages,
        respect_robots=respect_robots,
        output_dir=output_dir,
        analyze_all=analyze_all,
        playwright_options=playwright_options
    )

    # Log start of crawl
    logger.info(f"Starting Web Element Crawler with Scrapy")
    logger.info(f"Start URL: {start_url}")
    logger.info(f"Max depth: {max_depth}, Max pages: {max_pages}")

    # Start the crawl
    process.start()

    # Log completion
    logger.info(f"Crawl completed. Results saved to: {output_dir}")

    return output_path


def main():
    """Main entry point for the script"""
    # Try to import the analyzer first
    import_analyzer()
    
    # Parse command line arguments
    parser = argparse.ArgumentParser(description="Scrapy Integration for Web Element Analyzer")

    # Required arguments
    parser.add_argument("-u", "--url", type=str, required=True, help="Start URL to crawl")

    # Optional arguments
    parser.add_argument("-o", "--output", type=str, help="Base output directory")
    parser.add_argument("-d", "--depth", type=int, default=2, help="Maximum crawl depth")
    parser.add_argument("-p", "--max-pages", type=int, default=10, help="Maximum number of pages to crawl")
    parser.add_argument("-r", "--respect-robots", action="store_true", default=True, help="Respect robots.txt")
    parser.add_argument("-a", "--analyze-all", action="store_true", default=True, help="Analyze all crawled pages")
    parser.add_argument("-hl", "--headless", action="store_true", default=True, help="Run browser in headless mode")

    # Output options
    parser.add_argument("--csv", action="store_true", help="Generate CSV output for each page")
    parser.add_argument("--html", action="store_true", help="Generate HTML report for each page")
    parser.add_argument("--cucumber", action="store_true", help="Generate Cucumber steps for each page")
    parser.add_argument("--all", action="store_true", help="Enable all optional outputs (CSV, HTML, Cucumber)")

    args = parser.parse_args()

    # Determine output directory
    if not args.output:
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        output_dir = Path(f"./output_{timestamp}")
    else:
        output_dir = Path(args.output)

    # Run the crawler
    try:
        start_time = time.time()

        output_path = run_scrapy_crawler(
            start_url=args.url,
            output_dir=output_dir,
            max_depth=args.depth,
            max_pages=args.max_pages,
            respect_robots=args.respect_robots,
            analyze_all=args.analyze_all,
            headless=args.headless,
            generate_csv=args.csv,
            generate_html=args.html,
            generate_cucumber=args.cucumber,
            generate_all=args.all
        )

        end_time = time.time()

        # Display final summary
        logger.info("\n" + "=" * 60)
        logger.info(f"Crawl and Analysis Complete!")
        logger.info(f"Start URL: {args.url}")
        logger.info(f"Pages Crawled (max): {args.max_pages}")
        logger.info(f"Crawl Depth: {args.depth}")
        logger.info(f"Total time: {end_time - start_time:.2f} seconds")
        logger.info(f"Results saved to: {output_path}")
        logger.info("=" * 60)

    except Exception as e:
        logger.error(f"Error running crawler: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()