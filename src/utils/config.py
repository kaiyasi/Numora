"""
配置管理模組
處理環境變數和應用程式設定
"""

import os
from typing import Optional
from dotenv import load_dotenv

# 載入環境變數
load_dotenv()

class Config:
    """應用程式配置類"""
    
    # Discord 設定
    DISCORD_TOKEN: str = os.getenv('DISCORD_TOKEN', '')
    ADMIN_CHANNEL_ID: Optional[int] = int(os.getenv('ADMIN_CHANNEL_ID', '0')) or None
    
    # 資料庫設定
    DATABASE_URL: str = os.getenv('DATABASE_URL', 'sqlite:///crime_data.db')
    
    # 除錯模式
    DEBUG: bool = os.getenv('DEBUG', 'False').lower() == 'true'
    
    # API 金鑰
    OPENAI_API_KEY: str = os.getenv('OPENAI_API_KEY', '')
    GOOGLE_MAPS_API_KEY: str = os.getenv('GOOGLE_MAPS_API_KEY', '')
    
    # 檔案上傳限制
    MAX_FILE_SIZE_MB: int = int(os.getenv('MAX_FILE_SIZE_MB', '50'))
    ALLOWED_FILE_TYPES: list = os.getenv('ALLOWED_FILE_TYPES', 'csv,xlsx,json').split(',')
    
    # 圖表設定
    DEFAULT_CHART_WIDTH: int = int(os.getenv('DEFAULT_CHART_WIDTH', '1200'))
    DEFAULT_CHART_HEIGHT: int = int(os.getenv('DEFAULT_CHART_HEIGHT', '800'))
    CHART_DPI: int = int(os.getenv('CHART_DPI', '150'))
    
    # 快取設定
    ENABLE_CACHE: bool = os.getenv('ENABLE_CACHE', 'True').lower() == 'true'
    CACHE_TTL_SECONDS: int = int(os.getenv('CACHE_TTL_SECONDS', '3600'))
    
    # 字型設定
    FONT_PATH: str = os.getenv('FONT_PATH', './Huninn-Regular.ttf')
    
    @classmethod
    def validate(cls) -> bool:
        """驗證必要的配置是否已設定"""
        if not cls.DISCORD_TOKEN:
            raise ValueError("DISCORD_TOKEN 環境變數未設定")
        return True

# 創建全域配置實例
config = Config()
