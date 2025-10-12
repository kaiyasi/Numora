"""
地區分析模組
處理地區資訊提取和行政區劃分析
"""

import pandas as pd
import re
import logging
from typing import Dict, List, Optional

logger = logging.getLogger(__name__)

class AreaAnalyzer:
    """地區分析器類"""
    
    def __init__(self):
        self.area_patterns = [
            (r'(.+?市)(.+?區)', '市區'),
            (r'(.+?縣)(.+?市)', '縣市'),
            (r'(.+?縣)(.+?鄉)', '縣鄉'),
            (r'(.+?縣)(.+?鎮)', '縣鎮'),
        ]
    
    def extract_area_info(self, df: pd.DataFrame) -> Dict[str, List[str]]:
        """提取地區資訊並返回可用的地區列表"""
        df_copy = df.copy()
        areas_found = {}
        
        for pattern, area_type in self.area_patterns:
            try:
                matches = df_copy['地點'].str.extract(pattern, expand=False)
                if area_type in ['市區', '縣市', '縣鄉', '縣鎮']:
                    if isinstance(matches, pd.DataFrame) and len(matches.columns) >= 2:
                        combined = matches.iloc[:, 0] + matches.iloc[:, 1]
                        valid_matches = combined.dropna().unique()
                        if len(valid_matches) > 0:
                            areas_found[area_type] = list(valid_matches)
            except Exception as e:
                logger.warning(f"提取地區資訊時發生錯誤 ({area_type}): {e}")
                continue
        
        if areas_found:
            logger.info("提取到的地區資訊:")
            for area_type, areas in areas_found.items():
                logger.info(f"  {area_type}: {', '.join(areas[:10])}{'...' if len(areas) > 10 else ''}")
            logger.info(f"  總共 {sum(len(areas) for areas in areas_found.values())} 個地區")
        
        return areas_found
    
    def extract_district_by_area(self, df: pd.DataFrame, selected_area: str) -> pd.DataFrame:
        """根據選擇的地區提取行政區，避免誤判里名中的市字"""
        df_copy = df.copy()
        
        try:
            if selected_area == '全部地區':
                df_copy = self._extract_all_districts(df_copy)
            elif '區' in selected_area:
                df_copy = self._extract_specific_district(df_copy, selected_area)
            elif '市' in selected_area:
                df_copy = self._extract_city_districts(df_copy, selected_area)
            elif '縣' in selected_area:
                df_copy = self._extract_county_districts(df_copy, selected_area)
            
            # 清理資料
            df_copy = df_copy.dropna(subset=['區'])
            df_copy = df_copy[df_copy['區'].str.len() > 0]
            df_copy['區'] = df_copy['區'].str.strip()
            df_copy['區'] = df_copy['區'].str.replace(r'\s+', '', regex=True)
            
            return df_copy
            
        except Exception as e:
            logger.error(f"提取行政區時發生錯誤: {e}")
            return pd.DataFrame()
    
    def _extract_all_districts(self, df: pd.DataFrame) -> pd.DataFrame:
        """提取所有地區的行政區"""
        # 優先提取市區組合
        city_district_pattern = r'(.+?市)(.+?區)'
        matches = df['地點'].str.extract(city_district_pattern, expand=False)
        df['區'] = matches[0] + matches[1]
        
        # 補充縣市組合
        county_city_pattern = r'(.+?縣)(.+?市)'
        county_matches = df['地點'].str.extract(county_city_pattern, expand=False)
        county_combined = county_matches[0] + county_matches[1]
        
        # 補充縣鄉鎮組合
        county_township_pattern = r'(.+?縣)(.+?[鄉鎮])'
        township_matches = df['地點'].str.extract(county_township_pattern, expand=False)
        township_combined = township_matches[0] + township_matches[1]
        
        # 按優先順序填充
        df['區'] = df['區'].fillna(county_combined)
        df['區'] = df['區'].fillna(township_combined)
        
        return df
    
    def _extract_specific_district(self, df: pd.DataFrame, selected_area: str) -> pd.DataFrame:
        """提取特定區域"""
        filtered_df = df[df['地點'].str.contains(selected_area, na=False)]
        if not filtered_df.empty:
            df = filtered_df
            df['區'] = selected_area
        else:
            df['區'] = None
        return df
    
    def _extract_city_districts(self, df: pd.DataFrame, city_name: str) -> pd.DataFrame:
        """提取該市下的所有區"""
        pattern = f'{city_name}(.+?區)'
        matches = df['地點'].str.extract(pattern, expand=False)
        df['區'] = city_name + matches
        return df
    
    def _extract_county_districts(self, df: pd.DataFrame, county_name: str) -> pd.DataFrame:
        """提取該縣下的市/鄉/鎮"""
        patterns = [
            f'{county_name}(.+?市)',
            f'{county_name}(.+?鄉)', 
            f'{county_name}(.+?鎮)'
        ]
        df['區'] = None
        for pattern in patterns:
            matches = df['地點'].str.extract(pattern, expand=False)
            combined = county_name + matches
            df['區'] = df['區'].fillna(combined)
        return df
