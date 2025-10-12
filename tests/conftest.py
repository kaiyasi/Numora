"""
測試配置和工具
"""

import pytest
import pandas as pd
import os
import tempfile
import shutil
from unittest.mock import Mock, AsyncMock
import asyncio

# 測試資料
SAMPLE_CSV_DATA = """編號,案類,日期,時段,地點
1,竊盜,1120101,0-6,台北市中山區民權東路
2,詐欺,1120102,6-12,新北市板橋區中山路
3,竊盜,1120103,12-18,台北市信義區信義路
4,傷害,1120104,18-24,台中市西屯區台灣大道
5,竊盜,1120105,0-6,高雄市前金區中正四路"""

SAMPLE_TXT_DATA = """編號 案類 日期 時段 地點
1 竊盜 1120101 0-6 台北市中山區民權東路一段100號
2 詐欺 1120102 6-12 新北市板橋區中山路二段200號
3 竊盜 1120103 12-18 台北市信義區信義路三段300號
4 傷害 1120104 18-24 台中市西屯區台灣大道四段400號
5 竊盜 1120105 0-6 高雄市前金區中正四路五段500號"""

@pytest.fixture
def sample_dataframe():
    """創建測試用的 DataFrame"""
    data = {
        '編號': [1, 2, 3, 4, 5],
        '案類': ['竊盜', '詐欺', '竊盜', '傷害', '竊盜'],
        '日期': ['1120101', '1120102', '1120103', '1120104', '1120105'],
        '時段': ['0-6', '6-12', '12-18', '18-24', '0-6'],
        '地點': [
            '台北市中山區民權東路一段100號',
            '新北市板橋區中山路二段200號',
            '台北市信義區信義路三段300號',
            '台中市西屯區台灣大道四段400號',
            '高雄市前金區中正四路五段500號'
        ],
        '年份': [2023, 2023, 2023, 2023, 2023]
    }
    return pd.DataFrame(data)

@pytest.fixture
def temp_csv_file():
    """創建臨時 CSV 檔案"""
    with tempfile.NamedTemporaryFile(mode='w', suffix='.csv', delete=False, encoding='utf-8') as f:
        f.write(SAMPLE_CSV_DATA)
        temp_path = f.name
    
    yield temp_path
    
    # 清理
    if os.path.exists(temp_path):
        os.unlink(temp_path)

@pytest.fixture
def temp_txt_file():
    """創建臨時 TXT 檔案"""
    with tempfile.NamedTemporaryFile(mode='w', suffix='.txt', delete=False, encoding='utf-8') as f:
        f.write(SAMPLE_TXT_DATA)
        temp_path = f.name
    
    yield temp_path
    
    # 清理
    if os.path.exists(temp_path):
        os.unlink(temp_path)

@pytest.fixture
def temp_directory():
    """創建臨時目錄"""
    temp_dir = tempfile.mkdtemp()
    yield temp_dir
    shutil.rmtree(temp_dir)

@pytest.fixture
def mock_discord_interaction():
    """模擬 Discord 互動"""
    interaction = Mock()
    interaction.response = AsyncMock()
    interaction.followup = AsyncMock()
    interaction.edit_original_response = AsyncMock()
    interaction.user = Mock()
    interaction.user.id = 12345
    interaction.user.name = "TestUser"
    return interaction

@pytest.fixture
def mock_discord_bot():
    """模擬 Discord 機器人"""
    bot = Mock()
    bot.get_channel = Mock()
    bot.get_user = Mock()
    return bot

@pytest.fixture
def event_loop():
    """創建事件循環"""
    loop = asyncio.new_event_loop()
    yield loop
    loop.close()

class AsyncContextManager:
    """異步上下文管理器輔助類"""
    def __init__(self, async_func):
        self.async_func = async_func
    
    async def __aenter__(self):
        return await self.async_func()
    
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        pass

def create_mock_file_attachment(filename: str, content: bytes):
    """創建模擬的 Discord 檔案附件"""
    attachment = Mock()
    attachment.filename = filename
    attachment.size = len(content)
    attachment.read = AsyncMock(return_value=content)
    return attachment
