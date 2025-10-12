"""
Discord UI 元件 (Views, Selects, Buttons)
"""

import discord
from discord.ui import View, Select, Button
import os
import logging
from typing import TYPE_CHECKING

from src.charts.generator import ChartGenerator
from src.data.area_analyzer import AreaAnalyzer

if TYPE_CHECKING:
    import pandas as pd

logger = logging.getLogger(__name__)

class AreaYearSelectView(View):
    """地區和年份選擇視圖"""
    
    def __init__(self, df: 'pd.DataFrame'):
        super().__init__(timeout=300)
        self.df = df
        self.current_area = None
        self.current_year = None
        self.chart_generator = ChartGenerator()
        self.area_analyzer = AreaAnalyzer()
        self.areas_info = self.area_analyzer.extract_area_info(df)
        self._setup_selects()
    
    def _setup_selects(self):
        """設定選擇器"""
        self.clear_items()
        
        # 地區選擇
        area_options = [discord.SelectOption(label="全部地區", value="全部地區", description="查看所有地區統計")]
        
        for area_type, areas in self.areas_info.items():
            for area in areas[:10]:  # 限制顯示數量
                is_current = area == self.current_area
                label = f"📍 {area}" if is_current else area
                area_options.append(discord.SelectOption(
                    label=label,
                    value=area,
                    description=f"查看 {area} 的統計" + (" (目前選擇)" if is_current else "")
                ))
        
        area_select = Select(
            placeholder="選擇地區..." if not self.current_area else f"目前地區：{self.current_area}",
            options=area_options[:25],  # Discord 限制25個選項
            row=0
        )
        
        # 年份選擇
        years = sorted(self.df['年份'].unique())
        year_options = []
        
        for year in years:
            is_current = year == self.current_year
            label = f"📊 {year}" if is_current else str(year)
            year_options.append(discord.SelectOption(
                label=label,
                value=str(year),
                description=f"查看 {year} 年統計" + (" (目前選擇)" if is_current else "")
            ))
        
        # 新增「全年度統計」選項
        year_options.append(discord.SelectOption(
            label="📊 全年度統計",
            value="全年度統計",
            description="生成全年度統計圖表"
        ))
        
        year_placeholder = "選擇年份..."
        if self.current_year:
            year_placeholder = f"目前年份：{self.current_year}"
        elif hasattr(self, 'is_yearly_selected') and self.is_yearly_selected:
            year_placeholder = "目前：全年度統計"
        
        year_select = Select(
            placeholder=year_placeholder,
            options=year_options,
            row=1
        )
        
        async def area_callback(interaction):
            await interaction.response.defer()
            self.current_area = area_select.values[0]
            await self._update_display(interaction)
        
        async def year_callback(interaction):
            await interaction.response.defer()
            selected_year = year_select.values[0]
            
            if selected_year == "全年度統計":
                await self._handle_yearly_stats(interaction)
            else:
                self.is_yearly_selected = False
                self.current_year = int(selected_year)
                await self._update_display(interaction)
        
        area_select.callback = area_callback
        year_select.callback = year_callback
        
        self.add_item(area_select)
        self.add_item(year_select)
    
    async def _handle_yearly_stats(self, interaction):
        """處理全年度統計"""
        self.is_yearly_selected = True
        self.current_year = None
        area = self.current_area if self.current_area else "全部地區"
        
        try:
            filename = self.chart_generator.generate_yearly_plot(self.df, area)
            if not filename or not os.path.exists(filename):
                embed = discord.Embed(
                    title="❌ 錯誤",
                    description="全年度統計圖表生成失敗",
                    color=0xe74c3c
                )
                self._setup_selects()
                await interaction.edit_original_response(embed=embed, view=self)
                return
            
            embed = discord.Embed(
                title=f"📊 {area} - 全年度統計圖表",
                description=f"```\n地區：{area}\n```",
                color=0x3498db
            )
            embed.set_image(url=f"attachment://{filename}")
            
            self._setup_selects()
            
            with open(filename, 'rb') as f:
                file = discord.File(f, filename=filename)
                await interaction.edit_original_response(
                    content=None,
                    embed=embed,
                    attachments=[file],
                    view=self
                )
            
            # 清理暫存檔案
            self._cleanup_file(filename)
            
        except Exception as e:
            logger.error(f"處理全年度統計時發生錯誤: {e}")
            await interaction.edit_original_response(
                content=f"❌ 圖表處理錯誤: {str(e)}",
                embed=None,
                attachments=[],
                view=self
            )
    
    async def _update_display(self, interaction):
        """更新顯示"""
        if self.current_area and self.current_year:
            try:
                filename = self.chart_generator.generate_area_year_plot(
                    self.df, self.current_area, self.current_year
                )
                
                if not filename or not os.path.exists(filename):
                    self._setup_selects()
                    await interaction.edit_original_response(
                        content=f"❌ {self.current_area} - {self.current_year} 年沒有有效資料或圖表生成失敗",
                        embed=None,
                        attachments=[],
                        view=self
                    )
                    return
                
                area_text = self.current_area if self.current_area != '全部地區' else '全部地區'
                embed = discord.Embed(
                    title=f"📊 {area_text} - {self.current_year} 年犯罪統計圖",
                    description=f"```\n地區：{area_text}\n年份：{self.current_year} 年\n```",
                    color=0x3498db
                )
                embed.set_image(url=f"attachment://{filename}")
                
                self._setup_selects()
                
                with open(filename, 'rb') as f:
                    file = discord.File(f, filename=filename)
                    await interaction.edit_original_response(
                        content=None,
                        embed=embed,
                        attachments=[file],
                        view=self
                    )
                
                self._cleanup_file(filename)
                
            except Exception as e:
                logger.error(f"更新顯示時發生錯誤: {e}")
                await interaction.edit_original_response(
                    content=f"❌ 圖表處理錯誤: {str(e)}",
                    embed=None,
                    attachments=[],
                    view=self
                )
        else:
            self._setup_selects()
            await interaction.edit_original_response(view=self)
    
    def _cleanup_file(self, filename: str):
        """清理暫存檔案"""
        try:
            if os.path.exists(filename):
                os.remove(filename)
                logger.info(f"已移除暫存圖表: {filename}")
        except Exception as e:
            logger.warning(f"移除圖表檔案失敗: {str(e)}")


