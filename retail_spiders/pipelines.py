from scrapy.exceptions import DropItem

class QualityAssurancePipeline:
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