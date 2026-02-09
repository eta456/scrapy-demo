# ⚙️ System Architecture & Resilience Strategy

This document outlines the engineering decisions behind the resilience, quality, and governance layers of the scrapers.

Unlike basic scripts, this system is architected to handle **network hostility**, **schema drift**, and **infrastructure constraints** automatically.

---

## 1. The Middleware Layer (Network & Observability)

We employ custom middlewares to handle the nuances of modern anti-bot protection and production monitoring.

### 🛡️ Soft Ban Detection (`SoftBanMiddleware`)
**Problem:** Modern CDNs (Cloudflare/Akamai) often return `200 OK` status codes even when blocking a request with a Captcha or "Access Denied" page. Standard scrapers treat these as successful, leading to data corruption.

**Solution:**
* **Logic:** We inspect the response body for ban signatures (e.g., `Access Denied`, `Challenge`, `automated access is prohibited`) or empty JSON payloads.
* **Action:** If detected, the middleware triggers a **Retry**, ensuring only valid HTML reaches the parser.

### 📡 Lifecycle Monitoring (`RetailSpidersSpiderMiddleware`)
**Problem:** Default Scrapy logs are too verbose for high-level monitoring.

**Solution:**
* **Logic:** Hooks into Scrapy signals (`spider_opened`, `spider_closed`).
* **Action:** Logs concise, structured system events (Start Time, Finish Time, Item Count) to standard output for easy ingestion by logging tools.

---

## 2. The Data Pipeline (Integrity & Storage)

The pipeline utilizes a **Gatekeeper Pattern** to ensure strict data hygiene before storage.

### 🚧 1. The Gatekeeper: `QualityAssurancePipeline` (Priority: 200)
**Role:** Prevents "Schema Drift" from corrupting the database.
* **Critical Checks:** Drops items missing `price`, or `name`.
* **Logic Checks:** Drops items where `price <= 0`.
* **Outcome:** If validation fails, the item is dropped immediately and a `data_quality/failure` metric is incremented. Bad data never touches the database.

### 💾 2. The Vault: `MongoPipeline` (Priority: 300)
**Role:** Persistence and History.
* **Dynamic Routing:** The collection name is derived at runtime (`spider.name` → `bunnings_products`). This allows adding new retailers without config changes.
* **Append-Only Pattern:** We use `insert_one` with a `scraped_at` timestamp rather than `update_one`. This preserves pricing history, enabling time-series analysis rather than just a snapshot.

---

## 3. Operational Governance (Fail-Safes)

To prevent resource exhaustion or runaway costs in a production environment, we enforce strict governance limits.

### 🛑 Circuit Breaker (`CircuitBreakerExtension`)
**Risk:** A target site updates its WAF, causing 100% of requests to fail. A naive scraper would keep retrying, burning through expensive proxy bandwidth.
**Config:** `CIRCUIT_BREAKER_THRESHOLD = 0.35`
**Behavior:** If the failure rate (403/429/500 errors) exceeds **35%**, the spider automatically terminates.

### 👮 Resource Monitor
**Risk:** "Zombie" processes consuming shared server resources.
**Config:**
* `CLOSESPIDER_TIMEOUT = 14400`: Hard kill after 4 hours.
* `DOWNLOAD_TIMEOUT = 30`: Drops individual requests that hang for >30s.

---

## 4. Performance & Politeness

We balance throughput with site stability using standard Scrapy settings.

| Setting | Value | Rationale |
| :--- | :--- | :--- |
| `CONCURRENT_REQUESTS` | **32** | High concurrency to maximize bandwidth usage. |
| `DOWNLOAD_DELAY` | **1s** | A small delay to respect the target server's capacity. |
| `COOKIES_ENABLED` | **False** | Prevents session tracking and reduces the risk of "fingerprinting." |
| `JOBDIR` | **Optional** | Enables pausing and resuming large crawls (Persistence). |

---

## 5. TLS Fingerprinting (`scrapy-impersonate`)

**Problem:** Standard Python requests (urllib/requests) have distinct TLS Handshake fingerprints (JA3) that are easily blocked by Cloudflare or Datadome.

**Solution:**
We use `scrapy-impersonate` (binding to `curl_cffi`) to replace the default Twisted downloader. This allows us to mimic a real Chrome/Firefox browser handshake, bypassing sophisticated anti-bot checks at the network layer.

### 🚧 Future Architecture: Hybrid Solver Middleware
While TLS spoofing bypasses *passive* inspection, it cannot handle *active* JavaScript challenges (e.g., Turnstile).
* **Proposed Roadmap:** Implement a **Hybrid Solver Middleware**:
    1. Detect "Challenge" responses (403/429 status).
    2. Pause the high-speed Scrapy spider.
    3. Offload the specific URL to a headless browser (Playwright) to solve the Turnstile/CAPTCHA.
    4. Extract the clearance cookies and inject them back into the Scrapy session to resume high-speed crawling.