class AreaRankSelectView(View):
    """地區排名選擇視圖"""
    
    def __init__(self, df: 'pd.DataFrame'):
        super().__init__(timeout=300)
        self.df = df
        self.current_area = None
        self.chart_generator = ChartGenerator()
        self.area_analyzer = AreaAnalyzer()
        self.areas_info = self.area_analyzer.extract_area_info(df)
        self._setup_controls()
    
    def _setup_controls(self):
        """設定控制項"""
        self.clear_items()
        
        # 地區選擇
        area_options = [discord.SelectOption(label="全部地區", value="全部地區")]
        
        for area_type, areas in self.areas_info.items():
            for area in areas[:20]:
                is_current = area == self.current_area
                label = f"📍 {area}" if is_current else area
                area_options.append(discord.SelectOption(label=label, value=area))
        
        area_select = Select(
            placeholder="選擇地區..." if not self.current_area else f"目前：{self.current_area}",
            options=area_options[:25],
            row=0
        )
        
        async def area_callback(interaction):
            await interaction.response.defer()
            self.current_area = area_select.values[0]
            self._setup_controls()
            await interaction.edit_original_response(view=self)
        
        area_select.callback = area_callback
        self.add_item(area_select)
        
        # 排名按鈕
        if self.current_area:
            rank_options = [
                ("前5名", 5, "🥇"),
                ("前10名", 10, "🏆"),
                ("前15名", 15, "📊"),
                ("前20名", 20, "📈")
            ]
            
            for label, top_n, emoji in rank_options:
                button = Button(label=f"{emoji} {label}", style=discord.ButtonStyle.primary, row=1)
                
                async def button_callback(interaction, n=top_n):
                    try:
                        await interaction.response.defer()
                        
                        filename = self.chart_generator.generate_area_rank_plot(self.df, self.current_area, n)
                        
                        if not filename:
                            await interaction.followup.send("❌ 無法產生圖表", ephemeral=True)
                            return
                        
                        area_text = self.current_area if self.current_area != '全部地區' else '全部地區'
                        embed = discord.Embed(
                            title=f"🔥 {area_text} - 前{n}案件熱點",
                            description=f"```\n地區：{area_text}\n排名：前{n}名\n```",
                            color=0xe74c3c
                        )
                        embed.set_image(url=f"attachment://{filename}")
                        
                        with open(filename, 'rb') as f:
                            file = discord.File(f, filename=filename)
                            await interaction.edit_original_response(
                                embed=embed,
                                attachments=[file],
                                view=self
                            )
                        
                        self._cleanup_file(filename)
                        
                    except Exception as e:
                        logger.error(f"生成排名圖表時發生錯誤: {e}")
                        await interaction.followup.send(f"❌ 錯誤：{str(e)}", ephemeral=True)
                
                button.callback = button_callback
                self.add_item(button)
    
    def _cleanup_file(self, filename: str):
        """清理暫存檔案"""
        try:
            if os.path.exists(filename):
                os.remove(filename)
                logger.info(f"已移除暫存圖表: {filename}")
        except Exception as e:
            logger.warning(f"移除圖表檔案失敗: {str(e)}")
