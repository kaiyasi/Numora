"""
政府公開資料 API 模組
整合台灣政府各機關的公開資料 API
"""

import aiohttp
import asyncio
import json
import logging
from typing import Dict, List, Optional, Any
from datetime import datetime, timedelta
import pandas as pd
from src.utils.gov_data_config import VERIFIED_DATASETS, GOV_PLATFORM_DATASETS, CITY_APIS, CENTRAL_APIS

logger = logging.getLogger(__name__)

class GovernmentDataAPI:
    """政府公開資料 API 整合類"""
    
    def __init__(self):
        self.session = None
        # 使用實際驗證過的資料集
        self.verified_datasets = VERIFIED_DATASETS
        self.platform_datasets = GOV_PLATFORM_DATASETS
        
    async def __aenter__(self):
        """異步上下文管理器入口"""
        self.session = aiohttp.ClientSession(
            timeout=aiohttp.ClientTimeout(total=30),
            headers={
                'User-Agent': 'CrimeStatsBot/2.0 (Serelix Studio)',
                'Accept': 'application/json'
            }
        )
        return self
    
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        """異步上下文管理器出口"""
        if self.session:
            await self.session.close()
    
    async def fetch_data(self, url: str, params: Dict[str, Any] = None) -> Optional[Dict]:
        """通用資料獲取方法"""
        try:
            async with self.session.get(url, params=params) as response:
                if response.status == 200:
                    data = await response.json()
                    logger.info(f"成功獲取資料: {url}")
                    return data
                else:
                    logger.warning(f"API 請求失敗: {response.status} - {url}")
                    return None
        except Exception as e:
            logger.error(f"獲取資料時發生錯誤: {e}")
            return None
    
    async def get_taipei_youbike_data(self) -> Optional[pd.DataFrame]:
        """獲取台北市 YouBike 即時資料"""
        try:
            dataset = self.verified_datasets["taipei_youbike"]
            url = f"{dataset['api_url']}/resource_acquire"
            
            data = await self.fetch_data(url)
            if data and 'result' in data:
                records = data['result'].get('results', [])
                if records:
                    df = pd.DataFrame(records)
                    logger.info(f"獲取到 {len(df)} 筆 YouBike 資料")
                    return df
            
            return None
        except Exception as e:
            logger.error(f"獲取 YouBike 資料時發生錯誤: {e}")
            return None
    
    async def get_taipei_wifi_data(self) -> Optional[pd.DataFrame]:
        """獲取台北市 WiFi 熱點資料"""
        try:
            dataset = self.verified_datasets["taipei_wifi"]
            url = f"{dataset['api_url']}/resource_acquire"
            
            data = await self.fetch_data(url)
            if data and 'result' in data:
                records = data['result'].get('results', [])
                if records:
                    df = pd.DataFrame(records)
                    logger.info(f"獲取到 {len(df)} 筆 WiFi 熱點資料")
                    return df
            
            return None
        except Exception as e:
            logger.error(f"獲取 WiFi 熱點資料時發生錯誤: {e}")
            return None
    
    async def get_weather_forecast(self, api_key: str, location: str = "臺北市") -> Optional[Dict]:
        """獲取氣象預報資料（需要 API Key）"""
        try:
            dataset = self.verified_datasets["weather_forecast"]
            url = dataset['api_url']
            params = {
                'Authorization': api_key,
                'locationName': location
            }
            
            data = await self.fetch_data(url, params)
            if data:
                logger.info(f"獲取到 {location} 氣象預報資料")
                return data
            
            return None
        except Exception as e:
            logger.error(f"獲取氣象預報資料時發生錯誤: {e}")
            return None
    
    async def get_freeway_traffic_info(self) -> Optional[Dict]:
        """獲取高速公路交通資訊"""
        try:
            dataset = self.verified_datasets["freeway_info"]
            # 這是一個示例端點，實際使用時需要確認正確的 API
            url = "https://tisvcloud.freeway.gov.tw/history/TDCS/M03A/"
            
            data = await self.fetch_data(url)
            if data:
                logger.info("獲取到高速公路交通資訊")
                return data
            
            return None
        except Exception as e:
            logger.error(f"獲取高速公路交通資訊時發生錯誤: {e}")
            return None
    
    def get_available_datasets(self) -> Dict[str, str]:
        """取得可用的資料集列表"""
        available = {}
        
        # 實際可用的資料集
        for key, dataset in self.verified_datasets.items():
            if dataset.get('verified', False):
                available[dataset['name']] = key
        
        # 政府平臺資料集（需手動下載）
        for key, dataset in self.platform_datasets.items():
            available[f"{dataset['name']} (手動下載)"] = key
        
        return available
    
    def get_dataset_info(self, dataset_key: str) -> Optional[Dict]:
        """獲取資料集詳細資訊"""
        if dataset_key in self.verified_datasets:
            return self.verified_datasets[dataset_key]
        elif dataset_key in self.platform_datasets:
            return self.platform_datasets[dataset_key]
        else:
            return None
    
    async def search_datasets(self, keyword: str) -> List[Dict]:
        """搜尋相關資料集"""
        results = []
        
        # 在已驗證的資料集中搜尋
        for key, dataset in self.verified_datasets.items():
            if (keyword.lower() in dataset['name'].lower() or 
                keyword.lower() in dataset['description'].lower()):
                results.append({
                    'key': key,
                    'name': dataset['name'],
                    'description': dataset['description'],
                    'agency': dataset['agency'],
                    'verified': dataset.get('verified', False),
                    'type': 'API'
                })
        
        # 在政府平臺資料集中搜尋
        for key, dataset in self.platform_datasets.items():
            if (keyword.lower() in dataset['name'].lower() or 
                keyword.lower() in dataset['description'].lower()):
                results.append({
                    'key': key,
                    'name': dataset['name'],
                    'description': dataset['description'],
                    'agency': dataset['agency'],
                    'verified': True,
                    'type': 'Download'
                })
        
        logger.info(f"找到 {len(results)} 個相關資料集")
        return results

