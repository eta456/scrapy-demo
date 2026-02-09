import scrapy
from scrapy.loader import ItemLoader
from retail_spiders.items import ProductItem

class PLEComputers(scrapy.Spider):
    name = "ple"
    allowed_domains = ["ple.com.au"]

    custom_settings = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
        'ROBOTSTXT_OBEY': False,
        'DOWNLOAD_DELAY': 1.5,
        'IMPERSONATE': 'firefox135',  # Use the latest Firefox profile for impersonation
    }

    async def start(self):
        """
        Initiates the crawl at the 'All Categories' hub page. This approach ensures 
        we discover all current categories dynamically rather than hardcoding URLs.

        """
        url = 'https://www.ple.com.au/CategoryGroups/11/All-Categories'
        yield scrapy.Request(
            url=url,
            callback=self.get_all_categories,
            meta={'impersonate': self.custom_settings['IMPERSONATE']}
        )
    
    def get_all_categories(self, response):
        """
        Parses the main category hub to extract links to specific product listing pages.
        """
        self.logger.info(f"Scanning PLE Categories: {response.url}")
        # Target the outer wrapper of each category card
        categories = response.css('div.categoryGroupCategoryItemInner')
        for category in categories:
            # Access index [0] to get the FIRST <a> tag inside the wrapper.
            # This ensures we get the main 'Parent Category' link and ignore any 
            # smaller 'Sub-Category' links that might exist further down in the HTML.
            category_url = category.css('a::attr(href)')[0].get()
            yield scrapy.Request(
                url=response.urljoin(category_url),
                callback=self.parse_category,
                meta={'impersonate': self.custom_settings['IMPERSONATE']}
            )
    
    def parse_category(self, response):
        """
        Parses a specific category page to extract product details using CSS selectors.
        """
        self.logger.info(f"Scanning PLE: {response.url}")

        # Locate the specific product tiles in the grid
        products = response.css('div.itemGrid2TileStandard ')

        self.logger.info(f"Found {len(products)} products.")

        for card in products:
            l = ItemLoader(item=ProductItem(), selector=card)
            # Name: Inside the description div -> anchor tag
            l.add_css('name', 'div.itemGrid2TileStandardDescription a::text') 
            # Price: Directly inside the price div
            l.add_css('price', 'div.itemGrid2TileStandardPrice::text')
            # URL: Extracted from the href of the description link
            l.add_css('url', 'div.itemGrid2TileStandardDescription a::attr(href)')

            l.add_value('retailer', 'PLE Computers') # Static value since we know the retailer
            
            # Handle URL joining
            item = l.load_item()
            if 'url' in item:
                # Convert relative path (/products/...) to absolute URL (https://ple.com.au/...)
                item['url'] = response.urljoin(item['url'])

            yield item