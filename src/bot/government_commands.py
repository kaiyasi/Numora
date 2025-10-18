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
import json
import requests
import requests

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
            discord.SelectOption(label="📚 圖書館座位", value="library_seats", description="台北市圖書館即時座位資訊"),
            discord.SelectOption(label="🚲 自行車竊盜統計", value="bike_theft", description="台北市自行車竊盜案件統計"),
        ]
    )
    async def select_data_type(self, interaction: discord.Interaction, select: discord.ui.Select):
        await interaction.response.defer(ephemeral=True)
        
        data_type = select.values[0]
        
        # YouBike 需要先選城市，避免手動輸入
        if data_type == "youbike":
            await self.show_youbike_city_selector(interaction)
        else:
            # 直接查詢資料
            await self.query_data(interaction, data_type)

    async def show_youbike_city_selector(self, interaction: discord.Interaction):
        """顯示 YouBike 城市選擇下拉（台北/新北）"""
        view = YouBikeCitySelect(self.api)
        embed = discord.Embed(
            title="🚴 選擇 YouBike 城市",
            description="請從下方選單選擇城市（避免手動輸入格式差異）",
            color=0x3498db
        )
        await interaction.edit_original_response(embed=embed, view=view)
    
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
                    data_name = "YouBike 2.0 即時資訊"
                    df = await api.get_taipei_youbike_data()
                    if df is None or df.empty:
                        # Fallback: 直接以 requests 抓取官方 JSON 並轉為 DataFrame
                        try:
                            url = "https://tcgbusfs.blob.core.windows.net/dotapp/youbike/v2/youbike_immediate.json"
                            r = requests.get(url, timeout=15)
                            r.raise_for_status()
                            data = r.json()
                            if isinstance(data, list) and data:
                                df = pd.DataFrame(data)
                        except Exception as e:
                            logger.warning(f"YouBike fallback 失敗: {e}")
                elif data_type == "library_seats":
                    data_name = "圖書館座位資訊"
                    df = await api.get_library_seats()
                elif data_type == "bike_theft":
                    data_name = "自行車竊盜統計"
                    df = await api.get_bike_theft_data()
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
                    
                    # 類型化預覽
                    preview_lines = []
                    
                    if data_type == "library_seats":
                        # 圖書館座位格式化顯示
                        for _, row in df.head(5).iterrows():
                            branch = row.get('branchName', 'N/A')
                            floor = row.get('floorName', 'N/A')
                            area = row.get('areaName', 'N/A')
                            free = row.get('freeCount', 0)
                            total = row.get('totalCount', 0)
                            preview_lines.append(f"📚 {branch} {floor} {area}")
                            preview_lines.append(f"   可用: {free} / 總共: {total} 個座位")
                        if preview_lines:
                            embed.add_field(
                                name="📋 座位資訊預覽（前 5 筆）",
                                value="```\n" + "\n".join(preview_lines) + "\n```",
                                inline=False
                            )
                    
                    elif data_type == "bike_theft":
                        # 自行車竊盜案件格式化顯示
                        for _, row in df.head(5).iterrows():
                            case_type = row.get('案類', 'N/A')
                            date = row.get('發生日期', 'N/A')
                            time = row.get('發生時段', 'N/A')
                            location = row.get('發生地點', 'N/A')
                            
                            # 轉換民國年為西元年
                            if date != 'N/A' and len(str(date)) == 7:
                                try:
                                    year = int(str(date)[:3]) + 1911
                                    month = str(date)[3:5]
                                    day = str(date)[5:7]
                                    date_formatted = f"{year}/{month}/{day}"
                                except:
                                    date_formatted = date
                            else:
                                date_formatted = date
                            
                            preview_lines.append(f"🚲 {case_type}")
                            preview_lines.append(f"   📅 {date_formatted} {time}時")
                            preview_lines.append(f"   📍 {location[:50]}")
                        
                        if preview_lines:
                            embed.add_field(
                                name="📋 案件資訊預覽（前 5 筆）",
                                value="```\n" + "\n".join(preview_lines) + "\n```",
                                inline=False
                            )
                    
                    elif data_type == "wifi":
                        # WiFi 熱點格式化顯示
                        cols = {c.lower(): c for c in df.columns}
                        def pick(*names):
                            for n in names:
                                key = n.lower()
                                if key in cols:
                                    return cols[key]
                            for c in df.columns:
                                lc = str(c).lower()
                                if any(key in lc for key in names):
                                    return c
                            return None
                        name_col = pick('hotspot', 'name', '熱點', 'wifi', 'spot', '場所名稱')
                        addr_col = pick('address', 'addr', '地址', '地點')
                        ssid_col = pick('ssid')
                        for _, row in df.head(5).iterrows():
                            name = str(row.get(name_col, 'N/A')) if name_col else 'N/A'
                            addr = str(row.get(addr_col, 'N/A')) if addr_col else 'N/A'
                            ssid = str(row.get(ssid_col, 'N/A')) if ssid_col else 'N/A'
                            preview_lines.append(f"📶 {name}")
                            if addr != 'N/A':
                                preview_lines.append(f"   📍 {addr[:40]}")
                            if ssid != 'N/A':
                                preview_lines.append(f"   SSID: {ssid}")
                        if preview_lines:
                            embed.add_field(
                                name="📋 熱點預覽（前 5 筆）",
                                value="```\n" + "\n".join(preview_lines) + "\n```",
                                inline=False
                            )
                    
                    # 如果沒有生成預覽或不是特殊類型，使用一般表格預覽
                    if not preview_lines:
                        if len(df) > 0:
                            sample_data = df.head(3).to_string(max_cols=5, max_colwidth=30)
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
                        description=f"無法獲取{data_name}，可能是資料來源暫時無法使用或欄位不相容。",
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


