# Scrapy Demo

This project demonstrates web scraping architectures using **Scrapy**, **Python**, and **Reverse Engineering**. It targets four major Australian electronics retailers, each requiring a different technical approach to overcome specific challenges (Client-Side Rendering, Anti-Bots, and Hidden APIs).

## 🕷️ Spider Architectures

| Retailer | Architecture | Key Technique | Challenge Solved |
| :--- | :--- | :--- | :--- |
| **Bunnings** | **Next.js Hydration** | `__NEXT_DATA__` JSON Extraction | Bypassing CSR & Speed (Pagination Explosion) |
| **Officeworks** | **API Engineering** | API Interception | Obtaining structured data without HTML parsing |
| **Umart, SCA** | **Semantic HTML** | XPath & Semantic Tags | Handling deep navigation hierarchies |
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
The project is configured to output jsonlines automatically to the data/*.jsonl folder.
```bash
uv run scrapy crawl bunnings
uv run scrapy crawl officeworks
uv run scrapy crawl umart
uv run scrapy crawl ple
```
---

## 📚 Documentation
I have documented the system design and reverse-engineering process in detail:
* **[🕷️ Spider Strategy (docs/spiders.md)](docs/spiders.md)**
    * *Deep Dive:* Handling the **Next.js 13+ App Router shift** and **React Server Components**.
    * *Deep Dive:* Reverse-engineering **Algolia** signed payloads.
* **[⚙️ System Architecture (docs/architecture.md)](docs/architecture.md)**
    * Operational governance and scrapy configuration
    * Future Considerations: Designing a **Hybrid Solver Middleware** for CAPTCHAs.