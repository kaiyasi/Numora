"""
即時通知系統
監控犯罪數據變化並發送通知
"""

import asyncio
import discord
from discord.ext import tasks
import pandas as pd
import logging
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Set
import json
import os

from src.utils.config import config

logger = logging.getLogger(__name__)

class NotificationSystem:
    """即時通知系統"""
    
    def __init__(self, bot):
        self.bot = bot
        self.subscriptions = {}  # 用戶訂閱資訊
        self.last_data_hash = None
        self.notification_file = "data/notifications.json"
        self.load_subscriptions()
        
        # 啟動定期檢查任務
        if not self.check_data_updates.is_running():
            self.check_data_updates.start()
    
    def load_subscriptions(self):
        """載入訂閱資訊"""
        try:
            if os.path.exists(self.notification_file):
                with open(self.notification_file, 'r', encoding='utf-8') as f:
                    self.subscriptions = json.load(f)
                logger.info(f"載入 {len(self.subscriptions)} 個訂閱")
            else:
                os.makedirs(os.path.dirname(self.notification_file), exist_ok=True)
        except Exception as e:
            logger.error(f"載入訂閱資訊時發生錯誤: {e}")
            self.subscriptions = {}
    
    def save_subscriptions(self):
        """儲存訂閱資訊"""
        try:
            with open(self.notification_file, 'w', encoding='utf-8') as f:
                json.dump(self.subscriptions, f, ensure_ascii=False, indent=2)
        except Exception as e:
            logger.error(f"儲存訂閱資訊時發生錯誤: {e}")
    
    def subscribe_user(self, user_id: int, channel_id: int, notification_types: List[str], areas: List[str] = None):
        """訂閱通知"""
        user_key = str(user_id)
        
        if user_key not in self.subscriptions:
            self.subscriptions[user_key] = {
                'channel_id': channel_id,
                'types': [],
                'areas': [],
                'created_at': datetime.now().isoformat()
            }
        
        # 更新訂閱類型
        for notification_type in notification_types:
            if notification_type not in self.subscriptions[user_key]['types']:
                self.subscriptions[user_key]['types'].append(notification_type)
        
        # 更新關注地區
        if areas:
            for area in areas:
                if area not in self.subscriptions[user_key]['areas']:
                    self.subscriptions[user_key]['areas'].append(area)
        
        self.subscriptions[user_key]['updated_at'] = datetime.now().isoformat()
        self.save_subscriptions()
        
        logger.info(f"用戶 {user_id} 訂閱了通知: {notification_types}")
    
    def unsubscribe_user(self, user_id: int, notification_types: List[str] = None):
        """取消訂閱"""
        user_key = str(user_id)
        
        if user_key not in self.subscriptions:
            return False
        
        if notification_types is None:
            # 取消所有訂閱
            del self.subscriptions[user_key]
        else:
            # 取消特定類型訂閱
            for notification_type in notification_types:
                if notification_type in self.subscriptions[user_key]['types']:
                    self.subscriptions[user_key]['types'].remove(notification_type)
            
            # 如果沒有任何訂閱類型，刪除用戶
            if not self.subscriptions[user_key]['types']:
                del self.subscriptions[user_key]
        
        self.save_subscriptions()
        logger.info(f"用戶 {user_id} 取消訂閱: {notification_types}")
        return True
    
    def get_user_subscriptions(self, user_id: int) -> Dict:
        """取得用戶訂閱資訊"""
        user_key = str(user_id)
        return self.subscriptions.get(user_key, {})
    
    @tasks.loop(minutes=30)  # 每30分鐘檢查一次
    async def check_data_updates(self):
        """檢查資料更新"""
        try:
            # 取得當前資料
            data_processor = self.bot.get_data_processor()
            current_df = data_processor.get_current_data()
            
            if current_df is None:
                return
            
            # 計算資料雜湊值
            current_hash = hash(str(current_df.values.tobytes()))
            
            if self.last_data_hash is None:
                self.last_data_hash = current_hash
                return
            
            # 檢查是否有變化
            if current_hash != self.last_data_hash:
                await self.notify_data_update(current_df)
                self.last_data_hash = current_hash
                
        except Exception as e:
            logger.error(f"檢查資料更新時發生錯誤: {e}")
    
    async def notify_data_update(self, df: pd.DataFrame):
        """通知資料更新"""
        try:
            # 分析資料變化
            stats = self.analyze_data_changes(df)
            
            # 發送通知給訂閱用戶
            for user_id, subscription in self.subscriptions.items():
                if 'data_update' in subscription['types']:
                    await self.send_notification(
                        int(user_id),
                        subscription['channel_id'],
                        "📊 資料更新通知",
                        f"犯罪案件資料已更新\n\n{stats}",
                        discord.Color.blue()
                    )
                    
        except Exception as e:
            logger.error(f"發送資料更新通知時發生錯誤: {e}")
    
    def analyze_data_changes(self, df: pd.DataFrame) -> str:
        """分析資料變化"""
        try:
            stats = []
            stats.append(f"總案件數：{len(df)} 件")
            stats.append(f"年份範圍：{df['年份'].min()} - {df['年份'].max()}")
            
            # 最新案件統計
            latest_year = df['年份'].max()
            latest_count = len(df[df['年份'] == latest_year])
            stats.append(f"{latest_year} 年案件數：{latest_count} 件")
            
            # 熱點地區
            top_areas = df['地點'].str.extract(r'(.+?市)', expand=False).value_counts().head(3)
            if not top_areas.empty:
                stats.append("前3大熱點地區：")
                for area, count in top_areas.items():
                    stats.append(f"  • {area}：{count} 件")
            
            return "\n".join(stats)
            
        except Exception as e:
            logger.error(f"分析資料變化時發生錯誤: {e}")
            return "資料分析失敗"
    
    async def notify_high_crime_alert(self, area: str, count: int, threshold: int = 100):
        """高犯罪率警告"""
        try:
            if count < threshold:
                return
            
            message = f"⚠️ 高犯罪率警告\n\n地區：{area}\n案件數：{count} 件\n已超過警戒值：{threshold} 件"
            
            # 發送給關注該地區的用戶
            for user_id, subscription in self.subscriptions.items():
                if ('high_crime_alert' in subscription['types'] and 
                    (not subscription['areas'] or area in subscription['areas'])):
                    
                    await self.send_notification(
                        int(user_id),
                        subscription['channel_id'],
                        "⚠️ 高犯罪率警告",
                        message,
                        discord.Color.red()
                    )
                    
        except Exception as e:
            logger.error(f"發送高犯罪率警告時發生錯誤: {e}")
    
    async def notify_trend_analysis(self, area: str, trend: str, change_percent: float):
        """趨勢分析通知"""
        try:
            if abs(change_percent) < 10:  # 變化小於10%不通知
                return
            
            trend_emoji = "📈" if change_percent > 0 else "📉"
            trend_text = "上升" if change_percent > 0 else "下降"
            
            message = f"{trend_emoji} 犯罪趨勢分析\n\n地區：{area}\n趨勢：{trend_text}\n變化幅度：{change_percent:.1f}%"
            
            # 發送給關注趨勢分析的用戶
            for user_id, subscription in self.subscriptions.items():
                if ('trend_analysis' in subscription['types'] and 
                    (not subscription['areas'] or area in subscription['areas'])):
                    
                    await self.send_notification(
                        int(user_id),
                        subscription['channel_id'],
                        f"{trend_emoji} 趨勢分析",
                        message,
                        discord.Color.orange()
                    )
                    
        except Exception as e:
            logger.error(f"發送趨勢分析通知時發生錯誤: {e}")
    
    async def send_notification(self, user_id: int, channel_id: int, title: str, message: str, color: discord.Color):
        """發送通知"""
        try:
            channel = self.bot.get_channel(channel_id)
            if not channel:
                logger.warning(f"找不到頻道 {channel_id}")
                return
            
            embed = discord.Embed(
                title=title,
                description=message,
                color=color,
                timestamp=datetime.now()
            )
            
            embed.set_footer(text="犯罪案件統計機器人 • 即時通知")
            
            await channel.send(embed=embed)
            logger.info(f"已發送通知給用戶 {user_id}")
            
        except Exception as e:
            logger.error(f"發送通知時發生錯誤: {e}")
    
    def get_available_notification_types(self) -> List[Dict[str, str]]:
        """取得可用的通知類型"""
        return [
            {
                'type': 'data_update',
                'name': '資料更新',
                'description': '當犯罪案件資料更新時通知'
            },
            {
                'type': 'high_crime_alert',
                'name': '高犯罪率警告',
                'description': '當特定地區犯罪率超過警戒值時通知'
            },
            {
                'type': 'trend_analysis',
                'name': '趨勢分析',
                'description': '當犯罪趨勢有顯著變化時通知'
            },
            {
                'type': 'weekly_report',
                'name': '週報',
                'description': '每週發送犯罪統計報告'
            },
            {
                'type': 'monthly_report',
                'name': '月報',
                'description': '每月發送犯罪統計報告'
            }
        ]
    
    @tasks.loop(time=datetime.now().replace(hour=9, minute=0, second=0).time())  # 每天早上9點
    async def send_daily_reports(self):
        """發送每日報告"""
        try:
            # 檢查是否為週一（發送週報）
            if datetime.now().weekday() == 0:  # 週一
                await self.send_weekly_reports()
            
            # 檢查是否為月初（發送月報）
            if datetime.now().day == 1:  # 每月1號
                await self.send_monthly_reports()
                
        except Exception as e:
            logger.error(f"發送每日報告時發生錯誤: {e}")
    
    async def send_weekly_reports(self):
        """發送週報"""
        try:
            data_processor = self.bot.get_data_processor()
            current_df = data_processor.get_current_data()
            
            if current_df is None:
                return
            
            # 生成週報內容
            report = self.generate_weekly_report(current_df)
            
            # 發送給訂閱週報的用戶
            for user_id, subscription in self.subscriptions.items():
                if 'weekly_report' in subscription['types']:
                    await self.send_notification(
                        int(user_id),
                        subscription['channel_id'],
                        "📊 週報 - 犯罪案件統計",
                        report,
                        discord.Color.green()
                    )
                    
        except Exception as e:
            logger.error(f"發送週報時發生錯誤: {e}")
    
    async def send_monthly_reports(self):
        """發送月報"""
        try:
            data_processor = self.bot.get_data_processor()
            current_df = data_processor.get_current_data()
            
            if current_df is None:
                return
            
            # 生成月報內容
            report = self.generate_monthly_report(current_df)
            
            # 發送給訂閱月報的用戶
            for user_id, subscription in self.subscriptions.items():
                if 'monthly_report' in subscription['types']:
                    await self.send_notification(
                        int(user_id),
                        subscription['channel_id'],
                        "📊 月報 - 犯罪案件統計",
                        report,
                        discord.Color.purple()
                    )
                    
        except Exception as e:
            logger.error(f"發送月報時發生錯誤: {e}")
    
    def generate_weekly_report(self, df: pd.DataFrame) -> str:
        """生成週報"""
        try:
            report = ["📊 本週犯罪案件統計報告", ""]
            
            # 基本統計
            report.append(f"總案件數：{len(df)} 件")
            report.append(f"涵蓋年份：{df['年份'].min()} - {df['年份'].max()}")
            report.append("")
            
            # 案類統計
            top_cases = df['案類'].value_counts().head(5)
            report.append("前5大案件類型：")
            for case_type, count in top_cases.items():
                report.append(f"  • {case_type}：{count} 件")
            report.append("")
            
            # 地區統計
            top_areas = df['地點'].str.extract(r'(.+?市)', expand=False).value_counts().head(5)
            if not top_areas.empty:
                report.append("前5大案件地區：")
                for area, count in top_areas.items():
                    report.append(f"  • {area}：{count} 件")
            
            return "\n".join(report)
            
        except Exception as e:
            logger.error(f"生成週報時發生錯誤: {e}")
            return "週報生成失敗"
    
    def generate_monthly_report(self, df: pd.DataFrame) -> str:
        """生成月報"""
        try:
            report = ["📊 本月犯罪案件統計報告", ""]
            
            # 基本統計
            report.append(f"總案件數：{len(df)} 件")
            report.append(f"涵蓋年份：{df['年份'].min()} - {df['年份'].max()}")
            report.append("")
            
            # 年度趨勢
            yearly_counts = df['年份'].value_counts().sort_index()
            report.append("年度案件趨勢：")
            for year, count in yearly_counts.items():
                report.append(f"  • {year} 年：{count} 件")
            report.append("")
            
            # 時段分析
            time_counts = df['時段'].value_counts().head(5)
            report.append("案件高發時段：")
            for time_period, count in time_counts.items():
                report.append(f"  • {time_period}：{count} 件")
            
            return "\n".join(report)
            
        except Exception as e:
            logger.error(f"生成月報時發生錯誤: {e}")
            return "月報生成失敗"
    
    def stop(self):
        """停止通知系統"""
        if self.check_data_updates.is_running():
            self.check_data_updates.cancel()
        if self.send_daily_reports.is_running():
            self.send_daily_reports.cancel()
        logger.info("通知系統已停止")
