"""
圖表生成模組
處理各種統計圖表的生成
"""

import matplotlib.pyplot as plt
import matplotlib.font_manager as fm
import pandas as pd
import os
import logging
from typing import Optional
from src.utils.config import config
from src.data.area_analyzer import AreaAnalyzer

logger = logging.getLogger(__name__)

class ChartGenerator:
    """圖表生成器類"""
    
    def __init__(self):
        self.area_analyzer = AreaAnalyzer()
        self._setup_matplotlib_fonts()
    
    def _setup_matplotlib_fonts(self):
        """設定中文字型"""
        font_path = config.FONT_PATH
        
        if os.path.exists(font_path):
            try:
                font_prop = fm.FontProperties(fname=font_path)
                font_name = font_prop.get_name()
                
                fm.fontManager.addfont(font_path)
                plt.rcParams['font.sans-serif'] = [font_name, 'DejaVu Sans', 'Arial', 'sans-serif']
                
                logger.info(f"成功載入自訂中文字型：'{font_name}'，路徑：'{font_path}'")
                
            except Exception as e:
                logger.warning(f"載入自訂字型失敗：{e}")
                plt.rcParams['font.sans-serif'] = ['DejaVu Sans', 'Arial', 'sans-serif']
        else:
            logger.warning(f"未找到自訂中文字型檔案：'{font_path}'")
            plt.rcParams['font.sans-serif'] = ['DejaVu Sans', 'Arial', 'sans-serif']

        plt.rcParams['axes.unicode_minus'] = False 
        plt.rcParams['figure.max_open_warning'] = 0 
        
        logger.info("Matplotlib 字型設定完成")
    
    def generate_area_year_plot(self, df: pd.DataFrame, area: str, year: int) -> Optional[str]:
        """生成地區年度統計圖"""
        try:
            # 篩選年份
            year_data = df[df['年份'] == year]
            
            if year_data.empty:
                logger.warning(f"沒有 {year} 年的資料")
                return None
            
            # 篩選地區
            if area != '全部地區':
                area_data = year_data[year_data['地點'].str.contains(area, na=False)]
            else:
                area_data = year_data
            
            if area_data.empty:
                logger.warning(f"沒有 {area} 地區的資料")
                return None
            
            # 提取行政區
            area_data = self.area_analyzer.extract_district_by_area(area_data, area)
            
            if area_data.empty:
                logger.warning("提取行政區後沒有資料")
                return None
            
            # 計算案件數
            district_counts = area_data['區'].value_counts().sort_values(ascending=False)
            
            if district_counts.empty:
                logger.warning("沒有有效的行政區資料")
                return None

            district_counts = district_counts.astype(int)
            
            # 創建圖表
            fig, ax = plt.subplots(figsize=(config.DEFAULT_CHART_WIDTH/100, config.DEFAULT_CHART_HEIGHT/100))
            
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
            
            try:
                plt.savefig(filename, dpi=config.CHART_DPI, bbox_inches='tight', facecolor='white')
                plt.close('all')
                logger.info(f"成功生成圖表: {filename}")
                return filename
            except Exception as e:
                logger.error(f"儲存圖表失敗: {e}")
                plt.close('all')
                return None
                
        except Exception as e:
            logger.error(f"生成地區年度圖表時發生錯誤: {e}")
            plt.close('all')
            return None
    
    def generate_area_rank_plot(self, df: pd.DataFrame, area: str, top_n: int = 10) -> Optional[str]:
        """生成地區排名圖表"""
        try:
            # 篩選地區
            if area != '全部地區':
                area_data = df[df['地點'].str.contains(area, na=False)]
            else:
                area_data = df
            
            if area_data.empty:
                logger.warning(f"沒有 {area} 地區的資料")
                return None
            
            # 提取行政區
            area_data = self.area_analyzer.extract_district_by_area(area_data, area)
            
            if area_data.empty:
                logger.warning("提取行政區後沒有資料")
                return None
            
            district_counts = area_data['區'].value_counts().head(top_n)
            
            # 創建圖表
            fig, ax = plt.subplots(figsize=(config.DEFAULT_CHART_WIDTH/100, config.DEFAULT_CHART_HEIGHT/100))
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
            
            try:
                plt.savefig(filename, dpi=config.CHART_DPI, bbox_inches='tight', facecolor='white')
                plt.close('all')
                logger.info(f"成功生成排名圖表: {filename}")
                return filename
            except Exception as e:
                logger.error(f"儲存排名圖表失敗: {e}")
                plt.close('all')
                return None
                
        except Exception as e:
            logger.error(f"生成排名圖表時發生錯誤: {e}")
            plt.close('all')
            return None
    
    def generate_yearly_plot(self, df: pd.DataFrame, area: str) -> Optional[str]:
        """生成全年度統計圖表"""
        try:
            # 篩選地區
            if area != '全部地區':
                area_data = df[df['地點'].str.contains(area, na=False)]
            else:
                area_data = df
            
            if area_data.empty:
                logger.warning(f"沒有 {area} 地區的資料")
                return None
            
            # 提取行政區
            area_data = self.area_analyzer.extract_district_by_area(area_data, area)
            
            if area_data.empty:
                logger.warning("提取行政區後沒有資料")
                return None
            
            # 按年份分組計算案件數
            yearly_counts = area_data.groupby(['年份', '區']).size().unstack(fill_value=0)
            
            if yearly_counts.empty:
                logger.warning("年度計數結果為空")
                return None

            # 創建圖表
            fig, ax = plt.subplots(figsize=(config.DEFAULT_CHART_WIDTH/100, config.DEFAULT_CHART_HEIGHT/100))
            
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
            
            try:
                plt.savefig(filename, dpi=config.CHART_DPI, bbox_inches='tight', facecolor='white')
                plt.close('all')
                logger.info(f"成功生成年度圖表: {filename}")
                return filename
            except Exception as e:
                logger.error(f"儲存年度圖表失敗: {e}")
                plt.close('all')
                return None
                
        except Exception as e:
            logger.error(f"生成年度圖表時發生錯誤: {e}")
            plt.close('all')
            return None
