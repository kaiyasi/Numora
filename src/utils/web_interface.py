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
        self.app = Flask(__name__, template_folder='../templates', static_folder='../static')
        self.data_processor = data_processor
        self.area_analyzer = AreaAnalyzer()
        self.ml_model = CrimePredictionModel()
        self.setup_routes()
        self.server_thread = None
        
        # 創建模板和靜態檔案目錄
        os.makedirs('templates', exist_ok=True)
        os.makedirs('static/css', exist_ok=True)
        os.makedirs('static/js', exist_ok=True)
        
        # 創建基本的 HTML 模板
        self.create_templates()
    
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
    
    def get_current_data(self) -> Optional[pd.DataFrame]:
        """取得當前資料"""
        current_df = self.data_processor.get_current_data()
        if current_df is not None:
            return current_df
        
        try:
            return self.data_processor.load_default_data()
        except:
            return None
    
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
        # 基礎模板
        base_template = '''<!DOCTYPE html>
<html lang="zh-TW">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>{% block title %}犯罪案件統計分析系統{% endblock %}</title>
    <link href="https://cdn.jsdelivr.net/npm/bootstrap@5.1.3/dist/css/bootstrap.min.css" rel="stylesheet">
    <link href="https://cdnjs.cloudflare.com/ajax/libs/font-awesome/6.0.0/css/all.min.css" rel="stylesheet">
    <script src="https://cdn.plot.ly/plotly-latest.min.js"></script>
    <style>
        .navbar-brand { font-weight: bold; }
        .card { box-shadow: 0 2px 4px rgba(0,0,0,0.1); }
        .stat-card { text-align: center; padding: 20px; }
        .chart-container { margin: 20px 0; }
    </style>
</head>
<body>
    <nav class="navbar navbar-expand-lg navbar-dark bg-primary">
        <div class="container">
            <a class="navbar-brand" href="/"><i class="fas fa-chart-bar"></i> 犯罪案件統計系統</a>
            <div class="navbar-nav ms-auto">
                <a class="nav-link" href="/">首頁</a>
                <a class="nav-link" href="/dashboard">儀表板</a>
                <a class="nav-link" href="/analysis">分析</a>
                <a class="nav-link" href="/prediction">預測</a>
            </div>
        </div>
    </nav>
    
    <div class="container mt-4">
        {% block content %}{% endblock %}
    </div>
    
    <script src="https://cdn.jsdelivr.net/npm/bootstrap@5.1.3/dist/js/bootstrap.bundle.min.js"></script>
    {% block scripts %}{% endblock %}
</body>
</html>'''
        
        # 首頁模板
        index_template = '''{% extends "base.html" %}

{% block content %}
<div class="row">
    <div class="col-12 text-center">
        <h1 class="display-4 mb-4"><i class="fas fa-shield-alt"></i> 犯罪案件統計分析系統</h1>
        <p class="lead">專業的犯罪案件數據分析與視覺化平台</p>
        
        <div class="row mt-5">
            <div class="col-md-4">
                <div class="card">
                    <div class="card-body stat-card">
                        <i class="fas fa-chart-line fa-3x text-primary mb-3"></i>
                        <h4>數據分析</h4>
                        <p>深入分析犯罪案件趨勢與模式</p>
                        <a href="/dashboard" class="btn btn-primary">查看儀表板</a>
                    </div>
                </div>
            </div>
            <div class="col-md-4">
                <div class="card">
                    <div class="card-body stat-card">
                        <i class="fas fa-map-marked-alt fa-3x text-success mb-3"></i>
                        <h4>地區分析</h4>
                        <p>各地區犯罪案件分布與熱點分析</p>
                        <a href="/analysis" class="btn btn-success">開始分析</a>
                    </div>
                </div>
            </div>
            <div class="col-md-4">
                <div class="card">
                    <div class="card-body stat-card">
                        <i class="fas fa-crystal-ball fa-3x text-warning mb-3"></i>
                        <h4>AI 預測</h4>
                        <p>機器學習預測犯罪趨勢</p>
                        <a href="/prediction" class="btn btn-warning">查看預測</a>
                    </div>
                </div>
            </div>
        </div>
    </div>
</div>
{% endblock %}'''
        
        # 儀表板模板
        dashboard_template = '''{% extends "base.html" %}

{% block title %}儀表板 - 犯罪案件統計分析系統{% endblock %}

{% block content %}
<h1><i class="fas fa-tachometer-alt"></i> 統計儀表板</h1>

{% if error %}
<div class="alert alert-danger">{{ error }}</div>
{% else %}

<div class="row mb-4">
    <div class="col-md-3">
        <div class="card bg-primary text-white">
            <div class="card-body stat-card">
                <h3>{{ stats['總案件數'] }}</h3>
                <p>總案件數</p>
            </div>
        </div>
    </div>
    <div class="col-md-3">
        <div class="card bg-success text-white">
            <div class="card-body stat-card">
                <h3>{{ stats['年份範圍'] }}</h3>
                <p>資料年份範圍</p>
            </div>
        </div>
    </div>
    <div class="col-md-3">
        <div class="card bg-info text-white">
            <div class="card-body stat-card">
                <h3>{{ stats['可用地區']|length }}</h3>
                <p>地區類型數</p>
            </div>
        </div>
    </div>
    <div class="col-md-3">
        <div class="card bg-warning text-white">
            <div class="card-body stat-card">
                <h3>{{ stats['案類統計']|length }}</h3>
                <p>案件類型數</p>
            </div>
        </div>
    </div>
</div>

<div class="row">
    <div class="col-md-6">
        <div class="card">
            <div class="card-header"><h5>年度趨勢</h5></div>
            <div class="card-body">
                <div id="yearlyTrendChart"></div>
            </div>
        </div>
    </div>
    <div class="col-md-6">
        <div class="card">
            <div class="card-header"><h5>地區分布</h5></div>
            <div class="card-body">
                <div id="areaDistributionChart"></div>
            </div>
        </div>
    </div>
</div>

<div class="row mt-4">
    <div class="col-md-6">
        <div class="card">
            <div class="card-header"><h5>案件類型分布</h5></div>
            <div class="card-body">
                <div id="caseTypePieChart"></div>
            </div>
        </div>
    </div>
    <div class="col-md-6">
        <div class="card">
            <div class="card-header"><h5>時段熱力圖</h5></div>
            <div class="card-body">
                <div id="timeHeatmapChart"></div>
            </div>
        </div>
    </div>
</div>

{% endif %}
{% endblock %}

{% block scripts %}
<script>
// 載入圖表
fetch('/api/charts/yearly_trend')
    .then(response => response.json())
    .then(data => {
        if (!data.error) {
            Plotly.newPlot('yearlyTrendChart', JSON.parse(data));
        }
    });

fetch('/api/charts/area_distribution')
    .then(response => response.json())
    .then(data => {
        if (!data.error) {
            Plotly.newPlot('areaDistributionChart', JSON.parse(data));
        }
    });

fetch('/api/charts/case_type_pie')
    .then(response => response.json())
    .then(data => {
        if (!data.error) {
            Plotly.newPlot('caseTypePieChart', JSON.parse(data));
        }
    });

fetch('/api/charts/time_heatmap')
    .then(response => response.json())
    .then(data => {
        if (!data.error) {
            Plotly.newPlot('timeHeatmapChart', JSON.parse(data));
        }
    });
</script>
{% endblock %}'''
        
        # 寫入模板檔案
        with open('templates/base.html', 'w', encoding='utf-8') as f:
            f.write(base_template)
        
        with open('templates/index.html', 'w', encoding='utf-8') as f:
            f.write(index_template)
        
        with open('templates/dashboard.html', 'w', encoding='utf-8') as f:
            f.write(dashboard_template)
        
        logger.info("HTML 模板已創建")
    
    def start_server(self, host='0.0.0.0', port=5000, debug=False):
        """啟動 Web 伺服器"""
        def run_server():
            self.app.run(host=host, port=port, debug=debug, use_reloader=False)
        
        self.server_thread = threading.Thread(target=run_server)
        self.server_thread.daemon = True
        self.server_thread.start()
        
        logger.info(f"Web 介面已啟動：http://{host}:{port}")
    
    def stop_server(self):
        """停止 Web 伺服器"""
        # Flask 沒有內建的停止方法，這裡只是記錄
        logger.info("Web 介面停止請求已發送")