class YouBikeCitySelect(discord.ui.View):
    """YouBike 城市選擇視圖"""

    def __init__(self, api: GovernmentDataAPI):
        super().__init__(timeout=180)
        self.api = api

        self.city_select = discord.ui.Select(
            placeholder="選擇城市...",
            min_values=1,
            max_values=1,
            options=[
                discord.SelectOption(label="台北市", value="taipei", description="YouBike 2.0 台北市即時站況"),
                discord.SelectOption(label="新北市", value="new_taipei", description="YouBike 2.0 新北市即時站況"),
            ],
        )
        self.city_select.callback = self.on_city_selected  # 綁定回調
        self.add_item(self.city_select)

    async def on_city_selected(self, interaction: discord.Interaction):
        await interaction.response.defer(ephemeral=True)
        city = self.city_select.values[0]

        try:
            # 抓資料
            if city == "taipei":
                # 先用整合 API；若空則直接走官方 JSON
                async with self.api as api:
                    df = await api.get_taipei_youbike_data()
                if df is None or df.empty:
                    url = "https://tcgbusfs.blob.core.windows.net/dotapp/youbike/v2/youbike_immediate.json"
                    r = requests.get(url, timeout=15)
                    r.raise_for_status()
                    data = r.json()
                    if isinstance(data, list) and data:
                        import pandas as pd
                        df = pd.DataFrame(data)
            else:
                # 新北市端點（大量資料，僅示範統計）
                url = "https://data.ntpc.gov.tw/api/datasets/010e5b15-3823-4b20-b401-b1cf000550c5/json/?size=10000"
                r = requests.get(url, timeout=20)
                r.raise_for_status()
                data = r.json()
                if isinstance(data, dict) and 'data' in data:
                    data = data['data']
                import pandas as pd
                df = pd.DataFrame(data) if isinstance(data, list) and data else None

            if df is None or df.empty:
                embed = discord.Embed(
                    title="❌ 查詢失敗",
                    description="無法獲取 YouBike 即時資訊，可能是來源暫時不可用。",
                    color=0xe74c3c
                )
                await interaction.edit_original_response(embed=embed, view=None)
                return

            # 產出地區清單，提供使用者第二層選擇；預設提供「全部地區」
            areas = []
            if 'sarea' in df.columns:
                areas = sorted([str(a) for a in set(df['sarea'].dropna().astype(str)) if a.strip()])
            elif 'area' in df.columns:
                areas = sorted([str(a) for a in set(df['area'].dropna().astype(str)) if a.strip()])
            # 建立地區選擇視圖
            view = YouBikeAreaSelect(city=city, areas=areas)
            embed = discord.Embed(
                title=f"🚴 已選擇 {'台北市' if city=='taipei' else '新北市'}，請選擇地區",
                description="未選則預設顯示全部地區",
                color=0x3498db
            )
            await interaction.edit_original_response(embed=embed, view=view)
        except Exception as e:
            embed = discord.Embed(
                title="❌ 查詢過程發生錯誤",
                description=f"錯誤訊息：{str(e)}",
                color=0xe74c3c
            )
            await interaction.edit_original_response(embed=embed, view=None)

