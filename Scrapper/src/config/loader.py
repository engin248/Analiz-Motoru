"""
Config Loader - Load and parse YAML configuration files
"""

import os
import yaml
from typing import Dict, Any, Optional
from dataclasses import dataclass, field
from dotenv import load_dotenv

# Load environment variables
load_dotenv()


@dataclass
class DatabaseConfig:
    """Database configuration"""
    host: str
    port: int
    name: str
    user: str
    password: str
    table: str = "scraped_products"
    
    @property
    def connection_url(self) -> str:
        return f"postgresql://{self.user}:{self.password}@{self.host}:{self.port}/{self.name}"


@dataclass
class PlatformConfig:
    """Platform-specific configuration"""
    name: str
    enabled: bool
    keywords: list
    max_pages: int
    max_products: int
    database: DatabaseConfig
    selectors: Dict[str, Any] = field(default_factory=dict)


@dataclass
class Settings:
    """General scraper settings"""
    headless: bool = False
    loop_enabled: bool = False
    loop_interval_minutes: int = 15
    request_delay: int = 2
    scroll_count: int = 5
    retry_count: int = 3


@dataclass
class ScraperConfig:
    """Main configuration container"""
    platforms: Dict[str, PlatformConfig]
    settings: Settings


def load_config(config_path: str = "config.yaml", selectors_path: str = "platform_selectors.yaml") -> ScraperConfig:
    """
    Load configuration from YAML files and environment variables.
    """
    # Get base directory
    base_dir = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
    
    # Load main config
    config_full_path = os.path.join(base_dir, config_path)
    with open(config_full_path, 'r', encoding='utf-8') as f:
        config_data = yaml.safe_load(f)
    
    # Load selectors
    selectors_full_path = os.path.join(base_dir, selectors_path)
    with open(selectors_full_path, 'r', encoding='utf-8') as f:
        selectors_data = yaml.safe_load(f)
    
    # Get DB credentials from environment
    db_host = os.getenv('DB_HOST', 'localhost')
    db_port = int(os.getenv('DB_PORT', '5432'))
    db_user = os.getenv('DB_USER', 'postgres')
    db_password = os.getenv('DB_PASSWORD', 'postgres123')
    db_name_env = os.getenv('DB_NAME')

    # Build platform configs
    platforms = {}
    for platform_name, platform_data in config_data.get('platforms', {}).items():
        # Get database config for this platform
        db_config_data = config_data.get('databases', {}).get(platform_name, {})
        
        # Determine DB name: config.yaml > .env > default
        # But for this use case, we want common DB if configured in .env
        db_name = db_config_data.get('name') 
        if not db_name and db_name_env:
            db_name = db_name_env
        if not db_name:
            db_name = f'{platform_name}_db'

        db_config = DatabaseConfig(
            host=db_host,
            port=db_port,
            name=db_name,
            user=db_user,
            password=db_password,
            table=db_config_data.get('table', 'scraped_products')
        )
        
        platforms[platform_name] = PlatformConfig(
            name=platform_name,
            enabled=platform_data.get('enabled', False),
            keywords=platform_data.get('keywords', []),
            max_pages=platform_data.get('max_pages', 5),
            max_products=platform_data.get('max_products', 0),  # 0 = unlimited
            database=db_config,
            selectors=selectors_data.get(platform_name, {})
        )
    
    # Build settings
    settings_data = config_data.get('settings', {})
    settings = Settings(
        headless=settings_data.get('headless', False),
        loop_enabled=settings_data.get('loop_enabled', False),
        loop_interval_minutes=settings_data.get('loop_interval_minutes', 15),
        request_delay=settings_data.get('request_delay', 2),
        scroll_count=settings_data.get('scroll_count', 5),
        retry_count=settings_data.get('retry_count', 3)
    )
    
    return ScraperConfig(platforms=platforms, settings=settings)


def get_enabled_platforms(config: ScraperConfig) -> Dict[str, PlatformConfig]:
    """Get only enabled platforms"""
    return {name: platform for name, platform in config.platforms.items() if platform.enabled}
