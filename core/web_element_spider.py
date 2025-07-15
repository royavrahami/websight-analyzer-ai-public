#!/usr/bin/env python3
"""
Web Element Analyzer Spider

This spider crawls a website and integrates with the Playwright Web Element Analyzer
to analyze each page that it crawls.
It respects robots.txt, follows depth/breadth
configurations, and creates a unique folder for each analyzed page.

Usage:
    scrapy crawl web_element_spider -a start_url=https://example.com -a max_depth=3 -a max_pages=20
"""

import os
import json
import logging
from pathlib import Path
from urllib.parse import urlparse
from datetime import datetime
import re

import scrapy
from scrapy.spiders import CrawlSpider, Rule
from scrapy.linkextractors import LinkExtractor
from scrapy.exceptions import CloseSpider

# Import Web Element Analyzer
try:
    from playwright_web_elements_analyzer_fixed_v2 import WebElementAnalyzer
except ImportError:
    try:
        from playwright_web_elements_analyzer import WebElementAnalyzer
    except ImportError:
        raise ImportError("Web Element Analyzer not found. Please ensure it's in your Python path.")

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


class WebElementSpider(CrawlSpider):
    """Spider to crawl websites and analyze each page with the Playwright Analyzer"""

    name = 'web_element_spider'

    def __init__(self, start_url=None, max_depth=2, max_pages=10, output_dir=None,
                 *args, analyze_options=None, **kwargs):
        super(WebElementSpider, self).__init__(*args, **kwargs)

        # Validate start URL
        if not start_url:
            raise ValueError("start_url is required")

        self.start_urls = [start_url]
        parsed_url = urlparse(start_url)
        self.allowed_domains = [parsed_url.netloc]

        # Configuration
        self.max_depth = int(max_depth)
        self.max_pages = int(max_pages)
        self.output_dir = output_dir or Path("./results")
        self.results_dir = Path(self.output_dir) / "results"
        self.results_dir.mkdir(parents=True, exist_ok=True)

        # Analysis options
        self.analyze_options = analyze_options or {
            'headless': True,
            'csv': False,
            'html': False,
            'cucumber': False,
            'all': False
        }

        # Crawler state
        self.pages_crawled = 0

        # Define rules - all links within allowed domains that match depth
        self.rules = (
            Rule(
                LinkExtractor(allow_domains=self.allowed_domains),
                callback='parse_item',
                follow=True
            ),
        )

        # Initialize rule compilation
        self._compile_rules()

        # Log initialization
        logger.info(f"Spider initialized: Starting URL: {start_url}")
        logger.info(f"Max depth: {max_depth}, Max pages: {max_pages}")
        logger.info(f"Output directory: {self.results_dir}")

    def parse_start_url(self, response):
        """Parse the start URL"""
        return self.parse_item(response)

    def parse_item(self, response):
        """Process each page and run the analysis"""
        self.pages_crawled += 1

        # Check if we've reached the maximum number of pages
        if self.pages_crawled > self.max_pages:
            logger.info(f"Reached maximum pages limit ({self.max_pages}). Stopping crawl.")
            raise CloseSpider(f"Reached maximum {self.max_pages} pages")

        # Get page information
        url = response.url
        page_title = response.css('title::text').get() or sanitize_filename(url)
        page_name = sanitize_filename(url)

        # Log current page
        logger.info(f"Crawling page {self.pages_crawled}/{self.max_pages}: {url}")
        logger.info(f"Page title: {page_title}")

        # Create a directory for this page
        page_dir = self.results_dir / page_name
        page_dir.mkdir(parents=True, exist_ok=True)

        # Save basic page information
        page_info = {
            "url": url,
            "title": page_title,
            "crawl_time": datetime.now().isoformat(),
            "status": response.status
        }

        with open(page_dir / "page_info.json", "w", encoding="utf-8") as f:
            json.dump(page_info, f, indent=2)

        # Save raw HTML
        with open(page_dir / "raw_page.html", "w", encoding="utf-8") as f:
            f.write(response.text)

        # Run Playwright analysis
        self._analyze_with_playwright(url, page_dir)

        # Yield collected data
        depth = response.meta.get('depth', 0)
        yield {
            "url": url,
            "title": page_title,
            "depth": depth
        }

    def _analyze_with_playwright(self, url, page_dir):
        """Run Playwright Web Element Analyzer on the page"""
        logger.info(f"Starting Playwright analysis for: {url}")

        try:
            # Create analyzer instance
            analyzer = WebElementAnalyzer(headless=self.analyze_options.get('headless', True))

            # Run analysis
            try:
                output_path = analyzer.analyze_url(
                    url=url,
                    base_output_path=str(page_dir),
                    generate_all_outputs=self.analyze_options.get('all', False),
                    generate_csv=self.analyze_options.get('csv', False),
                    generate_cucumber=self.analyze_options.get('cucumber', False),
                    generate_report=self.analyze_options.get('html', False)
                )

                if output_path:
                    logger.info(f"Playwright analysis completed successfully for: {url}")
                else:
                    logger.warning(f"Playwright analysis completed with warnings for: {url}")

            except Exception as e:
                logger.error(f"Error during Playwright analysis of {url}: {e}")

            finally:
                # Cleanup resources
                analyzer.close()

        except Exception as e:
            logger.error(f"Failed to initialize Playwright analyzer for {url}: {e}")