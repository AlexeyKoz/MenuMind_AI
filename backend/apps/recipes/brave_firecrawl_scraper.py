"""
Smart Recipe Scraper using Brave Search + Firecrawl
- Brave Search: Find recipe URLs (better than DuckDuckGo)
- Firecrawl: Extract clean content (handles JavaScript)
"""

import os
import logging
import requests
from typing import List, Dict, Optional, Tuple
from django.conf import settings

logger = logging.getLogger(__name__)


class BraveFirecrawlScraper:
    """Professional recipe scraper using Brave Search + Firecrawl"""

    def __init__(self):
        self.brave_api_key = getattr(settings, 'BRAVE_SEARCH_API_KEY', '')
        self.firecrawl_api_key = getattr(settings, 'FIRECRAWL_API_KEY', '')

        if not self.brave_api_key:
            logger.warning("[BRAVE] API key not found - search will fail")
        if not self.firecrawl_api_key:
            logger.warning(
                "[FIRECRAWL] API key not found - scraping will fail")

    def search_recipes(self, query: str, max_results: int = 5) -> List[str]:
        """
        Search for recipe URLs using Brave Search API

        Args:
            query: Search query (e.g., "beef stew recipe")
            max_results: Maximum number of URLs to return

        Returns:
            List of recipe URLs
        """
        if not self.brave_api_key:
            logger.error("[BRAVE] Cannot search - API key missing")
            return []

        # Enhance query for better recipe results
        enhanced_query = f"{query} recipe step by step"
        logger.info(f"[BRAVE] Searching: {enhanced_query}")

        try:
            # Brave Search API endpoint
            url = "https://api.search.brave.com/res/v1/web/search"

            headers = {
                "Accept": "application/json",
                "Accept-Encoding": "gzip",
                "X-Subscription-Token": self.brave_api_key
            }

            params = {
                "q": enhanced_query,
                "count": max_results * 2,  # Get more results, filter later
                "safesearch": "off",
                "freshness": "",  # All results
                "text_decorations": False,
                "spellcheck": True
            }

            response = requests.get(
                url, headers=headers, params=params, timeout=10)
            response.raise_for_status()

            data = response.json()

            # Extract URLs from web results
            urls = []
            web_results = data.get('web', {}).get('results', [])

            logger.info(f"[BRAVE] Received {len(web_results)} results")

            # Filter for recipe sites
            recipe_indicators = [
                'recipe', 'cooking', 'food', 'kitchen', 'chef',
                'allrecipes', 'foodnetwork', 'epicurious', 'seriouseats',
                'bonappetit', 'tasty', 'delish', 'simplyrecipes'
            ]

            skip_domains = [
                'youtube.com', 'pinterest.com', 'amazon.com',
                'wikipedia.org', 'wiki', 'reddit.com', 'quora.com',
                'facebook.com', 'instagram.com', 'twitter.com',
                'tiktok.com', 'zhihu.com'  # Chinese Q&A site
            ]

            for result in web_results:
                url = result.get('url', '')
                title = result.get('title', '').lower()
                description = result.get('description', '').lower()

                # Skip non-recipe sites
                if any(domain in url.lower() for domain in skip_domains):
                    logger.debug(
                        f"[BRAVE] ⏭️ Skipping (blocked domain): {url}")
                    continue

                # Prioritize recipe sites
                is_recipe_site = any(
                    indicator in url.lower() or
                    indicator in title or
                    indicator in description
                    for indicator in recipe_indicators
                )

                if is_recipe_site:
                    urls.append(url)
                    logger.info(f"[BRAVE] ✅ Recipe URL: {url}")

                    if len(urls) >= max_results:
                        break

            logger.info(f"[BRAVE] ✅ Found {len(urls)} recipe URLs")
            return urls

        except requests.exceptions.RequestException as e:
            logger.error(f"[BRAVE] ❌ Search failed: {e}")
            return []
        except Exception as e:
            logger.error(f"[BRAVE] ❌ Unexpected error: {e}")
            return []

    def scrape_url(self, url: str) -> Tuple[Optional[str], bool]:
        """
        Scrape recipe content using Firecrawl API

        Args:
            url: Recipe URL to scrape

        Returns:
            Tuple of (content, success)
        """
        if not self.firecrawl_api_key:
            logger.error("[FIRECRAWL] Cannot scrape - API key missing")
            return None, False

        logger.info(f"[FIRECRAWL] Scraping: {url}")

        try:
            # Firecrawl API endpoint
            api_url = "https://api.firecrawl.dev/v1/scrape"

            headers = {
                "Authorization": f"Bearer {self.firecrawl_api_key}",
                "Content-Type": "application/json"
            }

            payload = {
                "url": url,
                "formats": ["markdown"],  # Get clean markdown format
                "onlyMainContent": True,  # Extract main content only
                "timeout": 30000,  # 30 seconds timeout
                "waitFor": 2000  # Wait 2 seconds for JavaScript to load
            }

            response = requests.post(
                api_url, headers=headers, json=payload, timeout=35)
            response.raise_for_status()

            data = response.json()

            # Check if scraping was successful
            if not data.get('success', False):
                logger.error(
                    f"[FIRECRAWL] ❌ Scraping failed: {data.get('error', 'Unknown error')}")
                return None, False

            # Extract markdown content
            content = data.get('data', {}).get('markdown', '')

            if not content or len(content.strip()) < 200:
                logger.warning(
                    f"[FIRECRAWL] ⚠️ Content too short ({len(content)} chars)")
                return None, False

            logger.info(f"[FIRECRAWL] ✅ Extracted {len(content)} characters")

            # Basic validation - ensure it looks like a recipe (multilingual)
            content_lower = content.lower()

            # Check for recipe keywords in multiple languages
            ingredient_keywords = [
                # English
                'ingredient', 'ingredients', 'you will need',
                # Russian
                'ингредиент', 'ингредиенты', 'состав', 'продукты',
                # Hebrew
                'מרכיבים', 'רכיבים',
                # Common patterns
                'flour', 'sugar', 'eggs', 'мука', 'сахар', 'яйца', 'קמח', 'סוכר', 'ביצים'
            ]

            instruction_keywords = [
                # English
                'instruction', 'directions', 'steps', 'method', 'preparation',
                # Russian
                'инструкция', 'приготовление', 'способ', 'шаги', 'этапы',
                # Hebrew
                'הוראות', 'הכנה', 'שלבים',
                # Common cooking verbs
                'bake', 'mix', 'heat', 'cook', 'печь', 'смешать', 'нагреть', 'готовить', 'לאפות', 'לערבב'
            ]

            has_ingredients = any(
                word in content_lower for word in ingredient_keywords)
            has_instructions = any(
                word in content_lower for word in instruction_keywords)

            if not (has_ingredients and has_instructions):
                logger.warning(
                    "[FIRECRAWL] ⚠️ Content doesn't look like a recipe (no recipe keywords found)")
                logger.warning(f"[FIRECRAWL] Content preview: {content[:200]}")
                return None, False

            return content, True

        except requests.exceptions.RequestException as e:
            logger.error(f"[FIRECRAWL] ❌ Scraping failed: {e}")
            return None, False
        except Exception as e:
            logger.error(f"[FIRECRAWL] ❌ Unexpected error: {e}")
            return None, False

    def search_and_scrape(self, query: str, max_results: int = 5) -> List[Dict]:
        """
        Search for recipes and scrape the best ones

        Args:
            query: Search query
            max_results: Maximum number of recipes to return

        Returns:
            List of dicts with 'url' and 'content'
        """
        logger.info(f"[BRAVE+FIRECRAWL] Starting search & scrape for: {query}")

        # Step 1: Search for URLs
        urls = self.search_recipes(query, max_results=max_results)

        if not urls:
            logger.error("[BRAVE+FIRECRAWL] ❌ No URLs found")
            return []

        # Step 2: Scrape each URL
        recipes = []
        for idx, url in enumerate(urls, 1):
            logger.info(f"[BRAVE+FIRECRAWL] Scraping {idx}/{len(urls)}: {url}")

            content, success = self.scrape_url(url)

            if success and content:
                recipes.append({
                    'url': url,
                    'content': content
                })
                logger.info(
                    f"[BRAVE+FIRECRAWL] ✅ Successfully scraped {idx}/{len(urls)}")

                # Stop if we have enough successful scrapes
                if len(recipes) >= max_results:
                    break
            else:
                logger.warning(
                    f"[BRAVE+FIRECRAWL] ⚠️ Failed to scrape {idx}/{len(urls)}")

        logger.info(
            f"[BRAVE+FIRECRAWL] ✅ Successfully scraped {len(recipes)}/{len(urls)} recipes")
        return recipes


# Convenience function for easy integration
def search_and_scrape_recipe(query: str, max_results: int = 5) -> List[Dict]:
    """
    Quick function to search and scrape recipes

    Args:
        query: Search query (e.g., "beef stew")
        max_results: Maximum number of recipes to return

    Returns:
        List of dicts with 'url' and 'content'
    """
    scraper = BraveFirecrawlScraper()
    return scraper.search_and_scrape(query, max_results)
