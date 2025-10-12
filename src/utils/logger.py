"""
日誌配置模組
"""

import logging
import os
from datetime import datetime
from src.utils.config import config

def setup_logging():
    """設定日誌配置"""
    
    # 創建 logs 目錄
    os.makedirs('logs', exist_ok=True)
    
    # 設定日誌格式
    formatter = logging.Formatter(
        '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )
    
    # 設定日誌等級
    level = logging.DEBUG if config.DEBUG else logging.INFO
    
    # 創建根日誌記錄器
    logger = logging.getLogger()
    logger.setLevel(level)
    
    # 清除現有的處理器
    logger.handlers.clear()
    
    # 控制台處理器
    console_handler = logging.StreamHandler()
    console_handler.setFormatter(formatter)
    logger.addHandler(console_handler)
    
    # 檔案處理器
    today = datetime.now().strftime('%Y-%m-%d')
    file_handler = logging.FileHandler(
        f'logs/bot_{today}.log', 
        encoding='utf-8'
    )
    file_handler.setFormatter(formatter)
    logger.addHandler(file_handler)
    
    # 錯誤檔案處理器
    error_handler = logging.FileHandler(
        f'logs/error_{today}.log', 
        encoding='utf-8'
    )
    error_handler.setLevel(logging.ERROR)
    error_handler.setFormatter(formatter)
    logger.addHandler(error_handler)
    
    return logger
