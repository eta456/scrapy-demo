from scrapy.loader import ItemLoader
from retail_spiders.items import ProductItem
import scrapy

class UmartSpider(scrapy.Spider):
    name = "umart"
    allowed_domains = ["umart.com.au"]
    
    custom_settings = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
        'ROBOTSTXT_OBEY': False,
        'DOWNLOAD_DELAY': 1.5,
    }

    async def start(self):
        """
        We target the main 'Computer Parts' hub page rather than individual categories.
        This allows the spider to dynamically discover all available sub-categories

        :param self: Description
        """
        # We start at the main PC Parts hub to find all sub-categories.
        url = "https://www.umart.com.au/pc-parts-1"
        yield scrapy.Request(url, callback=self.parse_top_level)
    
    def parse_top_level(self, response):
        """
        This method parses the hub page to find links to specific product categories.
        
        :param self: Description
        :param response: Previous response
        """
        self.logger.info(f"Scanning Top Categories: {response.url}")

        # Scope to the container that holds the main categories
        category_container = response.xpath('//div[contains(@class, "top_categories")]')
        category_links = category_container.xpath('.//div[contains(@class, "cat_name")]/a')

        for category in category_links:
            url = category.xpath('@href').get()
            category_name = category.xpath('text()').get()
            self.logger.info(f"Found Category: {category_name} | URL: {url}")
            if url:
                # Use response.urljoin to ensure the domain is attached.
                url = response.urljoin(url) + '?mystock=1-7-6&sort=salenum&order=ASC&pagesize=3'
                # Pass the category name down to the next parser
                yield response.follow(url, callback=self.parse_category, meta={'category': category_name})

    def parse_category(self, response):
        """
        This handles both extracting product data 
        and determining if there are more pages to crawl.
        
        :param self: Description
        :param response: Description
        """
        # Retrieve the context passed from the parent page
        category = response.meta.get('category', 'Unknown')
        self.logger.info(f"Scanning Category: {category} | URL: {response.url}")
        
        # Find all product tiles
        product_links = response.xpath('//li[contains(@class, "goods_info")]')
        if not product_links:
             self.logger.warning(f"No products found for {category}. Check selectors.")

        self.logger.info(f"Found {len(product_links)} products.")
        
        for card in product_links:
            l = ItemLoader(item=ProductItem(), selector=card)
            
            # Name: Found in <span itemprop="name">
            l.add_xpath('name', './/span[@itemprop="name"]/text()') 
            # Price: Found in <span itemprop="price">
            l.add_xpath('price', './/span[@itemprop="price"]/text()')
            # URL: Find the link in the goods_name div
            l.add_xpath('url', './/div[@class="goods_name"]/a/@href')
            l.add_value('retailer', 'Umart')
            
            # Handle URL joining
            item = l.load_item()
            if 'url' in item:
                item['url'] = response.urljoin(item['url'])
                
            yield item
        
        # Looks for the specific '>' text in the pagination bar
        next_page = response.xpath('//ul[contains(@class, "page")]//li/a[contains(text(), ">")]/@href').get()
        if next_page:
             # Recursive call to scrape the next page.
             yield response.follow(next_page, callback=self.parse_category, meta=response.meta)
