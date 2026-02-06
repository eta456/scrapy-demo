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
        }
    }

    async def start(self):
        url = "https://www.bunnings.com.au/products/garden/garden-power-tools?page=1"
        yield scrapy.Request(url, 
                             callback=self.parse, 
                             meta={'impersonate': 'firefox135', 'page': 1})
    
    def parse(self, response):
        next_data = response.xpath('//script[@id="__NEXT_DATA__"]/text()').get()
        if not next_data:
            return self.logger.error("No __NEXT_DATA__ script tag found on the page")

        data = json.loads(next_data)
        props = data['props']['pageProps']['initialState']['global']
        search_data = props['searchResults']['data']
        
        # Get pagination info
        total_count = search_data['totalCount']
        items_per_page = int(props['globalData']['globalConfigData']['searchConfig']['global']['numberOfSearchResults'])
        total_pages = math.ceil(total_count / items_per_page)
        
        self.logger.info(f"Page {response.meta['page']}/{total_pages} - {total_count} total products")

        # Navigate through the JSON structure to find product data
        product_data = props['results']
        for product in product_data:
            yield self.parse_product(product, response)

        # Handle pagination
        next_page = response.meta.get('page', 1) + 1
        if next_page <= total_pages:
            url = f"https://www.bunnings.com.au/products/garden/garden-power-tools?page={next_page}"
            yield scrapy.Request(url, 
                                 callback=self.parse, 
                                 meta={'impersonate': 'firefox135', 'page': next_page})
    
    def parse_product(self, product, response):
        l = ItemLoader(item=ProductItem())
        l.add_value('name', product.get('name', ''))
        l.add_value('price', '$' + str(product.get('price', 0)))
        l.add_value('url', response.urljoin(product.get('productroutingurl', '')))
        l.add_value('retailer', 'Bunnings')
        return l.load_item()

        