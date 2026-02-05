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

    def start_requests(self):
        url = "https://www.bunnings.com.au/products/garden/garden-power-tools?page=1"
        yield scrapy.Request(url, 
                             callback=self.parse, 
                             meta={'impersonate': 'firefox135'})
    
    def parse(self, response):
        next_data = response.xpath('//script[@id="__NEXT_DATA__"]/text()').get()
        if next_data:
            try:
                data = json.loads(next_data)
                # Navigate through the JSON structure to find product data
                product_data = data['props']['pageProps']['initialState']['global']['searchResults']['data']['results']

                for product in product_data:
                    raw = product.get('raw', {})

                    l = ItemLoader(item=ProductItem())
                    l.add_value('name', raw.get('name', ''))
                    l.add_value('price', '$' + str(raw.get('price', 0)))
                    l.add_value('url', f"https://www.bunnings.com.au{raw.get('productroutingurl', '')}")
                    l.add_value('retailer', 'Bunnings')
                    yield l.load_item()
            except json.JSONDecodeError:
                self.logger.error("Failed to parse NEXT_DATA JSON")
        pass

        