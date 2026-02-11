from scrapy.http import HtmlResponse
from curl_cffi.requests import AsyncSession

# CHANGE: Inherit from 'object', not 'HTTPDownloadHandler'
class CurlCffiDownloadHandler(object):
    
    lazy = False
    
    def __init__(self, settings):
        self.settings = settings
        self.impersonate_target = "chrome120"

    # Scrapy standard: handlers are often created via from_crawler
    @classmethod
    def from_crawler(cls, crawler):
        return cls(crawler.settings)

    async def download_request(self, request, spider):
        # 1. Convert Headers
        curl_headers = {}
        # Safely convert headers (some might be non-string bytes)
        for k, v in request.headers.items():
            curl_headers[k.decode('utf-8')] = v[0].decode('utf-8')

        # 2. Execute Request
        # We create a fresh session for every request to ensure isolation
        async with AsyncSession(impersonate=self.impersonate_target) as session:
            
            response = await session.request(
                method=request.method,
                url=request.url,
                headers=curl_headers,
                data=request.body,
                cookies=request.cookies,
                allow_redirects=request.meta.get('dont_redirect', True) == False,
                timeout=30
            )

            # 3. Return Scrapy Response
            return HtmlResponse(
                url=request.url,
                status=response.status_code,
                headers=dict(response.headers),
                body=response.content,
                encoding='utf-8',
                request=request
            )

    # Scrapy calls this when the spider finishes to clean up resources
    def close(self):
        pass