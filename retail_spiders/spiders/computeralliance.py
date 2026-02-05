import scrapy
from scrapy.loader import ItemLoader
from retail_spiders.items import ProductItem

class PLEComputers(scrapy.Spider):
    name = "ple"
    custom_settings = {
        # 'USER_AGENT': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/121.0.0.0 Safari/537.36',
        
        # # 2. The Headers (How you behave)
        # 'DEFAULT_REQUEST_HEADERS': {
        #     'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8,application/signed-exchange;v=b3;q=0.7',
        #     'Accept-Language': 'en-AU,en;q=0.9',
        #     'Accept-Encoding': 'gzip, deflate',
        #     'Referer': 'https://www.google.com/', # Pretend you came from Google
        #     'Upgrade-Insecure-Requests': '1',
        #     'Sec-Fetch-Dest': 'document',
        #     'Sec-Fetch-Mode': 'navigate',
        #     'Sec-Fetch-Site': 'cross-site',
        #     'Sec-Fetch-User': '?1',
        #     'Cache-Control': 'max-age=0',
        # },
        
        # 'DOWNLOAD_DELAY': 2, # Slow down slightly to avoid rate limiters
        # 'ROBOTSTXT_OBEY': False,
        'FEEDS': {
            'ple_laptops.jsonl': {
                'format': 'jsonlines',
                'encoding': 'utf8',
                'overwrite': True, # Replaces file every run
            }
        }
    }

    async def start(self):
        yield scrapy.Request(
            "https://www.ple.com.au/Categories/296/Monitors",
            callback=self.parse
        )
    
    def parse(self, response):
        self.logger.info(f"Scanning PLE: {response.url}")

        products = response.css('div.itemGrid2TileStandard ')

        self.logger.info(f"Found {len(products)} products.")

        for card in products:
            l = ItemLoader(item=ProductItem(), selector=card)
            
            l.add_css('name', 'div.itemGrid2TileStandardDescription a::text') 
            l.add_css('price', 'div.itemGrid2TileStandardPrice::text')
            l.add_css('url', 'div.itemGrid2TileStandardDescription a::attr(href)')

            l.add_value('retailer', 'PLE Computers') # Static value since we know the retailer
            
            # Handle URL joining
            item = l.load_item()
            if 'url' in item:
                item['url'] = response.urljoin(item['url'])

            yield item