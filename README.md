# Retail Price Engine

### Project Context
*This repository was built as a technical demonstration for the ShopGrok Data Engineer application. The goal was to demonstrate proficiency with the Python/Scrapy stack by solving three distinct data acquisition challenges (XPath, Selectors, and API interception).*

## 📋 Project Overview
This project implements a scalable **ETL (Extract, Transform, Load)** pipeline for retail pricing data. It consists of a robust Scrapy spider cluster that harvests data from major Australian retailers.

**Key Features:**
* **Polymorphic Extraction:** Demonstrates three distinct extraction strategies (XPath, CSS Selectors, and hidden API endpoints).
* **Strict Schema Validation:** Utilizes `Scrapy ItemLoaders` and `Processors` to enforce data types and clean currency/whitespace artifacts at the extraction layer.
* **Modular Architecture:** Adheres to strict separation of concerns—Spider logic is decoupled from Data Cleaning logic.

## 🛠️ Architecture

### 1. The Spiders (`/retail_spiders/spiders`)
| Spider | Target | Strategy | Why this approach? |
| :--- | :--- | :--- | :--- |
| `officeworks.py` | Officeworks | **XPath** | Robust navigation of complex, nested DOM structures where classes are unstable. |
| `jbhifi.py` | JB Hi-Fi | **CSS Selectors** | Efficient selection for standard HTML5 semantic layouts. |
| `bigw_api.py` | Big W | **JSON API** | Intercepts internal XHR requests to retrieve clean JSON data directly, bypassing HTML parsing for faster speed. |

## 🚀 Getting Started

### Installation
```bash
git clone [https://github.com/eta456/scrapy-demo.git](https://github.com/eta456/scrapy-demo.git)
cd shopgrok-demo
pip install -r requirements.txt
