"""
政府公開資料相關的 Discord 指令
"""

import discord
from discord import app_commands
from discord.ext import commands
import asyncio
import logging
from typing import Optional, List
import pandas as pd

from src.utils.government_data import GovernmentDataAPI, DataAnalyzer

logger = logging.getLogger(__name__)

class GovernmentDataView(discord.ui.View):
    """政府資料查詢視圖"""
    
    def __init__(self):
        super().__init__(timeout=300)
        self.api = GovernmentDataAPI()
        self.analyzer = DataAnalyzer()
    
    @discord.ui.select(
        placeholder="選擇要查詢的資料類型...",
        options=[
            discord.SelectOption(label="🚴 YouBike 即時資訊", value="youbike", description="台北市 YouBike 2.0 即時車輛數量"),
            discord.SelectOption(label="📶 WiFi 熱點", value="wifi", description="台北市免費 WiFi 熱點位置"),
            discord.SelectOption(label="🗑️ 垃圾車位置", value="garbage", description="台北市垃圾車即時位置"),
            discord.SelectOption(label="🌤️ 氣象預報", value="weather", description="中央氣象署天氣預報（需API Key）"),
            discord.SelectOption(label="🛣️ 交通資訊", value="traffic", description="高速公路即時路況資訊"),
            discord.SelectOption(label="📊 資料集搜尋", value="search", description="搜尋政府資料集"),
            discord.SelectOption(label="📋 可用資料集", value="datasets", description="查看所有可用資料集"),
            discord.SelectOption(label="🏙️ 台北市總覽", value="taipei_overview", description="台北市綜合資料分析"),
        ]
    )
    async def select_data_type(self, interaction: discord.Interaction, select: discord.ui.Select):
        await interaction.response.defer()
        
        data_type = select.values[0]
        
        if data_type == "taipei_overview":
            # 台北市綜合分析
            await self.show_taipei_overview(interaction)
        elif data_type == "search":
            # 資料集搜尋
            await self.show_search_prompt(interaction)
        elif data_type == "datasets":
            # 顯示可用資料集
            await self.show_available_datasets(interaction)
        else:
            # 直接查詢資料
            await self.query_data(interaction, data_type)
    
    async def show_taipei_overview(self, interaction: discord.Interaction):
        """顯示台北市綜合資料分析"""
        try:
            embed = discord.Embed(
                title="🔍 正在分析台北市資料...",
                description="整合 YouBike、WiFi 熱點等資料",
                color=0xf39c12
            )
            await interaction.edit_original_response(embed=embed, view=None)
            
            analysis_result = await self.analyzer.analyze_area_data("台北市")
            
            if analysis_result and 'data' in analysis_result:
                embed = discord.Embed(
                    title="🏙️ 台北市資料總覽",
                    color=0x27ae60
                )
                
                # 顯示各類資料統計
                data = analysis_result['data']
                if 'youbike' in data:
                    youbike_count = data['youbike']['count']
                    embed.add_field(
                        name="🚴 YouBike 站點",
                        value=f"```\n共 {youbike_count} 個站點\n```",
                        inline=True
                    )
                
                if 'wifi' in data:
                    wifi_count = data['wifi']['count']
                    embed.add_field(
                        name="📶 WiFi 熱點",
                        value=f"```\n共 {wifi_count} 個熱點\n```",
                        inline=True
                    )
                
                embed.set_footer(text=f"資料更新時間：{analysis_result.get('generated_at', 'N/A')}")
            else:
                embed = discord.Embed(
                    title="❌ 分析失敗",
                    description=analysis_result.get('message', '無法獲取台北市資料進行分析'),
                    color=0xe74c3c
                )
            
            await interaction.edit_original_response(embed=embed)
            
        except Exception as e:
            logger.error(f"台北市綜合分析時發生錯誤: {e}")
            embed = discord.Embed(
                title="❌ 分析過程發生錯誤",
                description=f"錯誤訊息：{str(e)}",
                color=0xe74c3c
            )
            await interaction.edit_original_response(embed=embed)
    
    async def show_search_prompt(self, interaction: discord.Interaction):
        """顯示搜尋提示"""
        embed = discord.Embed(
            title="🔍 資料集搜尋",
            description="請使用 `/gov_search` 指令並提供搜尋關鍵字",
            color=0x3498db
        )
        embed.add_field(
            name="使用範例",
            value="```\n/gov_search keyword:交通\n/gov_search keyword:醫療\n/gov_search keyword:環境\n```",
            inline=False
        )
        await interaction.edit_original_response(embed=embed, view=None)
    
    async def show_available_datasets(self, interaction: discord.Interaction):
        """顯示可用資料集"""
        try:
            embed = discord.Embed(
                title="📋 可用的政府資料集",
                color=0x3498db
            )
            
            available_datasets = self.api.get_available_datasets()
            
            # 分類顯示
            api_datasets = []
            download_datasets = []
            
            for name, key in available_datasets.items():
                if "(手動下載)" in name:
                    download_datasets.append(name.replace(" (手動下載)", ""))
                else:
                    api_datasets.append(name)
            
            if api_datasets:
                embed.add_field(
                    name="🔗 API 即時資料",
                    value="• " + "\n• ".join(api_datasets),
                    inline=False
                )
            
            if download_datasets:
                embed.add_field(
                    name="📥 手動下載資料",
                    value="• " + "\n• ".join(download_datasets),
                    inline=False
                )
            
            embed.set_footer(text="使用選單或指令查詢特定資料")
            await interaction.edit_original_response(embed=embed, view=None)
            
        except Exception as e:
            logger.error(f"顯示可用資料集時發生錯誤: {e}")
            embed = discord.Embed(
                title="❌ 無法載入資料集列表",
                description=f"錯誤訊息：{str(e)}",
                color=0xe74c3c
            )
            await interaction.edit_original_response(embed=embed)
    
    async def query_data(self, interaction: discord.Interaction, data_type: str):
        """查詢特定類型的資料"""
        try:
            embed = discord.Embed(
                title="🔍 正在查詢政府公開資料...",
                description=f"查詢類型：{data_type}",
                color=0xf39c12
            )
            await interaction.edit_original_response(embed=embed, view=None)
            
            async with self.api as api:
                df = None
                result_data = None
                
                if data_type == "youbike":
                    df = await api.get_taipei_youbike_data()
                    data_name = "YouBike 2.0 即時資訊"
                elif data_type == "wifi":
                    df = await api.get_taipei_wifi_data()
                    data_name = "WiFi 熱點資訊"
                elif data_type == "weather":
                    embed = discord.Embed(
                        title="⚠️ 需要 API Key",
                        description="氣象署資料需要申請 API Key 才能使用",
                        color=0xf39c12
                    )
                    embed.add_field(
                        name="申請方式",
                        value="請至中央氣象署開放資料平臺申請：\nhttps://opendata.cwb.gov.tw/",
                        inline=False
                    )
                    await interaction.edit_original_response(embed=embed)
                    return
                elif data_type == "traffic":
                    result_data = await api.get_freeway_traffic_info()
                    data_name = "高速公路交通資訊"
                else:
                    embed = discord.Embed(
                        title="❌ 不支援的資料類型",
                        description=f"目前不支援 {data_type} 類型的查詢",
                        color=0xe74c3c
                    )
                    await interaction.edit_original_response(embed=embed)
                    return
                
                if df is not None and not df.empty:
                    # 成功獲取 DataFrame 資料
                    embed = discord.Embed(
                        title=f"✅ {data_name}查詢成功",
                        color=0x27ae60
                    )
                    
                    embed.add_field(
                        name="📊 資料統計",
                        value=f"```\n資料筆數：{len(df)} 筆\n欄位數量：{len(df.columns)} 個\n```",
                        inline=False
                    )
                    
                    # 顯示前幾筆資料
                    if len(df) > 0:
                        sample_data = df.head(3).to_string(max_cols=3, max_colwidth=20)
                        embed.add_field(
                            name="📋 資料預覽",
                            value=f"```\n{sample_data[:500]}...\n```",
                            inline=False
                        )
                    
                elif result_data is not None:
                    # 成功獲取其他類型資料
                    embed = discord.Embed(
                        title=f"✅ {data_name}查詢成功",
                        color=0x27ae60
                    )
                    
                    embed.add_field(
                        name="📊 資料內容",
                        value=f"```json\n{json.dumps(result_data, indent=2, ensure_ascii=False)[:500]}...\n```",
                        inline=False
                    )
                    
                else:
                    embed = discord.Embed(
                        title="❌ 查詢失敗",
                        description=f"無法獲取{data_name}，可能是 API 暫時無法使用",
                        color=0xe74c3c
                    )
                
                await interaction.edit_original_response(embed=embed)
                
        except Exception as e:
            logger.error(f"查詢政府資料時發生錯誤: {e}")
            embed = discord.Embed(
                title="❌ 查詢過程發生錯誤",
                description=f"錯誤訊息：{str(e)}",
                color=0xe74c3c
            )
            await interaction.edit_original_response(embed=embed)

