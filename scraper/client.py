"""
HTTP client with anti-scraping measures.

Handles requests to Transfermarkt with delays, retries, and proper headers.
"""

import time
import random
from typing import Optional

import requests
from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry

from .config import (
    REQUEST_HEADERS,
    REQUEST_DELAY_RANGE,
    MAX_RETRIES,
    REQUEST_TIMEOUT,
)


class ScraperClient:
    """
    HTTP client for scraping with anti-detection measures.
    
    Features:
    - Session reuse for connection pooling
    - Randomized delays between requests
    - Automatic retry on failure
    - Browser-like headers
    """
    
    def __init__(self):
        self.session = requests.Session()
        self.session.headers.update(REQUEST_HEADERS)

        # 429 = rate limited, 5xx = server errors — all worth retrying
        # backoff_factor=1 means waits: 1s, 2s, 4s between retries
        retry_strategy = Retry(
            total=MAX_RETRIES,
            backoff_factor=1,
            status_forcelist=[429, 500, 502, 503, 504],
            allowed_methods=["GET"],
            respect_retry_after_header=True,  # honours Transfermarkt's Retry-After header
        )
        adapter = HTTPAdapter(max_retries=retry_strategy)
        self.session.mount("http://", adapter)
        self.session.mount("https://", adapter)

        self.last_request_time = 0  # tracks when the last request was made
    
    def get(self, url: str) -> Optional[str]:
        """
        Fetch a URL with anti-scraping measures.
        
        Args:
            url: Full URL to fetch
            
        Returns:
            HTML content as string, or None if request failed
        """
        self._apply_delay()
        
        try:
            response = self.session.get(url, timeout=REQUEST_TIMEOUT)
            response.raise_for_status()
            self.last_request_time = time.time()
            return response.text
        except requests.RequestException as e:
            print(f"Request failed for {url}: {e}")
            return None
    
    def _apply_delay(self):
        """Add randomized delay between requests to avoid detection."""
        if self.last_request_time > 0:
            elapsed = time.time() - self.last_request_time
            min_delay, max_delay = REQUEST_DELAY_RANGE
            # Randomized so requests don't follow a predictable pattern
            delay = random.uniform(min_delay, max_delay)

            # Only sleep for the remaining time needed, not the full delay
            if elapsed < delay:
                time.sleep(delay - elapsed)
