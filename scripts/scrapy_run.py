import sys
import argparse
import os
import json
import csv
import requests
from urllib.parse import urljoin
from bs4 import BeautifulSoup  # BeautifulSoup is typically included with requests

class SimpleCrawler:
    def __init__(self, start_urls=None):
        self.start_urls = start_urls or []
        self.visited_urls = set()
        self.results = []

    def parse(self, url):
        if url in self.visited_urls:
            return
        
        self.visited_urls.add(url)
        try:
            response = requests.get(url, timeout=10)
            soup = BeautifulSoup(response.text, 'html.parser')
            
            # Collect data (customize this based on your needs)
            data = {
                'url': url,
                'title': soup.title.string if soup.title else '',
                'links': [urljoin(url, a.get('href')) for a in soup.find_all('a', href=True)]
            }
            self.results.append(data)
            
            # Follow links (you might want to add more conditions)
            for link in data['links']:
                if link not in self.visited_urls:
                    self.parse(link)
                    
        except Exception as e:
            print(f"Error crawling {url}: {str(e)}")

def save_results(results, output_file, format_type):
    if format_type == 'json':
        with open(output_file, 'w', encoding='utf8') as f:
            json.dump(results, f, ensure_ascii=False, indent=2)
    elif format_type == 'csv':
        if results:
            with open(output_file, 'w', encoding='utf8', newline='') as f:
                writer = csv.DictWriter(f, fieldnames=results[0].keys())
                writer.writeheader()
                writer.writerows(results)

def main():
    parser = argparse.ArgumentParser(
        description="Simple web crawler with dynamic configuration."
    )
    parser.add_argument(
        "-u", "--url", type=str, required=True,
        help="Start URL to crawl"
    )
    parser.add_argument(
        "-o", "--output", type=str, default="results.json",
        help="Output file name (e.g. results.json or results.csv)"
    )
    parser.add_argument(
        "-f", "--format", type=str, default="json",
        help="Output format: json/csv (default: json)"
    )
    args = parser.parse_args()

    print(f"Start URL: {args.url}")
    print(f"Output: {args.output} (format: {args.format})")

    crawler = SimpleCrawler(start_urls=[args.url])
    crawler.parse(args.url)
    save_results(crawler.results, args.output, args.format)

if __name__ == "__main__":
    main()