class AreaInputModal(discord.ui.Modal):
    """地區輸入模態"""
    
    def __init__(self, analyzer: DataAnalyzer):
        super().__init__(title="地區綜合分析")
        self.analyzer = analyzer
    
    area_input = discord.ui.TextInput(
        label="地區名稱",
        placeholder="請輸入地區名稱，例如：台北市",
        required=True,
        max_length=20
    )
    
    async def on_submit(self, interaction: discord.Interaction):
        await interaction.response.defer()
        
        area = self.area_input.value
        
        embed = discord.Embed(
            title="🔍 正在進行綜合分析...",
            description=f"分析地區：{area}",
            color=0xf39c12
        )
        await interaction.edit_original_response(embed=embed)
        
        # 執行綜合分析
        analysis_result = await self.analyzer.analyze_crime_correlation(area)
        
        if analysis_result:
            embed = discord.Embed(
                title=f"📊 {area} 綜合分析報告",
                color=0x27ae60
            )
            
            # 資料來源
            if analysis_result.get('data_sources'):
                sources = ", ".join(analysis_result['data_sources'])
                embed.add_field(
                    name="📋 資料來源",
                    value=f"```\n{sources}\n```",
                    inline=False
                )
            
            # 統計資訊
            stats = []
            if 'crime_count' in analysis_result:
                stats.append(f"犯罪資料：{analysis_result['crime_count']} 筆")
            if 'population_count' in analysis_result:
                stats.append(f"人口資料：{analysis_result['population_count']} 筆")
            if 'school_count' in analysis_result:
                stats.append(f"學校資料：{analysis_result['school_count']} 筆")
            if 'hospital_count' in analysis_result:
                stats.append(f"醫療機構：{analysis_result['hospital_count']} 筆")
            
            if stats:
                embed.add_field(
                    name="📈 統計摘要",
                    value=f"```\n" + "\n".join(stats) + "\n```",
                    inline=False
                )
            
            # 分析洞察
            if analysis_result.get('insights'):
                insights = "\n".join(analysis_result['insights'])
                embed.add_field(
                    name="💡 分析洞察",
                    value=f"```\n{insights}\n```",
                    inline=False
                )
            
            embed.set_footer(text=f"分析時間：{analysis_result.get('analysis_date', 'N/A')}")
        else:
            embed = discord.Embed(
                title="❌ 分析失敗",
                description=f"無法獲取 {area} 的相關資料進行分析",
                color=0xe74c3c
            )
        
        await interaction.edit_original_response(embed=embed)

