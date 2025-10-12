"""
Discord 機器人客戶端
"""

import discord
from discord.ext import commands
import logging
from typing import Optional

from src.data.processor import DataProcessor
from src.bot.commands import setup_commands
from src.bot.views import *
from src.utils.config import config

logger = logging.getLogger(__name__)

class CrimeBotClient(commands.Bot):
    """犯罪案件統計機器人客戶端"""
    
    def __init__(self):
        # 設定 Discord intents
        intents = discord.Intents.default()
        intents.message_content = True
        
        super().__init__(
            command_prefix='!',
            intents=intents,
            help_command=None
        )
        
        # 初始化資料處理器
        self.data_processor = DataProcessor()
        
        # 設定指令
        setup_commands(self)
    
    async def setup_hook(self):
        """機器人設定鉤子"""
        try:
            # 同步指令樹
            await self.tree.sync()
            logger.info("指令樹同步完成")
        except Exception as e:
            logger.error(f"同步指令樹時發生錯誤: {e}")
    
    async def on_ready(self):
        """機器人就緒事件"""
        logger.info(f"機器人已上線：{self.user.name} (ID: {self.user.id})")
        logger.info(f"已加入 {len(self.guilds)} 個伺服器")
        
        # 設定機器人狀態
        activity = discord.Activity(
            type=discord.ActivityType.watching,
            name="犯罪案件統計數據"
        )
        await self.change_presence(activity=activity)
    
    async def on_guild_join(self, guild):
        """加入新伺服器事件"""
        logger.info(f"加入新伺服器：{guild.name} (ID: {guild.id})")
    
    async def on_guild_remove(self, guild):
        """離開伺服器事件"""
        logger.info(f"離開伺服器：{guild.name} (ID: {guild.id})")
    
    async def on_command_error(self, ctx, error):
        """指令錯誤處理"""
        if isinstance(error, commands.CommandNotFound):
            return
        
        logger.error(f"指令錯誤: {error}")
        
        if isinstance(error, commands.MissingPermissions):
            await ctx.send("❌ 您沒有權限執行此指令")
        elif isinstance(error, commands.BotMissingPermissions):
            await ctx.send("❌ 機器人缺少必要權限")
        else:
            await ctx.send(f"❌ 發生錯誤：{str(error)}")
    
    async def on_application_command_error(self, interaction, error):
        """應用程式指令錯誤處理"""
        logger.error(f"應用程式指令錯誤: {error}")
        
        try:
            if not interaction.response.is_done():
                await interaction.response.send_message(
                    f"❌ 發生錯誤：{str(error)}", 
                    ephemeral=True
                )
            else:
                await interaction.followup.send(
                    f"❌ 發生錯誤：{str(error)}", 
                    ephemeral=True
                )
        except Exception as e:
            logger.error(f"發送錯誤訊息時發生錯誤: {e}")
    
    def get_data_processor(self) -> DataProcessor:
        """取得資料處理器"""
        return self.data_processor
