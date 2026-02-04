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

    """Phase 2: logic step - Check for 'All _phones' etc."""
    def parse_sub_category(self, response):
        # 1. Determine the 'Base' slug from the current URL
        # e.g. .../technology/mobile-phones/apple-iphones -> "apple-iphones"
        path_parts = urlparse(response.url).path.strip("/").split("/")
        # We assume the structure is standard; usually the last part is the slug
        current_category_slug = path_parts[-1]
        
        # 2. Build the Base SEO Path
        # Note: We hardcode the prefix based on our requirement
        base_seo_path = f"technology/mobile-phones/{current_category_slug}"
        final_seo_path = base_seo_path

        # 3. The Logic: Look for a tile/text containing "phones"
        # We look inside h2, h3, or span tags within CategoryTiles on THIS page
        found_match = False
        
        # Find all sub-tiles on this brand page
        sub_tiles = response.xpath('//a[contains(@class, "CategoryTile")]')
        
        for tile in sub_tiles:
            # Get the visible text (e.g., "All iPhones", "iPhone 15", "Chargers")
            text = tile.xpath('.//text()').get()
            
            if text and "phones" in text.lower():
                # LOGIC FOUND: "All iPhones" or similar
                clean_text = text.strip()
                self.logger.info(f"Logic Match Found: '{clean_text}' inside {current_category_slug}")
                
                # eg. Turn "All iPhones" -> "all-iphones"
                sub_slug = clean_text.lower().replace(" ", "-")
                
                # Update the filter path
                final_seo_path = f"{base_seo_path}/{sub_slug}"
                found_match = True
                break # We only need one "All" path, usually the first one
        
        if not found_match:
             self.logger.info(f"No 'phones' sub-tile found. Using base: {base_seo_path}")

        # 4. Switch to API Mode, no longer using follow
        yield self.generate_api_request(final_seo_path, page=0)

    """Phase 3: API Mode - We have the final SEO path, now we call the Algolia API directly to get products"""
    def generate_api_request(self, seo_path, page):
        url = f"https://{self.ALGOLIA_APP_ID}-dsn.algolia.net/1/indexes/*/queries"
        
        params = {
            # Maximise results per page to reduce total requests; we will paginate through them
            "hitsPerPage": "100", 
            "page": str(page),
            # We inject the dynamic path we calculated
            "filters": f'categorySeoPaths:"{seo_path}"'
        }
        # 2. THE PAYLOAD
        payload = {
            "requests": [
                {
                    "indexName": self.INDEX_NAME,
                    "params": urlencode(params)
                }
            ]
        }

        return scrapy.Request(
            url,
            method="POST",
            body=json.dumps(payload),
            callback=self.parse_api,
            # Pass metadata so we know which category/page we are on
            meta={'seo_path': seo_path, 'page': page}

        )

    """Phase 4: Process API Response and paginate if needed"""
    def parse_api(self, response):
        # Get API response and extract products
        data= json.loads(response.body)
        results = data.get("results", [])[0]

        current_page = response.meta.get('page', 0)
        seo_path = response.meta.get('seo_path', 'unknown-category')

        nb_pages = results.get('nbPages', 0)
        hits = results.get('hits', [])
        for hit in hits:
            self.logger.info(f"API ({seo_path} | Pg {current_page}): Found {len(hits)} products")
            # Process each product hit and yield items
            l = ItemLoader(item=ProductItem())
            l.add_value('retailer', 'Officeworks')
            l.add_value('name', hit.get('name'))
            price = hit.get('price', 0)/100
            l.add_value('price', str(price))
            slug = hit.get('urlKeyword')
            l.add_value('url',f'https://www.officeworks.com.au/shop/officeworks/p/{slug}')
            yield l.load_item()

        # Recursively fetch next pages
        if (current_page + 1) < nb_pages:
            yield self.generate_api_request(seo_path, current_page + 1)