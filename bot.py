"""
現代化的 Discord 犯罪案件統計機器人
模組化版本 - 主程式入口
"""

import discord
from discord.ext import commands
import asyncio
import sys
import os

# 添加 src 目錄到 Python 路徑
sys.path.append(os.path.join(os.path.dirname(__file__), 'src'))

from src.utils.config import config
from src.utils.logger import setup_logging
from src.bot.client import CrimeBotClient

def main():
    """主程式入口"""
    try:
        # 設定日誌
        logger = setup_logging()
        logger.info("啟動犯罪案件統計機器人...")
        
        # 驗證配置
        config.validate()
        
        # 創建並啟動機器人
        bot = CrimeBotClient()
        bot.run(config.DISCORD_TOKEN)
        
    except KeyboardInterrupt:
        logger.info("收到中斷信號，正在關閉機器人...")
    except Exception as e:
        logger.error(f"啟動機器人時發生錯誤: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()
