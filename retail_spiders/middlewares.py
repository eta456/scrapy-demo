# Define here the models for your spider middleware
#
# See documentation in:
# https://docs.scrapy.org/en/latest/topics/spider-middleware.html

from scrapy import signals
import logging
from datetime import datetime
from scrapy.downloadermiddlewares.retry import RetryMiddleware

class RetailSpidersSpiderMiddleware:
    """
    A specific middleware to log the health and status of the crawl.
    Separates 'monitoring' logic from 'parsing' logic.
    """

    @classmethod
    def from_crawler(cls, crawler):
        # This method is the entry point for Scrapy to load the middleware
        # We use it to connect specific functions to Scrapy's internal signals
        s = cls()
        crawler.signals.connect(s.spider_opened, signal=signals.spider_opened)
        crawler.signals.connect(s.spider_closed, signal=signals.spider_closed)
        crawler.signals.connect(s.spider_error, signal=signals.spider_error)
        return s

    def spider_opened(self, spider):
        self.start_time = datetime.now()
        logging.info(f"🟢 [SYSTEM] LAUNCH: Spider '{spider.name}' initialized.")
        logging.info(f"📋 [SYSTEM] CONFIG: Job settings loaded. Resume capability: {spider.settings.get('JOBDIR', 'Disabled')}")

    def spider_closed(self, spider, reason):
        end_time = datetime.now()
        duration = end_time - self.start_time
        
        # Access Scrapy's internal stats collector
        stats = spider.crawler.stats.get_stats()
        item_count = stats.get('item_scraped_count', 0)
        request_count = stats.get('downloader/request_count', 0)
        
        logging.info(f"🏁 [SYSTEM] FINISH: Spider '{spider.name}' closed. Reason: {reason.upper()}")
        logging.info(f"⏱️  [SYSTEM] DURATION: {duration}")
        logging.info(f"📊 [SYSTEM] STATS: Scraped {item_count} items from {request_count} requests.")

    def spider_error(self, failure, response, spider):
        # This logs full stack traces if the spider crashes on a specific response
        logging.error(f"⚠️ [SYSTEM] CRITICAL: Exception on {response.url}")
        logging.error(failure.getTraceback())



class SoftBanMiddleware(RetryMiddleware):
    """
    Custom Retry Middleware to catch 'Soft Bans' where the site returns 200 OK
    but the content is actually a block/captcha page.
    """
    
    # Text snippets that indicate a ban
    BAN_SIGNATURES = [
        b"Access Denied",
        b"Pardon Our Interruption",
        b"challenge-platform", # Cloudflare
        b"automated access is prohibited"
    ]

    def process_response(self, request, response, spider):
        # Check if the response matches any ban signatures
        if any(sig in response.body for sig in self.BAN_SIGNATURES):
            reason = 'Soft Ban Detected'
            spider.logger.warning(f"🛡️ SOFT BAN: Retrying {request.url}...")
            
            # Triggers riggers the standard Scrapy retry logic
            return self._retry(request, reason, spider) or response

        # Check for empty JSON responses (common in API scraping)
        if 'application/json' in response.headers.get('Content-Type', b'').decode():
            if not response.body or len(response.body) < 10:
                reason = 'Empty JSON Response'
                return self._retry(request, reason, spider) or response

        return response