class YouBikePaginationView(discord.ui.View):
    """YouBike 分頁視圖（以下拉選單換頁，維持單一訊息）"""

    def __init__(self, city: str, area: str, page_size: int = 10):
        super().__init__(timeout=300)
        self.city = city
        self.area = area
        self.page_size = page_size
        self.total = 0
        self.total_pages = 1

    async def _fetch_df(self):
        import requests, pandas as pd
        if self.city == 'taipei':
            url = "https://tcgbusfs.blob.core.windows.net/dotapp/youbike/v2/youbike_immediate.json"
            r = requests.get(url, timeout=15)
            r.raise_for_status()
            data = r.json()
            df = pd.DataFrame(data) if isinstance(data, list) and data else None
        else:
            url = "https://data.ntpc.gov.tw/api/datasets/010e5b15-3823-4b20-b401-b1cf000550c5/json/?size=10000"
            r = requests.get(url, timeout=20)
            r.raise_for_status()
            data = r.json()
            if isinstance(data, dict) and 'data' in data:
                data = data['data']
            df = pd.DataFrame(data) if isinstance(data, list) and data else None

        if df is None or df.empty:
            return None

        area_col = 'sarea' if 'sarea' in df.columns else ('area' if 'area' in df.columns else None)
        if self.area != '__all__' and area_col:
            df = df[df[area_col].astype(str) == str(self.area)]
        if 'mday' in df.columns:
            df = df.sort_values('mday', ascending=False)
        self.total = len(df)
        self.total_pages = max(1, (self.total + self.page_size - 1) // self.page_size)
        return df

    def _rebuild_page_select(self, current_page: int = 1):
        for item in list(self.children):
            if isinstance(item, discord.ui.Select):
                self.remove_item(item)
        
        options = []
        # 上一頁
        if current_page > 1:
            options.append(discord.SelectOption(
                label="⬅️ 上一頁",
                value=f"prev_{current_page - 1}",
                description=f"返回第 {current_page - 1} 頁"
            ))
        
        # 下一頁
        if current_page < self.total_pages:
            options.append(discord.SelectOption(
                label="➡️ 下一頁",
                value=f"next_{current_page + 1}",
                description=f"前往第 {current_page + 1} 頁"
            ))
        
        # 回退地區選項
        options.append(discord.SelectOption(
            label="🔙 回退地區選項",
            value="back_area",
            description="重新選擇行政區"
        ))
        
        # 回退縣市選項
        options.append(discord.SelectOption(
            label="🏠 回退縣市選項",
            value="back_city",
            description="重新選擇縣市"
        ))
        
        sel = discord.ui.Select(
            placeholder="選擇操作...",
            min_values=1,
            max_values=1,
            options=options
        )
        
        async def on_select(interaction: discord.Interaction):
            await interaction.response.defer()
            action = sel.values[0]
            
            if action.startswith("prev_") or action.startswith("next_"):
                page = int(action.split("_")[1])
                await self.render_page(interaction, page)
            elif action == "back_area":
                # 重新顯示地區選擇
                await self.show_area_select(interaction)
            elif action == "back_city":
                # 重新顯示縣市選擇
                await self.show_city_select(interaction)
        
        sel.callback = on_select
        self.add_item(sel)
    
    async def show_area_select(self, interaction: discord.Interaction):
        """重新顯示地區選擇"""
        try:
            # 重新抓取資料以獲取地區列表
            df = await self._fetch_df_full()
            if df is None or df.empty:
                return
            
            areas = []
            if 'sarea' in df.columns:
                areas = sorted([str(a) for a in set(df['sarea'].dropna().astype(str)) if a.strip()])
            elif 'area' in df.columns:
                areas = sorted([str(a) for a in set(df['area'].dropna().astype(str)) if a.strip()])
            
            view = YouBikeAreaSelect(city=self.city, areas=areas)
            embed = discord.Embed(
                title=f"🚴 請選擇地區（{'台北市' if self.city=='taipei' else '新北市'}）",
                description="選擇行政區查看站點資訊",
                color=0x3498db
            )
            await interaction.edit_original_response(embed=embed, view=view)
        except Exception as e:
            embed = discord.Embed(
                title="❌ 錯誤",
                description=f"無法載入地區選項：{str(e)}",
                color=0xe74c3c
            )
            await interaction.edit_original_response(embed=embed, view=None)
    
    async def show_city_select(self, interaction: discord.Interaction):
        """重新顯示縣市選擇"""
        from src.utils.government_data import GovernmentDataAPI
        api = GovernmentDataAPI()
        view = YouBikeCitySelect(api)
        embed = discord.Embed(
            title="🚴 YouBike 即時資訊查詢",
            description="請選擇縣市",
            color=0x3498db
        )
        await interaction.edit_original_response(embed=embed, view=view)
    
    async def _fetch_df_full(self):
        """獲取完整資料（不篩選地區）"""
        import requests, pandas as pd
        if self.city == 'taipei':
            url = "https://tcgbusfs.blob.core.windows.net/dotapp/youbike/v2/youbike_immediate.json"
            r = requests.get(url, timeout=15)
            r.raise_for_status()
            data = r.json()
            return pd.DataFrame(data) if isinstance(data, list) and data else None
        else:
            url = "https://data.ntpc.gov.tw/api/datasets/010e5b15-3823-4b20-b401-b1cf000550c5/json/?size=10000"
            r = requests.get(url, timeout=20)
            r.raise_for_status()
            data = r.json()
            if isinstance(data, dict) and 'data' in data:
                data = data['data']
            return pd.DataFrame(data) if isinstance(data, list) and data else None

    async def render_page(self, interaction: discord.Interaction, page: int = 1):
        import math
        df = await self._fetch_df()
        if df is None or df.empty:
            embed = discord.Embed(
                title="❌ 查詢失敗",
                description="無法獲取 YouBike 即時資訊，可能是來源暫時不可用。",
                color=0xe74c3c
            )
            await interaction.edit_original_response(embed=embed, view=None)
            return
        start = (page - 1) * self.page_size
        end = min(start + self.page_size, len(df))
        page_df = df.iloc[start:end]

        def nz_str(v: object, default: str = '') -> str:
            if v is None:
                return default
            try:
                if isinstance(v, float) and math.isnan(v):
                    return default
            except Exception:
                pass
            s = str(v).strip()
            return s if s.lower() != 'none' else default
        def nz_num(v: object, default: str = '0') -> str:
            s = nz_str(v, '')
            if s == '':
                return default
            try:
                n = float(s)
                return str(int(n))
            except Exception:
                return s
        # 先收集所有資料並計算最大寬度
        records = page_df.to_dict(orient='records')
        parsed_data = []
        
        # 半形轉全形（數字和括號）
        def to_fullwidth(text):
            halfwidth = '0123456789()'
            fullwidth = '０１２３４５６７８９（）'
            trans = str.maketrans(halfwidth, fullwidth)
            return text.translate(trans)
        
        for row in records:
            name = nz_str(row.get('sna') or row.get('stationName') or row.get('name') or '站點', '站點')
            # 移除 YouBike2.0_ 前綴
            name = name.replace('YouBike2.0_', '').replace('YouBike_', '')
            # 將站點名稱中的數字和括號轉為全形
            name = to_fullwidth(name)
            
            sarea = nz_str(row.get('sarea') or row.get('area') or '')
            sbi = nz_num(row.get('sbi') or row.get('available_rent_bikes') or row.get('AvailableBikeCount') or row.get('available') or 0)
            bemp = nz_num(row.get('bemp') or row.get('available_return_bikes') or row.get('AvailableSpaceCount') or row.get('empty') or 0)
            
            parsed_data.append({
                'name': name,
                'sarea': sarea,
                'sbi': sbi,
                'bemp': bemp
            })
        
        # 處理站點名稱，將所有括號改為全形空格
        def process_station_name(name):
            """處理站點名稱，將括號內容改用全形空格分隔"""
            import re
            # 將所有括號內容提取並用全形空格連接
            # 例如：捷運後山埤站（３號出口）-> 捷運後山埤站　３號出口
            # 例如：仁愛金山路口（東南側）-> 仁愛金山路口　東南側
            processed_name = re.sub(r'（([^）]+)）', r'　\1', name)
            return processed_name
        
        # 處理每個站點名稱
        processed_data = []
        for d in parsed_data:
            processed_name = process_station_name(d['name'])
            processed_data.append({
                'name': processed_name,
                'sarea': d['sarea'],
                'sbi': d['sbi'],
                'bemp': d['bemp']
            })
        
        # 按照站點名稱長度升冪排序（從短到長）
        processed_data.sort(key=lambda x: len(x['name']))
        
        # 計算最大名稱長度
        max_name_len = max(len(d['name']) for d in processed_data) if processed_data else 0
        
        # 半形數字轉全形數字的函數
        def to_fullwidth_num(num):
            halfwidth = '0123456789'
            fullwidth = '０１２３４５６７８９'
            trans = str.maketrans(halfwidth, fullwidth)
            # 轉為字串，右對齊2位數，然後轉全形
            num_str = f"{int(num):>2}"
            return num_str.translate(trans)
        
        # 使用全形空格（　）填充以確保對齊
        lines = []
        for data in processed_data:
            # 站點名稱填充
            name_padding = max_name_len - len(data['name'])
            name_padded = data['name'] + '　' * name_padding
            
            # 行政區
            area_text = f"（{data['sarea']}）" if data['sarea'] else ""
            
            # 數字轉全形
            sbi_int = int(float(data['sbi'])) if data['sbi'] else 0
            bemp_int = int(float(data['bemp'])) if data['bemp'] else 0
            sbi_fullwidth = to_fullwidth_num(sbi_int)
            bemp_fullwidth = to_fullwidth_num(bemp_int)
            
            # 組合輸出
            line = f"{name_padded}{area_text}｜可借:{sbi_fullwidth} 可還:{bemp_fullwidth}｜"
            lines.append(line)
        city_name = '台北市' if self.city == 'taipei' else '新北市'
        area_name = '全部地區' if self.area == '__all__' else self.area
        embed = discord.Embed(
            title=f"✅ YouBike 即時資訊（{city_name}／{area_name}）",
            color=0x27ae60
        )
        embed.add_field(name="📊 資料統計", value=f"```\n第 {start+1}–{end} 筆，共 {self.total} 筆\n頁數：第 {page} / {self.total_pages} 頁\n```", inline=False)
        if lines:
            # 使用程式碼區塊保持等寬字體
            content = "\n".join(lines)
            embed.add_field(name="📋 站點清單", value=f"```\n{content}\n```", inline=False)

        self._rebuild_page_select(current_page=page)
        await interaction.edit_original_response(embed=embed, view=self)


class YouBikeAreaSelect(discord.ui.View):
    """YouBike 地區選擇視圖（預設全部地區）"""

    def __init__(self, city: str, areas: list[str]):
        super().__init__(timeout=180)
        self.city = city
        # 準備下拉選項，第一個是全部地區
        options = [discord.SelectOption(label="全部地區", value="__all__", description="不篩選全部顯示")]
        # 限制最多 25 個選項以符合 Discord UI 限制
        for a in areas[:24]:
            options.append(discord.SelectOption(label=a, value=a))

        self.area_select = discord.ui.Select(
            placeholder="選擇地區（預設全部）",
            min_values=1,
            max_values=1,
            options=options,
        )
        self.area_select.callback = self.on_area_selected
        self.add_item(self.area_select)

    async def on_area_selected(self, interaction: discord.Interaction):
        await interaction.response.defer(ephemeral=True)
        area = self.area_select.values[0]
        city = self.city
        try:
            # 重新抓資料（即時資料，避免傳遞大型 payload）
            import requests, pandas as pd
            if city == 'taipei':
                url = "https://tcgbusfs.blob.core.windows.net/dotapp/youbike/v2/youbike_immediate.json"
                r = requests.get(url, timeout=15)
                r.raise_for_status()
                data = r.json()
                df = pd.DataFrame(data) if isinstance(data, list) and data else None
                area_col = 'sarea' if df is not None and 'sarea' in df.columns else 'area'
            else:
                url = "https://data.ntpc.gov.tw/api/datasets/010e5b15-3823-4b20-b401-b1cf000550c5/json/?size=10000"
                r = requests.get(url, timeout=20)
                r.raise_for_status()
                data = r.json()
                if isinstance(data, dict) and 'data' in data:
                    data = data['data']
                df = pd.DataFrame(data) if isinstance(data, list) and data else None
                # 新北端點欄位命名不一，盡量容錯
                area_col = 'sarea' if df is not None and 'sarea' in df.columns else ('area' if df is not None and 'area' in df.columns else None)

            # 切換為分頁選單顯示
            pager = YouBikePaginationView(city=city, area=area)
            await pager.render_page(interaction, page=1)
        except Exception as e:
            embed = discord.Embed(
                title="❌ 查詢過程發生錯誤",
                description=f"錯誤訊息：{str(e)}",
                color=0xe74c3c
            )
            await interaction.edit_original_response(embed=embed, view=None)

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
        await interaction.response.defer(ephemeral=True)
        
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
        # 立即回應，不使用 defer()
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
        await interaction.edit_original_response(embed=embed)
        
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
        await interaction.edit_original_response(embed=embed)
        
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
        
        await interaction.response.defer()
        await interaction.edit_original_response(embed=embed)
    
    logger.info("政府資料查詢指令設定完成")
