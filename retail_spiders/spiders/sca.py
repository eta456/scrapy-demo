from scrapy.loader import ItemLoader
from retail_spiders.items import ProductItem
import scrapy

class ScaSpider(scrapy.Spider):
    name = "sca"
    allowed_domains = ["supercheapauto.com.au"]
    
    custom_settings = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
        'ROBOTSTXT_OBEY': False,
        'DOWNLOAD_DELAY': 1.5,
        'IMPERSONATE': 'firefox135',  # Use the latest Firefox profile for impersonation
    }

    async def start(self):
        """
        We target the main 'Computer Parts' hub page rather than individual categories.
        This allows the spider to dynamically discover all available sub-categories

        :param self: Description
        """
        # We start at the main PC Parts hub to find all sub-categories.
        url = "https://www.supercheapauto.com.au/4wd-recovery?sz=60"
        yield scrapy.Request(url, callback=self.parse_category, meta={'impersonate': self.custom_settings['IMPERSONATE']})

    def parse_category(self, response):
        """
        This handles both extracting product data 
        and determining if there are more pages to crawl.
        
        :param self: Description
        :param response: Description
        """
        # Retrieve the context passed from the parent page
        # category = response.meta.get('category', 'Unknown')
        # self.logger.info(f"Scanning Category: {category} | URL: {response.url}")
        
        # Find all product tiles
        product_links = response.xpath('//li[contains(@class, "grid-tile")]')
        if not product_links:
             self.logger.warning(f"No products found. Check selectors.")

        self.logger.info(f"Found {len(product_links)} products.")
        
        for card in product_links:
            l = ItemLoader(item=ProductItem(), selector=card)
            
            # Name: Found in <div class="product-name">
            # Clean the title by removing "Go to Product: " prefix if it exists.
            title = card.xpath('.//div[@class="product-name"]/a/@title').get()
            title = title.replace("Go to Product: ", "") if title else None
            l.add_value('name', title)
            # Price: Found in <span class="the-price">
            l.add_xpath('price', './/span[@class="the-price"]/text()')
            # URL: Find the link in the product-name div
            l.add_xpath('url', './/div[@class="product-name"]/a/@href')
            l.add_value('retailer', 'Supercheap Auto')
            
            # Handle URL joining
            item = l.load_item()
            if 'url' in item:
                item['url'] = response.urljoin(item['url'])
                
            yield item
        
        # Looks for next page link in the pagination bar using page-next a class
        next_page = response.xpath('//a[@class="page-next"]/@href').get()
        if next_page:
             # Recursive call to scrape the next page.
             yield response.follow(next_page, callback=self.parse_category, meta=response.meta)
