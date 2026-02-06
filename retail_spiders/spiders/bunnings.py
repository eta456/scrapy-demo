import math
from scrapy.loader import ItemLoader
from retail_spiders.items import ProductItem
import scrapy
import json

class BunningsSpider(scrapy.Spider):
    name = "impersonate"
    allowed_domains = ["bunnings.com.au"] 
    
    custom_settings = {
        'User-Agent': None,
        'TWISTED_REACTOR': 'twisted.internet.asyncioreactor.AsyncioSelectorReactor',

        'DOWNLOAD_HANDLERS': {
            "http": "scrapy_impersonate.ImpersonateDownloadHandler",
            "https": "scrapy_impersonate.ImpersonateDownloadHandler",
        },
        'FEEDS': {
            'bunnings.jsonl': {
                'format': 'jsonlines',
                'encoding': 'utf8',
                'overwrite': True, # Replaces file every run
            }
        },
        'LOG_LEVEL': 'INFO',
    }

    async def start(self):
        """        
        Initiates the crawl at a high-level category page (Garden).
        We use `impersonate` (Firefox 135) to mimic a real browser TLS fingerprint.
        """
        url = 'https://www.bunnings.com.au/products/garden'
        yield scrapy.Request(url, 
                             callback=self.get_sub_categories, 
                             meta={'impersonate': 'firefox135', 'page': 1})
    
    def get_sub_categories(self, response):
        """   
        Extracts the site's navigation tree from the Next.js global state.
        This allows us to find all 'Garden' sub-categories dynamically without 
        hardcoding URLs.
        """
        # Extract the hydration state (Raw JSON)
        next_data = response.xpath('//script[@id="__NEXT_DATA__"]/text()').get()
        if not next_data:
            return self.logger.error("No __NEXT_DATA__ script tag found on the page")
        
        data = json.loads(next_data)
        root_categories = data['props']['pageProps']['initialState']['global']['globalData']['navigation']
        for category in root_categories['levels']:
            if category.get('workShopCategory', '') == 'Garden':
                sub_categories = category['levels']
                self.logger.info(f'Found {len(sub_categories)} categories under {category["workShopCategory"]}')
                for sub_category in sub_categories:
                    self.logger.info(f"Found {sub_category['displayName']} sub-category with code: {sub_category['code']}")
                    # Construct the URL for the sub-category
                    # [1:] removes the leading '/' if internalPath is absolute (e.g. /products/...)
                    # We append ?page=1 to start the pagination sequence cleanly.
                    url_path = sub_category['internalPath'][1:] + '?page=1'
                    yield response.follow(url_path, 
                                         callback=self.parse, 
                                         meta={'impersonate': 'firefox135', 'page': 1, 'category': sub_category['displayName']})

    def parse(self, response):
        """        
        This method handles both extracting products from the current page's JSON
        and calculating if further pages need to be crawled.
        """
        next_data = response.xpath('//script[@id="__NEXT_DATA__"]/text()').get()
        if not next_data:
            return self.logger.error("No __NEXT_DATA__ script tag found on the page")

        data = json.loads(next_data)
        # Locate the search results within the state
        props = data['props']['pageProps']['initialState']['global']
        search_data = props['searchResults']['data']
        
        # Get total and products and pagination info
        total_count = search_data['totalCount']
        items_per_page = int(props['globalData']['globalConfigData']['searchConfig']['global']['numberOfSearchResults'])
        total_pages = math.ceil(total_count / items_per_page)
        self.logger.info(f"{response.meta['category']} Page {response.meta['page']}/{total_pages} - {total_count} total products")

        # Navigate through the JSON structure to find product data
        product_data = props['searchResults']['data']['results']
        for product in product_data:
            yield self.parse_product(product['raw'], response)
        
        current_page = response.meta.get('page', 1)
        # If this is Page 1, generate requests for ALL other pages at once to speed up the crawl
        if current_page == 1:
            self.logger.info(f"Exploding pagination: Generating requests for {total_pages-1} pages.")
            
            for page in range(2, total_pages + 1):
                # Reconstruct URL for specific page
                base_url = response.url.split('?')[0]
                next_url = f"{base_url}?page={p}"
                
                yield scrapy.Request(next_url, 
                                     callback=self.parse, 
                                     meta={'impersonate': 'firefox135', 'page': page}
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

        