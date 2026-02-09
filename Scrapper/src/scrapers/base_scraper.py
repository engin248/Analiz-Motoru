"""
Base Scraper - Abstract base class for all platform scrapers
"""

from abc import ABC, abstractmethod
from typing import Dict, List, Optional, Any
from playwright.async_api import Page
import asyncio
import re


class BaseScraper(ABC):
    """
    Abstract base class for e-commerce scrapers.
    All platform-specific scrapers must inherit from this class.
    """
    
    def __init__(self, page: Page, config: Dict[str, Any], selectors: Dict[str, Any]):
        self.page = page
        self.config = config
        self.selectors = selectors
        self.platform_name = "base"
    
    # ==================== ABSTRACT METHODS ====================
    
    @abstractmethod
    async def collect_product_urls(self, keyword: str, max_pages: int) -> List[str]:
        """
        Collect product URLs from search/category pages.
        Must be implemented by each platform scraper.
        """
        pass
    
    @abstractmethod
    async def scrape_product(self, url: str) -> Optional[Dict[str, Any]]:
        """
        Scrape a single product page and return product data.
        Must be implemented by each platform scraper.
        """
        pass
    
    @abstractmethod
    def get_trendyol_id(self, url: str) -> Optional[str]:
        """
        Extract platform-specific product ID from URL.
        """
        pass
    
    # ==================== COMMON UTILITY METHODS ====================
    
    def clean_price(self, text: str) -> float:
        """Parse price string to float"""
        if not text:
            return 0.0
        # Remove currency symbols and whitespace
        cleaned = text.replace('TL', '').replace('₺', '').replace('$', '').replace('€', '').strip()
        # Handle Turkish number format (1.234,56 -> 1234.56)
        cleaned = cleaned.replace('.', '').replace(',', '.')
        try:
            return float(cleaned)
        except ValueError:
            return 0.0
    
    def parse_metric(self, text: str) -> int:
        """Parse metric text like '1.2K' or '500 bin' to integer"""
        if not text:
            return 0
        
        text = text.lower().strip()
        
        # Remove time-related phrases
        text = re.sub(r'son\s+\d+\s+(saat|gün|dakika|hafta|ay)[te]*', '', text)
        text = re.sub(r'[\d.,]+\s+(saat|gün|dakika)(te|de)*', '', text)
        text = re.sub(r'kişi[a-z]*', '', text)
        
        # Find numeric pattern
        match = re.search(r'([\d.,]+)\s*(bin|mn|b|m|k)?', text)
        if not match:
            return 0
        
        num_str = match.group(1)
        unit = match.group(2)
        
        if unit:
            num_str = num_str.replace(',', '.')
        else:
            num_str = num_str.replace('.', '').replace(',', '.')
        
        try:
            val = float(num_str)
        except ValueError:
            return 0
        
        # Apply multiplier
        if unit in ['bin', 'b', 'k']:
            val *= 1000
        elif unit in ['mn', 'm']:
            val *= 1000000
        
        return int(round(val))
    
    def calculate_discount_rate(self, original_price: float, discounted_price: float) -> float:
        """Calculate discount percentage"""
        if original_price <= 0 or original_price <= discounted_price:
            return 0.0
        return ((original_price - discounted_price) / original_price) * 100
    
    async def scroll_page(self, scroll_count: int = 5, scroll_amount: int = 1000, delay: float = 0.8):
        """Scroll page to trigger lazy loading"""
        for _ in range(scroll_count):
            await self.page.mouse.wheel(0, scroll_amount)
            await asyncio.sleep(delay)
    
    async def wait_for_content(self, selector: str, timeout: int = 10000) -> bool:
        """Wait for specific content to load"""
        try:
            await self.page.wait_for_selector(selector, timeout=timeout)
            return True
        except:
            return False
    
    def extract_id_from_url(self, url: str, pattern: str) -> Optional[str]:
        """Extract product ID from URL using regex pattern"""
        match = re.search(pattern, url)
        return match.group(1) if match else None
