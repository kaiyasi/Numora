"""
機器學習預測模組
提供犯罪案件趨勢預測功能
"""

import pandas as pd
import numpy as np
from sklearn.ensemble import RandomForestRegressor
from sklearn.linear_model import LinearRegression
from sklearn.preprocessing import LabelEncoder
from sklearn.model_selection import train_test_split
from sklearn.metrics import mean_absolute_error, r2_score
import logging
from typing import Dict, List, Optional, Tuple
import pickle
import os

logger = logging.getLogger(__name__)

class CrimePredictionModel:
    """犯罪案件預測模型"""
    
    def __init__(self):
        self.models = {}
        self.encoders = {}
        self.is_trained = False
        self.model_path = "models/"
        os.makedirs(self.model_path, exist_ok=True)
    
    def prepare_features(self, df: pd.DataFrame) -> pd.DataFrame:
        """準備特徵資料"""
        try:
            # 創建特徵副本
            features_df = df.copy()
            
            # 時間特徵
            features_df['月份'] = pd.to_datetime(features_df['日期'], format='%Y%m%d', errors='coerce').dt.month
            features_df['季度'] = pd.to_datetime(features_df['日期'], format='%Y%m%d', errors='coerce').dt.quarter
            features_df['星期'] = pd.to_datetime(features_df['日期'], format='%Y%m%d', errors='coerce').dt.dayofweek
            
            # 時段特徵編碼
            if '時段' in features_df.columns:
                if 'time_encoder' not in self.encoders:
                    self.encoders['time_encoder'] = LabelEncoder()
                    features_df['時段_encoded'] = self.encoders['time_encoder'].fit_transform(features_df['時段'].fillna('未知'))
                else:
                    features_df['時段_encoded'] = self.encoders['time_encoder'].transform(features_df['時段'].fillna('未知'))
            
            # 地區特徵編碼
            if '地點' in features_df.columns:
                # 提取市區資訊
                features_df['市'] = features_df['地點'].str.extract(r'(.+?市)', expand=False)
                features_df['區'] = features_df['地點'].str.extract(r'市(.+?區)', expand=False)
                
                if 'area_encoder' not in self.encoders:
                    self.encoders['area_encoder'] = LabelEncoder()
                    features_df['地區_encoded'] = self.encoders['area_encoder'].fit_transform(features_df['市'].fillna('未知'))
                else:
                    features_df['地區_encoded'] = self.encoders['area_encoder'].transform(features_df['市'].fillna('未知'))
            
            # 案類特徵編碼
            if '案類' in features_df.columns:
                if 'case_encoder' not in self.encoders:
                    self.encoders['case_encoder'] = LabelEncoder()
                    features_df['案類_encoded'] = self.encoders['case_encoder'].fit_transform(features_df['案類'].fillna('未知'))
                else:
                    features_df['案類_encoded'] = self.encoders['case_encoder'].transform(features_df['案類'].fillna('未知'))
            
            # 選擇特徵欄位
            feature_columns = ['年份', '月份', '季度', '星期', '時段_encoded', '地區_encoded', '案類_encoded']
            feature_columns = [col for col in feature_columns if col in features_df.columns]
            
            return features_df[feature_columns].fillna(0)
            
        except Exception as e:
            logger.error(f"準備特徵時發生錯誤: {e}")
            return pd.DataFrame()
    
    def train_models(self, df: pd.DataFrame) -> Dict[str, float]:
        """訓練預測模型"""
        try:
            logger.info("開始訓練犯罪預測模型...")
            
            # 準備特徵
            features_df = self.prepare_features(df)
            if features_df.empty:
                raise ValueError("無法準備特徵資料")
            
            # 創建目標變數 - 按年份和地區統計案件數
            target_data = []
            for year in df['年份'].unique():
                for area in df['地點'].str.extract(r'(.+?市)', expand=False).dropna().unique():
                    count = len(df[(df['年份'] == year) & (df['地點'].str.contains(area, na=False))])
                    if count > 0:
                        target_data.append({
                            '年份': year,
                            '地區': area,
                            '案件數': count
                        })
            
            target_df = pd.DataFrame(target_data)
            
            if target_df.empty:
                raise ValueError("無法創建目標資料")
            
            # 編碼目標資料的地區
            if 'target_area_encoder' not in self.encoders:
                self.encoders['target_area_encoder'] = LabelEncoder()
            
            target_df['地區_encoded'] = self.encoders['target_area_encoder'].fit_transform(target_df['地區'])
            
            # 準備訓練資料
            X = target_df[['年份', '地區_encoded']]
            y = target_df['案件數']
            
            # 分割訓練和測試資料
            X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.2, random_state=42)
            
            # 訓練多個模型
            models_to_train = {
                'random_forest': RandomForestRegressor(n_estimators=100, random_state=42),
                'linear_regression': LinearRegression()
            }
            
            results = {}
            
            for model_name, model in models_to_train.items():
                try:
                    # 訓練模型
                    model.fit(X_train, y_train)
                    
                    # 預測
                    y_pred = model.predict(X_test)
                    
                    # 評估
                    mae = mean_absolute_error(y_test, y_pred)
                    r2 = r2_score(y_test, y_pred)
                    
                    # 儲存模型
                    self.models[model_name] = model
                    results[model_name] = {'mae': mae, 'r2': r2}
                    
                    logger.info(f"{model_name} - MAE: {mae:.2f}, R²: {r2:.3f}")
                    
                except Exception as e:
                    logger.error(f"訓練 {model_name} 時發生錯誤: {e}")
                    continue
            
            if results:
                self.is_trained = True
                self.save_models()
                logger.info("模型訓練完成")
            
            return results
            
        except Exception as e:
            logger.error(f"訓練模型時發生錯誤: {e}")
            return {}
    
    def predict_crime_trends(self, area: str, years: List[int]) -> Dict[int, float]:
        """預測特定地區的犯罪趨勢"""
        try:
            if not self.is_trained or 'random_forest' not in self.models:
                raise ValueError("模型尚未訓練")
            
            # 編碼地區
            if 'target_area_encoder' not in self.encoders:
                raise ValueError("地區編碼器未初始化")
            
            try:
                area_encoded = self.encoders['target_area_encoder'].transform([area])[0]
            except ValueError:
                logger.warning(f"未知地區: {area}，使用平均值預測")
                area_encoded = 0
            
            # 預測
            predictions = {}
            model = self.models['random_forest']
            
            for year in years:
                X_pred = pd.DataFrame({'年份': [year], '地區_encoded': [area_encoded]})
                pred = model.predict(X_pred)[0]
                predictions[year] = max(0, pred)  # 確保預測值不為負
            
            return predictions
            
        except Exception as e:
            logger.error(f"預測犯罪趨勢時發生錯誤: {e}")
            return {}
    
    def get_feature_importance(self) -> Dict[str, float]:
        """取得特徵重要性"""
        try:
            if not self.is_trained or 'random_forest' not in self.models:
                return {}
            
            model = self.models['random_forest']
            feature_names = ['年份', '地區_encoded']
            
            importance_dict = {}
            for i, importance in enumerate(model.feature_importances_):
                importance_dict[feature_names[i]] = importance
            
            return importance_dict
            
        except Exception as e:
            logger.error(f"取得特徵重要性時發生錯誤: {e}")
            return {}
    
    def save_models(self):
        """儲存模型"""
        try:
            for model_name, model in self.models.items():
                model_file = os.path.join(self.model_path, f"{model_name}.pkl")
                with open(model_file, 'wb') as f:
                    pickle.dump(model, f)
            
            # 儲存編碼器
            encoder_file = os.path.join(self.model_path, "encoders.pkl")
            with open(encoder_file, 'wb') as f:
                pickle.dump(self.encoders, f)
                
            logger.info("模型已儲存")
            
        except Exception as e:
            logger.error(f"儲存模型時發生錯誤: {e}")
    
    def load_models(self):
        """載入模型"""
        try:
            # 載入模型
            for model_file in os.listdir(self.model_path):
                if model_file.endswith('.pkl') and model_file != 'encoders.pkl':
                    model_name = model_file.replace('.pkl', '')
                    model_path = os.path.join(self.model_path, model_file)
                    with open(model_path, 'rb') as f:
                        self.models[model_name] = pickle.load(f)
            
            # 載入編碼器
            encoder_file = os.path.join(self.model_path, "encoders.pkl")
            if os.path.exists(encoder_file):
                with open(encoder_file, 'rb') as f:
                    self.encoders = pickle.load(f)
            
            if self.models:
                self.is_trained = True
                logger.info(f"已載入 {len(self.models)} 個模型")
            
        except Exception as e:
            logger.error(f"載入模型時發生錯誤: {e}")
