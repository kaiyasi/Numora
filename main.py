import discord
from discord.ext import commands
from discord.ui import View, Select, Button
import matplotlib.pyplot as plt
import pandas as pd
import matplotlib.font_manager as fm
import os
import io
import chardet
import re
from dotenv import load_dotenv

# ✅ 設定中文字型
def setup_matplotlib_fonts():
    """Configure matplotlib to properly display Chinese characters"""
    # DisCloud 環境通常沒有中文字型，使用 DejaVu Sans 作為備選
    plt.rcParams['font.sans-serif'] = ['DejaVu Sans', 'Arial', 'sans-serif']
    plt.rcParams['axes.unicode_minus'] = False
    plt.rcParams['figure.max_open_warning'] = 0
    
    print("✅ 字型設定完成（雲端環境）")

# Call this function right after imports
setup_matplotlib_fonts()

# Discord bot 設定
intents = discord.Intents.default()
bot = commands.Bot(command_prefix='!', intents=intents)
tree = bot.tree

# 全域變數儲存資料
current_df = None

# 📊 提取地區資訊的函式
def extract_area_info(df):
    """提取地區資訊並返回可用的地區列表"""
    df_copy = df.copy()
    
    # 修正地區提取方式，優先匹配完整的市區格式，避免誤判
    area_patterns = [
        (r'(.+?市)(.+?區)', '市區'),  # 使用非貪婪匹配，台北市中山區
        (r'(.+?縣)(.+?市)', '縣市'),  # 新竹縣竹北市
        (r'(.+?縣)(.+?鄉)', '縣鄉'),  # 南投縣埔里鄉
        (r'(.+?縣)(.+?鎮)', '縣鎮'),  # 新增鎮的支援
    ]
    
    areas_found = {}
    
    for pattern, area_type in area_patterns:
        matches = df_copy['地點'].str.extract(pattern, expand=False)
        if area_type in ['市區', '縣市', '縣鄉', '縣鎮']:
            # 組合型地區
            if isinstance(matches, pd.DataFrame) and len(matches.columns) >= 2:
                combined = matches.iloc[:, 0] + matches.iloc[:, 1]
                valid_matches = combined.dropna().unique()  # 使用unique去重
                if len(valid_matches) > 0:
                    areas_found[area_type] = list(valid_matches)
    
    # 輸出提取到的地區資訊
    if areas_found:
        print("✅ 提取到的地區資訊:")
        for area_type, areas in areas_found.items():
            print(f"  {area_type}: {', '.join(areas[:10])}{'...' if len(areas) > 10 else ''}")
        print(f"  總共 {sum(len(areas) for areas in areas_found.values())} 個地區")
    
    return areas_found

def extract_district_by_area(df, selected_area):
    """根據選擇的地區提取行政區，避免誤判里名中的市字"""
    df_copy = df.copy()
    
    if selected_area == '全部地區':
        # 使用最簡單且準確的方式提取
        # 優先提取市區組合
        city_district_pattern = r'(.+?市)(.+?區)'
        matches = df_copy['地點'].str.extract(city_district_pattern, expand=False)
        df_copy['區'] = matches[0] + matches[1]
        
        # 補充縣市組合
        county_city_pattern = r'(.+?縣)(.+?市)'
        county_matches = df_copy['地點'].str.extract(county_city_pattern, expand=False)
        county_combined = county_matches[0] + county_matches[1]
        
        # 補充縣鄉鎮組合
        county_township_pattern = r'(.+?縣)(.+?[鄉鎮])'
        township_matches = df_copy['地點'].str.extract(county_township_pattern, expand=False)
        township_combined = township_matches[0] + township_matches[1]
        
        # 按優先順序填充
        df_copy['區'] = df_copy['區'].fillna(county_combined)
        df_copy['區'] = df_copy['區'].fillna(township_combined)
        
    elif '區' in selected_area:
        # 如果已經是完整的市區格式，篩選包含該地區的記錄
        filtered_df = df_copy[df_copy['地點'].str.contains(selected_area, na=False)]
        if not filtered_df.empty:
            df_copy = filtered_df
            df_copy['區'] = selected_area
        else:
            df_copy['區'] = None
            
    elif '市' in selected_area:
        # 提取該市下的所有區
        city_name = selected_area
        pattern = f'{city_name}(.+?區)'
        matches = df_copy['地點'].str.extract(pattern, expand=False)
        df_copy['區'] = city_name + matches
        
    elif '縣' in selected_area:
        # 提取該縣下的市/鄉/鎮
        county_name = selected_area
        patterns = [
            f'{county_name}(.+?市)',
            f'{county_name}(.+?鄉)', 
            f'{county_name}(.+?鎮)'
        ]
        df_copy['區'] = None
        for pattern in patterns:
            matches = df_copy['地點'].str.extract(pattern, expand=False)
            combined = county_name + matches
            df_copy['區'] = df_copy['區'].fillna(combined)
    
    # 清理資料
    df_copy = df_copy.dropna(subset=['區'])
    df_copy = df_copy[df_copy['區'].str.len() > 0]
    df_copy['區'] = df_copy['區'].str.strip()
    df_copy['區'] = df_copy['區'].str.replace(r'\s+', '', regex=True)
    
    return df_copy

