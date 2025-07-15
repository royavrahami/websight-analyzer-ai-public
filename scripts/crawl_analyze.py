#!/usr/bin/env python3
"""
Crawl & Analyze - Web Element Analyzer with Scrapy Crawler

This script combines Scrapy's crawling capabilities with the Playwright Web Element Analyzer.
It crawls websites following depth/breadth configurations and analyzes each page.

Usage:
    python crawl_analyze.py <url> [options]

Options:
    --depth DEPTH         Maximum crawl depth (default: 2)
    --max-pages PAGES     Maximum number of pages to crawl (default: 10)
    --output DIR          Output directory for results (default: ./results_TIMESTAMP)
    --no-robots           Don't respect robots.txt
    --headless            Run browser in headless mode (default)
    --no-headless         Run browser with GUI
    --csv                 Generate CSV reports
    --html                Generate HTML reports
    --cucumber            Generate Cucumber step definitions
    --all                 Generate all report types
    --json-only           Only generate JSON data (faster)

Example:
    python crawl_analyze.py https://example.com --depth 3 --max-pages 20 --all
"""

import os
import sys
import argparse
import logging
import time
from pathlib import Path
from datetime import datetime
from scrapy.crawler import CrawlerProcess
from scrapy.utils.project import get_project_settings
import json

# Fix encoding issues for Windows
import io

