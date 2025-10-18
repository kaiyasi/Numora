"""
舊版入口封裝：委派至新版 bot.py
保留向後相容，避免重複邏輯。
"""

from bot import main as run_bot


if __name__ == "__main__":
    run_bot()

        if area_data.empty:
            print(f"⚠️ 警告: 提取行政區後沒有資料")
            return None
        
        # 按年份分組計算案件數
        yearly_counts = area_data.groupby(['年份', '區']).size().unstack(fill_value=0)
        print(f"年度分組計數結果: {yearly_counts}")
        
        if yearly_counts.empty:
            print("⚠️ 警告: 年度計數結果為空")
            return None

        # 使用更大的圖表尺寸
        fig, ax = plt.subplots(figsize=(16, 10))
        
        yearly_counts.plot(kind='bar', stacked=True, ax=ax, colormap='viridis')
        
        # 設定標題和標籤
        title = f'{area} - 全年度案件統計' if area != '全部地區' else '全年度各地區案件統計'
        ax.set_title(title, fontsize=18, pad=25)
        ax.set_xlabel('年份', fontsize=14)
        ax.set_ylabel('案件數', fontsize=14)
        
        # 調整邊距
        plt.subplots_adjust(bottom=0.25, left=0.1, right=0.95, top=0.9)
        
        plt.tight_layout()
        filename = f"yearly_plot_{area}.png"
        
        # Add more robust file handling
        try:
            plt.savefig(filename, dpi=150, bbox_inches='tight', facecolor='white')
            plt.close('all')  # Close all figures to prevent memory leaks
            return filename
        except Exception as e:
            plt.close('all')
            return None
            
    except Exception as e:
        plt.close('all')  # Ensure we close any open figures
        return None

# 📁 載入文字資料
def load_data():
    # 適應不同環境的檔案路徑
    file_paths = [
        'crime_data.txt',  # DisCloud 環境
        'c:\\Users\\zenge\\Downloads\\discord_crime_bot\\crime_data.txt',  # 本地環境
        './crime_data.txt'  # 相對路徑
    ]
    
    file_path = None
    for path in file_paths:
        if os.path.exists(path):
            file_path = path
            break
    
    if file_path is None:
        # 如果找不到檔案，建立一個空的 DataFrame
        print("⚠️ 找不到預設資料檔案，使用空資料集")
        return pd.DataFrame(columns=['編號', '案類', '日期', '時段', '地點', '年份'])
    
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            lines = f.readlines()
        
        data_lines = lines[1:] if len(lines) > 1 else []
        
        data = []
        for line_num, line in enumerate(data_lines, 2):
            line = line.strip()
            if not line:
                continue
                
            try:
                parts = re.split(r'\s+', line)
                if len(parts) >= 5:
                    編號 = parts[0]
                    案類 = parts[1]
                    日期 = parts[2]
                    時段 = parts[3]
                    地點 = ' '.join(parts[4:])
                    
                    if 日期.isdigit() and len(日期) == 7:
                        data.append([編號, 案類, 日期, 時段, 地點])
                        
            except Exception as e:
                continue
        
        if not data:
            raise ValueError("沒有有效的資料行")
        
        df = pd.DataFrame(data, columns=['編號', '案類', '日期', '時段', '地點'])
        df['年份'] = df['日期'].astype(str).str[:3].astype(int) + 1911
        
        print(f"✅ 成功載入 {len(df)} 筆有效資料")
        
        # 輸出地區統計
        extract_area_info(df)
        
        return df
        
    except Exception as e:
        print(f"❌ 載入資料時發生錯誤：{e}")
        raise

