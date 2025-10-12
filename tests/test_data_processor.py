"""
資料處理模組測試
"""

import pytest
import pandas as pd
import io
from unittest.mock import patch, mock_open

from src.data.processor import DataProcessor

class TestDataProcessor:
    """資料處理器測試類"""
    
    def setup_method(self):
        """設定測試方法"""
        self.processor = DataProcessor()
    
    def test_load_csv_data_utf8(self):
        """測試載入 UTF-8 編碼的 CSV 資料"""
        csv_content = "編號,案類,日期,時段,地點\n1,竊盜,1120101,0-6,台北市中山區\n".encode('utf-8')
        
        df = self.processor.load_csv_data(csv_content)
        
        assert not df.empty
        assert len(df) == 1
        assert '編號' in df.columns
        assert '案類' in df.columns
        assert '年份' in df.columns
        assert df.iloc[0]['年份'] == 2023
    
    def test_load_csv_data_big5(self):
        """測試載入 Big5 編碼的 CSV 資料"""
        csv_content = "編號,案類,日期,時段,地點\n1,竊盜,1120101,0-6,台北市中山區\n".encode('big5')
        
        df = self.processor.load_csv_data(csv_content)
        
        assert not df.empty
        assert len(df) == 1
        assert df.iloc[0]['年份'] == 2023
    
    def test_load_csv_data_invalid_encoding(self):
        """測試載入無效編碼的資料"""
        invalid_content = b'\xff\xfe\x00\x00invalid'
        
        with pytest.raises(ValueError):
            self.processor.load_csv_data(invalid_content)
    
    def test_map_columns_standard(self):
        """測試標準欄位映射"""
        df = pd.DataFrame({
            '編號': [1, 2],
            '案類': ['竊盜', '詐欺'],
            '日期': ['1120101', '1120102'],
            '時段': ['0-6', '6-12'],
            '地點': ['台北市', '新北市']
        })
        
        mapped_df = self.processor._map_columns(df)
        
        assert '編號' in mapped_df.columns
        assert '案類' in mapped_df.columns
        assert '日期' in mapped_df.columns
        assert '時段' in mapped_df.columns
        assert '地點' in mapped_df.columns
    
    def test_map_columns_english(self):
        """測試英文欄位映射"""
        df = pd.DataFrame({
            'ID': [1, 2],
            'Type': ['theft', 'fraud'],
            'Date': ['1120101', '1120102'],
            'Time': ['0-6', '6-12'],
            'Location': ['Taipei', 'New Taipei']
        })
        
        mapped_df = self.processor._map_columns(df)
        
        assert '編號' in mapped_df.columns
        assert '案類' in mapped_df.columns
        assert '日期' in mapped_df.columns
        assert '時段' in mapped_df.columns
        assert '地點' in mapped_df.columns
    
    def test_map_columns_missing_required(self):
        """測試缺少必要欄位"""
        df = pd.DataFrame({
            'ID': [1, 2],
            'Type': ['theft', 'fraud']
            # 缺少日期、時段、地點欄位
        })
        
        with pytest.raises(ValueError, match="找不到必要欄位"):
            self.processor._map_columns(df)
    
    def test_process_dates_minguo(self):
        """測試民國年日期處理"""
        df = pd.DataFrame({
            '編號': [1, 2],
            '案類': ['竊盜', '詐欺'],
            '日期': ['1120101', '1130102'],
            '時段': ['0-6', '6-12'],
            '地點': ['台北市', '新北市']
        })
        
        processed_df = self.processor._process_dates(df)
        
        assert '年份' in processed_df.columns
        assert processed_df.iloc[0]['年份'] == 2023
        assert processed_df.iloc[1]['年份'] == 2024
    
    def test_process_dates_western(self):
        """測試西元年日期處理"""
        df = pd.DataFrame({
            '編號': [1, 2],
            '案類': ['竊盜', '詐欺'],
            '日期': ['2023-01-01', '2024-01-02'],
            '時段': ['0-6', '6-12'],
            '地點': ['台北市', '新北市']
        })
        
        processed_df = self.processor._process_dates(df)
        
        assert '年份' in processed_df.columns
        assert processed_df.iloc[0]['年份'] == 2023
        assert processed_df.iloc[1]['年份'] == 2024
    
    def test_generate_statistics(self, sample_dataframe):
        """測試統計資料生成"""
        stats = self.processor.generate_statistics(sample_dataframe)
        
        assert '總案件數' in stats
        assert '年份範圍' in stats
        assert '可用地區' in stats
        assert '年份統計' in stats
        assert '時段統計' in stats
        assert '案類統計' in stats
        
        assert stats['總案件數'] == 5
        assert '2023' in stats['年份範圍']
    
    @patch('builtins.open', mock_open(read_data="編號 案類 日期 時段 地點\n1 竊盜 1120101 0-6 台北市中山區"))
    @patch('os.path.exists', return_value=True)
    def test_load_default_data(self):
        """測試載入預設資料"""
        df = self.processor.load_default_data()
        
        assert not df.empty
        assert len(df) == 1
        assert '年份' in df.columns
    
    @patch('os.path.exists', return_value=False)
    def test_load_default_data_no_file(self):
        """測試載入預設資料（檔案不存在）"""
        df = self.processor.load_default_data()
        
        assert df.empty
        assert list(df.columns) == ['編號', '案類', '日期', '時段', '地點', '年份']
    
    def test_set_get_current_data(self, sample_dataframe):
        """測試設定和取得當前資料"""
        self.processor.set_current_data(sample_dataframe)
        
        retrieved_df = self.processor.get_current_data()
        
        assert retrieved_df is not None
        assert len(retrieved_df) == 5
        pd.testing.assert_frame_equal(retrieved_df, sample_dataframe)
    
    def test_clear_current_data(self, sample_dataframe):
        """測試清除當前資料"""
        self.processor.set_current_data(sample_dataframe)
        assert self.processor.get_current_data() is not None
        
        self.processor.clear_current_data()
        assert self.processor.get_current_data() is None
