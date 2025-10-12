"""
地區分析模組測試
"""

import pytest
import pandas as pd

from src.data.area_analyzer import AreaAnalyzer

class TestAreaAnalyzer:
    """地區分析器測試類"""
    
    def setup_method(self):
        """設定測試方法"""
        self.analyzer = AreaAnalyzer()
    
    def test_extract_area_info(self, sample_dataframe):
        """測試提取地區資訊"""
        areas_info = self.analyzer.extract_area_info(sample_dataframe)
        
        assert isinstance(areas_info, dict)
        assert '市區' in areas_info
        assert '台北市中山區' in areas_info['市區']
        assert '台北市信義區' in areas_info['市區']
    
    def test_extract_area_info_empty_dataframe(self):
        """測試空 DataFrame 的地區資訊提取"""
        empty_df = pd.DataFrame(columns=['地點'])
        areas_info = self.analyzer.extract_area_info(empty_df)
        
        assert isinstance(areas_info, dict)
        assert len(areas_info) == 0
    
    def test_extract_district_by_area_all(self, sample_dataframe):
        """測試提取全部地區的行政區"""
        result_df = self.analyzer.extract_district_by_area(sample_dataframe, '全部地區')
        
        assert '區' in result_df.columns
        assert not result_df.empty
        assert '台北市中山區' in result_df['區'].values
        assert '台北市信義區' in result_df['區'].values
    
    def test_extract_district_by_area_specific_district(self, sample_dataframe):
        """測試提取特定區域"""
        result_df = self.analyzer.extract_district_by_area(sample_dataframe, '台北市中山區')
        
        assert '區' in result_df.columns
        assert not result_df.empty
        assert all(result_df['區'] == '台北市中山區')
    
    def test_extract_district_by_area_city(self, sample_dataframe):
        """測試提取特定市的所有區"""
        result_df = self.analyzer.extract_district_by_area(sample_dataframe, '台北市')
        
        assert '區' in result_df.columns
        assert not result_df.empty
        # 應該包含台北市的所有區
        taipei_districts = result_df['區'].unique()
        assert any('台北市' in district for district in taipei_districts)
    
    def test_extract_district_by_area_county(self):
        """測試提取縣級地區"""
        # 創建包含縣級地區的測試資料
        county_data = pd.DataFrame({
            '編號': [1, 2, 3],
            '案類': ['竊盜', '詐欺', '傷害'],
            '日期': ['1120101', '1120102', '1120103'],
            '時段': ['0-6', '6-12', '12-18'],
            '地點': [
                '新竹縣竹北市成功路',
                '南投縣埔里鄉中山路',
                '彰化縣員林鎮民權路'
            ],
            '年份': [2023, 2023, 2023]
        })
        
        result_df = self.analyzer.extract_district_by_area(county_data, '新竹縣')
        
        assert '區' in result_df.columns
        assert not result_df.empty
        assert '新竹縣竹北市' in result_df['區'].values
    
    def test_extract_district_by_area_no_match(self, sample_dataframe):
        """測試沒有匹配的地區"""
        result_df = self.analyzer.extract_district_by_area(sample_dataframe, '不存在的地區')
        
        # 應該返回空的 DataFrame 或沒有有效的區域資料
        assert result_df.empty or result_df['區'].isna().all()
    
    def test_extract_all_districts(self, sample_dataframe):
        """測試提取所有行政區的私有方法"""
        result_df = self.analyzer._extract_all_districts(sample_dataframe.copy())
        
        assert '區' in result_df.columns
        assert not result_df.empty
        # 檢查是否正確提取了市區組合
        district_values = result_df['區'].dropna().unique()
        assert len(district_values) > 0
    
    def test_extract_specific_district(self, sample_dataframe):
        """測試提取特定區域的私有方法"""
        result_df = self.analyzer._extract_specific_district(sample_dataframe.copy(), '台北市中山區')
        
        assert '區' in result_df.columns
        assert not result_df.empty
        assert all(result_df['區'] == '台北市中山區')
    
    def test_extract_city_districts(self, sample_dataframe):
        """測試提取城市行政區的私有方法"""
        result_df = self.analyzer._extract_city_districts(sample_dataframe.copy(), '台北市')
        
        assert '區' in result_df.columns
        # 檢查是否包含台北市的區域
        taipei_districts = result_df['區'].dropna()
        assert len(taipei_districts) > 0
        assert all('台北市' in str(district) for district in taipei_districts)
    
    def test_extract_county_districts(self):
        """測試提取縣級行政區的私有方法"""
        county_data = pd.DataFrame({
            '地點': [
                '新竹縣竹北市成功路',
                '新竹縣新埔鎮中山路',
                '新竹縣關西鄉民權路'
            ]
        })
        
        result_df = self.analyzer._extract_county_districts(county_data.copy(), '新竹縣')
        
        assert '區' in result_df.columns
        county_districts = result_df['區'].dropna()
        assert len(county_districts) > 0
        assert all('新竹縣' in str(district) for district in county_districts)
    
    def test_area_patterns(self):
        """測試地區模式匹配"""
        test_locations = [
            '台北市中山區民權東路',
            '新竹縣竹北市成功路',
            '南投縣埔里鄉中山路',
            '彰化縣員林鎮民權路'
        ]
        
        test_df = pd.DataFrame({'地點': test_locations})
        areas_info = self.analyzer.extract_area_info(test_df)
        
        # 檢查是否正確識別了不同類型的地區
        assert '市區' in areas_info  # 台北市中山區
        assert '縣市' in areas_info  # 新竹縣竹北市
        assert '縣鄉' in areas_info  # 南投縣埔里鄉
        assert '縣鎮' in areas_info  # 彰化縣員林鎮
    
    def test_data_cleaning(self, sample_dataframe):
        """測試資料清理功能"""
        # 添加一些需要清理的資料
        dirty_data = sample_dataframe.copy()
        dirty_data.loc[len(dirty_data)] = {
            '編號': 6,
            '案類': '竊盜',
            '日期': '1120106',
            '時段': '0-6',
            '地點': '   台北市 大安區   ',  # 包含多餘空格
            '年份': 2023
        }
        
        result_df = self.analyzer.extract_district_by_area(dirty_data, '全部地區')
        
        # 檢查資料是否被正確清理
        assert '區' in result_df.columns
        districts = result_df['區'].dropna()
        
        # 確保沒有空字串或只包含空格的值
        assert all(len(str(district).strip()) > 0 for district in districts)
        
        # 確保沒有多餘的空格
        assert all('  ' not in str(district) for district in districts)
