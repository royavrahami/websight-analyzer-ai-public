#!/usr/bin/env python3
"""
Working Crawler with Enhanced MCP Master Automation Integration - UPDATED VERSION
"""

import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(os.path.dirname(__file__)), 'core'))

import requests
from bs4 import BeautifulSoup
from urllib.parse import urljoin, urlparse
import time
from pathlib import Path
import json
from datetime import datetime
import argparse
import asyncio
import subprocess

def working_crawl_with_analysis(start_url, output_dir, max_pages=10, max_depth=5, headless=True):
    """Working crawler that crawls multiple pages and runs full Enhanced MCP analysis on each"""
    print(f"🚀 Starting ENHANCED crawler from: {start_url}")
    print(f"📄 Max pages: {max_pages}, Max depth: {max_depth}")
    print(f"📁 Output: {output_dir}")
    print("=" * 80)
    
    # Try to import basic Playwright analyzer at function start
    WebElementAnalyzer = None
    basic_analyzer_available = False
    try:
        sys.path.append(os.path.dirname(os.path.dirname(__file__)))
        from core.playwright_web_elements_analyzer import WebElementAnalyzer
        basic_analyzer_available = True
        print("✅ Basic Playwright analyzer imported successfully")
    except ImportError:
        print("⚠️ Basic Playwright analyzer not available")
    
    # Create output directory
    output_path = Path(output_dir)
    output_path.mkdir(parents=True, exist_ok=True)
    
    visited = set()
    to_visit = [(start_url, 0)]  # (url, depth)
    crawled_pages = []
    
    session = requests.Session()
    session.headers.update({
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36'
    })
    
    # Check for Enhanced MCP Master Automation
    enhanced_mcp_script = Path("enhanced_mcp_master_automation.py")
    if not enhanced_mcp_script.exists():
        # Try relative path from scripts directory
        enhanced_mcp_script = Path("../enhanced_mcp_master_automation.py")
        if not enhanced_mcp_script.exists():
            enhanced_mcp_script = Path(os.path.join(os.path.dirname(os.path.dirname(__file__)), "enhanced_mcp_master_automation.py"))
    
    enhanced_mcp_available = enhanced_mcp_script.exists()
    
    if enhanced_mcp_available:
        print("✅ Enhanced MCP Master Automation found - Full analysis will be performed!")
    
    if not enhanced_mcp_available and not basic_analyzer_available:
        print("⚠️ No analysis engines available - will save basic info only")
    
    page_num = 0
    while to_visit and page_num < max_pages:
        current_url, depth = to_visit.pop(0)
        
        if current_url in visited or depth > max_depth:
            continue
        
        page_num += 1
        
        try:
            print(f"\n🔍 Crawling page {page_num}/{max_pages}: {current_url}")
            print(f"   📊 Depth: {depth}")
            
            response = session.get(current_url, timeout=15)
            if response.status_code != 200:
                print(f"❌ Error {response.status_code}")
                continue
                
            visited.add(current_url)
            
            # Parse HTML for links
            soup = BeautifulSoup(response.content, 'html.parser')
            title_tag = soup.find('title')
            page_title = title_tag.get_text().strip() if title_tag else 'Unknown Title'
            
            print(f"   ✅ Title: {page_title[:60]}...")
            
            page_info = {
                'url': current_url,
                'title': page_title,
                'depth': depth,
                'crawl_time': datetime.now().isoformat(),
                'status_code': response.status_code
            }
            
            # Create page directory with enhanced naming
            safe_url = urlparse(current_url).path.replace('/', '_').strip('_')
            if not safe_url:
                safe_url = urlparse(current_url).netloc.replace('.', '_')
            
            page_name = f"page_{page_num:03d}_{safe_url}"
            if len(page_name) > 100:  # Limit filename length
                page_name = f"page_{page_num:03d}_{hash(current_url) % 10000:04d}"
            
            page_dir = output_path / page_name
            page_dir.mkdir(parents=True, exist_ok=True)
            
            # Save basic page info
            with open(page_dir / "page_info.json", "w", encoding="utf-8") as f:
                json.dump(page_info, f, indent=2, ensure_ascii=False)
            
            # Save raw HTML
            with open(page_dir / "raw_page.html", "w", encoding="utf-8") as f:
                f.write(response.text)
            
            # ALWAYS run basic Playwright analysis first (to ensure all basic files are created)
            basic_analysis_success = False
            analysis_dir_path = None
            if basic_analyzer_available and WebElementAnalyzer is not None:
                print(f"   🔍 Running basic Playwright analysis...")
                try:
                    analyzer = WebElementAnalyzer(headless=headless)
                    # The analyzer creates its own sub-directory, capture its path
                    result_path = analyzer.analyze_url(
                        url=current_url,
                        base_output_path=str(page_dir), # Base for this page
                        generate_all_outputs=True,
                        generate_csv=True,
                        generate_cucumber=True,
                        generate_report=True,
                        json_only=False
                    )
                    analyzer.close()
                    print(f"   ✅ Basic Playwright analysis completed!")
                    basic_analysis_success = True
                    analysis_dir_path = result_path # This is the path to the 'analysis_...' folder
                    page_info['analysis_type'] = 'basic_playwright'
                        
                except Exception as e:
                    print(f"   ❌ Basic Playwright analysis failed: {e}")
                    page_info['analysis_type'] = 'failed'
            
            # THEN run Enhanced MCP Master Automation if available (to add advanced features)
            if enhanced_mcp_available and basic_analysis_success and analysis_dir_path:
                print(f"   🚀 Running Enhanced MCP Master Automation (in same directory)...")
                try:
                    # Run Enhanced MCP, targeting the *exact same directory* the basic analysis used
                    success = _run_enhanced_mcp_for_page(current_url, str(analysis_dir_path), headless, enhanced_mcp_script)
                    
                    if success:
                        print(f"   ✅ Enhanced MCP analysis completed successfully!")
                        page_info['analysis_directory'] = str(analysis_dir_path)
                        page_info['analysis_type'] = 'enhanced_mcp_full'  # Both basic and enhanced
                    else:
                        print(f"   ⚠️ Enhanced MCP analysis had issues")
                        # Keep type as 'basic_playwright' as the basic part succeeded
                        
                except Exception as e:
                    print(f"   ❌ Enhanced MCP analysis failed: {e}")

            # Always save updated page info
            with open(page_dir / "page_info.json", "w", encoding="utf-8") as f:
                json.dump(page_info, f, indent=2, ensure_ascii=False)
            
            crawled_pages.append(page_info)
            
            # Find new links for next depth
            if depth < max_depth:
                links = soup.find_all('a', href=True)
                base_domain = urlparse(start_url).netloc
                
                found_links = 0
                for link in links:
                    href = link.get('href')
                    if href:
                        absolute_url = urljoin(current_url, href)
                        parsed = urlparse(absolute_url)
                        
                        # Only same domain and not visited
                        if (parsed.netloc == base_domain and 
                            absolute_url not in visited and 
                            not any(absolute_url == url for url, _ in to_visit)):
                            
                            to_visit.append((absolute_url, depth + 1))
                            found_links += 1
                            
                            if found_links <= 2:
                                print(f"   🔗 Found link: {absolute_url}")
                
                print(f"   📊 Added {found_links} new links to queue")
            
            # Small delay
            time.sleep(0.5)
            
        except Exception as e:
            print(f"❌ Error crawling {current_url}: {e}")
            continue
    
    # Create comprehensive summary
    summary = {
        'start_url': start_url,
        'total_pages_crawled': len(crawled_pages),
        'max_pages_requested': max_pages,
        'max_depth': max_depth,
        'crawl_completed_at': datetime.now().isoformat(),
        'enhanced_mcp_available': enhanced_mcp_available,
        'analysis_summary': {
            'enhanced_mcp_full': len([p for p in crawled_pages if p.get('analysis_type') == 'enhanced_mcp_full']),
            'enhanced_mcp_only': len([p for p in crawled_pages if p.get('analysis_type') == 'enhanced_mcp_only']),
            'basic_playwright': len([p for p in crawled_pages if p.get('analysis_type') == 'basic_playwright']),
            'basic_info_only': len([p for p in crawled_pages if p.get('analysis_type') == 'basic_info_only']),
            'failed': len([p for p in crawled_pages if p.get('analysis_type') == 'failed'])
        },
        'pages': crawled_pages
    }
    
    with open(output_path / "crawl_summary.json", "w", encoding="utf-8") as f:
        json.dump(summary, f, indent=2, ensure_ascii=False)
    
    # Create comprehensive README
    readme_content = f"""# Enhanced Web Crawling Analysis Report

## Crawl Configuration
- **Start URL:** {start_url}
- **Pages Crawled:** {len(crawled_pages)} / {max_pages} requested
- **Max Depth:** {max_depth}
- **Completed:** {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}

## Analysis Summary
- **Full Analysis (Basic + Enhanced):** {summary['analysis_summary']['enhanced_mcp_full']} pages
- **Enhanced MCP Only:** {summary['analysis_summary']['enhanced_mcp_only']} pages  
- **Basic Playwright Only:** {summary['analysis_summary']['basic_playwright']} pages  
- **Basic Info Only:** {summary['analysis_summary']['basic_info_only']} pages
- **Failed Analysis:** {summary['analysis_summary']['failed']} pages

## Features Generated (for Enhanced MCP pages)
- 🧪 **Test Suites** (API, UI, Functional, GUI, E2E)
- 📊 **Test Summary & Metadata**
- ♿ **MCP Accessibility Analysis**
- 🕵️ **API Hunter Network Analysis**
- 📈 **AI-Generated Summaries**
- 🗂️ **Complete Selector Libraries** (CSS, XPath, A11y)
- 📸 **Screenshots & Visual Maps**
- 🐍 **Ready-to-use Page Objects & Test Templates**

## Directory Structure
Each crawled page is stored in a `page_XXX_` directory containing:
- `page_info.json` - Basic page metadata
- `raw_page.html` - Original page HTML
- `analysis_DOMAIN_TIMESTAMP/` - Full analysis results from both basic and enhanced analyzers.

## Page Details
"""
    
    for i, page in enumerate(crawled_pages, 1):
        analysis_type_desc = {
            'enhanced_mcp_full': '✅ Full Analysis (Basic + Enhanced MCP)',
            'enhanced_mcp_only': '🎯 Enhanced MCP Only',
            'basic_playwright': '🔧 Basic Playwright Analysis', 
            'basic_info_only': 'ℹ️ Basic Info Only',
            'failed': '❌ Analysis Failed'
        }.get(page.get('analysis_type', 'unknown'), '❓ Unknown')
        
        readme_content += f"""
### {i}. {page['title'][:50]}...
- **URL:** {page['url']}
- **Depth:** {page['depth']}
- **Analysis:** {analysis_type_desc}
- **Directory:** page_{i:03d}_*
"""
    
    readme_content += """

## Usage Instructions
1. **View Results:** Open any `analysis_*/analysis_report.html` for interactive dashboard
2. **Run Tests:** Use generated `.py` test files with Playwright
3. **API Tests:** Check `generated_tests/API/` for captured network analysis
4. **Page Objects:** Import `.py` page object classes for automation

## Support
For issues or questions, refer to the main project documentation.
"""
    
    with open(output_path / "README.md", "w", encoding="utf-8") as f:
        f.write(readme_content)
    
    print("\n" + "=" * 80)
    print("📊 ENHANCED CRAWL SUMMARY")
    print("=" * 80)
    for i, page in enumerate(crawled_pages, 1):
        analysis_icon = {
            'enhanced_mcp_full': '✅',
            'basic_playwright': '🔧', 
            'basic_playwright_fallback': '⚠️',
            'basic_info_only': 'ℹ️',
            'failed': '❌'
        }.get(page.get('analysis_type', 'unknown'), '❓')
        
        print(f"{i:2d}. {analysis_icon} {page['url']}")
        print(f"     Title: {page['title'][:50]}...")
        print(f"     Depth: {page['depth']} | Analysis: {page.get('analysis_type', 'unknown')}")
        if page.get('analysis_directory'):
            print(f"     📁 Analysis: {Path(page['analysis_directory']).name}")
        print()
    
    print(f"✅ Successfully crawled {len(crawled_pages)} pages!")
    print(f"🎯 Enhanced MCP analysis: {summary['analysis_summary']['enhanced_mcp_full'] + summary['analysis_summary']['enhanced_mcp_only']} pages")
    print(f"🔧 Basic analysis: {summary['analysis_summary']['enhanced_mcp_full'] + summary['analysis_summary']['basic_playwright']} pages")
    print(f"📁 Results saved to: {output_path}")
    return output_path