if os.name == 'nt':  # Windows
    try:
        sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')
        sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding='utf-8', errors='replace')
    except Exception as e:
        print(f"Warning: Could not set UTF-8 encoding: {e}")

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s [%(levelname)s] %(message)s',
    handlers=[
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

# Try to import the spider
try:
    # First check the local spiders directory
    sys.path.append(os.path.join(os.path.dirname(os.path.abspath(__file__)), 'spiders'))
    from web_element_spider import WebElementSpider
except ImportError:
    try:
        # Fall back to looking in the current directory
        from web_element_spider import WebElementSpider
    except ImportError:
        print("Error: Spider module 'web_element_spider.py' not found.")
        print("Please ensure it's in ./spiders/ directory or the current directory.")
        sys.exit(1)


def run_crawler(start_url, output_dir, max_depth=2, max_pages=10, respect_robots=True,
                headless=True, csv=False, html=False, cucumber=False, all_reports=False, json_only=False):
    """Run the Scrapy crawler with specified options"""

    # Ensure output directory exists
    output_path = Path(output_dir)
    output_path.mkdir(parents=True, exist_ok=True)

    # Log file setup
    log_file = output_path / "crawl_log.txt"
    file_handler = logging.FileHandler(log_file)
    file_handler.setFormatter(logging.Formatter('%(asctime)s [%(levelname)s] %(message)s'))
    logger.addHandler(file_handler)

    # Analysis options
    analyze_options = {
        'headless': headless,
        'csv': csv,
        'html': html,
        'cucumber': cucumber,
        'all': all_reports,
        'json_only': json_only
    }

    # Scrapy settings
    settings = {
        'BOT_NAME': 'web_element_analyzer',
        'ROBOTSTXT_OBEY': respect_robots,
        'CONCURRENT_REQUESTS': 8,
        'DOWNLOAD_DELAY': 1,  # 1 second delay between requests
        'COOKIES_ENABLED': True,
        'USER_AGENT': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
        'DEPTH_LIMIT': max_depth,
        'DEPTH_PRIORITY': 1,
        'SCHEDULER_DISK_QUEUE': 'scrapy.squeues.PickleFifoDiskQueue',
        'SCHEDULER_MEMORY_QUEUE': 'scrapy.squeues.FifoMemoryQueue',
        'LOG_LEVEL': 'INFO',
        'LOG_FILE': str(output_path / 'scrapy_log.txt')
    }

    # Start crawling
    logger.info(f"Starting crawl from: {start_url}")
    logger.info(f"Output directory: {output_path}")
    logger.info(f"Max depth: {max_depth}, Max pages: {max_pages}")
    logger.info(f"Respect robots.txt: {respect_robots}")

    try:
        # Create crawler process
        process = CrawlerProcess(settings)

        # Add spider to the process
        process.crawl(
            WebElementSpider,
            start_url=start_url,
            max_depth=max_depth,
            max_pages=max_pages,
            output_dir=output_dir,
            analyze_options=analyze_options
        )

        # Start the crawl process (this blocks until crawling is finished)
        process.start()

        logger.info("Crawl and analysis completed successfully")
        return True, output_path

    except Exception as e:
        logger.error(f"Error during crawl process: {e}")
        return False, output_path


def _generate_ai_summary(raw_dir, analysis_dir, summary_dir):
    """Generate an AI summary of the webpage content using comprehensive data analysis (English only)"""
    try:
        print("🤖 Starting AI-powered analysis of webpage data...")

        # ... (Load files and data - as in your code)

        # Load enhanced elements (main analysis file)
        element_insights = []
        element_stats = {"interactive": 0, "content": 0, "forms": 0, "structural": 0, "total": 0}
        if os.path.exists(enhanced_elements_file):
            try:
                with open(enhanced_elements_file, "r", encoding="utf-8") as f:
                    elements_data = json.load(f)
                    if isinstance(elements_data, dict):
                        for category, elements in elements_data.items():
                            if isinstance(elements, list):
                                count = len(elements)
                                element_stats[category] = count
                                element_stats["total"] += count
                                for element in elements[:5]:
                                    if isinstance(element, dict) and element.get("description"):
                                        element_insights.append({
                                            "category": category,
                                            "description": element.get("description", ""),
                                            "tag": element.get("tagName", ""),
                                            "text": element.get("text", "")[:100]
                                        })
            except Exception as e:
                print(f"⚠️ Error loading enhanced elements: {e}")

        # ... (Continue code - creating summary, saving, HTML reports etc.)

    except Exception as e:
        print(f"⚠️ Error generating AI summary: {e}")
        import traceback
        traceback.print_exc()
        # Fallback summary
        try:
            error_summary = {
                "page_title": "Analysis Error",
                "generation_time": datetime.now().isoformat(),
                "ai_powered": False,
                "summary": f"Error generating AI summary: {str(e)}",
                "error": str(e)
            }
            with open(os.path.join(summary_dir, "ai_summary.json"), "w", encoding="utf-8") as f:
                json.dump(error_summary, f, indent=2, ensure_ascii=False)
        except Exception as save_error:
            print(f"Failed to save error summary: {save_error}")


def main():
    """Main entry point"""
    parser = argparse.ArgumentParser(description="Crawl websites and analyze each page with Playwright")

    # Required arguments
    parser.add_argument("url", help="Starting URL to crawl")

    # Optional arguments
    parser.add_argument("--depth", type=int, default=2, help="Maximum crawl depth (default: 2)")
    parser.add_argument("--max-pages", type=int, default=10, help="Maximum number of pages to crawl (default: 10)")
    parser.add_argument("--output", type=str, help="Output directory for results (default: ./results_TIMESTAMP)")
    parser.add_argument("--no-robots", action="store_true", help="Don't respect robots.txt")
    parser.add_argument("--headless", action="store_true", default=True, help="Run browser in headless mode (default)")
    parser.add_argument("--no-headless", action="store_false", dest="headless", help="Run browser with GUI")

    # Report options
    parser.add_argument("--csv", action="store_true", help="Generate CSV reports")
    parser.add_argument("--html", action="store_true", help="Generate HTML reports")
    parser.add_argument("--cucumber", action="store_true", help="Generate Cucumber step definitions")
    parser.add_argument("--all", action="store_true", help="Generate all report types")
    parser.add_argument("--json-only", action="store_true", help="Only generate JSON data (faster)")

    args = parser.parse_args()

    # Determine output directory
    if not args.output:
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        output_dir = f"./results_{timestamp}"
    else:
        output_dir = args.output

    # Run the crawler
    start_time = time.time()

    success, output_path = run_crawler(
        start_url=args.url,
        output_dir=output_dir,
        max_depth=args.depth,
        max_pages=args.max_pages,
        respect_robots=not args.no_robots,
        headless=args.headless,
        csv=args.csv,
        html=args.html,
        cucumber=args.cucumber,
        all_reports=args.all,
        json_only=args.json_only
    )

    end_time = time.time()

    # Final status message
    if success:
        print("\n" + "=" * 60)
        print(f"Crawl and Analysis Complete!")
        print(f"Start URL: {args.url}")
        print(f"Pages crawled (max): {args.max_pages}")
        print(f"Crawl depth: {args.depth}")
        print(f"Total time: {end_time - start_time:.2f} seconds")
        print(f"Results saved to: {output_path}")
        print("=" * 60)
        sys.exit(0)
    else:
        print("\n" + "=" * 60)
        print(f"Crawl and Analysis encountered errors. Check the logs.")
        print(f"Log files: {output_path}/crawl_log.txt and {output_path}/scrapy_log.txt")
        print("=" * 60)
        sys.exit(1)


if __name__ == "__main__":
    main()