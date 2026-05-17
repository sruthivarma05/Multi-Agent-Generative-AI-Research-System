# tools.py
from langchain.tools import tool
import requests
from bs4 import BeautifulSoup
from tavily import TavilyClient
import os
from dotenv import load_dotenv
from rich import print
from playwright.sync_api import sync_playwright
# ── CHANGE: added retry logic so scraping doesn't silently fail ───────────────
from tenacity import retry, stop_after_attempt, wait_exponential
# ── CHANGE: added caching to avoid re-querying Tavily for the same topic ──────
from functools import lru_cache

load_dotenv()

tavily = TavilyClient(api_key=os.getenv("TAVILY_API_KEY"))


# ── Tool 1: Web search (with cache) ──────────────────────────────────────────
@lru_cache(maxsize=50)          # ── CHANGE: caches up to 50 unique queries ───
def _cached_tavily_search(query: str) -> str:
    """Internal cached search — results reused if same query appears again."""
    results = tavily.search(query=query, max_results=5)
    out = []
    for r in results["results"]:
        out.append(
            f"Title: {r['title']}\nURL: {r['url']}\nSnippet: {r['content'][:300]}\n"
        )
    return "\n----\n".join(out)


@tool
def web_search(query: str) -> str:
    """Search the web for recent and reliable information on a topic.
    Returns titles, URLs and snippets. Results are cached per query."""
    return _cached_tavily_search(query)          # ← hits cache if already run


# ── Helpers ───────────────────────────────────────────────────────────────────
def is_js_rendered(url: str) -> bool:
    """Check if a page needs JS rendering by trying plain requests first."""
    try:
        resp = requests.get(url, timeout=8, headers={"User-Agent": "Mozilla/5.0"})
        soup = BeautifulSoup(resp.text, "html.parser")
        text = soup.get_text(strip=True)
        return len(text) < 200
    except Exception:
        return True


# ── CHANGE: added @retry so transient network errors don't crash the pipeline ─
@retry(stop=stop_after_attempt(3), wait=wait_exponential(multiplier=1, min=2, max=8))
def scrape_with_requests(url: str) -> str:
    """Scrape static HTML websites using requests + BeautifulSoup."""
    resp = requests.get(url, timeout=8, headers={"User-Agent": "Mozilla/5.0"})
    soup = BeautifulSoup(resp.text, "html.parser")
    for tag in soup(["script", "style", "nav", "footer"]):
        tag.decompose()
    return soup.get_text(separator=" ", strip=True)[:3000]


# ── CHANGE: added @retry here too ─────────────────────────────────────────────
@retry(stop=stop_after_attempt(3), wait=wait_exponential(multiplier=1, min=2, max=8))
def scrape_with_playwright(url: str) -> str:
    """Scrape JavaScript-rendered websites using Playwright headless browser."""
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        page = browser.new_page()
        page.goto(url, timeout=15000)
        page.wait_for_load_state("networkidle")
        html = page.content()
        browser.close()

    soup = BeautifulSoup(html, "html.parser")
    for tag in soup(["script", "style", "nav", "footer"]):
        tag.decompose()
    return soup.get_text(separator=" ", strip=True)[:3000]


# ── Tool 2: Single URL scraper (unchanged interface, retries added internally) ─
@tool
def scrape_url(url: str) -> str:
    """Scrape and return clean text content from a given URL.
    Automatically detects and handles both static and JS-rendered websites.
    Retries up to 3 times on failure."""
    try:
        if is_js_rendered(url):
            print(f"[yellow]JS-rendered site detected, using Playwright for: {url}[/yellow]")
            return scrape_with_playwright(url)
        else:
            print(f"[green]Static site detected, using BeautifulSoup for: {url}[/green]")
            return scrape_with_requests(url)
    except Exception as e:
        return f"Could not scrape URL after 3 attempts: {str(e)}"


# ── CHANGE: new tool — scrapes up to 3 URLs for richer report content ─────────
@tool
def scrape_multiple_urls(urls: list[str]) -> str:
    """Scrape up to 3 URLs and combine their content.
    Use this when you want richer, multi-source content for a report.
    Input: a list of URL strings."""
    results = []
    for url in urls[:3]:                          # cap at 3 to control cost/time
        content = scrape_url.invoke(url)
        results.append(f"[SOURCE: {url}]\n{content}")
    return "\n\n---\n\n".join(results)