def setup_government_data_commands(bot):
    """設定政府資料相關指令"""
    
    @bot.tree.command(name="gov_data", description="查詢政府公開資料")
    async def gov_data_command(interaction: discord.Interaction):
        """政府公開資料查詢指令"""
        embed = discord.Embed(
            title="🏛️ 政府公開資料查詢系統",
            description="選擇您要查詢的資料類型，系統將為您獲取最新的政府公開資料",
            color=0x3498db
        )
        
        embed.add_field(
            name="📊 可用資料類型",
            value="• 犯罪統計\n• 警察機關\n• 人口統計\n• 學校資料\n• 醫療機構\n• 交通資訊\n• 氣象資料\n• 綜合分析",
            inline=False
        )
        
        embed.set_footer(text="資料來源：政府資料開放平臺")
        
        view = GovernmentDataView()
        await interaction.response.send_message(embed=embed, view=view)
    
    @bot.tree.command(name="gov_analysis", description="地區綜合分析")
    @app_commands.describe(area="要分析的地區名稱，例如：台北市")
    async def gov_analysis_command(interaction: discord.Interaction, area: str):
        """地區綜合分析指令"""
        await interaction.response.defer()
        
        analyzer = DataAnalyzer()
        
        embed = discord.Embed(
            title="🔍 正在進行綜合分析...",
            description=f"分析地區：{area}",
            color=0xf39c12
        )
        await interaction.followup.send(embed=embed)
        
        # 執行分析
        analysis_result = await analyzer.analyze_crime_correlation(area)
        
        if analysis_result:
            embed = discord.Embed(
                title=f"📊 {area} 綜合分析報告",
                color=0x27ae60
            )
            
            # 資料來源
            if analysis_result.get('data_sources'):
                sources = ", ".join(analysis_result['data_sources'])
                embed.add_field(
                    name="📋 資料來源",
                    value=f"```\n{sources}\n```",
                    inline=False
                )
            
            # 統計資訊
            stats = []
            if 'crime_count' in analysis_result:
                stats.append(f"犯罪資料：{analysis_result['crime_count']} 筆")
            if 'population_count' in analysis_result:
                stats.append(f"人口資料：{analysis_result['population_count']} 筆")
            if 'school_count' in analysis_result:
                stats.append(f"學校資料：{analysis_result['school_count']} 筆")
            if 'hospital_count' in analysis_result:
                stats.append(f"醫療機構：{analysis_result['hospital_count']} 筆")
            
            if stats:
                embed.add_field(
                    name="📈 統計摘要",
                    value=f"```\n" + "\n".join(stats) + "\n```",
                    inline=False
                )
            
            # 分析洞察
            if analysis_result.get('insights'):
                insights = "\n".join(analysis_result['insights'])
                embed.add_field(
                    name="💡 分析洞察",
                    value=f"```\n{insights}\n```",
                    inline=False
                )
            
            embed.set_footer(text=f"分析時間：{analysis_result.get('analysis_date', 'N/A')}")
        else:
            embed = discord.Embed(
                title="❌ 分析失敗",
                description=f"無法獲取 {area} 的相關資料進行分析",
                color=0xe74c3c
            )
        
        await interaction.edit_original_response(embed=embed)
    
    @bot.tree.command(name="gov_search", description="搜尋政府資料集")
    @app_commands.describe(keyword="搜尋關鍵字")
    async def gov_search_command(interaction: discord.Interaction, keyword: str):
        """搜尋政府資料集指令"""
        await interaction.response.defer()
        
        api = GovernmentDataAPI()
        
        embed = discord.Embed(
            title="🔍 正在搜尋相關資料集...",
            description=f"搜尋關鍵字：{keyword}",
            color=0xf39c12
        )
        await interaction.followup.send(embed=embed)
        
        async with api as gov_api:
            results = await gov_api.search_datasets(keyword, limit=10)
            
            if results:
                embed = discord.Embed(
                    title=f"📊 搜尋結果：{keyword}",
                    color=0x27ae60
                )
                
                for i, dataset in enumerate(results[:5], 1):
                    title = dataset.get('title', 'N/A')
                    description = dataset.get('notes', 'N/A')[:100] + "..." if len(dataset.get('notes', '')) > 100 else dataset.get('notes', 'N/A')
                    
                    embed.add_field(
                        name=f"{i}. {title}",
                        value=f"```{description}```",
                        inline=False
                    )
                
                embed.set_footer(text=f"找到 {len(results)} 個相關資料集")
            else:
                embed = discord.Embed(
                    title="❌ 搜尋失敗",
                    description=f"找不到與 '{keyword}' 相關的資料集",
                    color=0xe74c3c
                )
        
        await interaction.edit_original_response(embed=embed)
    
    @bot.tree.command(name="gov_datasets", description="查看可用的政府資料集")
    async def gov_datasets_command(interaction: discord.Interaction):
        """查看可用資料集指令"""
        api = GovernmentDataAPI()
        datasets = api.get_available_datasets()
        
        embed = discord.Embed(
            title="📋 可用的政府資料集",
            description="以下是系統內建的政府公開資料集",
            color=0x3498db
        )
        
        # 分類顯示
        categories = {
            "🚔 治安相關": ["犯罪統計", "警察機關", "交通事故"],
            "👥 人口統計": ["人口統計", "戶數統計"],
            "📊 經濟指標": ["失業率", "物價指數"],
            "🏫 教育資源": ["學校名錄", "學生數統計"],
            "🏥 醫療資源": ["醫療機構", "藥局資訊"],
            "🚌 交通資訊": ["停車場", "公車站牌"],
            "🌍 環境資料": ["空氣品質", "氣象站"],
            "🤝 社會福利": ["長照機構", "社福機構"]
        }
        
        for category, items in categories.items():
            available_items = [item for item in items if item in datasets]
            if available_items:
                embed.add_field(
                    name=category,
                    value="• " + "\n• ".join(available_items),
                    inline=True
                )
        
        embed.set_footer(text="使用 /gov_data 指令查詢特定資料")
        
        await interaction.response.send_message(embed=embed)
    
    logger.info("政府資料查詢指令設定完成")