# 📊 載入 CSV 資料
def load_csv_data(file_content):
    try:
        # 嘗試檢測檔案編碼
        detected_encoding = chardet.detect(file_content)
        encoding = detected_encoding['encoding']
        
        print(f"檢測到的編碼：{encoding} (信心度：{detected_encoding['confidence']:.2f})")
        
        # 常見的中文編碼順序嘗試
        encodings_to_try = [
            encoding,
            'utf-8',
            'big5',
            'cp950',
            'gb2312',
            'gbk',
            'utf-8-sig',
            'latin1'
        ]
        
        encodings_to_try = list(dict.fromkeys(filter(None, encodings_to_try)))
        
        df = None
        
        for enc in encodings_to_try:
            try:
                decoded_content = file_content.decode(enc)
                df = pd.read_csv(io.StringIO(decoded_content))
                print(f"✅ 成功使用編碼：{enc}")
                break
            except (UnicodeDecodeError, UnicodeError):
                continue
            except Exception as e:
                continue
        
        if df is None:
            raise ValueError("無法解析檔案")
        
        # 檢查欄位名稱
        df.columns = df.columns.str.strip().str.replace('\ufeff', '')
        
        # 檢查必要欄位
        required_mapping = {
            '編號': ['編號', 'ID', 'id', '序號', 'No', 'number'],
            '案類': ['案類', '案件類型', '類型', 'Type', 'type', '案件類別'],
            '日期': ['日期', '發生日期', '時間', 'Date', 'date', '發生(現)日期', '發生時間'],
            '時段': ['時段', '時間段', '發生時段', 'Time', 'time', '時間'],
            '地點': ['地點', '發生地點', '位置', 'Location', 'location', '地址', '發生地址']
        }
        
        column_mapping = {}
        for required_col, possible_names in required_mapping.items():
            found = False
            for possible_name in possible_names:
                if possible_name in df.columns:
                    column_mapping[possible_name] = required_col
                    found = True
                    break
            if not found:
                for col in df.columns:
                    if any(name in col for name in possible_names):
                        column_mapping[col] = required_col
                        found = True
                        break
                
                if not found:
                    raise ValueError(f"找不到必要欄位：{required_col}")
        
        df = df.rename(columns=column_mapping)
        
        # 處理年份
        try:
            df['年份'] = df['日期'].astype(str).str[:3].astype(int) + 1911
        except:
            try:
                df['年份'] = pd.to_datetime(df['日期'], errors='coerce').dt.year
                df = df.dropna(subset=['年份'])
                df['年份'] = df['年份'].astype(int)
            except:
                try:
                    df['年份'] = df['日期'].astype(str).str[:4].astype(int)
                except:
                    raise ValueError("無法處理日期格式")
        
        print(f"✅ 成功載入 CSV 資料：{len(df)} 筆記錄")
        return df
        
    except Exception as e:
        raise ValueError(f"CSV 檔案處理錯誤：{str(e)}")

# 統計資料生成
def generate_statistics(df):
    try:
        stats = {}
        stats['總案件數'] = len(df)
        stats['年份範圍'] = f"{df['年份'].min()} - {df['年份'].max()}"
        
        # 地區統計
        areas_info = extract_area_info(df)
        stats['可用地區'] = areas_info
        
        # 年份統計
        stats['年份統計'] = df['年份'].value_counts().sort_index().to_dict()
        stats['時段統計'] = df['時段'].value_counts().to_dict()
        stats['案類統計'] = df['案類'].value_counts().to_dict()
        
        return stats
        
    except Exception as e:
        return {
            '總案件數': len(df),
            '年份範圍': f"{df['年份'].min()} - {df['年份'].max()}",
            '可用地區': {},
            '年份統計': df['年份'].value_counts().sort_index().to_dict(),
            '時段統計': df['時段'].value_counts().to_dict(),
            '案類統計': df['案類'].value_counts().to_dict()
        }

