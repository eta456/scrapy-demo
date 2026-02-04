from urllib.parse import urlencode, urlparse
from scrapy.loader import ItemLoader
from retail_spiders.items import ProductItem
import scrapy
import json

class OfficeworksSpider(scrapy.Spider):
    name = "officeworks"
    # We need to allow both the main site and the Algolia API domain
    allowed_domains = ["officeworks.com.au", "algolia.net"]  
    
    ALGOLIA_APP_ID = "K535CAAWVE" 
    ALGOLIA_API_KEY = "8a831febe0110932cfa06ff0e2024b4f" 
    ALGOLIA_AGENT = "Algolia for JavaScript (3.35.1); Browser (lite); react (16.14.0); react-instantsearch (5.7.0); JS Helper (2.28.1)"

    custom_settings = {
        'DEFAULT_REQUEST_HEADERS': {
            'Accept': '*/*',
            'x-algolia-application-id': ALGOLIA_APP_ID,
            'x-algolia-api-key': ALGOLIA_API_KEY,
            'x-algolia-agent': ALGOLIA_AGENT,
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36'
        },
        'FEEDS': {
            'officeworks_mobile_phones.jsonl': {
                'format': 'jsonlines',
                'encoding': 'utf8',
                'overwrite': True, # Replaces file every run
            }
        }
    }

    INDEX_NAME = "prod-product-wc-bestmatch-personal" 
    
    """Phase 0: Navigate to the main category page (Mobile Phones) to find all brand tiles"""
    def start_requests(self):
        url = "https://www.officeworks.com.au/shop/officeworks/c/technology/mobile-phones/"
        yield scrapy.Request(url, callback=self.parse_parent_category)

    """Phase 1: Find all Brand tiles (Apple, Samsung, Google, etc.)"""
    def parse_parent_category(self, response):
        self.logger.info(f"Scanning Parent Page: {response.url}")
        
        # Find all Category Tiles
        brand_links = response.xpath('//a[contains(@class, "CategoryTile")]')
        
        for link in brand_links:
            url = link.xpath('./@href').get()
            name = link.xpath('.//h2/text() | .//h3/text()').get()
            
            if url:
                self.logger.info(f"Entering Category: {name}")
                # GO INSIDE the tile to check for 'All X'
                yield response.follow(url, callback=self.parse_sub_category)

   