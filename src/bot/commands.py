"""
Discord 機器人指令設定
"""

import discord
from discord import app_commands
from discord.ext import commands
import logging
from typing import TYPE_CHECKING

from src.bot.views import AreaYearSelectView, AreaRankSelectView
from src.bot.government_commands import setup_government_data_commands

if TYPE_CHECKING:
    from src.bot.client import CrimeBotClient

logger = logging.getLogger(__name__)

def setup_commands(bot: 'CrimeBotClient'):
    """設定機器人指令"""
    
    # 設定政府資料查詢指令
    setup_government_data_commands(bot)
    
    @bot.tree.command(name="upload", description="上傳 CSV 檔案")
    @app_commands.describe(file="要上傳的 CSV 檔案")
    async def upload_command(interaction: discord.Interaction, file: discord.Attachment):
        """上傳 CSV 檔案指令"""
        try:
            if not file.filename.lower().endswith('.csv'):
                await interaction.response.send_message("❌ 請上傳 CSV 檔案", ephemeral=True)
                return
            
            await interaction.response.defer()
            
            # 檢查檔案大小
            max_size = bot.data_processor.config.MAX_FILE_SIZE_MB * 1024 * 1024
            if file.size > max_size:
                await interaction.followup.send(
                    f"❌ 檔案過大，最大允許 {bot.data_processor.config.MAX_FILE_SIZE_MB}MB",
                    ephemeral=True
                )
                return
            
            file_content = await file.read()
            
            # 處理 CSV 資料
            df = bot.data_processor.load_csv_data(file_content)
            bot.data_processor.set_current_data(df)
            
            # 生成統計資料
            stats = bot.data_processor.generate_statistics(df)
            
            embed = discord.Embed(
                title="✅ CSV 檔案上傳成功",
                description=f"```\n檔案名稱：{file.filename}\n總案件數：{stats['總案件數']} 件\n年份範圍：{stats['年份範圍']}\n```",
                color=0x00ff00
            )
            
            # 顯示可用地區
            if stats['可用地區']:
                area_text = ""
                for area_type, areas in stats['可用地區'].items():
                    area_text += f"{area_type}: {', '.join(areas[:5])}\n"
                embed.add_field(name="可用地區", value=f"```\n{area_text}\n```", inline=False)
            
            await interaction.followup.send(embed=embed)
            logger.info(f"用戶 {interaction.user} 成功上傳檔案: {file.filename}")
            
        except Exception as e:
            logger.error(f"上傳檔案時發生錯誤: {e}")
            await interaction.followup.send(f"❌ 上傳失敗：{str(e)}")
    
    @bot.tree.command(name="summary", description="顯示總覽並選擇地區年份查圖或全年度統計")
    async def summary_command(interaction: discord.Interaction):
        """統計總覽指令"""
        try:
            current_df = bot.data_processor.get_current_data()
            if current_df is not None:
                df = current_df
                data_source = "上傳的資料"
            else:
                df = bot.data_processor.load_default_data()
                data_source = "預設資料"
            
            if df.empty:
                await interaction.response.send_message("❌ 沒有資料可以顯示")
                return
            
            stats = bot.data_processor.generate_statistics(df)
            
            embed = discord.Embed(
                title="📈 犯罪案件統計總覽",
                description=f"```\n資料來源：{data_source}\n總案件數：{stats['總案件數']} 件\n年份範圍：{stats['年份範圍']}\n請選擇地區和年份查看統計圖表或生成全年度統計圖表\n```",
                color=0x2ecc71
            )
            
            view = AreaYearSelectView(df)
            await interaction.response.send_message(embed=embed, view=view)
            logger.info(f"用戶 {interaction.user} 查看統計總覽")
            
        except Exception as e:
            logger.error(f"顯示統計總覽時發生錯誤: {e}")
            await interaction.response.send_message(f"❌ 錯誤：{str(e)}")
    
    @bot.tree.command(name="rank", description="顯示地區排名統計")
    async def rank_command(interaction: discord.Interaction):
        """地區排名統計指令"""
        try:
            current_df = bot.data_processor.get_current_data()
            if current_df is not None:
                df = current_df
                data_source = "上傳的資料"
            else:
                df = bot.data_processor.load_default_data()
                data_source = "預設資料"
            
            if df.empty:
                await interaction.response.send_message("❌ 沒有資料可以顯示")
                return
            
            embed = discord.Embed(
                title="📊 地區排名統計",
                description=f"```\n資料來源：{data_source}\n請先選擇地區，然後選擇排名數量\n```",
                color=0xe74c3c
            )
            
            view = AreaRankSelectView(df)
            await interaction.response.send_message(embed=embed, view=view)
            logger.info(f"用戶 {interaction.user} 查看地區排名")
            
        except Exception as e:
            logger.error(f"顯示地區排名時發生錯誤: {e}")
            await interaction.response.send_message(f"❌ 錯誤：{str(e)}")
    
    @bot.tree.command(name="stats", description="顯示詳細統計資料")
    async def stats_command(interaction: discord.Interaction):
        """詳細統計資料指令"""
        try:
            current_df = bot.data_processor.get_current_data()
            if current_df is not None:
                df = current_df
                data_source = "上傳的資料"
            else:
                df = bot.data_processor.load_default_data()
                data_source = "預設資料"
            
            if df.empty:
                await interaction.response.send_message("❌ 沒有資料可以顯示")
                return
            
            stats = bot.data_processor.generate_statistics(df)
            
            embed = discord.Embed(
                title="📈 詳細統計資料",
                color=0x3498db
            )
            
            embed.add_field(
                name="📊 基本資訊",
                value=f"```\n資料來源：{data_source}\n總案件數：{stats['總案件數']} 件\n年份範圍：{stats['年份範圍']}\n```",
                inline=False
            )
            
            # 顯示可用地區
            if stats['可用地區']:
                area_text = ""
                for area_type, areas in stats['可用地區'].items():
                    area_text += f"{area_type}: {', '.join(areas[:5])}\n"
                embed.add_field(name="🌍 可用地區", value=f"```\n{area_text}\n```", inline=False)
            
            # 案類統計
            if stats['案類統計']:
                top_types = list(stats['案類統計'].items())[:10]
                type_text = "\n".join([f"{i+1:2d}. {case_type}: {count}件" for i, (case_type, count) in enumerate(top_types)])
                embed.add_field(name="📋 前10大案件類型", value=f"```\n{type_text}\n```", inline=False)
            
            await interaction.response.send_message(embed=embed)
            logger.info(f"用戶 {interaction.user} 查看詳細統計")
            
        except Exception as e:
            logger.error(f"顯示詳細統計時發生錯誤: {e}")
            await interaction.response.send_message(f"❌ 錯誤：{str(e)}")
    
    @bot.tree.command(name="clear", description="清除上傳的資料")
    async def clear_command(interaction: discord.Interaction):
        """清除資料指令"""
        try:
            current_df = bot.data_processor.get_current_data()
            if current_df is not None:
                bot.data_processor.clear_current_data()
                await interaction.response.send_message("✅ 已清除上傳的資料，現在將使用預設資料")
                logger.info(f"用戶 {interaction.user} 清除了上傳的資料")
            else:
                await interaction.response.send_message("ℹ️ 目前沒有上傳的資料")
                
        except Exception as e:
            logger.error(f"清除資料時發生錯誤: {e}")
            await interaction.response.send_message(f"❌ 錯誤：{str(e)}")
    
    @bot.tree.command(name="help", description="顯示指令說明")
    async def help_command(interaction: discord.Interaction):
        """幫助指令"""
        embed = discord.Embed(
            title="🤖 犯罪案件統計機器人 - 指令說明",
            description="這是一個功能強大的犯罪案件統計分析機器人",
            color=0x3498db
        )
        
        commands_info = [
            ("📤 `/upload`", "上傳 CSV 檔案進行分析"),
            ("📊 `/summary`", "顯示統計總覽並生成圖表"),
            ("🏆 `/rank`", "顯示地區排名統計"),
            ("📈 `/stats`", "顯示詳細統計資料"),
            ("🗑️ `/clear`", "清除上傳的資料"),
            ("❓ `/help`", "顯示此說明")
        ]
        
        for name, desc in commands_info:
            embed.add_field(name=name, value=desc, inline=False)
        
        embed.set_footer(text="提示：上傳 CSV 檔案後，可以使用其他指令進行詳細分析")
        
        await interaction.response.send_message(embed=embed)
        logger.info(f"用戶 {interaction.user} 查看幫助")
    
    logger.info("指令設定完成")
