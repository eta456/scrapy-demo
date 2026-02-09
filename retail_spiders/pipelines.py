from datetime import datetime, timezone
from scrapy.exceptions import DropItem
from itemadapter import ItemAdapter
import pymongo
import logging

class MongoPipeline:
    """
    Handles the persistence layer for the scraping system.
    
    Instead of updating existing records, we insert every scrape as a new document.
    This allows for historical price tracking and trend analysis over time.
    """
    def __init__(self, mongo_uri, mongo_db):
        self.mongo_uri = mongo_uri
        self.mongo_db = mongo_db

    @classmethod
    def from_crawler(cls, crawler):
        """
        Pulls configuration from settings.py.
        This keeps credentials and config out of the code.
        """
        return cls(
            mongo_uri=crawler.settings.get('MONGO_URI'),
            mongo_db=crawler.settings.get('MONGO_DATABASE', 'retailer_data'),
        )

    def open_spider(self, spider):
        """
        Initializes the database connection when the spider starts.
        """
        self.client = pymongo.MongoClient(self.mongo_uri)
        self.db = self.client[self.mongo_db]

         # Dynamic collection name based on spider
        self.collection_name = f'{spider.name}_products' 
        
        # Ensure an index exists on 'name' to make future queries fast.
        self.db[self.collection_name].create_index("name")
        logging.info(f"🔗 MONGO: Connected to DB '{self.mongo_db}' -> Collection '{self.collection_name}'")

    def close_spider(self, spider):
        self.client.close()

    def process_item(self, item, spider):
        adapter = ItemAdapter(item)
        
        # Add timestamp for history tracking
        # Specific UTC timestamp allows us to reconstruct the exact state of the site
        adapter['scraped_at'] = datetime.now(timezone.utc)
        # Add spider name for easier querying
        adapter['spider'] = spider.name

        # Insert into the specific collection for this spider
        self.db[self.collection_name].insert_one(adapter.asdict())
        
        return item

class QualityAssurancePipeline:
    """
    Enforces Data Contracts to ensure no corrupt or invalid data ever reaches the database.
    """
    def process_item(self, item, spider):
        # Critical Field Check
        if not item.get('price'):
            spider.crawler.stats.inc_value('data_quality/missing_price')
            raise DropItem(f"❌ DATA QUALITY: Item {item.get('name')} missing price.")

        # Logic Check (Price must be positive)
        if item['price'] <= 0:
            spider.crawler.stats.inc_value('data_quality/invalid_price')
            raise DropItem(f"❌ DATA QUALITY: Item {item.get('name')} has zero/negative price.")

        return item