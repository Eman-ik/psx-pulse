"""PSX API Client — Centralized access to PSX endpoints with token management.

Handles:
- X-Req-Id token fetching and refresh
- Request resilience (retries, timeouts, backoff)
- Rate limiting awareness
- Clean interface for screener, history, announcements

This layer isolates all PSX HTTP concerns from the rest of the application.
"""

import logging
import time
from datetime import datetime, timedelta
from typing import Optional, Dict, Any

import httpx
from bs4 import BeautifulSoup

logger = logging.getLogger(__name__)

# PSX constants
BASE_URL = "https://dps.psx.com.pk"
SCREENER_URL = f"{BASE_URL}/company"
HISTORY_URL = f"{BASE_URL}/company"
ANNOUNCEMENTS_URL = f"{BASE_URL}/company"

# Token management
TOKEN_TTL_SECONDS = 180  # 3 minutes
TOKEN_REFRESH_THRESHOLD = 30  # Refresh when 30s left


class PSXClient:
    """PSX API client with automatic token management and resilience."""

    def __init__(self, timeout_seconds: int = 30, max_retries: int = 3):
        """Initialize PSX client.

        Args:
            timeout_seconds: Request timeout (default 30s)
            max_retries: Number of retry attempts (default 3)
        """
        self.timeout = timeout_seconds
        self.max_retries = max_retries

        # Token state
        self.token: Optional[str] = None
        self.token_expires_at: Optional[datetime] = None

        # Headers template
        self.headers = {
            "User-Agent": (
                "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
                "AppleWebKit/537.36 (KHTML, like Gecko) "
                "Chrome/91.0.4472.124 Safari/537.36"
            ),
        }

    def _is_token_valid(self) -> bool:
        """Check if current token is still valid."""
        if self.token is None or self.token_expires_at is None:
            return False

        time_left = (self.token_expires_at - datetime.now()).total_seconds()
        return time_left > TOKEN_REFRESH_THRESHOLD

    def _fetch_token(self) -> bool:
        """Fetch X-Req-Id token from PSX homepage.

        Returns:
            True if successful, False otherwise
        """
        try:
            with httpx.Client(timeout=self.timeout) as client:
                response = client.get(f"{BASE_URL}/", headers=self.headers)
                response.raise_for_status()

            soup = BeautifulSoup(response.content, "html.parser")
            script_tag = soup.find("script", {"id": "__NEXT_DATA__"})

            if not script_tag:
                logger.warning("Could not find __NEXT_DATA__ script in PSX homepage")
                return False

            import json
            data = json.loads(script_tag.string)
            token = data.get("props", {}).get("initialState", {}).get("xReqId")

            if not token:
                logger.warning("Could not extract X-Req-Id token from PSX page")
                return False

            self.token = token
            self.token_expires_at = datetime.now() + timedelta(seconds=TOKEN_TTL_SECONDS)
            logger.debug(f"Fetched new X-Req-Id token, valid until {self.token_expires_at}")
            return True

        except Exception as e:
            logger.error(f"Failed to fetch X-Req-Id token: {e}")
            return False

    def _ensure_token(self) -> bool:
        """Ensure a valid token exists, refreshing if needed.

        Returns:
            True if valid token obtained, False otherwise
        """
        if self._is_token_valid():
            return True

        logger.debug("Token expired or missing, refreshing...")
        return self._fetch_token()

    def _request_with_retry(
        self,
        method: str,
        url: str,
        params: Optional[Dict[str, Any]] = None,
        **kwargs
    ) -> Optional[httpx.Response]:
        """Make HTTP request with retry logic and exponential backoff.

        Args:
            method: HTTP method (GET, POST, etc.)
            url: Request URL
            params: Query parameters
            **kwargs: Additional arguments to pass to httpx

        Returns:
            Response object if successful, None otherwise
        """
        for attempt in range(self.max_retries):
            try:
                with httpx.Client(timeout=self.timeout) as client:
                    headers = {**self.headers}
                    if self.token:
                        headers["X-Req-Id"] = self.token

                    response = client.request(
                        method,
                        url,
                        params=params,
                        headers=headers,
                        **kwargs
                    )

                    if response.status_code == 200:
                        return response

                    # Token expired, refresh and retry
                    if response.status_code == 401 and attempt < self.max_retries - 1:
                        logger.debug("Got 401, refreshing token...")
                        if self._fetch_token():
                            continue
                        else:
                            return None

                    # Other errors
                    logger.warning(
                        f"PSX request failed: {response.status_code} "
                        f"(attempt {attempt + 1}/{self.max_retries})"
                    )
                    if attempt < self.max_retries - 1:
                        wait = 2 ** attempt  # Exponential backoff: 1s, 2s, 4s
                        logger.debug(f"Retrying in {wait}s...")
                        time.sleep(wait)

            except httpx.TimeoutException:
                logger.warning(
                    f"Request timeout (attempt {attempt + 1}/{self.max_retries})"
                )
                if attempt < self.max_retries - 1:
                    time.sleep(2 ** attempt)

            except Exception as e:
                logger.error(f"Request error: {e}")
                if attempt < self.max_retries - 1:
                    time.sleep(2 ** attempt)

        return None

    def screener(self, symbol: str = None) -> Optional[Dict[str, Any]]:
        """Get screener data for a company or all companies.

        Args:
            symbol: Company symbol (None for all)

        Returns:
            Screener data or None if failed
        """
        if not self._ensure_token():
            logger.error("Could not ensure valid token for screener request")
            return None

        params = {}
        if symbol:
            params["symbol"] = symbol

        response = self._request_with_retry("GET", SCREENER_URL, params=params)
        if response:
            try:
                return response.json()
            except Exception as e:
                logger.error(f"Failed to parse screener response: {e}")
                return None

        return None

    def history(
        self,
        symbol: str,
        start_date: Optional[str] = None,
        end_date: Optional[str] = None
    ) -> Optional[Dict[str, Any]]:
        """Get historical price data for a company.

        Args:
            symbol: Company symbol
            start_date: Start date (YYYY-MM-DD)
            end_date: End date (YYYY-MM-DD)

        Returns:
            Historical data or None if failed
        """
        if not self._ensure_token():
            logger.error("Could not ensure valid token for history request")
            return None

        params = {"symbol": symbol}
        if start_date:
            params["startDate"] = start_date
        if end_date:
            params["endDate"] = end_date

        response = self._request_with_retry("GET", HISTORY_URL, params=params)
        if response:
            try:
                return response.json()
            except Exception as e:
                logger.error(f"Failed to parse history response: {e}")
                return None

        return None

    def announcements(self, symbol: str) -> Optional[Dict[str, Any]]:
        """Get announcements for a company.

        Args:
            symbol: Company symbol

        Returns:
            Announcements data or None if failed
        """
        if not self._ensure_token():
            logger.error("Could not ensure valid token for announcements request")
            return None

        params = {"symbol": symbol}

        response = self._request_with_retry(
            "GET",
            ANNOUNCEMENTS_URL,
            params=params
        )
        if response:
            try:
                return response.json()
            except Exception as e:
                logger.error(f"Failed to parse announcements response: {e}")
                return None

        return None

    def request(
        self,
        method: str,
        endpoint: str,
        params: Optional[Dict[str, Any]] = None,
        **kwargs
    ) -> Optional[httpx.Response]:
        """Generic request method for custom PSX API calls.

        Args:
            method: HTTP method
            endpoint: API endpoint (relative to BASE_URL)
            params: Query parameters
            **kwargs: Additional arguments

        Returns:
            Response object or None if failed
        """
        if not self._ensure_token():
            logger.error("Could not ensure valid token for generic request")
            return None

        url = f"{BASE_URL}/{endpoint.lstrip('/')}"
        return self._request_with_retry(method, url, params=params, **kwargs)
