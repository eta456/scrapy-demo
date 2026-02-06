# Scrapy Demo

This project demonstrates web scraping architectures using **Scrapy**, **Python**, and **Reverse Engineering**. It targets four major Australian electronics retailers, each requiring a different technical approach to overcome specific challenges (Client-Side Rendering, Anti-Bots, and Hidden APIs).

## 🕷️ Spider Architectures

| Retailer | Architecture | Key Technique | Challenge Solved |
| :--- | :--- | :--- | :--- |
| **Bunnings** | **Next.js Hydration** | `__NEXT_DATA__` JSON Extraction | Bypassing CSR & Speed (Pagination Explosion) |
| **Officeworks** | **API Engineering** | API Interception | Obtaining structured data without HTML parsing |
| **Umart** | **Semantic HTML** | XPath & Semantic Tags | Handling deep navigation hierarchies |
| **PLE** | **CSS Selectors** | CSS Selectors | High-speed traversal of legacy HTML structures |
---

## 🚀 Setup & Usage

### Prerequisites
* Python 3.10+
* `uv` (or pip)

### Installation
```bash
uv pip install -r requirements.txt
```

### Running the Spiders
The project is configured to output jsonlines automatically to the data/ folder.
```bash
uv run scrapy crawl bunnings
uv run scrapy crawl officeworks
uv run scrapy crawl umart
uv run scrapy crawl ple
```
---
## 🧠 Technical Deep Dive & Architecture

### 1. Reverse Engineering Next.js (Bunnings)
Instead of using slow, resource-heavy browsers (Selenium/Playwright) to render the site, I reverse-engineered the React hydration state.
* **Technique:** Extracted the hidden `__NEXT_DATA__` JSON blob directly from the HTML response.
* **Result:** Achieved 100% data accuracy with 0% JavaScript execution overhead, enabling a "Scatter-Gather" concurrency model that crawls 10,000+ items in seconds.

### ⚠️ Future Considerations: Next.js 13+ Shift

**Current State:**
The Bunnings spider relies on the `__NEXT_DATA__` script tag, which is standard in Next.js "Pages Router" architecture. This provides a clean, singular JSON blob of the entire page state.

**The Upcoming Challenge (App Router):**
Modern Next.js sites (v13/14+) are migrating to the **App Router** and **React Server Components (RSC)**.
* **Impact:** The `__NEXT_DATA__` blob is removed. Data is no longer a single JSON object but is streamed incrementally using the **React Flight** protocol.
* **Detection:** These sites are identified by multiple script tags executing `self.__next_f.push([...])`, which inject partial data chunks into the client runtime.

### 2. API Interception (Officeworks)
Bypassed the complex HTML structure entirely by targeting the backend search infrastructure.
* **Technique:** Intercepted traffic to the **Algolia** search API, constructing valid signed payloads to retrieve raw product data.
* **Result:** Eliminated the need for HTML parsing maintenance and gained access to structured data fields not visible on the frontend.

### 3. TLS Fingerprinting
Overcame WAFs (Cloudflare/Datadome) that block standard Python scrapers.
* **Technique:** Integrated `curl_cffi` to mimic the TLS (JA3) fingerprints of real browsers (Chrome 120 / Firefox 135).
* **Result:** The scraper is mathematically indistinguishable from a legitimate user at the network layer, preventing 403 Forbidden blocks.

**⚠️ Future Considerations (Active Challenges):**
While TLS spoofing bypasses *passive* inspection, it cannot handle *active* JavaScript challenges (e.g., **Cloudflare Turnstile** or **Datadome Interstitial**).
* **Current Limitation:** The spider cannot execute Client-Side JavaScript. If a CAPTCHA is triggered, the request fails.
* **Proposed Roadmap:** Implement a **Hybrid Solver Middleware**:
    1. Detect "Challenge" responses (403/429 status).
    2. Pause the high-speed Scrapy spider.
    3. Offload the specific URL to a headless browser (Playwright) to solve the Turnstile/CAPTCHA.
    4. Extract the clearance cookies and inject them back into the Scrapy session to resume high-speed crawling.
### 4. Semantic Extraction (Umart & PLE)
Prioritised long-term stability for legacy HTML sites.
* **Technique:** Utilised **Semantic XPath** selectors (e.g., `itemprop="price"`) and CSS chaining rather than fragile visual class names.
* **Result:** Created "self-healing" spiders that remain functional even when the retailer updates their visual CSS styles.
---