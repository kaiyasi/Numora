"""
資料提交相關的 Discord 指令
包含 API 提交和 CSV 上傳功能
"""

import discord
from discord import app_commands
from discord.ext import commands
import asyncio
import logging
from typing import Optional
import pandas as pd
import io
import json
from datetime import datetime

logger = logging.getLogger(__name__)

# 提交頻道 ID
SUBMISSION_CHANNEL_ID = 1429141848781488128

class APISubmissionModal(discord.ui.Modal, title='📡 提交新的 API 資料來源'):
    """API 提交表單"""
    
    api_url = discord.ui.TextInput(
        label='API 網址',
        placeholder='https://example.com/api/data',
        required=True,
        style=discord.TextStyle.short,
        max_length=500
    )
    
    data_format = discord.ui.TextInput(
        label='回傳資料格式',
        placeholder='JSON / CSV / XML',
        required=True,
        style=discord.TextStyle.short,
        max_length=50
    )
    
    email = discord.ui.TextInput(
        label='Email（選填）',
        placeholder='your.email@example.com',
        required=False,
        style=discord.TextStyle.short,
        max_length=100
    )
    
    description = discord.ui.TextInput(
        label='資料說明',
        placeholder='請簡單描述這個 API 提供什麼資料...',
        required=True,
        style=discord.TextStyle.paragraph,
        max_length=1000
    )
    
    sample_data = discord.ui.TextInput(
        label='資料範例（選填）',
        placeholder='貼上回傳資料的範例...',
        required=False,
        style=discord.TextStyle.paragraph,
        max_length=1000
    )
    
    async def on_submit(self, interaction: discord.Interaction):
        await interaction.response.defer(ephemeral=True)
        
        try:
            # 準備提交資訊
            submission_embed = discord.Embed(
                title="📡 新的 API 資料來源提交",
                color=0x3498db,
                timestamp=datetime.now()
            )
            
            submission_embed.add_field(
                name="📌 API 網址",
                value=f"```{self.api_url.value}```",
                inline=False
            )
            
            submission_embed.add_field(
                name="📊 資料格式",
                value=f"`{self.data_format.value}`",
                inline=True
            )
            
            submission_embed.add_field(
                name="👤 提交人",
                value=f"{interaction.user.mention}\nID: `{interaction.user.id}`",
                inline=True
            )
            
            if self.email.value:
                submission_embed.add_field(
                    name="📧 Email",
                    value=f"`{self.email.value}`",
                    inline=True
                )
            
            submission_embed.add_field(
                name="📝 說明",
                value=self.description.value[:500],
                inline=False
            )
            
            if self.sample_data.value:
                submission_embed.add_field(
                    name="📋 資料範例",
                    value=f"```json\n{self.sample_data.value[:500]}\n```",
                    inline=False
                )
            
            submission_embed.set_footer(
                text=f"提交者: {interaction.user.name}",
                icon_url=interaction.user.avatar.url if interaction.user.avatar else None
            )
            
            # 發送到提交頻道
            channel = interaction.client.get_channel(SUBMISSION_CHANNEL_ID)
            if channel:
                await channel.send(embed=submission_embed)
                
                # 回覆提交者
                success_embed = discord.Embed(
                    title="✅ 提交成功",
                    description="您的 API 資料來源已成功提交！\n管理員將會審核您的提交。",
                    color=0x27ae60
                )
                await interaction.followup.send(embed=success_embed, ephemeral=True)
                
                logger.info(f"API 提交成功: {self.api_url.value} by {interaction.user.name}")
            else:
                raise Exception("無法找到提交頻道")
                
        except Exception as e:
            logger.error(f"API 提交失敗: {e}", exc_info=True)
            error_embed = discord.Embed(
                title="❌ 提交失敗",
                description=f"提交過程中發生錯誤：{str(e)}",
                color=0xe74c3c
            )
            await interaction.followup.send(embed=error_embed, ephemeral=True)


class CSVSubmissionModal(discord.ui.Modal, title='📊 提交 CSV 資料集'):
    """CSV 公開提交表單"""
    
    dataset_name = discord.ui.TextInput(
        label='資料集名稱',
        placeholder='例如：台北市停車場資訊',
        required=True,
        style=discord.TextStyle.short,
        max_length=100
    )
    
    email = discord.ui.TextInput(
        label='Email（選填）',
        placeholder='your.email@example.com',
        required=False,
        style=discord.TextStyle.short,
        max_length=100
    )
    
    description = discord.ui.TextInput(
        label='資料說明',
        placeholder='請描述這個資料集的內容、來源、更新頻率等...',
        required=True,
        style=discord.TextStyle.paragraph,
        max_length=1000
    )
    
    data_source = discord.ui.TextInput(
        label='資料來源',
        placeholder='資料的原始來源或網址...',
        required=False,
        style=discord.TextStyle.short,
        max_length=200
    )
    
    async def on_submit(self, interaction: discord.Interaction):
        await interaction.response.defer(ephemeral=True)
        
        # 儲存表單資料，等待檔案上傳
        self.interaction = interaction
        
        # 提示用戶上傳檔案
        upload_embed = discord.Embed(
            title="📤 請上傳 CSV 檔案",
            description="請在接下來的訊息中上傳您的 CSV 檔案。\n\n⏱️ 您有 5 分鐘的時間上傳檔案。",
            color=0xf39c12
        )
        await interaction.followup.send(embed=upload_embed, ephemeral=True)


