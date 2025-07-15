import scrapy


class GenericCrawlerSpider(scrapy.Spider):
    name = "generic_crawler"
    allowed_domains = ["anysite.com"]
    start_urls = ["https://anysite.com"]

    def parse(self, response):
        pass 