# 地區和年份選擇 View
class AreaYearSelectView(View):
    def __init__(self, df):
        super().__init__(timeout=300)
        self.df = df
        self.current_area = None
        self.current_year = None
        self.areas_info = extract_area_info(df)
        self._setup_selects()
    
    def _setup_selects(self):
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
        
        # 新增「全年度統計」選項到年份選擇器
        year_options.append(discord.SelectOption(
            label="📊 全年度統計",
            value="全年度統計",
            description="生成全年度統計圖表"
        ))
        
        # 設定年份選擇器的 placeholder
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
                self.is_yearly_selected = True
                self.current_year = None
                area = self.current_area if self.current_area else "全部地區"
                filename = generate_yearly_plot(self.df, area)
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
                try:
                    if os.path.exists(filename):
                        os.remove(filename)
                except Exception as e:
                    print(f"⚠️ 移除圖表檔案失敗: {str(e)}")
            else:
                self.is_yearly_selected = False
                self.current_year = int(selected_year)
                await self._update_display(interaction)
        
        area_select.callback = area_callback
        year_select.callback = year_callback
        
        self.add_item(area_select)
        self.add_item(year_select)
    
    async def _update_display(self, interaction):
        if self.current_area and self.current_year:
            try:
                # 生成圖表
                filename = generate_area_year_plot(self.df, self.current_area, self.current_year)
                
                if not filename or not os.path.exists(filename):
                    self._setup_selects()
                    await interaction.edit_original_response(
                        content=f"❌ {self.current_area} - {self.current_year} 年沒有有效資料或圖表生成失敗",
                        embed=None,
                        attachments=[],
                        view=self
                    )
                    return
                
                # 更新 embed
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
                
                # Improve file cleanup with try-except
                try:
                    if os.path.exists(filename):
                        os.remove(filename)
                        print(f"✅ 已移除暫存圖表: {filename}")
                except Exception as e:
                    print(f"⚠️ 移除圖表檔案失敗: {str(e)}")
                    
            except Exception as e:
                await interaction.edit_original_response(
                    content=f"❌ 圖表處理錯誤: {str(e)}",
                    embed=None,
                    attachments=[],
                    view=self
                )
        else:
            # 只更新選單
            self._setup_selects()
            await interaction.edit_original_response(view=self)

# 地區排名選擇 View
class AreaRankSelectView(View):
    def __init__(self, df):
        super().__init__(timeout=300)
        self.df = df
        self.current_area = None
        self.areas_info = extract_area_info(df)
        self._setup_controls()
    
    def _setup_controls(self):
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
                
                # 修正：直接定義 callback 函數
                async def button_callback(interaction, n=top_n):
                    try:
                        await interaction.response.defer()
                        
                        filename = generate_area_rank_plot(self.df, self.current_area, n)
                        
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
                        
                        # Improve file cleanup with try-except
                        try:
                            if os.path.exists(filename):
                                os.remove(filename)
                                print(f"✅ 已移除暫存圖表: {filename}")
                        except Exception as e:
                            print(f"⚠️ 移除圖表檔案失敗: {str(e)}")
                            
                    except Exception as e:
                        await interaction.followup.send(f"❌ 錯誤：{str(e)}", ephemeral=True)
                
                button.callback = button_callback
                self.add_item(button)

@tree.command(name="upload", description="上傳 CSV 檔案")
async def upload_command(interaction: discord.Interaction, file: discord.Attachment):
    try:
        if not file.filename.lower().endswith('.csv'):
            await interaction.response.send_message("❌ 請上傳 CSV 檔案", ephemeral=True)
            return
        
        await interaction.response.defer()
        
        file_content = await file.read()
        
        global current_df
        current_df = load_csv_data(file_content)
        
        stats = generate_statistics(current_df)
        
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
        
    except Exception as e:
        await interaction.followup.send(f"❌ 上傳失敗：{str(e)}")

@tree.command(name="summary", description="顯示總覽並選擇地區年份查圖或全年度統計")
async def summary_command(interaction: discord.Interaction):
    try:
        df = current_df if current_df is not None else load_data()
        
        if df.empty:
            await interaction.response.send_message("❌ 沒有資料可以顯示")
            return
        
        stats = generate_statistics(df)
        data_source = "上傳的資料" if current_df is not None else "預設資料"
        
        embed = discord.Embed(
            title="📈 犯罪案件統計總覽",
            description=f"```\n資料來源：{data_source}\n總案件數：{stats['總案件數']} 件\n年份範圍：{stats['年份範圍']}\n請選擇地區和年份查看統計圖表或生成全年度統計圖表\n```",
            color=0x2ecc71
        )
        
        view = AreaYearSelectView(df)
        await interaction.response.send_message(embed=embed, view=view)
        
    except Exception as e:
        await interaction.response.send_message(f"❌ 錯誤：{str(e)}")