class SubmissionCommands(commands.Cog):
    """資料提交指令"""
    
    def __init__(self, bot):
        self.bot = bot
    
    @app_commands.command(name="submit_api", description="📡 提交新的 API 資料來源")
    async def submit_api(self, interaction: discord.Interaction):
        """提交 API 資料來源"""
        modal = APISubmissionModal()
        await interaction.response.send_modal(modal)
    
    @app_commands.command(name="submit_csv", description="📊 提交 CSV 資料集（公開）")
    async def submit_csv_public(self, interaction: discord.Interaction):
        """提交 CSV 資料集（公開使用）"""
        modal = CSVSubmissionModal()
        await interaction.response.send_modal(modal)
        
        # 等待表單提交
        try:
            await modal.wait()
            if hasattr(modal, 'interaction'):
                # 等待用戶上傳檔案
                def check(m):
                    return (m.author.id == interaction.user.id and 
                           m.attachments and 
                           m.attachments[0].filename.endswith('.csv'))
                
                try:
                    message = await self.bot.wait_for('message', timeout=300.0, check=check)
                    attachment = message.attachments[0]
                    
                    # 下載並驗證 CSV
                    csv_data = await attachment.read()
                    
                    try:
                        # 驗證 CSV 格式
                        df = pd.read_csv(io.BytesIO(csv_data))
                        rows = len(df)
                        cols = len(df.columns)
                        
                        # 準備提交資訊
                        submission_embed = discord.Embed(
                            title="📊 新的 CSV 資料集提交",
                            color=0x9b59b6,
                            timestamp=datetime.now()
                        )
                        
                        submission_embed.add_field(
                            name="📌 資料集名稱",
                            value=f"`{modal.dataset_name.value}`",
                            inline=False
                        )
                        
                        submission_embed.add_field(
                            name="📊 檔案資訊",
                            value=f"```\n檔名: {attachment.filename}\n大小: {attachment.size / 1024:.2f} KB\n資料筆數: {rows} 筆\n欄位數: {cols} 個\n```",
                            inline=False
                        )
                        
                        submission_embed.add_field(
                            name="👤 提交人",
                            value=f"{interaction.user.mention}\nID: `{interaction.user.id}`",
                            inline=True
                        )
                        
                        if modal.email.value:
                            submission_embed.add_field(
                                name="📧 Email",
                                value=f"`{modal.email.value}`",
                                inline=True
                            )
                        
                        submission_embed.add_field(
                            name="📝 說明",
                            value=modal.description.value[:500],
                            inline=False
                        )
                        
                        if modal.data_source.value:
                            submission_embed.add_field(
                                name="🔗 資料來源",
                                value=modal.data_source.value[:200],
                                inline=False
                            )
                        
                        # 顯示欄位預覽
                        columns_preview = ", ".join(df.columns[:10].tolist())
                        if len(df.columns) > 10:
                            columns_preview += f" ... (共 {len(df.columns)} 個欄位)"
                        submission_embed.add_field(
                            name="📋 欄位預覽",
                            value=f"```{columns_preview}```",
                            inline=False
                        )
                        
                        submission_embed.set_footer(
                            text=f"提交者: {interaction.user.name}",
                            icon_url=interaction.user.avatar.url if interaction.user.avatar else None
                        )
                        
                        # 發送到提交頻道
                        channel = self.bot.get_channel(SUBMISSION_CHANNEL_ID)
                        if channel:
                            # 發送 embed
                            await channel.send(embed=submission_embed)
                            # 發送檔案
                            await channel.send(
                                content=f"**📎 CSV 檔案：** `{attachment.filename}`",
                                file=await attachment.to_file()
                            )
                            
                            # 回覆提交者
                            success_embed = discord.Embed(
                                title="✅ 提交成功",
                                description=f"您的 CSV 資料集已成功提交！\n\n**資料集：** {modal.dataset_name.value}\n**筆數：** {rows} 筆\n**欄位：** {cols} 個\n\n管理員將會審核您的提交。",
                                color=0x27ae60
                            )
                            await message.reply(embed=success_embed)
                            
                            logger.info(f"CSV 提交成功: {modal.dataset_name.value} by {interaction.user.name}")
                        else:
                            raise Exception("無法找到提交頻道")
                            
                    except Exception as e:
                        error_embed = discord.Embed(
                            title="❌ CSV 格式錯誤",
                            description=f"無法解析 CSV 檔案：{str(e)}",
                            color=0xe74c3c
                        )
                        await message.reply(embed=error_embed)
                        
                except asyncio.TimeoutError:
                    timeout_embed = discord.Embed(
                        title="⏱️ 上傳逾時",
                        description="上傳時間已超過 5 分鐘，請重新提交。",
                        color=0xe74c3c
                    )
                    await interaction.followup.send(embed=timeout_embed, ephemeral=True)
                    
        except Exception as e:
            logger.error(f"CSV 提交處理失敗: {e}", exc_info=True)
    
    @app_commands.command(name="upload_csv", description="📁 上傳 CSV 進行個人分析（單次有效）")
    async def upload_csv_temp(self, interaction: discord.Interaction):
        """上傳 CSV 進行臨時分析"""
        await interaction.response.defer(ephemeral=True)
        
        # 提示用戶上傳檔案
        upload_embed = discord.Embed(
            title="📤 請上傳 CSV 檔案",
            description=(
                "請在接下來的訊息中上傳您的 CSV 檔案。\n\n"
                "**注意事項：**\n"
                "• 此為臨時分析功能，資料不會被儲存\n"
                "• 僅供您個人使用\n"
                "• 檔案大小限制：8 MB\n"
                "⏱️ 您有 5 分鐘的時間上傳檔案。"
            ),
            color=0x3498db
        )
        await interaction.followup.send(embed=upload_embed, ephemeral=True)
        
        # 等待用戶上傳檔案
        def check(m):
            return (m.author.id == interaction.user.id and 
                   m.attachments and 
                   m.attachments[0].filename.endswith('.csv'))
        
        try:
            message = await self.bot.wait_for('message', timeout=300.0, check=check)
            attachment = message.attachments[0]
            
            # 檢查檔案大小
            if attachment.size > 8 * 1024 * 1024:  # 8 MB
                error_embed = discord.Embed(
                    title="❌ 檔案過大",
                    description="檔案大小超過 8 MB 限制。",
                    color=0xe74c3c
                )
                await message.reply(embed=error_embed, delete_after=10)
                return
            
            # 下載並分析 CSV
            csv_data = await attachment.read()
            
            try:
                # 讀取 CSV
                df = pd.read_csv(io.BytesIO(csv_data))
                rows = len(df)
                cols = len(df.columns)
                
                # 生成分析報告
                analysis_embed = discord.Embed(
                    title=f"📊 CSV 分析結果：{attachment.filename}",
                    color=0x27ae60
                )
                
                analysis_embed.add_field(
                    name="📈 基本統計",
                    value=f"```\n資料筆數：{rows:,} 筆\n欄位數量：{cols} 個\n檔案大小：{attachment.size / 1024:.2f} KB\n```",
                    inline=False
                )
                
                # 欄位資訊
                columns_info = []
                for col in df.columns[:10]:
                    dtype = str(df[col].dtype)
                    non_null = df[col].count()
                    columns_info.append(f"• {col} ({dtype}) - {non_null}/{rows} 非空值")
                
                if len(df.columns) > 10:
                    columns_info.append(f"... 還有 {len(df.columns) - 10} 個欄位")
                
                analysis_embed.add_field(
                    name="📋 欄位資訊",
                    value="```\n" + "\n".join(columns_info) + "\n```",
                    inline=False
                )
                
                # 資料預覽
                preview = df.head(3).to_string(max_cols=5, max_colwidth=20)
                if len(preview) > 500:
                    preview = preview[:500] + "..."
                
                analysis_embed.add_field(
                    name="👀 資料預覽（前 3 筆）",
                    value=f"```\n{preview}\n```",
                    inline=False
                )
                
                # 數值欄位統計
                numeric_cols = df.select_dtypes(include=['int64', 'float64']).columns
                if len(numeric_cols) > 0:
                    stats_info = []
                    for col in numeric_cols[:3]:
                        mean_val = df[col].mean()
                        max_val = df[col].max()
                        min_val = df[col].min()
                        stats_info.append(f"• {col}: 平均={mean_val:.2f}, 最大={max_val:.2f}, 最小={min_val:.2f}")
                    
                    if len(numeric_cols) > 3:
                        stats_info.append(f"... 還有 {len(numeric_cols) - 3} 個數值欄位")
                    
                    analysis_embed.add_field(
                        name="📊 數值統計（前 3 個欄位）",
                        value="```\n" + "\n".join(stats_info) + "\n```",
                        inline=False
                    )
                
                analysis_embed.set_footer(text="💡 這是臨時分析，資料不會被儲存")
                
                await message.reply(embed=analysis_embed)
                
                logger.info(f"CSV 臨時分析完成: {attachment.filename} by {interaction.user.name}")
                
            except Exception as e:
                error_embed = discord.Embed(
                    title="❌ CSV 處理錯誤",
                    description=f"無法處理 CSV 檔案：{str(e)}",
                    color=0xe74c3c
                )
                await message.reply(embed=error_embed)
                
        except asyncio.TimeoutError:
            timeout_embed = discord.Embed(
                title="⏱️ 上傳逾時",
                description="上傳時間已超過 5 分鐘，請重新使用指令。",
                color=0xe74c3c
            )
            # 嘗試發送 followup（如果還在時限內）
            try:
                await interaction.followup.send(embed=timeout_embed, ephemeral=True)
            except:
                pass


async def setup(bot):
    await bot.add_cog(SubmissionCommands(bot))

