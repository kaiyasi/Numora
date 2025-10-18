"""
Web 介面模組
提供基於 Flask 的 Web 儀表板
"""

from flask import Flask, render_template, request, jsonify, send_file
import pandas as pd
import json
import os
import logging
from typing import Dict, Any, Optional
import threading
import plotly.graph_objects as go
import plotly.express as px
from plotly.utils import PlotlyJSONEncoder

from src.data.processor import DataProcessor
from src.data.area_analyzer import AreaAnalyzer
from src.utils.ml_predictor import CrimePredictionModel
from src.utils.config import config

logger = logging.getLogger(__name__)

class WebInterface:
    """Web 介面類"""
    
    def __init__(self, data_processor: DataProcessor):
        # 獲取專案根目錄
        self.root_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), '../..'))
        template_dir = os.path.join(self.root_dir, 'templates')
        static_dir = os.path.join(self.root_dir, 'static')

        self.app = Flask(__name__, template_folder=template_dir, static_folder=static_dir)
        self.data_processor = data_processor
        self.area_analyzer = AreaAnalyzer()
        self.ml_model = CrimePredictionModel()
        self.setup_routes()
        self.server_thread = None
        # 動態資料來源設定（CKAN 優先，其次 CSV）
        self.ckan_base = os.environ.get('CKAN_BASE', 'https://data.taipei/api/3/action')
        self.ckan_dataset_id = os.environ.get('TAIPEI_DATASET_ID')
        self.ckan_query = os.environ.get('CKAN_QUERY')
        try:
            self.ckan_limit = int(os.environ.get('CKAN_LIMIT', '200') or '200')
        except Exception:
            self.ckan_limit = 200
        self.dynamic_data_url = os.environ.get('DYNAMIC_DATA_URL')
        self.data_refresh_minutes = int(os.environ.get('DATA_REFRESH_MINUTES', '0') or '0')

        # 創建模板和靜態檔案目錄
        os.makedirs(template_dir, exist_ok=True)
        os.makedirs(os.path.join(static_dir, 'css'), exist_ok=True)
        os.makedirs(os.path.join(static_dir, 'js'), exist_ok=True)

        # 創建基本的 HTML 模板
        self.create_templates()

        # 啟動動態資料來源：CKAN > CSV
        started = False
        if self.ckan_dataset_id:
            logger.info(f"啟用 CKAN 動態來源: {self.ckan_base} dataset={self.ckan_dataset_id}")
            try:
                self.refresh_data_from_ckan()
                started = True
            except Exception as e:
                logger.warning(f"啟動時載入 CKAN 資料失敗: {e}")
        if (not started) and self.dynamic_data_url:
            logger.info(f"啟用 CSV 動態來源: {self.dynamic_data_url}")
            try:
                self.refresh_data_from_url()
                started = True
            except Exception as e:
                logger.warning(f"啟動時載入 CSV 動態資料失敗: {e}")
        if self.data_refresh_minutes > 0 and (self.ckan_dataset_id or self.dynamic_data_url):
            self.start_periodic_refresh()
    
    def setup_routes(self):
        """設定路由"""
        
        @self.app.route('/')
        def index():
            """首頁"""
            return render_template('index.html')
        
        @self.app.route('/dashboard')
        def dashboard():
            """儀表板"""
            try:
                df = self.get_current_data()
                if df is None or df.empty:
                    return render_template('dashboard.html', error="沒有可用的資料")
                
                # 基本統計
                stats = self.data_processor.generate_statistics(df)
                
                # 生成圖表
                charts = self.generate_charts(df)
                
                return render_template('dashboard.html', stats=stats, charts=charts)
                
            except Exception as e:
                logger.error(f"載入儀表板時發生錯誤: {e}")
                return render_template('dashboard.html', error=str(e))
        
        @self.app.route('/api/data')
        def api_data():
            """API - 取得資料"""
            try:
                df = self.get_current_data()
                if df is None or df.empty:
                    return jsonify({'error': '沒有可用的資料'})
                
                stats = self.data_processor.generate_statistics(df)
                return jsonify(stats)
                
            except Exception as e:
                logger.error(f"API 取得資料時發生錯誤: {e}")
                return jsonify({'error': str(e)})

        @self.app.route('/health')
        def health():
            try:
                df = self.get_current_data()
                return jsonify({
                    'status': 'ok',
                    'has_data': bool(df is not None and not df.empty)
                })
            except Exception as e:
                return jsonify({'status': 'error', 'message': str(e)}), 500

        @self.app.route('/api/refresh', methods=['POST'])
        def api_refresh():
            """手動觸發資料刷新（優先 CKAN，其次 CSV）"""
            try:
                mode = (request.args.get('mode') or '').lower()
                if (self.ckan_dataset_id and mode != 'csv') or (not self.dynamic_data_url):
                    count = self.refresh_data_from_ckan()
                else:
                    if not self.dynamic_data_url:
                        return jsonify({'error': '未設定 DYNAMIC_DATA_URL'}), 400
                    count = self.refresh_data_from_url()
                return jsonify({'status': 'ok', 'rows': count})
            except Exception as e:
                logger.error(f"手動刷新資料失敗: {e}")
                return jsonify({'error': str(e)}), 500
        
        @self.app.route('/api/charts/<chart_type>')
        def api_charts(chart_type):
            """API - 取得圖表資料"""
            try:
                df = self.get_current_data()
                if df is None or df.empty:
                    return jsonify({'error': '沒有可用的資料'})
                
                area = request.args.get('area', '全部地區')
                year = request.args.get('year', type=int)
                
                if chart_type == 'yearly_trend':
                    chart_data = self.create_yearly_trend_chart(df, area)
                elif chart_type == 'area_distribution':
                    chart_data = self.create_area_distribution_chart(df, year)
                elif chart_type == 'case_type_pie':
                    chart_data = self.create_case_type_pie_chart(df, area, year)
                elif chart_type == 'time_heatmap':
                    chart_data = self.create_time_heatmap(df, area)
                else:
                    return jsonify({'error': '未知的圖表類型'})
                
                return jsonify(chart_data)
                
            except Exception as e:
                logger.error(f"API 取得圖表時發生錯誤: {e}")
                return jsonify({'error': str(e)})
        
        @self.app.route('/api/prediction')
        def api_prediction():
            """API - 犯罪預測"""
            try:
                df = self.get_current_data()
                if df is None or df.empty:
                    return jsonify({'error': '沒有可用的資料'})
                
                area = request.args.get('area', '台北市')
                years = request.args.getlist('years', type=int)
                
                if not years:
                    years = [2024, 2025, 2026]
                
                # 訓練模型（如果尚未訓練）
                if not self.ml_model.is_trained:
                    self.ml_model.train_models(df)
                
                # 預測
                predictions = self.ml_model.predict_crime_trends(area, years)
                
                return jsonify({
                    'area': area,
                    'predictions': predictions,
                    'feature_importance': self.ml_model.get_feature_importance()
                })
                
            except Exception as e:
                logger.error(f"API 預測時發生錯誤: {e}")
                return jsonify({'error': str(e)})
        
        @self.app.route('/api/areas')
        def api_areas():
            """API - 取得可用地區"""
            try:
                df = self.get_current_data()
                if df is None or df.empty:
                    return jsonify({'error': '沒有可用的資料'})
                areas_info = self.area_analyzer.extract_area_info(df)
                return jsonify(areas_info)
            except Exception as e:
                logger.error(f"API 取得地區時發生錯誤: {e}")
                return jsonify({'error': str(e)})
        
        @self.app.route('/analysis')
        def analysis():
            """分析頁面"""
            return render_template('analysis.html')
        
        @self.app.route('/prediction')
        def prediction():
            """預測頁面"""
            return render_template('prediction.html')

        @self.app.route('/youbike')
        def youbike_page():
            """YouBike 即時資訊頁面（城市/地區選擇 + 分頁）"""
            return render_template('youbike.html')
        
        @self.app.route('/library')
        def library_page():
            """圖書館座位資訊頁面"""
            return render_template('library.html')
        
        @self.app.route('/bike_theft')
        def bike_theft_page():
            """自行車竊盜統計頁面"""
            return render_template('bike_theft.html')

        @self.app.route('/api/library/seats')
        def api_library_seats():
            """圖書館座位 API"""
            try:
                import asyncio
                from src.utils.government_data import GovernmentDataAPI
                
                async def fetch_data():
                    async with GovernmentDataAPI() as api:
                        return await api.get_library_seats()
                
                df = asyncio.run(fetch_data())
                
                if df is None or df.empty:
                    return jsonify({'seats': [], 'total': 0})
                
                # 分頁
                page = int(request.args.get('page', 1))
                size = int(request.args.get('size', 10))
                branch = request.args.get('branch', '')
                
                # 過濾分館
                if branch and branch != '__all__':
                    df = df[df['branchName'] == branch]
                
                total = len(df)
                start = (page - 1) * size
                end = start + size
                df_page = df.iloc[start:end]
                
                seats = []
                for _, row in df_page.iterrows():
                    seats.append({
                        'branch': row.get('branchName', ''),
                        'floor': row.get('floorName', ''),
                        'area': row.get('areaName', ''),
                        'free': int(row.get('freeCount', 0)),
                        'total': int(row.get('totalCount', 0))
                    })
                
                return jsonify({'seats': seats, 'total': total, 'page': page})
            except Exception as e:
                logger.error(f"圖書館座位 API 錯誤: {e}")
                return jsonify({'seats': [], 'total': 0, 'error': str(e)})
        
        @self.app.route('/api/library/branches')
        def api_library_branches():
            """取得圖書館分館列表"""
            try:
                import asyncio
                from src.utils.government_data import GovernmentDataAPI
                
                async def fetch_data():
                    async with GovernmentDataAPI() as api:
                        return await api.get_library_seats()
                
                df = asyncio.run(fetch_data())
                
                if df is None or df.empty:
                    return jsonify({'branches': []})
                
                branches = sorted(df['branchName'].unique().tolist())
                return jsonify({'branches': branches})
            except Exception as e:
                logger.error(f"取得分館列表失敗: {e}")
                return jsonify({'branches': []})
        
        @self.app.route('/api/bike_theft/data')
        def api_bike_theft():
            """自行車竊盜資料 API"""
            try:
                import asyncio
                from src.utils.government_data import GovernmentDataAPI
                
                async def fetch_data():
                    async with GovernmentDataAPI() as api:
                        return await api.get_bike_theft_data()
                
                df = asyncio.run(fetch_data())
                
                if df is None or df.empty:
                    return jsonify({'cases': [], 'total': 0})
                
                # 分頁
                page = int(request.args.get('page', 1))
                size = int(request.args.get('size', 10))
                
                total = len(df)
                start = (page - 1) * size
                end = start + size
                df_page = df.iloc[start:end]
                
                cases = []
                for _, row in df_page.iterrows():
                    # 轉換民國年為西元年
                    date_str = str(row.get('發生日期', ''))
                    if len(date_str) == 7:
                        try:
                            year = int(date_str[:3]) + 1911
                            month = date_str[3:5]
                            day = date_str[5:7]
                            formatted_date = f"{year}/{month}/{day}"
                        except:
                            formatted_date = date_str
                    else:
                        formatted_date = date_str
                    
                    cases.append({
                        'case_type': row.get('案類', ''),
                        'date': formatted_date,
                        'time': row.get('發生時段', ''),
                        'location': row.get('發生地點', '')
                    })
                
                return jsonify({'cases': cases, 'total': total, 'page': page})
            except Exception as e:
                logger.error(f"自行車竊盜 API 錯誤: {e}")
                return jsonify({'cases': [], 'total': 0, 'error': str(e)})
        
        @self.app.route('/api/youbike/areas')
        def api_youbike_areas():
            try:
                city = (request.args.get('city') or 'taipei').lower()
                df = self._youbike_fetch_df(city)
                if df is None or df.empty:
                    return jsonify({'areas': []})
                area_col = 'sarea' if 'sarea' in df.columns else ('area' if 'area' in df.columns else None)
                areas = []
                if area_col:
                    areas = sorted([str(a) for a in set(df[area_col].dropna().astype(str)) if str(a).strip()])
                return jsonify({'areas': areas})
            except Exception as e:
                logger.error(f"YouBike 取地區失敗: {e}")
                return jsonify({'areas': []})

        @self.app.route('/api/youbike/stations')
        def api_youbike_stations():
            try:
                city = (request.args.get('city') or 'taipei').lower()
                area = request.args.get('area') or '__all__'
                page = max(1, request.args.get('page', type=int, default=1))
                size = min(50, max(1, request.args.get('size', type=int, default=10)))

                df = self._youbike_fetch_df(city)
                if df is None or df.empty:
                    return jsonify({'total': 0, 'page': page, 'size': size, 'stations': []})

                area_col = 'sarea' if 'sarea' in df.columns else ('area' if 'area' in df.columns else None)
                if area != '__all__' and area_col:
                    df = df[df[area_col].astype(str) == str(area)]
                total = len(df)
                start = (page - 1) * size
                end = min(start + size, total)
                page_df = df.iloc[start:end]

                def to_int(v):
                    try:
                        if v is None:
                            return 0
                        return int(float(str(v)))
                    except Exception:
                        return 0

                def nz(v):
                    return '' if v is None else str(v)

                items = []
                for rec in page_df.to_dict(orient='records'):
                    name = rec.get('sna') or rec.get('stationName') or rec.get('name')
                    sarea = rec.get('sarea') or rec.get('area')
                    bikes = rec.get('available_rent_bikes') or rec.get('sbi') or rec.get('AvailableBikeCount') or rec.get('available')
                    docks = rec.get('available_return_bikes') or rec.get('bemp') or rec.get('AvailableSpaceCount') or rec.get('empty')
                    addr = rec.get('ar') or rec.get('Address') or rec.get('address')
                    items.append({
                        'name': nz(name),
                        'area': nz(sarea),
                        'available_bikes': to_int(bikes),
                        'available_docks': to_int(docks),
                        'address': nz(addr),
                    })

                return jsonify({'total': total, 'page': page, 'size': size, 'stations': items})
            except Exception as e:
                logger.error(f"YouBike 取站點失敗: {e}")
                return jsonify({'total': 0, 'page': 1, 'size': 10, 'stations': []})

    def _youbike_fetch_df(self, city: str) -> Optional[pd.DataFrame]:
        """抓取 YouBike 即時資料（city: taipei|new_taipei）"""
        import requests
        try:
            if city == 'new_taipei':
                url = "https://data.ntpc.gov.tw/api/datasets/010e5b15-3823-4b20-b401-b1cf000550c5/json/?size=10000"
                r = requests.get(url, timeout=20)
                r.raise_for_status()
                data = r.json()
                if isinstance(data, dict) and 'data' in data:
                    data = data['data']
            else:
                url = "https://tcgbusfs.blob.core.windows.net/dotapp/youbike/v2/youbike_immediate.json"
                r = requests.get(url, timeout=15)
                r.raise_for_status()
                data = r.json()
            if isinstance(data, list) and data:
                return pd.DataFrame(data)
            return None
        except Exception as e:
            logger.warning(f"YouBike 抓取失敗: {e}")
            return None
    
    def get_current_data(self) -> Optional[pd.DataFrame]:
        """取得當前資料"""
        current_df = self.data_processor.get_current_data()
        if current_df is not None:
            return current_df
        
        return None

    def refresh_data_from_url(self) -> int:
        """從動態 URL 載入 CSV 並設為當前資料"""
        import requests
        if not self.dynamic_data_url:
            raise ValueError('未設定 DYNAMIC_DATA_URL')
        resp = requests.get(self.dynamic_data_url, timeout=30)
        resp.raise_for_status()
        content = resp.content
        df = self.data_processor.load_csv_data(content)
        if df is None or df.empty:
            raise ValueError('遠端資料為空或無法解析')
        self.data_processor.set_current_data(df)
        logger.info(f"已載入動態資料：{len(df)} 筆")
        return len(df)

    def start_periodic_refresh(self):
        """啟動週期刷新背景工作"""
        interval = max(1, self.data_refresh_minutes) * 60
        def _job():
            try:
                if self.ckan_dataset_id:
                    self.refresh_data_from_ckan()
                elif self.dynamic_data_url:
                    self.refresh_data_from_url()
            except Exception as e:
                logger.warning(f"週期刷新失敗: {e}")
            finally:
                # 重新排程
                self._refresh_timer = threading.Timer(interval, _job)
                self._refresh_timer.daemon = True
                self._refresh_timer.start()
        self._refresh_timer = threading.Timer(interval, _job)
        self._refresh_timer.daemon = True
        self._refresh_timer.start()

    def refresh_data_from_ckan(self) -> int:
        """從 CKAN 以 dataset UUID 取得 records 並設為當前資料"""
        import requests
        if not self.ckan_dataset_id:
            raise ValueError('未設定 TAIPEI_DATASET_ID')
        base = self.ckan_base.rstrip('/')
        # 1) 取 resource_id
        pkg_url = f"{base}/package_show"
        r = requests.get(pkg_url, params={'id': self.ckan_dataset_id}, timeout=20)
        r.raise_for_status()
        j = r.json()
        if not j.get('success'):
            raise ValueError('package_show 失敗')
        resources = j.get('result', {}).get('resources', [])
        resource_id = None
        for res in resources:
            if res.get('datastore_active'):
                resource_id = res.get('id')
                break
        if not resource_id and resources:
            resource_id = resources[0].get('id')
        if not resource_id:
            raise ValueError('找不到可查詢的 resource_id')
        # 2) 查 records
        ds_url = f"{base}/datastore_search"
        params = {'resource_id': resource_id, 'limit': self.ckan_limit}
        if self.ckan_query:
            params['q'] = self.ckan_query
        r2 = requests.get(ds_url, params=params, timeout=30)
        r2.raise_for_status()
        j2 = r2.json()
        if not j2.get('success'):
            raise ValueError('datastore_search 失敗')
        records = j2.get('result', {}).get('records', [])
        if not records:
            raise ValueError('CKAN 無資料')
        # 3) 轉為 DataFrame 並嘗試映射欄位
        df = pd.DataFrame(records)
        # 嘗試沿用資料處理器的欄位映射與日期處理
        df = self.data_processor._map_columns(df)
        df = self.data_processor._process_dates(df)
        self.data_processor.set_current_data(df)
        logger.info(f"已載入 CKAN 資料：{len(df)} 筆")
        return len(df)
    
    def generate_charts(self, df: pd.DataFrame) -> Dict[str, str]:
        """生成圖表"""
        charts = {}
        
        try:
            # 年度趨勢圖
            charts['yearly_trend'] = self.create_yearly_trend_chart(df)
            
            # 地區分布圖
            charts['area_distribution'] = self.create_area_distribution_chart(df)
            
            # 案件類型圓餅圖
            charts['case_type_pie'] = self.create_case_type_pie_chart(df)
            
        except Exception as e:
            logger.error(f"生成圖表時發生錯誤: {e}")
        
        return charts
    
    def create_yearly_trend_chart(self, df: pd.DataFrame, area: str = '全部地區') -> str:
        """創建年度趨勢圖"""
        try:
            if area != '全部地區':
                filtered_df = df[df['地點'].str.contains(area, na=False)]
            else:
                filtered_df = df
            
            yearly_counts = filtered_df['年份'].value_counts().sort_index()
            
            fig = go.Figure()
            fig.add_trace(go.Scatter(
                x=yearly_counts.index,
                y=yearly_counts.values,
                mode='lines+markers',
                name='案件數',
                line=dict(color='#1f77b4', width=3),
                marker=dict(size=8)
            ))
            
            fig.update_layout(
                title=f'{area} - 年度案件趨勢',
                xaxis_title='年份',
                yaxis_title='案件數',
                template='plotly_white',
                height=400
            )
            
            return json.dumps(fig, cls=PlotlyJSONEncoder)
            
        except Exception as e:
            logger.error(f"創建年度趨勢圖時發生錯誤: {e}")
            return '{}'
    
    def create_area_distribution_chart(self, df: pd.DataFrame, year: int = None) -> str:
        """創建地區分布圖"""
        try:
            if year:
                filtered_df = df[df['年份'] == year]
            else:
                filtered_df = df
            
            # 提取市級地區
            areas = filtered_df['地點'].str.extract(r'(.+?市)', expand=False).value_counts().head(10)
            
            fig = go.Figure()
            fig.add_trace(go.Bar(
                x=areas.values,
                y=areas.index,
                orientation='h',
                marker=dict(color='#ff7f0e')
            ))
            
            title = f'{year} 年地區案件分布' if year else '地區案件分布'
            fig.update_layout(
                title=title,
                xaxis_title='案件數',
                yaxis_title='地區',
                template='plotly_white',
                height=500
            )
            
            return json.dumps(fig, cls=PlotlyJSONEncoder)
            
        except Exception as e:
            logger.error(f"創建地區分布圖時發生錯誤: {e}")
            return '{}'
    
    def create_case_type_pie_chart(self, df: pd.DataFrame, area: str = '全部地區', year: int = None) -> str:
        """創建案件類型圓餅圖"""
        try:
            filtered_df = df
            
            if area != '全部地區':
                filtered_df = filtered_df[filtered_df['地點'].str.contains(area, na=False)]
            
            if year:
                filtered_df = filtered_df[filtered_df['年份'] == year]
            
            case_counts = filtered_df['案類'].value_counts().head(8)
            
            fig = go.Figure()
            fig.add_trace(go.Pie(
                labels=case_counts.index,
                values=case_counts.values,
                hole=0.3
            ))
            
            title = f'{area} - 案件類型分布'
            if year:
                title += f' ({year} 年)'
            
            fig.update_layout(
                title=title,
                template='plotly_white',
                height=400
            )
            
            return json.dumps(fig, cls=PlotlyJSONEncoder)
            
        except Exception as e:
            logger.error(f"創建案件類型圓餅圖時發生錯誤: {e}")
            return '{}'
    
    def create_time_heatmap(self, df: pd.DataFrame, area: str = '全部地區') -> str:
        """創建時段熱力圖"""
        try:
            if area != '全部地區':
                filtered_df = df[df['地點'].str.contains(area, na=False)]
            else:
                filtered_df = df
            
            # 創建年份-時段的交叉表
            heatmap_data = pd.crosstab(filtered_df['年份'], filtered_df['時段'])
            
            fig = go.Figure()
            fig.add_trace(go.Heatmap(
                z=heatmap_data.values,
                x=heatmap_data.columns,
                y=heatmap_data.index,
                colorscale='Blues'
            ))
            
            fig.update_layout(
                title=f'{area} - 時段案件熱力圖',
                xaxis_title='時段',
                yaxis_title='年份',
                template='plotly_white',
                height=400
            )
            
            return json.dumps(fig, cls=PlotlyJSONEncoder)
            
        except Exception as e:
            logger.error(f"創建時段熱力圖時發生錯誤: {e}")
            return '{}'
    
    def create_templates(self):
        """創建 HTML 模板"""
        template_dir = os.path.join(self.root_dir, 'templates')

        # 基礎模板
        base_template = '''<!DOCTYPE html>
<html lang="zh-TW">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>{% block title %}Numora - 智能犯罪案件統計分析平台{% endblock %}</title>

    <!-- CSS Libraries -->
    <link href="https://cdn.jsdelivr.net/npm/bootstrap@5.3.0/dist/css/bootstrap.min.css" rel="stylesheet">
    <link href="https://cdnjs.cloudflare.com/ajax/libs/font-awesome/6.4.0/css/all.min.css" rel="stylesheet">
    <link href="{{ url_for('static', filename='css/style.css') }}" rel="stylesheet">

    <!-- Plotly -->
    <script src="https://cdn.plot.ly/plotly-2.26.0.min.js"></script>

    {% block extra_css %}{% endblock %}
</head>
<body style="opacity: 0; transition: opacity 0.3s;">
    <!-- 動畫背景 -->
    <div class="animated-bg">
        <div class="gradient-orb orb-1"></div>
        <div class="gradient-orb orb-2"></div>
        <div class="gradient-orb orb-3"></div>
    </div>

    <!-- 導航列 -->
    <nav class="navbar navbar-expand-lg">
        <div class="container">
            <a class="navbar-brand" href="/">
                <i class="fas fa-shield-alt"></i> Numora
            </a>

            <button class="navbar-toggler" type="button" data-bs-toggle="collapse" data-bs-target="#navbarNav">
                <span class="navbar-toggler-icon"></span>
            </button>

            <div class="collapse navbar-collapse" id="navbarNav">
                <ul class="navbar-nav ms-auto">
                    <li class="nav-item">
                        <a class="nav-link" href="/"><i class="fas fa-home"></i> 首頁</a>
                    </li>
                    <li class="nav-item">
                        <a class="nav-link" href="/dashboard"><i class="fas fa-chart-line"></i> 儀表板</a>
                    </li>
                    <li class="nav-item">
                        <a class="nav-link" href="/analysis"><i class="fas fa-map-marked-alt"></i> 分析</a>
                    </li>
                    <li class="nav-item">
                        <a class="nav-link" href="/prediction"><i class="fas fa-crystal-ball"></i> 預測</a>
                    </li>
                    <li class="nav-item">
                        <button class="theme-toggle" id="themeToggle" title="切換主題">
                            <i class="fas fa-moon"></i>
                        </button>
                    </li>
                </ul>
            </div>
        </div>
    </nav>

    <!-- 主要內容 -->
    <div class="container">
        {% block content %}{% endblock %}
    </div>

    <!-- JavaScript Libraries -->
    <script src="https://cdn.jsdelivr.net/npm/bootstrap@5.3.0/dist/js/bootstrap.bundle.min.js"></script>
    <script src="{{ url_for('static', filename='js/main.js') }}"></script>

    {% block scripts %}{% endblock %}
</body>
</html>'''
        
        # 首頁模板
        index_template = '''{% extends "base.html" %}

{% block content %}
<!-- 主標題區 -->
<div class="text-center my-5">
    <h1 class="page-title">
        <i class="fas fa-shield-alt"></i> Numora
    </h1>
    <p class="page-subtitle">智能犯罪案件統計分析平台 | 讓數據說話，讓分析更簡單</p>
</div>

<!-- 功能卡片區 -->
<div class="row g-4 my-5">
    <div class="col-md-4" data-aos="fade-up" data-aos-delay="100">
        <div class="feature-card glass-card">
            <div class="feature-icon">
                <i class="fas fa-chart-line"></i>
            </div>
            <h3 class="feature-title">數據分析</h3>
            <p class="feature-description">
                深入分析犯罪案件趨勢與模式<br>
                提供多維度的數據洞察
            </p>
            <a href="/dashboard" class="btn btn-gradient">
                <i class="fas fa-arrow-right"></i> 查看儀表板
            </a>
        </div>
    </div>

    <div class="col-md-4" data-aos="fade-up" data-aos-delay="200">
        <div class="feature-card glass-card">
            <div class="feature-icon">
                <i class="fas fa-map-marked-alt"></i>
            </div>
            <h3 class="feature-title">地區分析</h3>
            <p class="feature-description">
                各地區犯罪案件分布與熱點分析<br>
                智能識別高風險區域
            </p>
            <a href="/analysis" class="btn btn-gradient">
                <i class="fas fa-arrow-right"></i> 開始分析
            </a>
        </div>
    </div>

    <div class="col-md-4" data-aos="fade-up" data-aos-delay="300">
        <div class="feature-card glass-card">
            <div class="feature-icon">
                <i class="fas fa-brain"></i>
            </div>
            <h3 class="feature-title">AI 預測</h3>
            <p class="feature-description">
                機器學習預測犯罪趨勢<br>
                提前識別潛在風險
            </p>
            <a href="/prediction" class="btn btn-gradient">
                <i class="fas fa-arrow-right"></i> 查看預測
            </a>
        </div>
    </div>
</div>

<!-- 特色展示區 -->
<div class="row g-4 my-5">
    <div class="col-12">
        <div class="glass-card text-center">
            <h2 class="mb-4">
                <i class="fas fa-sparkles"></i> 平台特色
            </h2>
            <div class="row g-4 mt-4">
                <div class="col-md-3">
                    <div class="p-3">
                        <i class="fas fa-robot fa-3x mb-3" style="color: #667eea;"></i>
                        <h5>AI 驅動</h5>
                        <p class="text-muted">機器學習預測模型</p>
                    </div>
                </div>
                <div class="col-md-3">
                    <div class="p-3">
                        <i class="fas fa-chart-bar fa-3x mb-3" style="color: #f5576c;"></i>
                        <h5>視覺化</h5>
                        <p class="text-muted">互動式圖表分析</p>
                    </div>
                </div>
                <div class="col-md-3">
                    <div class="p-3">
                        <i class="fas fa-database fa-3x mb-3" style="color: #00f2fe;"></i>
                        <h5>多格式支援</h5>
                        <p class="text-muted">CSV, Excel, JSON</p>
                    </div>
                </div>
                <div class="col-md-3">
                    <div class="p-3">
                        <i class="fas fa-shield-alt fa-3x mb-3" style="color: #fee140;"></i>
                        <h5>安全可靠</h5>
                        <p class="text-muted">企業級數據安全</p>
                    </div>
                </div>
            </div>
        </div>
    </div>
</div>

<!-- CTA 區域 -->
<div class="row my-5">
    <div class="col-12">
        <div class="glass-card text-center p-5" style="background: linear-gradient(135deg, rgba(102, 126, 234, 0.1) 0%, rgba(118, 75, 162, 0.1) 100%);">
            <h2 class="mb-3">準備好開始分析了嗎？</h2>
            <p class="lead mb-4">立即體驗強大的數據分析功能</p>
            <a href="/dashboard" class="btn btn-gradient btn-lg me-3">
                <i class="fas fa-rocket"></i> 立即開始
            </a>
            <a href="https://github.com/kaiyasi/Numora" target="_blank" class="btn btn-outline-primary btn-lg">
                <i class="fab fa-github"></i> View on GitHub
            </a>
        </div>
    </div>
</div>
{% endblock %}'''
        
        # 儀表板模板
        dashboard_template = '''{% extends "base.html" %}

{% block title %}儀表板 - Numora{% endblock %}

{% block content %}
<!-- 頁面標題 -->
<div class="text-center my-4">
    <h1 class="page-title">
        <i class="fas fa-tachometer-alt"></i> 統計儀表板
    </h1>
    <p class="page-subtitle">即時數據分析與視覺化</p>
</div>

{% if error %}
<div class="alert alert-danger glass-card">
    <i class="fas fa-exclamation-triangle"></i> {{ error }}
</div>
{% else %}

<!-- 統計卡片區 -->
<div class="row g-4 mb-5">
    <div class="col-md-3">
        <div class="stat-card primary">
            <div class="stat-icon">
                <i class="fas fa-file-alt"></i>
            </div>
            <div class="stat-value" data-value="{{ stats['總案件數'] }}">0</div>
            <div class="stat-label">總案件數</div>
        </div>
    </div>
    <div class="col-md-3">
        <div class="stat-card secondary">
            <div class="stat-icon">
                <i class="fas fa-calendar-alt"></i>
            </div>
            <div class="stat-value">{{ stats['年份範圍'] }}</div>
            <div class="stat-label">資料年份範圍</div>
        </div>
    </div>
    <div class="col-md-3">
        <div class="stat-card success">
            <div class="stat-icon">
                <i class="fas fa-map-marked-alt"></i>
            </div>
            <div class="stat-value" data-value="{{ stats['可用地區']|length }}">0</div>
            <div class="stat-label">地區類型數</div>
        </div>
    </div>
    <div class="col-md-3">
        <div class="stat-card warning">
            <div class="stat-icon">
                <i class="fas fa-list"></i>
            </div>
            <div class="stat-value" data-value="{{ stats['案類統計']|length }}">0</div>
            <div class="stat-label">案件類型數</div>
        </div>
    </div>
</div>

<!-- 圖表區域 -->
<div class="row g-4 mb-4">
    <div class="col-lg-6">
        <div class="glass-card chart-container">
            <div class="chart-header">
                <i class="fas fa-chart-line"></i> 年度案件趨勢
            </div>
            <div id="yearlyTrendChart"></div>
        </div>
    </div>
    <div class="col-lg-6">
        <div class="glass-card chart-container">
            <div class="chart-header">
                <i class="fas fa-map"></i> 地區案件分布
            </div>
            <div id="areaDistributionChart"></div>
        </div>
    </div>
</div>

<div class="row g-4 mb-4">
    <div class="col-lg-6">
        <div class="glass-card chart-container">
            <div class="chart-header">
                <i class="fas fa-chart-pie"></i> 案件類型分布
            </div>
            <div id="caseTypePieChart"></div>
        </div>
    </div>
    <div class="col-lg-6">
        <div class="glass-card chart-container">
            <div class="chart-header">
                <i class="fas fa-fire"></i> 時段熱力圖
            </div>
            <div id="timeHeatmapChart"></div>
        </div>
    </div>
</div>

{% endif %}
{% endblock %}

{% block scripts %}
<script>
document.addEventListener('DOMContentLoaded', function() {
    // 載入圖表
    if (typeof NumoraApp !== 'undefined') {
        NumoraApp.loadChart('yearly_trend', 'yearlyTrendChart');
        NumoraApp.loadChart('area_distribution', 'areaDistributionChart');
        NumoraApp.loadChart('case_type_pie', 'caseTypePieChart');
        NumoraApp.loadChart('time_heatmap', 'timeHeatmapChart');
    }
});
</script>
{% endblock %}'''
        
        # 分析頁面模板
        analysis_template = '''{% extends "base.html" %}

{% block title %}地區分析 - Numora{% endblock %}

{% block content %}
<div class="text-center my-4">
    <h1 class="page-title">
        <i class="fas fa-map-marked-alt"></i> 地區分析
    </h1>
    <p class="page-subtitle">深入分析各地區犯罪案件分布與趨勢</p>
</div>

<div class="row g-4">
    <div class="col-12">
        <div class="glass-card">
            <h4 class="mb-4"><i class="fas fa-filter"></i> 篩選條件</h4>
            <div class="row g-3">
                <div class="col-md-4">
                    <label class="form-label">選擇地區</label>
                    <select class="form-select" id="areaSelect">
                        <option value="all">全部地區</option>
                        <option value="台北市">台北市</option>
                        <option value="新北市">新北市</option>
                        <option value="桃園市">桃園市</option>
                        <option value="台中市">台中市</option>
                        <option value="台南市">台南市</option>
                        <option value="高雄市">高雄市</option>
                    </select>
                </div>
                <div class="col-md-4">
                    <label class="form-label">選擇年份</label>
                    <select class="form-select" id="yearSelect">
                        <option value="all">全部年份</option>
                    </select>
                </div>
                <div class="col-md-4">
                    <label class="form-label">&nbsp;</label>
                    <button class="btn btn-gradient w-100" id="applyFilter">
                        <i class="fas fa-search"></i> 開始分析
                    </button>
                </div>
            </div>
        </div>
    </div>
</div>

<div class="row g-4 mt-3">
    <div class="col-lg-8">
        <div class="glass-card chart-container">
            <div class="chart-header">
                <i class="fas fa-chart-area"></i> 地區案件趨勢
            </div>
            <div id="areaAnalysisChart"></div>
        </div>
    </div>
    <div class="col-lg-4">
        <div class="glass-card">
            <h5 class="mb-3"><i class="fas fa-trophy"></i> 高風險地區排名</h5>
            <div id="rankingList"></div>
        </div>
    </div>
</div>
{% endblock %}

{% block scripts %}
<script>
document.addEventListener('DOMContentLoaded', function() {
    document.getElementById('applyFilter').addEventListener('click', function() {
        const area = document.getElementById('areaSelect').value;
        const year = document.getElementById('yearSelect').value;

        NumoraApp.showNotification('正在分析數據...', 'info');

        // 載入圖表
        NumoraApp.loadChart('area_distribution', 'areaAnalysisChart', { area, year });
    });
});
</script>
{% endblock %}'''

        # 預測頁面模板
        prediction_template = '''{% extends "base.html" %}

{% block title %}AI 預測 - Numora{% endblock %}

{% block content %}
<div class="text-center my-4">
    <h1 class="page-title">
        <i class="fas fa-brain"></i> AI 犯罪趨勢預測
    </h1>
    <p class="page-subtitle">使用機器學習預測未來犯罪趨勢</p>
</div>

<div class="row g-4">
    <div class="col-12">
        <div class="glass-card">
            <h4 class="mb-4"><i class="fas fa-cogs"></i> 預測設定</h4>
            <div class="row g-3">
                <div class="col-md-4">
                    <label class="form-label">選擇地區</label>
                    <select class="form-select" id="predAreaSelect">
                        <option value="台北市">台北市</option>
                        <option value="新北市">新北市</option>
                        <option value="桃園市">桃園市</option>
                        <option value="台中市">台中市</option>
                        <option value="台南市">台南市</option>
                        <option value="高雄市">高雄市</option>
                    </select>
                </div>
                <div class="col-md-4">
                    <label class="form-label">預測年份</label>
                    <select class="form-select" id="predYearSelect">
                        <option value="2024">2024</option>
                        <option value="2025">2025</option>
                        <option value="2026">2026</option>
                    </select>
                </div>
                <div class="col-md-4">
                    <label class="form-label">&nbsp;</label>
                    <button class="btn btn-gradient w-100" id="startPrediction">
                        <i class="fas fa-magic"></i> 開始預測
                    </button>
                </div>
            </div>
        </div>
    </div>
</div>

<div class="row g-4 mt-3">
    <div class="col-lg-8">
        <div class="glass-card chart-container">
            <div class="chart-header">
                <i class="fas fa-chart-line"></i> 預測結果
            </div>
            <div id="predictionChart"></div>
        </div>
    </div>
    <div class="col-lg-4">
        <div class="glass-card">
            <h5 class="mb-3"><i class="fas fa-info-circle"></i> 預測資訊</h5>
            <div id="predictionInfo">
                <p class="text-muted">請選擇地區和年份後開始預測</p>
            </div>
        </div>
    </div>
</div>

<div class="row g-4 mt-3">
    <div class="col-12">
        <div class="glass-card">
            <h5 class="mb-3"><i class="fas fa-lightbulb"></i> AI 洞察</h5>
            <div class="alert alert-info">
                <i class="fas fa-robot"></i> 本系統使用隨機森林與線性回歸機器學習模型進行預測，基於歷史數據分析未來趨勢。預測結果僅供參考，實際情況可能因多種因素而有所不同。
            </div>
        </div>
    </div>
</div>
{% endblock %}

{% block scripts %}
<script>
document.addEventListener('DOMContentLoaded', function() {
    document.getElementById('startPrediction').addEventListener('click', async function() {
        const area = document.getElementById('predAreaSelect').value;
        const year = document.getElementById('predYearSelect').value;

        NumoraApp.showLoading('predictionChart');
        NumoraApp.showNotification('正在運行AI預測模型...', 'info');

        try {
            const data = await NumoraApp.fetchData(`/api/prediction?area=${area}&years=${year}`);

            if (data.error) {
                NumoraApp.showNotification('預測失敗: ' + data.error, 'danger');
                return;
            }

            // 顯示預測結果
            document.getElementById('predictionInfo').innerHTML = `
                <div class="mb-3">
                    <strong>預測地區:</strong> ${data.area}
                </div>
                <div class="mb-3">
                    <strong>預測年份:</strong> ${year}
                </div>
                <div class="alert alert-success">
                    <i class="fas fa-check-circle"></i> 預測完成！
                </div>
            `;

            NumoraApp.showNotification('預測完成！', 'success');

        } catch (error) {
            NumoraApp.showNotification('預測失敗: ' + error.message, 'danger');
        }
    });
});
</script>
{% endblock %}'''

        # 寫入所有模板檔案
        templates = {
            'base.html': base_template,
            'index.html': index_template,
            'dashboard.html': dashboard_template,
            'analysis.html': analysis_template,
            'prediction.html': prediction_template
        }

        for filename, content in templates.items():
            with open(os.path.join(template_dir, filename), 'w', encoding='utf-8') as f:
                f.write(content)

        # 追加 YouBike 模板檔案
        youbike_template = '''{% extends "base.html" %}

{% block title %}YouBike 即時資訊 - Numora{% endblock %}

{% block content %}
<div class="text-center my-4">
    <h1 class="page-title">
        <i class="fas fa-bicycle"></i> YouBike 即時資訊
    </h1>
    <p class="page-subtitle">選擇城市與地區，瀏覽即時站點資訊</p>
    <div class="row justify-content-center g-3 mt-3">
        <div class="col-md-3">
            <select id="citySelect" class="form-select">
                <option value="taipei">台北市</option>
                <option value="new_taipei">新北市</option>
            </select>
        </div>
        <div class="col-md-3">
            <select id="areaSelect" class="form-select">
                <option value="__all__">全部地區</option>
            </select>
        </div>
        <div class="col-md-2">
            <select id="pageSelect" class="form-select">
                <option value="1">第 1 頁</option>
            </select>
        </div>
    </div>
</div>

<div class="glass-card p-3">
    <div id="youbikeStats" class="mb-2 text-muted"></div>
    <ul id="stationList" class="list-group list-group-flush"></ul>
    <div id="emptyHint" class="text-center text-muted py-3" style="display:none;">無資料</div>
    <div class="mt-3 text-end">
        <small class="text-muted">每頁 10 筆</small>
    </div>
</div>

<script>
async function fetchJSON(url) {
  const r = await fetch(url);
  if (!r.ok) throw new Error('HTTP ' + r.status);
  return await r.json();
}

async function loadAreas() {
  const city = document.getElementById('citySelect').value;
  const data = await fetchJSON(`/api/youbike/areas?city=${city}`);
  const sel = document.getElementById('areaSelect');
  sel.innerHTML = '<option value="__all__">全部地區</option>' +
    (data.areas || []).map(a => `<option value="${a}">${a}</option>`).join('');
}

async function loadStations(page=1) {
  const city = document.getElementById('citySelect').value;
  const area = document.getElementById('areaSelect').value;
  const size = 10;
  const data = await fetchJSON(`/api/youbike/stations?city=${city}&area=${encodeURIComponent(area)}&page=${page}&size=${size}`);
  const list = document.getElementById('stationList');
  const stats = document.getElementById('youbikeStats');
  const empty = document.getElementById('emptyHint');
  list.innerHTML = '';
  if ((data.stations || []).length === 0) {
    empty.style.display = '';
    stats.textContent = '第 0–0 筆，共 0 筆';
    return;
  }
  empty.style.display = 'none';
  stats.textContent = `第 ${(data.page-1)*size+1}–${(data.page-1)*size + data.stations.length} 筆，共 ${data.total} 筆`;
  for (const s of data.stations) {
    const li = document.createElement('li');
    li.className = 'list-group-item';
    const area = s.area ? ` (${s.area})` : '';
    li.textContent = `${s.name}${area}｜可借:${s.available_bikes} 可還:${s.available_docks}｜${s.address || ''}`;
    list.appendChild(li);
  }
  // 重建頁碼
  const pages = Math.max(1, Math.ceil(data.total / size));
  const pageSelect = document.getElementById('pageSelect');
  pageSelect.innerHTML = Array.from({length: Math.min(50, pages)}, (_, i) => {
    const p = i+1; return `<option value=\"${p}\" ${p==data.page?'selected':''}>第 ${p} 頁</option>`;
  }).join('');
}

document.getElementById('citySelect').addEventListener('change', async () => {
  await loadAreas();
  await loadStations(1);
});
document.getElementById('areaSelect').addEventListener('change', async () => {
  await loadStations(1);
});
document.getElementById('pageSelect').addEventListener('change', async (e) => {
  await loadStations(parseInt(e.target.value, 10) || 1);
});

(async function init(){
  await loadAreas();
  await loadStations(1);
})();
</script>
{% endblock %}
'''

        with open(os.path.join(template_dir, 'youbike.html'), 'w', encoding='utf-8') as f:
            f.write(youbike_template)


        logger.info(f"HTML 模板已創建於: {template_dir}")
    
    def start_server(self, host='0.0.0.0', port=5000, debug=False):
        """啟動 Web 伺服器"""
        logger.info(f"Web 介面已啟動：http://{host}:{port}")
        self.app.run(host=host, port=port, debug=debug, use_reloader=False)
    
    def stop_server(self):
        """停止 Web 伺服器"""
        # Flask 沒有內建的停止方法，這裡只是記錄
        logger.info("Web 介面停止請求已發送")
