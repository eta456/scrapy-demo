# GLOBAL SETTINGS
BOT_NAME = 'retail_spiders'
SPIDER_MODULES = ['retail_spiders.spiders']
NEWSPIDER_MODULE = 'retail_spiders.spiders'

DOWNLOADER_MIDDLEWARES = {
    # Disable default RetryMiddleware if you want to fully replace it, 
    # OR just put yours at a higher priority (lower number)
    'scrapy.downloadermiddlewares.retry.RetryMiddleware': None, 
    'retail_spiders.middlewares.SoftBanMiddleware': 550,
}

SPIDER_MIDDLEWARES = {
   'retail_spiders.middlewares.RetailSpidersSpiderMiddleware': 500,
}

EXTENSIONS = {
    'retail_spiders.extensions.CircuitBreakerExtension': 500,
}
# Stop if >35% requests fail
CIRCUIT_BREAKER_THRESHOLD = 0.35  

ITEM_PIPELINES = {
   'retail_spiders.pipelines.QualityAssurancePipeline': 200,
}

JOBDIR = "crawls/%(name)s"

# Concurrency & Performance
# These settings are aggressive and may need to be dialed back for more polite crawling or to avoid IP bans.
CONCURRENT_REQUESTS = 10
CONCURRENT_REQUESTS_PER_DOMAIN = 16
DOWNLOAD_DELAY = 1
COOKIES_ENABLED = False
LOG_LEVEL = 'INFO'

# Async Reactor (Required for Impersonate/Curl_Cffi)
TWISTED_REACTOR = 'twisted.internet.asyncioreactor.AsyncioSelectorReactor'

# Download Handlers (Register Impersonate globally)
DOWNLOAD_HANDLERS = {
    "http": "scrapy_impersonate.ImpersonateDownloadHandler",
    "https": "scrapy_impersonate.ImpersonateDownloadHandler",
}

# Global Feed Export (Dynamic naming based on spider name)
# This saves you from defining FEEDS in every spider.
# It saves to: data/bunnings.jsonl, data/officeworks.jsonl, etc.
FEEDS = {
    'data/%(name)s.jsonl': {
        'format': 'jsonlines',
        'encoding': 'utf8', 
        'overwrite': True
    }
}