class DataAnalyzer:
    """政府資料分析器"""
    
    def __init__(self):
        self.api = GovernmentDataAPI()
    
    async def get_taipei_overview(self) -> Optional[Dict]:
        """獲取台北市資料總覽"""
        try:
            async with self.api as api:
                overview = {
                    'area': '台北市',
                    'generated_at': datetime.now().isoformat(),
                    'data': {}
                }
                
                # 並行獲取台北市資料
                tasks = [
                    api.get_taipei_youbike_data(),
                    api.get_taipei_wifi_data()
                ]
                
                results = await asyncio.gather(*tasks, return_exceptions=True)
                data_types = ['youbike', 'wifi']
                
                for i, result in enumerate(results):
                    if isinstance(result, pd.DataFrame) and not result.empty:
                        overview['data'][data_types[i]] = {
                            'count': len(result),
                            'columns': list(result.columns),
                            'sample': result.head(3).to_dict('records') if len(result) > 0 else []
                        }
                    elif isinstance(result, Exception):
                        logger.warning(f"獲取 {data_types[i]} 資料時發生錯誤: {result}")
                
                return overview
                
        except Exception as e:
            logger.error(f"獲取台北市總覽時發生錯誤: {e}")
            return None
    
    async def analyze_area_data(self, area: str) -> Optional[Dict]:
        """分析地區資料（目前主要支援台北市）"""
        try:
            if area in ["台北市", "臺北市", "Taipei"]:
                return await self.get_taipei_overview()
            else:
                # 對於其他地區，返回基本資訊
                return {
                    'area': area,
                    'generated_at': datetime.now().isoformat(),
                    'message': f'目前主要支援台北市的即時資料，{area} 的資料可能需要手動下載政府資料集',
                    'available_datasets': self.api.get_available_datasets()
                }
                
        except Exception as e:
            logger.error(f"分析 {area} 資料時發生錯誤: {e}")
            return None
    
    async def __aenter__(self):
        """異步上下文管理器入口"""
        self.session = aiohttp.ClientSession(
            timeout=aiohttp.ClientTimeout(total=30),
            headers={
                'User-Agent': 'CrimeStatsBot/2.0 (Serelix Studio)',
                'Accept': 'application/json'
            }
        )
        return self
    
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        """異步上下文管理器出口"""
        if self.session:
            await self.session.close()
    
    async def fetch_data(self, url: str, params: Dict[str, Any] = None) -> Optional[Dict]:
        """通用資料獲取方法"""
        try:
            async with self.session.get(url, params=params) as response:
                if response.status == 200:
                    data = await response.json()
                    logger.info(f"成功獲取資料: {url}")
                    return data
                else:
                    logger.warning(f"API 請求失敗: {response.status} - {url}")
                    return None
        except Exception as e:
            logger.error(f"獲取資料時發生錯誤: {e}")
            return None
    
    async def get_crime_statistics(self, area: str = None, year: int = None) -> Optional[pd.DataFrame]:
        """獲取犯罪統計資料"""
        try:
            url = f"{self.base_urls['police']}{self.datasets['crime_stats']}"
            params = {'format': 'json', 'limit': 1000}
            
            if area:
                params['q'] = area
            if year:
                params['year'] = year
            
            data = await self.fetch_data(url, params)
            if data and 'result' in data:
                records = data['result'].get('records', [])
                if records:
                    df = pd.DataFrame(records)
                    logger.info(f"獲取到 {len(df)} 筆犯罪統計資料")
                    return df
            
            return None
        except Exception as e:
            logger.error(f"獲取犯罪統計資料時發生錯誤: {e}")
            return None
    
    async def get_police_stations(self, city: str = None) -> Optional[pd.DataFrame]:
        """獲取警察機關資料"""
        try:
            url = f"{self.base_urls['police']}{self.datasets['police_stations']}"
            params = {'format': 'json', 'limit': 500}
            
            if city:
                params['q'] = city
            
            data = await self.fetch_data(url, params)
            if data and 'result' in data:
                records = data['result'].get('records', [])
                if records:
                    df = pd.DataFrame(records)
                    logger.info(f"獲取到 {len(df)} 筆警察機關資料")
                    return df
            
            return None
        except Exception as e:
            logger.error(f"獲取警察機關資料時發生錯誤: {e}")
            return None
    
    async def get_population_data(self, area: str = None) -> Optional[pd.DataFrame]:
        """獲取人口統計資料"""
        try:
            url = f"{self.base_urls['police']}{self.datasets['population']}"
            params = {'format': 'json', 'limit': 1000}
            
            if area:
                params['q'] = area
            
            data = await self.fetch_data(url, params)
            if data and 'result' in data:
                records = data['result'].get('records', [])
                if records:
                    df = pd.DataFrame(records)
                    logger.info(f"獲取到 {len(df)} 筆人口統計資料")
                    return df
            
            return None
        except Exception as e:
            logger.error(f"獲取人口統計資料時發生錯誤: {e}")
            return None
    
    async def get_taipei_data(self, dataset_id: str, params: Dict[str, Any] = None) -> Optional[pd.DataFrame]:
        """獲取台北市政府公開資料"""
        try:
            url = f"{self.base_urls['taipei']}{dataset_id}"
            if not params:
                params = {'scope': 'resourceAquire'}
            
            data = await self.fetch_data(url, params)
            if data and 'result' in data:
                records = data['result'].get('results', [])
                if records:
                    df = pd.DataFrame(records)
                    logger.info(f"獲取到 {len(df)} 筆台北市資料")
                    return df
            
            return None
        except Exception as e:
            logger.error(f"獲取台北市資料時發生錯誤: {e}")
            return None
    
    async def get_weather_data(self, location: str = "臺北市") -> Optional[Dict]:
        """獲取氣象資料"""
        try:
            # 這裡需要氣象局 API Key
            url = f"{self.base_urls['weather']}F-C0032-001"
            params = {
                'Authorization': 'YOUR_CWB_API_KEY',  # 需要申請
                'locationName': location
            }
            
            data = await self.fetch_data(url, params)
            if data:
                logger.info(f"獲取到 {location} 氣象資料")
                return data
            
            return None
        except Exception as e:
            logger.error(f"獲取氣象資料時發生錯誤: {e}")
            return None
    
    async def get_hospital_data(self, city: str = None) -> Optional[pd.DataFrame]:
        """獲取醫療機構資料"""
        try:
            url = f"{self.base_urls['health']}{self.datasets['hospitals']}"
            params = {'format': 'json', 'limit': 1000}
            
            if city:
                params['q'] = city
            
            data = await self.fetch_data(url, params)
            if data and 'result' in data:
                records = data['result'].get('records', [])
                if records:
                    df = pd.DataFrame(records)
                    logger.info(f"獲取到 {len(df)} 筆醫療機構資料")
                    return df
            
            return None
        except Exception as e:
            logger.error(f"獲取醫療機構資料時發生錯誤: {e}")
            return None
    
    async def get_school_data(self, level: str = None, city: str = None) -> Optional[pd.DataFrame]:
        """獲取學校資料"""
        try:
            url = f"{self.base_urls['education']}{self.datasets['schools']}"
            params = {'format': 'json', 'limit': 1000}
            
            query_parts = []
            if level:
                query_parts.append(level)
            if city:
                query_parts.append(city)
            
            if query_parts:
                params['q'] = ' '.join(query_parts)
            
            data = await self.fetch_data(url, params)
            if data and 'result' in data:
                records = data['result'].get('records', [])
                if records:
                    df = pd.DataFrame(records)
                    logger.info(f"獲取到 {len(df)} 筆學校資料")
                    return df
            
            return None
        except Exception as e:
            logger.error(f"獲取學校資料時發生錯誤: {e}")
            return None
    
    async def search_datasets(self, keyword: str, limit: int = 10) -> Optional[List[Dict]]:
        """搜尋相關資料集"""
        try:
            url = "https://data.gov.tw/api/v2/rest/dataset"
            params = {
                'format': 'json',
                'q': keyword,
                'limit': limit
            }
            
            data = await self.fetch_data(url, params)
            if data and 'result' in data:
                results = data['result'].get('results', [])
                logger.info(f"找到 {len(results)} 個相關資料集")
                return results
            
            return None
        except Exception as e:
            logger.error(f"搜尋資料集時發生錯誤: {e}")
            return None
    
    def get_available_datasets(self) -> Dict[str, str]:
        """取得可用的資料集列表"""
        return {
            '犯罪統計': 'crime_stats',
            '警察機關': 'police_stations',
            '交通事故': 'accident_stats',
            '人口統計': 'population',
            '戶數統計': 'household',
            '失業率': 'unemployment',
            '物價指數': 'price_index',
            '學校名錄': 'schools',
            '學生數統計': 'students',
            '醫療機構': 'hospitals',
            '藥局資訊': 'pharmacies',
            '停車場': 'parking',
            '公車站牌': 'bus_stops',
            '空氣品質': 'air_quality',
            '氣象站': 'weather_stations',
            '長照機構': 'elderly_care',
            '社福機構': 'social_welfare'
        }

