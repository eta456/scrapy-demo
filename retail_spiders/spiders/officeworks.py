from urllib.parse import urlencode, urlparse
from scrapy.loader import ItemLoader
from retail_spiders.items import ProductItem
import scrapy
import json

class OfficeworksSpider(scrapy.Spider):
    name = "officeworks"
    allowed_domains = ["officeworks.com.au", "algolia.net"]  
    
    # Algolia Config
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
    }

    INDEX_NAME = "prod-product-wc-bestmatch-personal" 
    
    """Phase 0: Navigate to the main category page (Mobile Phones) to find all brand tiles"""
    async def start(self):
        url = "https://www.officeworks.com.au/shop/officeworks/c/technology/mobile-phones/"
        yield scrapy.Request(url, callback=self.parse_parent_category)

    def parse_parent_category(self, response):
        """
        Find Brand Tiles
        """
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

    def parse_sub_category(self, response):
        """
        Find 'All Phones' tile or fallback to base slug
        Check for 'All _phones.
        """
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
        sub_tiles = response.xpath('//a[contains(@class, "CategoryTile")]')
        found_match = False
                
        for tile in sub_tiles:
            # Get the visible text (e.g., "All iPhones", "iPhone 15", "Chargers")
            text = tile.xpath('.//text()').get()
            if text and "phones" in text.lower():
                # LOGIC FOUND: "All iPhones" or similar
                # eg. Turn "All iPhones" -> "all-iphones"
                sub_slug = text.strip().lower().replace(" ", "-")
                # Update the filter path
                final_seo_path = f"{base_seo_path}/{sub_slug}"
                found_match = True
                # We only need one "All" path, usually the first one
                break
        
        if not found_match:
             self.logger.info(f"No 'phones' sub-tile found. Using base: {base_seo_path}")

        # Switch to API Mode
        yield self.create_algolia_request(final_seo_path, page=0)

    def create_algolia_request(self, seo_path, page):
        """Helper to build the complex Algolia POST request."""
        url = f"https://{self.ALGOLIA_APP_ID}-dsn.algolia.net/1/indexes/*/queries"
        
        params = {
            "hitsPerPage": "100", 
            "page": str(page),
            "filters": f'categorySeoPaths:"{seo_path}"'
        }
        
        payload = {"requests": [{"indexName": self.INDEX_NAME, "params": urlencode(params)}]}
        return scrapy.Request(
            url,
            method="POST",
            body=json.dumps(payload),
            callback=self.parse_api,
            meta={'seo_path': seo_path, 'page': page}
        )
    
    def parse_api(self, response):
        """
        Process API Response and paginate if needed
        """
        data= json.loads(response.body)
        # Algolia returns a list of results (one per request). We sent 1 request.
        try:
            results = data.get("results", [])[0]
        except IndexError:
            return self.logger.error("Empty results list from Algolia")

        hits = results.get('hits', [])
        current_page = response.meta.get('page', 0)
        nb_pages = results.get('nbPages', 0)

        seo_path = response.meta.get('seo_path', 'unknown-category')
        self.logger.info(f"API ({seo_path} | Pg {current_page}): Found {len(hits)} items")

        for hit in hits:
            l = ItemLoader(item=ProductItem())
            l.add_value('retailer', 'Officeworks')
            l.add_value('name', hit.get('name'))
            l.add_value('price', str(hit.get('price', 0) / 100)) # Convert cents to dollars
            l.add_value('url', f"https://www.officeworks.com.au/shop/officeworks/p/{hit.get('urlKeyword')}")
            yield l.load_item()

        # Recursively fetch next pages
        if (current_page + 1) < nb_pages:
            yield self.create_algolia_request(seo_path, current_page + 1)