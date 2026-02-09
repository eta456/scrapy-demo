import os
from dotenv import load_dotenv

# =============================================================================
# 1. INITIALIZATION & SECRETS
# =============================================================================
load_dotenv()  # Load environment variables from .env

BOT_NAME = 'retail_spiders'
SPIDER_MODULES = ['retail_spiders.spiders']
NEWSPIDER_MODULE = 'retail_spiders.spiders'
LOG_LEVEL = os.getenv('LOG_LEVEL', 'INFO')

# =============================================================================
# 2. ARCHITECTURE & ASYNC (THE ENGINE)
# =============================================================================
# Modern Scrapy requires AsyncIO reactor for new tools like curl_cffi/playwright
TWISTED_REACTOR = 'twisted.internet.asyncioreactor.AsyncioSelectorReactor'

# Register 'scrapy-impersonate' to handle TLS Fingerprinting
DOWNLOAD_HANDLERS = {
    "http": "scrapy_impersonate.ImpersonateDownloadHandler",
    "https": "scrapy_impersonate.ImpersonateDownloadHandler",
}

# =============================================================================
# 3. CONCURRENCY & POLITENESS
# =============================================================================
# Aggressive settings for high-throughput retail scraping
CONCURRENT_REQUESTS = 32
CONCURRENT_REQUESTS_PER_DOMAIN = 16
DOWNLOAD_DELAY = 1  # 1s delay to be polite but fast
COOKIES_ENABLED = False  # Disable to avoid tracking/sessions

# =============================================================================
# 4. SAFETY & LIMITS (FAIL-SAFES)
# =============================================================================
DOWNLOAD_TIMEOUT = 30       # Drop request if proxy hangs for >30s
CLOSESPIDER_TIMEOUT = 14400 # Hard kill after 4 hours (4 * 3600)

# Circuit Breaker: Stop spider if failure rate exceeds 35%
CIRCUIT_BREAKER_THRESHOLD = 0.35 

# Persistence: Resume crawls from this directory if stopped
# Usage: scrapy crawl bunnings -s JOBDIR=crawls/bunnings-1
JOBDIR = None  # Default to None, override via CLI when needed

# =============================================================================
# 5. MIDDLEWARE PIPELINE (THE NETWORK LAYER)
# =============================================================================
DOWNLOADER_MIDDLEWARES = {
    'retail_spiders.middlewares.SoftBanMiddleware': 550,
}

SPIDER_MIDDLEWARES = {
   # Lifecycle monitoring (Logs start/stop stats)
   'retail_spiders.middlewares.RetailSpidersSpiderMiddleware': 500,
}

EXTENSIONS = {
    # Monitors error rates and kills job if too high
    'retail_spiders.extensions.CircuitBreakerExtension': 500,
}

# =============================================================================
# 6. DATA PIPELINE (THE PROCESSING LAYER)
# =============================================================================
ITEM_PIPELINES = {
   # Validates price/integrity
   'retail_spiders.pipelines.QualityAssurancePipeline': 200,
   
   # Saves to MongoDB
   'retail_spiders.pipelines.MongoPipeline': 300,
}

# MongoDB Config (Loaded from Env)
MONGO_URI = os.getenv('MONGO_URI')
MONGO_DATABASE = os.getenv('MONGO_DATABASE', 'shopgrok_test')

# =============================================================================
# 7. EXPORTS & ARTIFACTS
# =============================================================================
# Save a local JSONL backup automatically for every run
FEEDS = {
    'data/%(name)s_%(time)s.jsonl': {  # Added timestamp to filename
        'format': 'jsonlines',
        'encoding': 'utf8', 
        'overwrite': True
    }
}