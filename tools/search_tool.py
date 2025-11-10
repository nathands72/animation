"""Web search tool with Tavily API integration and child-safety filtering."""

import time
import logging
from typing import List, Dict, Any, Optional
from datetime import datetime, timedelta

from config import get_config
from utils.validators import validate_age_appropriateness

logger = logging.getLogger(__name__)


class RateLimiter:
    """Simple rate limiter for API calls."""
    
    def __init__(self, max_calls: int, time_window: float):
        """
        Initialize rate limiter.
        
        Args:
            max_calls: Maximum number of calls allowed
            time_window: Time window in seconds
        """
        self.max_calls = max_calls
        self.time_window = time_window
        self.calls = []
    
    def wait_if_needed(self):
        """Wait if rate limit would be exceeded."""
        now = time.time()
        
        # Remove old calls outside the time window
        self.calls = [call_time for call_time in self.calls if now - call_time < self.time_window]
        
        # If at limit, wait until oldest call expires
        if len(self.calls) >= self.max_calls:
            oldest_call = min(self.calls)
            wait_time = self.time_window - (now - oldest_call) + 0.1
            if wait_time > 0:
                logger.info(f"Rate limit reached, waiting {wait_time:.2f} seconds")
                time.sleep(wait_time)
                # Clean up again after waiting
                now = time.time()
                self.calls = [call_time for call_time in self.calls if now - call_time < self.time_window]
        
        # Record this call
        self.calls.append(time.time())


class WebSearchTool:
    """Web search tool with Tavily API and child-safety filtering."""
    
    def __init__(self):
        """Initialize web search tool."""
        self.config = get_config()
        self.rate_limiter = RateLimiter(max_calls=10, time_window=60.0)  # 10 calls per minute
        self.tavily_client = None
        self.serpapi_client = None
        self._initialize_clients()
    
    def _initialize_clients(self):
        """Initialize search API clients."""
        try:
            if self.config.search.provider == "tavily" and self.config.search.api_key:
                from tavily import TavilyClient
                self.tavily_client = TavilyClient(api_key=self.config.search.api_key)
                logger.info("Tavily client initialized")
            elif self.config.search.provider == "serpapi" and self.config.search.api_key:
                from serpapi import GoogleSearch
                self.serpapi_client = GoogleSearch
                logger.info("SerpAPI client initialized")
            else:
                logger.warning("No search API key found. Web search will be disabled.")
        except ImportError as e:
            logger.warning(f"Search API library not installed: {e}")
        except Exception as e:
            logger.error(f"Error initializing search client: {e}")
    
    def search(
        self,
        query: str,
        max_results: Optional[int] = None,
        age_group: str = "6-8",
        filter_child_safe: bool = True
    ) -> List[Dict[str, Any]]:
        """
        Execute web search with child-safety filtering.
        
        Args:
            query: Search query
            max_results: Maximum number of results to return
            age_group: Target age group for content filtering
            filter_child_safe: Whether to filter for child-safe content
            
        Returns:
            List of search results with title, url, content, and relevance score
        """
        if not self.tavily_client and not self.serpapi_client:
            logger.warning("Search API not available, returning empty results")
            return []
        
        if max_results is None:
            max_results = self.config.search.max_results
        
        # Rate limiting
        self.rate_limiter.wait_if_needed()
        
        try:
            if self.tavily_client:
                results = self._search_tavily(query, max_results)
            elif self.serpapi_client:
                results = self._search_serpapi(query, max_results)
            else:
                return []
            
            # Filter for child safety
            if filter_child_safe and self.config.search.enable_child_safety_filter:
                results = self._filter_child_safe(results, age_group)
            
            return results[:max_results]
            
        except Exception as e:
            logger.error(f"Error executing search: {e}")
            return []
    
    def _search_tavily(self, query: str, max_results: int) -> List[Dict[str, Any]]:
        """Search using Tavily API."""
        try:
            response = self.tavily_client.search(
                query=query,
                max_results=max_results,
                search_depth="basic"
            )
            
            results = []
            for result in response.get("results", []):
                results.append({
                    "title": result.get("title", ""),
                    "url": result.get("url", ""),
                    "content": result.get("content", ""),
                    "score": result.get("score", 0.0),
                    "published_date": result.get("published_date"),
                })
            
            return results
            
        except Exception as e:
            logger.error(f"Tavily search error: {e}")
            return []
    
    def _search_serpapi(self, query: str, max_results: int) -> List[Dict[str, Any]]:
        """Search using SerpAPI."""
        try:
            params = {
                "q": query,
                "api_key": self.config.search.api_key,
                "num": max_results,
            }
            
            search = self.serpapi_client(params)
            results_data = search.get_dict()
            
            results = []
            for result in results_data.get("organic_results", [])[:max_results]:
                results.append({
                    "title": result.get("title", ""),
                    "url": result.get("link", ""),
                    "content": result.get("snippet", ""),
                    "score": 1.0,  # SerpAPI doesn't provide scores
                })
            
            return results
            
        except Exception as e:
            logger.error(f"SerpAPI search error: {e}")
            return []
    
    def _filter_child_safe(
        self,
        results: List[Dict[str, Any]],
        age_group: str
    ) -> List[Dict[str, Any]]:
        """
        Filter results for child-safe content.
        
        Args:
            results: List of search results
            age_group: Target age group
            
        Returns:
            Filtered list of child-safe results
        """
        filtered = []
        
        inappropriate_keywords = [
            "violence", "weapon", "kill", "death", "blood", "horror",
            "scary", "frightening", "adult", "mature", "inappropriate",
            "explicit", "graphic", "trauma", "fear"
        ]
        
        for result in results:
            # Check title and content
            text_to_check = f"{result.get('title', '')} {result.get('content', '')}".lower()
            
            # Check for inappropriate keywords
            has_inappropriate = any(keyword in text_to_check for keyword in inappropriate_keywords)
            
            if not has_inappropriate:
                # Additional age-appropriateness check
                is_appropriate, _ = validate_age_appropriateness(
                    result.get('content', ''),
                    age_group
                )
                
                if is_appropriate:
                    filtered.append(result)
                else:
                    logger.debug(f"Filtered out result: {result.get('title', '')}")
            else:
                logger.debug(f"Filtered out inappropriate result: {result.get('title', '')}")
        
        return filtered
    
    def search_multiple(
        self,
        queries: List[str],
        age_group: str = "6-8",
        filter_child_safe: bool = True
    ) -> Dict[str, List[Dict[str, Any]]]:
        """
        Execute multiple searches.
        
        Args:
            queries: List of search queries
            age_group: Target age group
            filter_child_safe: Whether to filter for child-safe content
            
        Returns:
            Dictionary mapping queries to their results
        """
        all_results = {}
        
        for query in queries:
            logger.info(f"Searching: {query}")
            results = self.search(
                query=query,
                age_group=age_group,
                filter_child_safe=filter_child_safe
            )
            all_results[query] = results
        
        return all_results
    
    def summarize_results(self, results: List[Dict[str, Any]]) -> str:
        """
        Summarize search results into a text summary.
        
        Args:
            results: List of search results
            
        Returns:
            Text summary of results
        """
        if not results:
            return "No search results available."
        
        summary_parts = []
        for i, result in enumerate(results[:5], 1):  # Top 5 results
            title = result.get("title", "Untitled")
            content = result.get("content", "")[:200]  # First 200 chars
            summary_parts.append(f"{i}. {title}\n   {content}...")
        
        return "\n\n".join(summary_parts)

