# Define here the models for your scraped items
#
# See documentation in:
# https://docs.scrapy.org/en/latest/topics/items.html

import scrapy
from itemloaders.processors import TakeFirst, MapCompose

def remove_currency_symbol(value):
    # This function cleans input before it's stored
    if value:
        return value.replace('$', '').replace(',', '').strip()
    return value

class ProductItem(scrapy.Item):
    # define the fields for your item here like:
    # name = scrapy.Field()
    # 1. The Retailer Name (e.g., 'Officeworks') - needed for analysis later
    retailer = scrapy.Field(output_processor=TakeFirst())
    
    # 2. The Product Name (Cleaned)
    name = scrapy.Field(output_processor=TakeFirst())
    
    # 3. The Price (Cleaned and ready for math)
    # MapCompose applies the cleaning function automatically
    price = scrapy.Field(
        input_processor=MapCompose(remove_currency_symbol),
        output_processor=TakeFirst()
    )
    
    # 4. The URL (So you can click through to verify)
    url = scrapy.Field(output_processor=TakeFirst())