class DataAnalyzer:
    """政府資料分析器"""
    
    def __init__(self):
        self.api = GovernmentDataAPI()
    
    async def analyze_crime_correlation(self, area: str) -> Optional[Dict]:
        """分析犯罪與其他因素的相關性"""
        try:
            async with self.api as api:
                # 獲取多種資料
                crime_data = await api.get_crime_statistics(area=area)
                population_data = await api.get_population_data(area=area)
                school_data = await api.get_school_data(city=area)
                hospital_data = await api.get_hospital_data(city=area)
                
                analysis_result = {
                    'area': area,
                    'analysis_date': datetime.now().isoformat(),
                    'data_sources': [],
                    'correlations': {},
                    'insights': []
                }
                
                if crime_data is not None:
                    analysis_result['data_sources'].append('犯罪統計')
                    analysis_result['crime_count'] = len(crime_data)
                
                if population_data is not None:
                    analysis_result['data_sources'].append('人口統計')
                    analysis_result['population_count'] = len(population_data)
                
                if school_data is not None:
                    analysis_result['data_sources'].append('學校資料')
                    analysis_result['school_count'] = len(school_data)
                
                if hospital_data is not None:
                    analysis_result['data_sources'].append('醫療機構')
                    analysis_result['hospital_count'] = len(hospital_data)
                
                # 簡單的相關性分析
                if crime_data is not None and population_data is not None:
                    analysis_result['insights'].append("已整合犯罪統計與人口資料進行分析")
                
                return analysis_result
                
        except Exception as e:
            logger.error(f"分析犯罪相關性時發生錯誤: {e}")
            return None
    
    async def get_area_overview(self, area: str) -> Optional[Dict]:
        """獲取地區總覽資訊"""
        try:
            async with self.api as api:
                overview = {
                    'area': area,
                    'generated_at': datetime.now().isoformat(),
                    'data': {}
                }
                
                # 並行獲取多種資料
                tasks = [
                    api.get_crime_statistics(area=area),
                    api.get_population_data(area=area),
                    api.get_police_stations(city=area),
                    api.get_school_data(city=area),
                    api.get_hospital_data(city=area)
                ]
                
                results = await asyncio.gather(*tasks, return_exceptions=True)
                
                data_types = ['crime', 'population', 'police', 'schools', 'hospitals']
                
                for i, result in enumerate(results):
                    if isinstance(result, pd.DataFrame) and not result.empty:
                        overview['data'][data_types[i]] = {
                            'count': len(result),
                            'columns': list(result.columns),
                            'sample': result.head(3).to_dict('records') if len(result) > 0 else []
                        }
                    elif isinstance(result, Exception):
                        logger.warning(f"獲取 {data_types[i]} 資料時發生錯誤: {result}")
                
                return overview
                
        except Exception as e:
            logger.error(f"獲取地區總覽時發生錯誤: {e}")
            return None