@tree.command(name="rank", description="顯示地區排名統計")
async def rank_command(interaction: discord.Interaction):
    try:
        df = current_df if current_df is not None else load_data()
        
        if df.empty:
            await interaction.response.send_message("❌ 沒有資料可以顯示")
            return
        
        data_source = "上傳的資料" if current_df is not None else "預設資料"
        
        embed = discord.Embed(
            title="📊 地區排名統計",
            description=f"```\n資料來源：{data_source}\n請先選擇地區，然後選擇排名數量\n```",
            color=0xe74c3c
        )
        
        view = AreaRankSelectView(df)
        await interaction.response.send_message(embed=embed, view=view)
        
    except Exception as e:
        await interaction.response.send_message(f"❌ 錯誤：{str(e)}")

@tree.command(name="stats", description="顯示詳細統計資料")
async def stats_command(interaction: discord.Interaction):
    try:
        df = current_df if current_df is not None else load_data()
        
        if df.empty:
            await interaction.response.send_message("❌ 沒有資料可以顯示")
            return
        
        stats = generate_statistics(df)
        data_source = "上傳的資料" if current_df is not None else "預設資料"
        
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
        
    except Exception as e:
        await interaction.response.send_message(f"❌ 錯誤：{str(e)}")

@tree.command(name="clear", description="清除上傳的資料")
async def clear_command(interaction: discord.Interaction):
    global current_df
    if current_df is not None:
        current_df = None
        await interaction.response.send_message("✅ 已清除上傳的資料，現在將使用預設資料")
    else:
        await interaction.response.send_message("ℹ️ 目前沒有上傳的資料")

@bot.event
async def on_ready():
    await tree.sync()
    print(f"✅ Bot 已上線：{bot.user.name}")

# 載入環境變數
load_dotenv()

# 從環境變數獲取 token
token = os.getenv('DISCORD_TOKEN')
if not token:
    raise ValueError("找不到 DISCORD_TOKEN 環境變數")

bot.run(token)

