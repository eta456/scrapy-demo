import math
from scrapy.loader import ItemLoader
from retail_spiders.items import ProductItem
import scrapy
import json

class BunningsSpider(scrapy.Spider):
    name = "impersonate"
    allowed_domains = ["bunnings.com.au"] 
    
    custom_settings = {
        'ROBOTSTXT_OBEY': False,
        'IMPERSONATE': 'firefox135',  # Use the latest Firefox profile for impersonation
    }

    async def start(self):
        """        
        Initiates the crawl at a high-level category page (Garden).
        """
        url = 'https://www.bunnings.com.au/products/garden'
        yield scrapy.Request(url, 
                             callback=self.get_sub_categories, 
                             meta={'impersonate': self.custom_settings['IMPERSONATE'], 'page': 1})
    
    def get_next_data(self, response):
        """Helper to safely extract the __NEXT_DATA__ blob."""
        # Extract the hydration state (Raw JSON)
        raw_json = response.xpath('//script[@id="__NEXT_DATA__"]/text()').get()
        if not raw_json:
            self.logger.error(f"Missing __NEXT_DATA__ on {response.url}")
            return None
        return json.loads(raw_json)
    
    def get_sub_categories(self, response):
        """   
        Extracts the site's navigation tree from the Next.js global state.
        This allows us to find all 'Garden' sub-categories dynamically without 
        hardcoding URLs.
        """
        data = self.get_next_data(response)
        # Navigate JSON Path
        try:
            root_categories_levels = data['props']['pageProps']['initialState']['global']['globalData']['navigation']['levels']
        except KeyError:
            self.logger.error(f"Failed to extract navigation levels from __NEXT_DATA__ on {response.url}")
            return
        for category in root_categories_levels:
            if category.get('workShopCategory', '') == 'Garden':
                sub_categories = category['levels']
                self.logger.info(f'Found {len(sub_categories)} categories under {category["workShopCategory"]}')

                for sub_category in sub_categories:
                    self.logger.info(f"Found {sub_category['displayName']} sub-category with code: {sub_category['code']}")
                    # Clean URL: Remove leading slash + append page param.
                    url_path = sub_category['internalPath'].lstrip('/') + '?page=1'
                    yield response.follow(url_path, 
                                         callback=self.parse, 
                                         meta={'impersonate': self.custom_settings['IMPERSONATE'], 'page': 1, 'category': sub_category['displayName']})

    def parse(self, response):
        """        
        This method handles both extracting products from the current page's JSON
        and calculating if further pages need to be crawled.
        """
        data = self.get_next_data(response)
        if not data: return
        try:
            # Locate search results
            props = data['props']['pageProps']['initialState']['global']
            search_data = props['searchResults']['data']
            product_data = search_data['results']
            
            # Pagination Logic
            total_count = search_data['totalCount']
            items_per_page = int(props['globalData']['globalConfigData']['searchConfig']['global']['numberOfSearchResults'])
            total_pages = math.ceil(total_count / items_per_page)
        except KeyError:
             return self.logger.error("JSON structure changed for Search Results")
        
        self.logger.info(f"{response.meta.get('category')} - Page {response.meta['page']}/{total_pages} - {total_count} items")

        for product in product_data:
            yield self.parse_product(product['raw'], response)
        
        current_page = response.meta.get('page', 1)
        # If we are on Page 1, we calculate ALL future pages and fire requests immediately
        if current_page == 1:
            self.logger.info(f"Exploding pagination: Generating requests for {total_pages-1} pages.")

            base_url = response.url.split('?')[0]
            for page in range(2, total_pages + 1):
                # Reconstruct URL for specific page
                next_url = f"{base_url}?page={p}"
                
                yield scrapy.Request(next_url, 
                                     callback=self.parse, 
                                     meta={'impersonate': self.custom_settings['IMPERSONATE'], 'page': page, 'category': response.meta.get('category')}
                                     )
                                     
    
    def parse_product(self, product, response):
        """
        Helper method to map raw JSON product data to the Scrapy Item.
        """
        l = ItemLoader(item=ProductItem())
        l.add_value('name', product.get('title', ''))
        l.add_value('price', '$' + str(product.get('price', 0)))
        l.add_value('url', response.urljoin(product.get('productroutingurl', '')))
        l.add_value('retailer', 'Bunnings')
        return l.load_item()

        