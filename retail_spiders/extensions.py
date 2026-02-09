import logging
from scrapy import signals
from scrapy.exceptions import NotConfigured

class CircuitBreakerExtension:
    def __init__(self, stats, threshold):
        self.stats = stats
        self.threshold = threshold
        self.items_scraped = 0
    
    @classmethod
    def from_crawler(cls, crawler):
        # Get threshold from settings (default 30% failure rate)
        threshold = crawler.settings.getfloat('CIRCUIT_BREAKER_THRESHOLD', 0.3)
        if not threshold:
            raise NotConfigured
        
        ext = cls(crawler.stats, threshold)
        crawler.signals.connect(ext.item_scraped, signal=signals.item_scraped)
        crawler.signals.connect(ext.spider_idle, signal=signals.spider_idle)
        return ext

    def item_scraped(self, item, spider):
        self.items_scraped += 1

    def spider_idle(self, spider):
        # We check this periodically (e.g., when spider is idle or via a LoopTask)
        # Calculate failure rate
        response_count = self.stats.get_value('downloader/request_count', 0)
        error_count = (
            self.stats.get_value('downloader/response_status_count/403', 0) + 
            self.stats.get_value('downloader/response_status_count/429', 0) +
            self.stats.get_value('downloader/response_status_count/500', 0)
        )
        
        # Only check after a meaningful sample size
        if response_count > 50: 
            failure_rate = error_count / response_count
            
            if failure_rate > self.threshold:
                spider.logger.critical(f"🛑 CIRCUIT BREAKER TRIPPED! Failure rate is {failure_rate:.2%}. Stopping Spider.")
                spider.crawler.engine.close_spider(spider, 'high_failure_rate')