def _run_enhanced_mcp_for_page(url, analysis_dir, headless, enhanced_mcp_script_path):
    """Run Enhanced MCP Master Automation for a single page"""
    try:
        # Build command for Enhanced MCP Master Automation
        cmd = [
            sys.executable,
            str(enhanced_mcp_script_path),
            url,
            "--output-dir", analysis_dir,
            "--full-analysis"
        ]
        
        if headless:
            cmd.append("--headless")
        
        # Run the Enhanced MCP process
        process = subprocess.Popen(
            cmd,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True,
            cwd=str(enhanced_mcp_script_path.parent)  # Set working directory
        )
        
        # Wait for completion with timeout
        try:
            stdout, stderr = process.communicate(timeout=120)  # 2 minute timeout per page
            
            if process.returncode == 0:
                return True
            else:
                if stderr:
                    print(f"   ❌ Enhanced MCP stderr: {stderr[:200]}...")
                return False
                
        except subprocess.TimeoutExpired:
            print(f"   ⏰ Enhanced MCP analysis timed out after 2 minutes")
            process.kill()
            return False
            
    except Exception as e:
        print(f"   ❌ Error running Enhanced MCP: {e}")
        return False


def main():
    parser = argparse.ArgumentParser(description="Working Web Crawler with Playwright Analysis")
    parser.add_argument("-u", "--url", required=True, help="Start URL to crawl")
    parser.add_argument("-o", "--output", required=True, help="Output directory")
    parser.add_argument("-p", "--max-pages", type=int, default=10, help="Maximum pages to crawl")
    parser.add_argument("-d", "--depth", type=int, default=5, help="Maximum crawl depth")
    parser.add_argument("--headless", action="store_true", default=True, help="Run headless browser")
    
    args = parser.parse_args()
    
    working_crawl_with_analysis(
        start_url=args.url,
        output_dir=args.output,
        max_pages=args.max_pages,
        max_depth=args.depth,
        headless=args.headless
    )

if __name__ == "__main__":
    main()