@tree.command(name="query", description="查詢多個 API 資料來源")
async def query_command(interaction: discord.Interaction, keyword: str, api_source: str):
    try:
        await interaction.response.defer()

        # 定義資料來源
        api_sources = {
            # 臺北市政府資料開放平臺 dataset UUIDs
            "school": "f37de02a-623d-4f72-bca9-7c7aad2f0e10",
            "cases": "5a5b36e0-f870-4b7f-8378-c91ac5f57941",
            "friendly_stores": "25b1ee0a-e4cd-4ed1-86ac-fd748ca9cf71",
            # YouBike 即時資料（直接 JSON 端點）
            "youbike_taipei": "https://tcgbusfs.blob.core.windows.net/dotapp/youbike/v2/youbike_immediate.json",
            "youbike_new_taipei": "https://data.ntpc.gov.tw/api/datasets/010e5b15-3823-4b20-b401-b1cf000550c5/json/?size=10000",
            # YouBike 月租借使用量（CSV 下載連結）
            "youbike_taipei_monthly": "https://data.taipei/api/dataset/d8cefb03-aba2-41ca-9996-d8774313cdc6/resource/8f690548-61bc-4bff-8baa-01d465eb672c/download",
            # 臺北市自行車竊盜點位（CKAN dataset UUID，改用 CKAN 方式）
            "bike_theft_taipei": "adf80a2b-b29d-4fca-888c-bcd26ae314e0",
        }

        if api_source not in api_sources:
            await interaction.followup.send("❌ 無效的 API 資料來源，請選擇正確的來源。", ephemeral=True)
            return

        data = []
        source_url = api_sources[api_source]

        try:
            if api_source in ("youbike_taipei", "youbike_new_taipei"):
                # 直接 JSON 清單端點
                resp = requests.get(source_url, timeout=20)
                resp.raise_for_status()
                arr = resp.json()
                if isinstance(arr, dict) and 'data' in arr:
                    arr = arr['data']
                if isinstance(arr, list):
                    kw = (keyword or '').strip().lower()
                    def pick(rec: dict):
                        # 名稱、地址、可借/可還的常見鍵名
                        name = rec.get('sna') or rec.get('stationName') or rec.get('StationName') or rec.get('name')
                        addr = rec.get('ar') or rec.get('address') or rec.get('StationAddress') or rec.get('Address')
                        sarea = rec.get('sarea') or rec.get('area')
                        bikes = rec.get('sbi') or rec.get('available_rent_bikes') or rec.get('AvailableBikeCount') or rec.get('available') or rec.get('bikeAvailable')
                        docks = rec.get('bemp') or rec.get('available_return_bikes') or rec.get('AvailableSpaceCount') or rec.get('empty') or rec.get('dockAvailable')
                        return name, addr, sarea, bikes, docks
                    def matches(rec: dict):
                        if not kw:
                            return True
                        try:
                            return any(kw in str(v).lower() for v in rec.values())
                        except Exception:
                            return False
                    for rec in arr:
                        if not isinstance(rec, dict):
                            continue
                        if matches(rec):
                            data.append(rec)
                        if len(data) >= 10:
                            break
                else:
                    data = []
            elif api_source == "youbike_taipei_monthly":
                # 下載 CSV 並解析
                resp = requests.get(source_url, timeout=30)
                resp.raise_for_status()
                text = resp.content.decode('utf-8', errors='ignore')
                import csv
                rows = list(csv.DictReader(text.splitlines()))
                kw = (keyword or '').strip().lower()
                def matches_row(row: dict):
                    if not kw:
                        return True
                    try:
                        return any(kw in str(v).lower() for v in row.values())
                    except Exception:
                        return False
                for row in rows:
                    if matches_row(row):
                        data.append(row)
                    if len(data) >= 10:
                        break
            else:
                # CKAN 路徑（dataset UUID → package_show → datastore_search）
                dataset_id = source_url if len(source_url) == 36 else source_url
                package_url = "https://data.taipei/api/3/action/package_show"
                ds_url = "https://data.taipei/api/3/action/datastore_search"
                pkg_resp = requests.get(package_url, params={"id": dataset_id}, timeout=15)
                pkg_resp.raise_for_status()
                pkg_json = pkg_resp.json()
                resources = pkg_json.get("result", {}).get("resources", []) if pkg_json.get("success") else []
                resource_id = None
                for r in resources:
                    if r.get("datastore_active"):
                        resource_id = r.get("id")
                        break
                if not resource_id and resources:
                    resource_id = resources[0].get("id")
                if resource_id:
                    ds_params = {"resource_id": resource_id, "q": keyword, "limit": 10}
                    ds_resp = requests.get(ds_url, params=ds_params, timeout=20)
                    ds_resp.raise_for_status()
                    ds_json = ds_resp.json()
                    if ds_json.get("success"):
                        data = ds_json.get("result", {}).get("records", [])
                    if not data:
                        ds_params_fallback = {"resource_id": resource_id, "limit": 50}
                        ds_resp2 = requests.get(ds_url, params=ds_params_fallback, timeout=20)
                        ds_resp2.raise_for_status()
                        ds_json2 = ds_resp2.json()
                        if ds_json2.get("success"):
                            records = ds_json2.get("result", {}).get("records", [])
                            kw = str(keyword).strip().lower()
                            def match_any(rec):
                                try:
                                    return any(kw in str(v).lower() for v in rec.values())
                                except Exception:
                                    return False
                            data = [r for r in records if match_any(r)][:10]
        except requests.RequestException:
            data = []

        if not data:
            await interaction.followup.send("❌ 查無相關資料，請嘗試其他關鍵字。", ephemeral=True)
            return

        # 格式化查詢結果
        embed = discord.Embed(
            title=f"🔍 查詢結果：{keyword}",
            description=f"資料來源：{api_source}",
            color=0x3498db,
        )

        # 嘗試從常見欄位擷取標題/描述，否則以前兩個欄位組合
        def summarize_record(rec: dict) -> tuple:
            # YouBike 資料優先顯示站名與地址、可借可還
            if api_source in ("youbike_taipei", "youbike_new_taipei"):
                name = rec.get('sna') or rec.get('stationName') or rec.get('StationName') or rec.get('name') or "YouBike 站點"
                addr = rec.get('ar') or rec.get('address') or rec.get('StationAddress') or rec.get('Address') or "無地址"
                sarea = rec.get('sarea') or rec.get('area')
                bikes = rec.get('sbi') or rec.get('available_rent_bikes') or rec.get('AvailableBikeCount') or rec.get('available') or rec.get('bikeAvailable')
                docks = rec.get('bemp') or rec.get('available_return_bikes') or rec.get('AvailableSpaceCount') or rec.get('empty') or rec.get('dockAvailable')
                title = f"{name} ({sarea})" if sarea else str(name)
                desc_parts = []
                if bikes is not None: desc_parts.append(f"可借: {bikes}")
                if docks is not None: desc_parts.append(f"可還: {docks}")
                desc_parts.append(str(addr))
                return title, " | ".join(map(str, desc_parts))
            if api_source == "youbike_taipei_monthly":
                # 嘗試常見欄位
                station = rec.get('站點名稱') or rec.get('StationName') or rec.get('站名') or rec.get('sna') or rec.get('name') or 'YouBike 站點'
                month = rec.get('月份') or rec.get('Month') or rec.get('month')
                usage = rec.get('租借次數') or rec.get('租借量') or rec.get('usage') or rec.get('count')
                title = f"{station} {month}" if month else str(station)
                desc = f"租借次數: {usage}" if usage is not None else (rec.get('地址') or rec.get('地點') or rec.get('address') or '無描述')
                return title, str(desc)

            title = rec.get("title") or rec.get("name") or rec.get("學校名稱") or rec.get("店名") or rec.get("案件類型")
            desc = rec.get("description") or rec.get("地址") or rec.get("地點") or rec.get("內容")
            if not title:
                # 任取前兩個欄位簡述
                items = list(rec.items())
                if items:
                    title = f"{items[0][0]}: {items[0][1]}"
            if not desc:
                items = list(rec.items())
                if len(items) > 1:
                    desc = f"{items[1][0]}: {items[1][1]}"
            return title or "無標題", (desc or "無描述")

        for item in data[:5]:
            t, d = summarize_record(item if isinstance(item, dict) else {})
            embed.add_field(name=str(t)[:256], value=str(d)[:1024], inline=False)

        await interaction.followup.send(embed=embed)

    except requests.RequestException as e:
        await interaction.followup.send(f"❌ API 請求失敗：{str(e)}", ephemeral=True)
    except Exception as e:
        await interaction.followup.send(f"❌ 發生錯誤：{str(e)}", ephemeral=True)

@tree.command(name="data", description="上傳資料並通知管理者")
async def data_command(interaction: discord.Interaction, file: discord.Attachment):
    try:
        await interaction.response.defer()

        # 下載檔案內容
        file_content = await file.read()
        backup_path = f"backups/{file.filename}"

        # 儲存備份
        os.makedirs("backups", exist_ok=True)
        with open(backup_path, "wb") as f:
            f.write(file_content)

        # 通知用戶
        await interaction.followup.send(f"✅ 資料已成功上傳並備份：{file.filename}，管理者將審核後決定是否採用。")

        # 通知管理者
        admin_channel_id = 1234567890  # 替換為您的管理者頻道 ID
        admin_channel = bot.get_channel(admin_channel_id)
        if admin_channel:
            await admin_channel.send(f"📁 收到新的資料上傳：{file.filename}，已備份至 {backup_path}", file=discord.File(backup_path))

    except Exception as e:
        await interaction.followup.send(f"❌ 上傳失敗：{str(e)}", ephemeral=True)
