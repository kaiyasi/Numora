"""
資料處理模組
處理 CSV 檔案載入、編碼檢測和資料清理
"""

import pandas as pd
import chardet
import io
import os
import re
import logging
from typing import Optional, Dict, List, Any

logger = logging.getLogger(__name__)

class DataProcessor:
    """資料處理器類"""
    
    def __init__(self):
        self.current_df: Optional[pd.DataFrame] = None
    
    def load_default_data(self) -> pd.DataFrame:
        """載入預設資料檔案"""
        file_paths = [
            'crime_data.txt',
            'data/crime_data.txt',
            './crime_data.txt'
        ]
        
        file_path = None
        for path in file_paths:
            if os.path.exists(path):
                file_path = path
                break
        
        if file_path is None:
            logger.warning("找不到預設資料檔案，使用空資料集")
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
                    logger.warning(f"解析第 {line_num} 行時發生錯誤: {e}")
                    continue
            
            if not data:
                raise ValueError("沒有有效的資料行")
            
            df = pd.DataFrame(data, columns=['編號', '案類', '日期', '時段', '地點'])
            df['年份'] = df['日期'].astype(str).str[:3].astype(int) + 1911
            
            logger.info(f"成功載入 {len(df)} 筆有效資料")
            return df
            
        except Exception as e:
            logger.error(f"載入資料時發生錯誤：{e}")
            raise
    
    def load_csv_data(self, file_content: bytes) -> pd.DataFrame:
        """載入並處理 CSV 資料"""
        try:
            # 檢測檔案編碼
            detected_encoding = chardet.detect(file_content)
            encoding = detected_encoding['encoding']
            
            logger.info(f"檢測到的編碼：{encoding} (信心度：{detected_encoding['confidence']:.2f})")
            
            # 嘗試多種編碼
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
                    logger.info(f"成功使用編碼：{enc}")
                    break
                except (UnicodeDecodeError, UnicodeError):
                    continue
                except Exception as e:
                    logger.warning(f"使用編碼 {enc} 時發生錯誤: {e}")
                    continue
            
            if df is None:
                raise ValueError("無法解析檔案")
            
            # 清理欄位名稱
            df.columns = df.columns.str.strip().str.replace('\ufeff', '')
            
            # 映射欄位名稱
            df = self._map_columns(df)
            
            # 處理年份
            df = self._process_dates(df)
            
            logger.info(f"成功載入 CSV 資料：{len(df)} 筆記錄")
            return df
            
        except Exception as e:
            logger.error(f"CSV 檔案處理錯誤：{str(e)}")
            raise ValueError(f"CSV 檔案處理錯誤：{str(e)}")
    
    def _map_columns(self, df: pd.DataFrame) -> pd.DataFrame:
        """映射欄位名稱到標準格式"""
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
        
        return df.rename(columns=column_mapping)
    
    def _process_dates(self, df: pd.DataFrame) -> pd.DataFrame:
        """處理日期欄位，轉換為年份"""
        try:
            # 嘗試民國年格式
            df['年份'] = df['日期'].astype(str).str[:3].astype(int) + 1911
        except:
            try:
                # 嘗試標準日期格式
                df['年份'] = pd.to_datetime(df['日期'], errors='coerce').dt.year
                df = df.dropna(subset=['年份'])
                df['年份'] = df['年份'].astype(int)
            except:
                try:
                    # 嘗試西元年格式
                    df['年份'] = df['日期'].astype(str).str[:4].astype(int)
                except:
                    raise ValueError("無法處理日期格式")
        
        return df
    
    def generate_statistics(self, df: pd.DataFrame) -> Dict[str, Any]:
        """生成統計資料"""
        try:
            from src.data.area_analyzer import AreaAnalyzer
            
            analyzer = AreaAnalyzer()
            areas_info = analyzer.extract_area_info(df)
            
            stats = {
                '總案件數': len(df),
                '年份範圍': f"{df['年份'].min()} - {df['年份'].max()}",
                '可用地區': areas_info,
                '年份統計': df['年份'].value_counts().sort_index().to_dict(),
                '時段統計': df['時段'].value_counts().to_dict(),
                '案類統計': df['案類'].value_counts().to_dict()
            }
            
            return stats
            
        except Exception as e:
            logger.error(f"生成統計資料時發生錯誤: {e}")
            return {
                '總案件數': len(df),
                '年份範圍': f"{df['年份'].min()} - {df['年份'].max()}",
                '可用地區': {},
                '年份統計': df['年份'].value_counts().sort_index().to_dict(),
                '時段統計': df['時段'].value_counts().to_dict(),
                '案類統計': df['案類'].value_counts().to_dict()
            }
    
    def set_current_data(self, df: pd.DataFrame):
        """設定當前資料"""
        self.current_df = df
    
    def get_current_data(self) -> Optional[pd.DataFrame]:
        """取得當前資料"""
        return self.current_df
    
    def clear_current_data(self):
        """清除當前資料"""
        self.current_df = None