# 📊 圖表產生函式 - 支援地區選擇
def generate_area_year_plot(df, area, year):
    try:
        # 篩選年份
        year_data = df[df['年份'] == year]
        
        if year_data.empty:
            return None
        
        # 篩選地區
        if area != '全部地區':
            area_data = year_data[year_data['地點'].str.contains(area, na=False)]
        else:
            area_data = year_data
        
        if area_data.empty:
            return None
        
        # 提取行政區
        area_data = extract_district_by_area(area_data, area)
        
        if area_data.empty:
            return None
        
        # 正確計算案件數
        district_counts = area_data['區'].value_counts().sort_values(ascending=False)
        
        if district_counts.empty:
            return None

        # 確保計數是整數而非小數
        district_counts = district_counts.astype(int)
        
        # 使用更大的圖表尺寸
        fig, ax = plt.subplots(figsize=(16, 10))
        
        bars = ax.bar(range(len(district_counts)), district_counts.values, color='skyblue')
        
        # 設定標題和標籤
        title = f'{area} - {year} 年各行政區案件數' if area != '全部地區' else f'{year} 年各地區案件數'
        ax.set_title(title, fontsize=18, pad=25)
        ax.set_xlabel('行政區', fontsize=14)
        ax.set_ylabel('案件數', fontsize=14)
        
        # 設定 x 軸標籤
        ax.set_xticks(range(len(district_counts)))
        ax.set_xticklabels(district_counts.index, rotation=45, ha='right', fontsize=12)
        
        # 確保 y 軸顯示整數刻度
        ax.yaxis.set_major_locator(plt.MaxNLocator(integer=True))
        
        # 移除上方的標籤（解決上排顯示 1 的問題）
        ax.tick_params(top=False, labeltop=False)
        
        # 調整邊距
        plt.subplots_adjust(bottom=0.25, left=0.1, right=0.95, top=0.9)
        
        # 在柱狀圖上顯示數值
        for i, bar in enumerate(bars):
            height = bar.get_height()
            ax.text(bar.get_x() + bar.get_width()/2., height + 0.5,
                    f'{int(height)}', ha='center', va='bottom', fontsize=10)
        
        plt.tight_layout()
        filename = f"plot_{area}_{year}.png"
        
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

def generate_area_rank_plot(df, area, top_n=10):
    try:
        # 篩選地區
        if area != '全部地區':
            area_data = df[df['地點'].str.contains(area, na=False)]
        else:
            area_data = df
        
        if area_data.empty:
            return None
        
        # 提取行政區
        area_data = extract_district_by_area(area_data, area)
        
        if area_data.empty:
            return None
        
        district_counts = area_data['區'].value_counts().head(top_n)
        
        # 使用更大的圖表尺寸
        fig, ax = plt.subplots(figsize=(16, 10))
        bars = ax.bar(range(len(district_counts)), district_counts.values, color='tomato')
        
        # 設定標題和標籤
        title = f'{area} - 前{top_n}案件熱點行政區' if area != '全部地區' else f'前{top_n}案件熱點地區'
        ax.set_title(title, fontsize=18, pad=25)
        ax.set_xlabel('行政區', fontsize=14)
        ax.set_ylabel('案件數', fontsize=14)
        
        # 設定 x 軸標籤
        ax.set_xticks(range(len(district_counts)))
        ax.set_xticklabels(district_counts.index, rotation=45, ha='right', fontsize=12)
        
        # 調整邊距
        plt.subplots_adjust(bottom=0.25, left=0.1, right=0.95, top=0.9)
        
        # 在柱狀圖上顯示數值
        for i, bar in enumerate(bars):
            height = bar.get_height()
            ax.text(bar.get_x() + bar.get_width()/2., height + 0.5,
                    f'{int(height)}', ha='center', va='bottom', fontsize=10)
        
        plt.tight_layout()
        filename = f"rank_{area}_top{top_n}.png"
        
        # Add more robust file handling
        try:
            plt.savefig(filename, dpi=150, bbox_inches='tight', facecolor='white')
            plt.close('all')
            return filename
        except Exception as e:
            plt.close('all')
            return None
            
    except Exception as e:
        plt.close('all')
        return None

def generate_yearly_plot(df, area):
    """生成全年度的統計圖表"""
    try:
        # 篩選地區
        if area != '全部地區':
            area_data = df[df['地點'].str.contains(area, na=False)]
        else:
            area_data = df
        
        if area_data.empty:
            print(f"⚠️ 警告: {area} 地區沒有資料")
            return None
        
        # 提取行政區
        area_data = extract_district_by_area(area_data, area)
        
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
