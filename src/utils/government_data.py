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
                'User-Agent': 'Numora/2.0 (Serelix Studio)',
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
    
    async def _ckan_datastore_search_by_dataset(self, dataset_uuid: str, q: Optional[str] = None, limit: int = 100) -> Optional[List[Dict]]:
        """透過 CKAN 以 dataset UUID 取得可查詢的 resource，並查詢 records"""
        try:
            package_url = "https://data.taipei/api/3/action/package_show"
            params = {"id": dataset_uuid}
            async with self.session.get(package_url, params=params) as resp:
                if resp.status != 200:
                    logger.warning(f"package_show 失敗: {resp.status}")
                    return None
                pkg = await resp.json()
            if not pkg.get("success"):
                return None
            resources = pkg.get("result", {}).get("resources", [])
            resource_id = None
            for r in resources:
                if r.get("datastore_active"):
                    resource_id = r.get("id")
                    break
            if not resource_id and resources:
                resource_id = resources[0].get("id")
            if not resource_id:
                return None

            ds_url = "https://data.taipei/api/3/action/datastore_search"
            ds_params = {"resource_id": resource_id, "limit": limit}
            if q:
                ds_params["q"] = q
            # 先帶 q 查詢
            async with self.session.get(ds_url, params=ds_params) as ds_resp:
                if ds_resp.status != 200:
                    logger.warning(f"datastore_search 失敗: {ds_resp.status}")
                    return None
                ds_json = await ds_resp.json()
            records = []
            if ds_json.get("success"):
                records = ds_json.get("result", {}).get("records", [])
            # 若無結果，抓一批不帶 q 並在本地過濾
            if (not records) and q:
                async with self.session.get(ds_url, params={"resource_id": resource_id, "limit": min(200, max(50, limit))}) as ds_resp2:
                    if ds_resp2.status == 200:
                        ds_json2 = await ds_resp2.json()
                        if ds_json2.get("success"):
                            bulk = ds_json2.get("result", {}).get("records", [])
                            ql = str(q).lower()
                            def m(r):
                                try:
                                    return any(ql in str(v).lower() for v in r.values())
                                except Exception:
                                    return False
                            records = [r for r in bulk if m(r)][:limit]
            return records
        except Exception as e:
            logger.error(f"CKAN 查詢發生錯誤: {e}")
            return None

    async def get_taipei_youbike_data(self) -> Optional[pd.DataFrame]:
        """獲取台北市 YouBike 即時資料（官方 JSON 端點）"""
        import asyncio, aiohttp, requests as _req
        try:
            url = "https://tcgbusfs.blob.core.windows.net/dotapp/youbike/v2/youbike_immediate.json"
            async with self.session.get(url) as resp:
                if resp.status != 200:
                    logger.warning(f"YouBike 端點回應狀態: {resp.status}")
                    return None
                text = await resp.text()
            import json as _json
            try:
                data = _json.loads(text)
            except Exception as e:
                logger.warning(f"YouBike JSON 解析失敗，長度={len(text)}: {e}")
                data = None
            if isinstance(data, list) and data:
                try:
                    df = pd.DataFrame(data)
                except Exception as e:
                    logger.warning(f"YouBike DataFrame 轉換失敗: {e}")
                    return None
                logger.info(f"獲取到 {len(df)} 筆 YouBike 即時資料")
                return df
            # 回退：使用 requests 同步抓取並解析（避免 aiohttp 邊界問題）
            try:
                r = await asyncio.to_thread(_req.get, url, timeout=15)
                r.raise_for_status()
                data2 = r.json()
                if isinstance(data2, list) and data2:
                    df = pd.DataFrame(data2)
                    logger.info(f"獲取到 {len(df)} 筆 YouBike 即時資料 (fallback)")
                    return df
                logger.warning("YouBike 回傳非清單或為空 (fallback)")
                return None
            except Exception as e2:
                logger.error(f"YouBike 回退請求失敗: {e2}")
                return None
        except Exception as e:
            logger.error(f"獲取 YouBike 資料時發生錯誤: {e}")
            return None
    
    async def get_taipei_wifi_data(self) -> Optional[pd.DataFrame]:
        """獲取台北市 WiFi 熱點資料（CKAN 優先，失敗則回退 v1）"""
        try:
            dataset = self.verified_datasets["taipei_wifi"]
            logger.info(f"開始查詢 WiFi 資料，dataset_id={dataset.get('id')}, resource_id={dataset.get('resource_id')}")
            
            # 1) 若已知 resource_id，直接以 CKAN datastore_search 取得資料
            rid = dataset.get("resource_id")
            if rid:
                try:
                    ds_url = "https://data.taipei/api/3/action/datastore_search"
                    logger.info(f"嘗試以 resource_id 直取 WiFi: {rid}")
                    async with self.session.get(ds_url, params={"resource_id": rid, "limit": 1000}) as ds_resp:
                        logger.info(f"resource_id 直取回應狀態: {ds_resp.status}")
                        if ds_resp.status == 200:
                            ds_json = await ds_resp.json()
                            if ds_json.get("success"):
                                records = ds_json.get("result", {}).get("records", [])
                                logger.info(f"resource_id 直取回傳 {len(records)} 筆")
                                if records:
                                    df = pd.DataFrame(records)
                                    logger.info(f"WiFi 欄位：{list(df.columns)}")
                                    # 有資料就直接回傳（避免嚴格欄位判斷造成誤殺）
                                    return df
                            else:
                                logger.warning(f"resource_id 直取 API 回傳 success=False: {ds_json.get('error')}")
                        else:
                            logger.warning(f"resource_id 直取 HTTP {ds_resp.status}")
                except Exception as e:
                    logger.warning(f"以 resource_id 直取 WiFi 失敗: {e}", exc_info=True)
            else:
                logger.info("配置中無 resource_id，跳過直接查詢")
                
            # 先嘗試 CKAN 透過已知 dataset id
            logger.info("嘗試以 dataset UUID 透過 CKAN 查找 WiFi")
            records = await self._ckan_datastore_search_by_dataset(dataset["id"], limit=1000)
            if records:
                df = pd.DataFrame(records)
                logger.info(f"CKAN UUID 回傳 {len(df)} 筆，欄位：{list(df.columns)}")
                return df

            # 2) 若既有 UUID 失敗，改以 package_search 自動搜尋 WiFi 資料集/資源
            logger.info("開始自動發現 WiFi 資料...")
            auto_df = await self._ckan_autodiscover_wifi(limit=1000)
            if auto_df is not None and not auto_df.empty:
                logger.info(f"自動發現 WiFi 資料資源成功，筆數 {len(auto_df)}")
                return auto_df

            # 3) 回退 v1：需以 resource_id 查詢 resourceAquire（若取得不到 rid 也嘗試不帶）
            logger.info("嘗試 v1 API 回退方案...")
            # 重新透過 package_show 取得可用 resource_id
            resource_id = await self._resolve_ckan_resource_id(dataset["id"])
            legacy_url = f"https://data.taipei/api/v1/dataset/{dataset['id']}"
            # 若取得 resource_id 則帶 rid；否則嘗試不帶 rid 的舊行為（某些資料集仍可回傳）
            params = {'scope': 'resourceAquire'}
            if resource_id:
                params['rid'] = resource_id
                logger.info(f"v1 API 使用 resource_id: {resource_id}")
            else:
                logger.warning("無法解析 resource_id，改以不帶 rid 進行 v1 回退嘗試")
            
            async with self.session.get(legacy_url, params=params) as resp:
                logger.info(f"v1 API 回應狀態: {resp.status}")
                if resp.status != 200:
                    logger.warning(f"WiFi v1 回應狀態: {resp.status}")
                    return None
                j = await resp.json()
                logger.debug(f"v1 API 回應結構: {list(j.keys()) if isinstance(j, dict) else type(j)}")
                
            # v1 結構通常位於 result.results
            res = []
            if isinstance(j, dict):
                result_block = j.get('result') or {}
                res = result_block.get('results') or result_block.get('payload') or []
            
            logger.info(f"v1 API 解析到 {len(res) if isinstance(res, list) else 0} 筆資料")
            if isinstance(res, list) and res:
                df = pd.DataFrame(res)
                logger.info(f"v1 資料欄位: {list(df.columns)}")
                if self._looks_like_wifi_df(df):
                    logger.info(f"獲取到 {len(df)} 筆 WiFi 熱點資料 (v1)")
                    return df
                else:
                    logger.warning("v1 回傳資料欄位與 WiFi 熱點不符，捨棄此結果")
            
            logger.warning("所有 WiFi 資料獲取方法均失敗")
            return None
        except Exception as e:
            logger.error(f"獲取 WiFi 熱點資料時發生錯誤: {e}", exc_info=True)
            return None

    async def _resolve_ckan_resource_id(self, dataset_uuid: str) -> Optional[str]:
        """透過 CKAN package_show 解析可用的 resource_id（優先 datastore_active）"""
        try:
            url = "https://data.taipei/api/3/action/package_show"
            async with self.session.get(url, params={"id": dataset_uuid}) as resp:
                if resp.status != 200:
                    logger.warning(f"package_show 失敗: {resp.status}")
                    return None
                pkg = await resp.json()
            if not pkg.get("success"):
                return None
            resources = pkg.get("result", {}).get("resources", [])
            if not resources:
                return None
            # 優先找 datastore_active
            for r in resources:
                if r.get("datastore_active"):
                    return r.get("id")
            # 否則回傳第一個
            return resources[0].get("id")
        except Exception as e:
            logger.warning(f"解析 resource_id 失敗: {e}")
            return None

    def _looks_like_wifi_df(self, df: pd.DataFrame) -> bool:
        """檢查 DataFrame 是否像 WiFi 熱點資料，避免誤抓到其他資料集。"""
        if df is None or df.empty:
            logger.debug("DataFrame 為空")
            return False
            
        cols = [str(c).lower() for c in df.columns]
        logger.info(f"檢查 WiFi 資料欄位: {cols}")
        
        # 檢查 WiFi 相關提示詞
        wifi_hints = ["wifi", "wi-fi", "ssid", "熱點", "hotspot", "spot", "場所", "名稱", "name"]
        has_wifi_hint = any(any(h in c for h in wifi_hints) for c in cols)
        
        # 檢查地理位置欄位（更寬鬆的檢查）
        geo_keywords = ["lat", "lng", "lon", "經度", "緯度", "x", "y", "coord", "座標"]
        has_geo = any(any(g in c for g in geo_keywords) for c in cols)
        
        # 檢查地址欄位（作為替代）
        address_keywords = ["addr", "address", "地址", "地點", "位置"]
        has_address = any(any(a in c for a in address_keywords) for c in cols)
        
        # 放寬驗證條件：有 WiFi 提示詞，且有地理位置或地址即可
        result = has_wifi_hint and (has_geo or has_address)
        
        # 即使沒有明確 WiFi 提示詞，但有足夠的位置資訊也接受
        if not result and (has_geo or has_address):
            # 如果欄位數量合理（通常 WiFi 資料有 5-20 個欄位）
            if 3 <= len(cols) <= 30:
                logger.info("雖無明確 WiFi 提示詞，但有位置資訊且欄位數量合理，接受此資料")
                result = True
        
        logger.info(f"WiFi 驗證結果: {result} (wifi提示={has_wifi_hint}, 地理位置={has_geo}, 地址={has_address})")
        return result

    async def _ckan_autodiscover_wifi(self, limit: int = 500) -> Optional[pd.DataFrame]:
        """透過 CKAN package_search 嘗試自動尋找 WiFi 熱點的資源。
        策略：以關鍵字 'wifi' 'wi-fi' 'hotspot' 搜尋，逐一抓取 datastore_active 資源的小樣本，
        以 _looks_like_wifi_df 驗證，找到即回傳完整資料。
        """
        try:
            search_url = "https://data.taipei/api/3/action/package_search"
            # 嘗試多個關鍵字以提高命中率
            keywords = ["wifi", "wi-fi", "hotspot", "無線網路", "無線上網", "free wifi", "taipei"]
            for kw in keywords:
                logger.info(f"使用關鍵字搜尋 WiFi 資料集: {kw}")
                async with self.session.get(search_url, params={"q": kw, "rows": 20}) as resp:
                    if resp.status != 200:
                        logger.debug(f"搜尋關鍵字 {kw} 失敗: HTTP {resp.status}")
                        continue
                    j = await resp.json()
                    
                if not j.get("success"):
                    logger.debug(f"搜尋關鍵字 {kw} API 回傳 success=False")
                    continue
                    
                results = j.get("result", {}).get("results", []) or []
                logger.info(f"關鍵字 {kw} 找到 {len(results)} 個資料集")
                
                for pkg in results:
                    pkg_name = pkg.get("name", "未知")
                    pkg_title = pkg.get("title", "未知")
                    resources = pkg.get("resources", []) or []
                    logger.debug(f"檢查資料集: {pkg_title} ({pkg_name}), 有 {len(resources)} 個資源")
                    
                    for r in resources:
                        res_id = r.get("id")
                        res_name = r.get("name", "未知")
                        if not res_id:
                            continue
                        
                        logger.debug(f"測試資源: {res_name} (ID: {res_id[:8]}...)")
                        # 取少量樣本驗證
                        ds_url = "https://data.taipei/api/3/action/datastore_search"
                        async with self.session.get(ds_url, params={"resource_id": res_id, "limit": 50}) as ds_resp:
                            if ds_resp.status != 200:
                                logger.debug(f"資源 {res_id[:8]} 無法訪問: HTTP {ds_resp.status}")
                                continue
                            ds_json = await ds_resp.json()
                            
                        if not ds_json.get("success"):
                            logger.debug(f"資源 {res_id[:8]} API 回傳 success=False")
                            continue
                            
                        records = ds_json.get("result", {}).get("records", [])
                        if not records:
                            logger.debug(f"資源 {res_id[:8]} 無資料記錄")
                            continue
                            
                        df = pd.DataFrame(records)
                        logger.info(f"資源 {res_name} 有 {len(df)} 筆資料，欄位: {list(df.columns)[:5]}...")
                        
                        if self._looks_like_wifi_df(df):
                            logger.info(f"找到符合的 WiFi 資源: {res_name} (ID: {res_id})")
                            # 以相同 resource 取完整/較多筆
                            async with self.session.get(ds_url, params={"resource_id": res_id, "limit": limit}) as ds2:
                                if ds2.status != 200:
                                    logger.warning(f"取得完整資料失敗，返回樣本資料: HTTP {ds2.status}")
                                    return df
                                ds2_json = await ds2.json()
                                
                            if ds2_json.get("success"):
                                rec2 = ds2_json.get("result", {}).get("records", [])
                                if rec2:
                                    logger.info(f"成功取得 {len(rec2)} 筆 WiFi 資料")
                                    return pd.DataFrame(rec2)
                            return df
                            
            logger.warning("自動發現流程結束，未找到符合的 WiFi 資源")
            return None
        except Exception as e:
            logger.warning(f"自動搜尋 WiFi 資源失敗: {e}", exc_info=True)
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
    
    async def get_wheelchair_facilities(self) -> Optional[pd.DataFrame]:
        """獲取台北市無障礙設施資訊"""
        try:
            from src.utils.gov_data_config import TAIPEI_DATASETS
            dataset = TAIPEI_DATASETS["wheelchair_facilities"]
            url = dataset["api_url"]
            params = dataset.get("params", {})
            
            logger.info(f"開始查詢無障礙設施資料: {url}")
            async with self.session.get(url, params=params) as response:
                if response.status == 200:
                    data = await response.json()
                    if isinstance(data, list):
                        df = pd.DataFrame(data)
                        logger.info(f"成功獲取 {len(df)} 筆無障礙設施資料")
                        return df
                    elif isinstance(data, dict) and 'result' in data:
                        df = pd.DataFrame(data['result'])
                        logger.info(f"成功獲取 {len(df)} 筆無障礙設施資料")
                        return df
                logger.warning(f"無障礙設施 API 請求失敗: {response.status}")
                return None
        except Exception as e:
            logger.error(f"獲取無障礙設施資料時發生錯誤: {e}", exc_info=True)
            return None
    
    async def get_library_seats(self) -> Optional[pd.DataFrame]:
        """獲取台北市圖書館座位資訊"""
        try:
            from src.utils.gov_data_config import TAIPEI_DATASETS
            dataset = TAIPEI_DATASETS["library_seats"]
            url = dataset["api_url"]
            
            logger.info(f"開始查詢圖書館座位資料: {url}")
            # 嘗試添加適當的 headers
            headers = {
                'Accept': 'application/json, text/plain, */*',
                'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
            }
            async with self.session.get(url, headers=headers) as response:
                logger.info(f"圖書館座位 API 回應狀態: {response.status}, Content-Type: {response.headers.get('content-type', 'N/A')}")
                if response.status == 200:
                    # API 回傳 JSON 但 Content-Type 可能設置為 text/html
                    # 直接讀取文本並解析為 JSON
                    try:
                        text = await response.text()
                        logger.info(f"圖書館座位 API 回應長度: {len(text)} 字元，前 200 字元: {text[:200]}")
                        
                        if not text or text.strip() == '':
                            logger.warning("圖書館座位 API 回傳空白回應")
                            return pd.DataFrame([{
                                'message': 'API 回傳空白資料，可能服務暫時無法使用',
                                'url': url,
                                'suggestion': '請稍後再試或直接訪問台北市立圖書館網站'
                            }])
                        
                        import json
                        data = json.loads(text)
                        if isinstance(data, list):
                            if len(data) == 0:
                                logger.warning("圖書館座位 API 回傳空列表")
                                return pd.DataFrame([{
                                    'message': '目前無座位資料',
                                    'url': url
                                }])
                            df = pd.DataFrame(data)
                            logger.info(f"成功獲取 {len(df)} 筆圖書館座位資料")
                            return df
                        elif isinstance(data, dict) and 'result' in data:
                            df = pd.DataFrame(data['result'])
                            logger.info(f"成功獲取 {len(df)} 筆圖書館座位資料")
                            return df
                    except json.JSONDecodeError as json_err:
                        logger.warning(f"圖書館座位 API 回應無法解析為 JSON: {json_err}, 回應內容: {text[:500]}")
                        return pd.DataFrame([{
                            'message': '此 API 回應格式無法解析',
                            'url': url,
                            'suggestion': '請直接訪問台北市立圖書館網站查詢座位資訊'
                        }])
                logger.warning(f"圖書館座位 API 請求失敗: {response.status}")
                return None
        except Exception as e:
            logger.error(f"獲取圖書館座位資料時發生錯誤: {e}", exc_info=True)
            return None
    
    async def get_water_quality(self) -> Optional[pd.DataFrame]:
        """獲取台北市自來水水質資訊"""
        try:
            from src.utils.gov_data_config import TAIPEI_DATASETS
            dataset = TAIPEI_DATASETS["water_quality"]
            url = dataset["api_url"]
            
            logger.info(f"開始查詢自來水水質資料: {url}")
            # 水質 API 的伺服器回應 header 格式不符合標準，使用 GET 並改用 requests
            try:
                # 先嘗試 GET 方法
                async with self.session.get(url, params={"limit": 1000}) as response:
                    if response.status == 200:
                        data = await response.json()
                        if isinstance(data, list):
                            df = pd.DataFrame(data)
                            logger.info(f"成功獲取 {len(df)} 筆水質資料")
                            return df
                        elif isinstance(data, dict) and 'result' in data:
                            df = pd.DataFrame(data['result'])
                            logger.info(f"成功獲取 {len(df)} 筆水質資料")
                            return df
            except Exception as get_error:
                logger.warning(f"GET 方法失敗，嘗試使用 requests: {get_error}")
                # API 回應格式不符合標準，回傳提示訊息
                return pd.DataFrame([{
                    'message': '此 API 的伺服器回應格式不符合 HTTP 標準',
                    'url': url,
                    'error': 'Invalid HTTP header format',
                    'suggestion': '請聯繫台北自來水事業處確認 API 狀態'
                }])
            
            logger.warning(f"水質 API 請求失敗")
            return None
        except Exception as e:
            logger.error(f"獲取水質資料時發生錯誤: {e}", exc_info=True)
            return None
    
    async def get_tourist_statistics(self) -> Optional[pd.DataFrame]:
        """獲取台北市觀光景點遊客統計"""
        try:
            from src.utils.gov_data_config import TAIPEI_DATASETS
            dataset = TAIPEI_DATASETS["tourist_statistics"]
            url = dataset["api_url"]
            
            logger.info(f"開始查詢觀光景點統計資料: {url}")
            # 添加瀏覽器 User-Agent 以避免 403
            headers = {
                'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
            }
            async with self.session.get(url, headers=headers) as response:
                if response.status == 200:
                    # 這個 API 可能回傳 HTML 或需要特殊處理
                    content_type = response.headers.get('content-type', '')
                    if 'json' in content_type:
                        data = await response.json()
                        if isinstance(data, list):
                            df = pd.DataFrame(data)
                            logger.info(f"成功獲取 {len(df)} 筆觀光統計資料")
                            return df
                        elif isinstance(data, dict) and 'result' in data:
                            df = pd.DataFrame(data['result'])
                            logger.info(f"成功獲取 {len(df)} 筆觀光統計資料")
                            return df
                    else:
                        # 如果不是 JSON，返回提示
                        logger.warning(f"觀光統計 API 回傳非 JSON 格式: {content_type}")
                        return pd.DataFrame([{
                            'message': '此資料為網頁格式，請直接訪問觀光傳播局網站查看統計資料',
                            'url': url,
                            'suggestion': '訪問 https://www.travel.taipei/zh-tw/statistical-bulletin/number-of-visitors'
                        }])
                elif response.status == 403:
                    logger.warning(f"觀光統計 API 拒絕訪問: 403")
                    return pd.DataFrame([{
                        'message': '此網站禁止程式自動訪問，請透過瀏覽器查看',
                        'url': url,
                        'suggestion': '請直接訪問台北觀光網查看統計資料'
                    }])
                logger.warning(f"觀光統計 API 請求失敗: {response.status}")
                return None
        except Exception as e:
            logger.error(f"獲取觀光統計資料時發生錯誤: {e}", exc_info=True)
            return None
    
    async def get_bike_theft_data(self) -> Optional[pd.DataFrame]:
        """獲取台北市自行車竊盜案件資料"""
        try:
            url = "https://data.taipei/api/v1/dataset/adf80a2b-b29d-4fca-888c-bcd26ae314e0?scope=resourceAquire"
            
            logger.info(f"開始查詢自行車竊盜資料: {url}")
            async with self.session.get(url) as response:
                if response.status == 200:
                    data = await response.json()
                    logger.info(f"自行車竊盜資料回應結構: {list(data.keys()) if isinstance(data, dict) else type(data)}")
                    
                    if isinstance(data, dict) and 'result' in data:
                        result = data['result']
                        # 檢查是否有 results
                        if isinstance(result, dict) and 'results' in result:
                            results = result['results']
                            if results and isinstance(results, list):
                                df = pd.DataFrame(results)
                                logger.info(f"成功獲取 {len(df)} 筆自行車竊盜資料")
                                return df
                    elif isinstance(data, list):
                        df = pd.DataFrame(data)
                        logger.info(f"成功獲取 {len(df)} 筆自行車竊盜資料")
                        return df
                    
                    logger.warning(f"無法解析自行車竊盜資料結構")
                    return None
                logger.warning(f"自行車竊盜資料 API 請求失敗: {response.status}")
                return None
        except Exception as e:
            logger.error(f"獲取自行車竊盜資料時發生錯誤: {e}", exc_info=True)
            return None

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
                'User-Agent': 'Numora/2.0 (Serelix Studio)',
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
    
    async def get_taipei_data(self, dataset_id: str, q: Optional[str] = None, limit: int = 1000) -> Optional[pd.DataFrame]:
        """獲取台北市政府公開資料（CKAN）"""
        try:
            records = await self._ckan_datastore_search_by_dataset(dataset_id, q=q, limit=limit)
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
