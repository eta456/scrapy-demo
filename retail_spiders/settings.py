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

JOBDIR = "crawls/%(name)s"

# 1. Concurrency & Performance
# These settings are aggressive and may need to be dialed back for more polite crawling or to avoid IP bans.
CONCURRENT_REQUESTS = 10
CONCURRENT_REQUESTS_PER_DOMAIN = 16
DOWNLOAD_DELAY = 1
COOKIES_ENABLED = False
LOG_LEVEL = 'INFO'

# 2. Async Reactor (Required for Impersonate/Curl_Cffi)
TWISTED_REACTOR = 'twisted.internet.asyncioreactor.AsyncioSelectorReactor'

# 3. Download Handlers (Register Impersonate globally)
DOWNLOAD_HANDLERS = {
    "http": "scrapy_impersonate.ImpersonateDownloadHandler",
    "https": "scrapy_impersonate.ImpersonateDownloadHandler",
}

# 4. Global Feed Export (Dynamic naming based on spider name)
# This saves you from defining FEEDS in every spider.
# It saves to: data/bunnings.jsonl, data/officeworks.jsonl, etc.
FEEDS = {
    'data/%(name)s.jsonl': {
        'format': 'jsonlines',
        'encoding': 'utf8', 
        'overwrite': True
    }
}