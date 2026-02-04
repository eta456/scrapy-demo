from urllib.parse import urlencode, urlparse
from scrapy.loader import ItemLoader
from retail_spiders.items import ProductItem
import scrapy
import json

class OfficeworksSpider(scrapy.Spider):
    