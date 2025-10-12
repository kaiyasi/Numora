# 開發者指南

## 專案結構

```
Data_Analysis/
├── src/                          # 源碼目錄
│   ├── bot/                      # Discord 機器人模組
│   │   ├── __init__.py
│   │   ├── client.py            # 機器人客戶端
│   │   ├── commands.py          # 指令處理
│   │   └── views.py             # UI 元件
│   ├── data/                     # 資料處理模組
│   │   ├── __init__.py
│   │   ├── processor.py         # 資料處理器
│   │   └── area_analyzer.py     # 地區分析器
│   ├── charts/                   # 圖表生成模組
│   │   ├── __init__.py
│   │   └── generator.py         # 圖表生成器
│   └── utils/                    # 工具模組
│       ├── __init__.py
│       ├── config.py            # 配置管理
│       ├── logger.py            # 日誌配置
│       ├── ml_predictor.py      # 機器學習預測
│       ├── notification_system.py # 通知系統
│       └── web_interface.py     # Web 介面
├── tests/                        # 測試目錄
│   ├── conftest.py              # 測試配置
│   ├── test_data_processor.py   # 資料處理測試
│   └── test_area_analyzer.py    # 地區分析測試
├── docs/                         # 文檔目錄
│   ├── API.md                   # API 文檔
│   └── DEVELOPMENT.md           # 開發者指南
├── templates/                    # Web 模板
├── static/                       # 靜態檔案
├── logs/                         # 日誌檔案
├── models/                       # ML 模型檔案
├── backups/                      # 備份檔案
├── main.py                       # 原始主程式（向後相容）
├── bot.py                        # 新版主程式入口
├── requirements.txt              # Python 依賴
├── Procfile                      # 部署配置
├── env.example                   # 環境變數範例
├── .gitignore                    # Git 忽略檔案
├── README.md                     # 專案說明
└── LICENSE                       # 授權條款
```

## 開發環境設定

### 1. 環境需求

- Python 3.8+
- Git
- Discord 開發者帳號

### 2. 克隆專案

```bash
git clone https://github.com/your-username/crime-statistics-discord-bot.git
cd crime-statistics-discord-bot
```

### 3. 建立虛擬環境

```bash
python -m venv venv

# Windows
venv\Scripts\activate

# macOS/Linux
source venv/bin/activate
```

### 4. 安裝依賴

```bash
pip install -r requirements.txt
```

### 5. 環境變數設定

複製 `env.example` 為 `.env` 並填入相關資訊：

```bash
cp env.example .env
```

編輯 `.env` 檔案：

```env
DISCORD_TOKEN=your_discord_bot_token_here
DEBUG=True
ADMIN_CHANNEL_ID=your_admin_channel_id
```

### 6. 執行機器人

```bash
# 使用新版模組化架構
python bot.py

# 或使用原始版本（向後相容）
python main.py
```

## 核心模組說明

### 1. 配置管理 (`src/utils/config.py`)

集中管理所有配置選項：

```python
from src.utils.config import config

# 取得 Discord Token
token = config.DISCORD_TOKEN

# 檢查除錯模式
if config.DEBUG:
    print("除錯模式已啟用")
```

### 2. 資料處理 (`src/data/processor.py`)

處理 CSV 檔案載入和資料清理：

```python
from src.data.processor import DataProcessor

processor = DataProcessor()

# 載入 CSV 資料
df = processor.load_csv_data(file_content)

# 生成統計資料
stats = processor.generate_statistics(df)
```

### 3. 地區分析 (`src/data/area_analyzer.py`)

分析地區資訊和行政區劃：

```python
from src.data.area_analyzer import AreaAnalyzer

analyzer = AreaAnalyzer()

# 提取地區資訊
areas_info = analyzer.extract_area_info(df)

# 按地區篩選行政區
filtered_df = analyzer.extract_district_by_area(df, '台北市')
```

### 4. 圖表生成 (`src/charts/generator.py`)

生成各種統計圖表：

```python
from src.charts.generator import ChartGenerator

generator = ChartGenerator()

# 生成年度統計圖
filename = generator.generate_area_year_plot(df, '台北市', 2023)

# 生成排名圖
filename = generator.generate_area_rank_plot(df, '台北市', 10)
```

### 5. 機器學習預測 (`src/utils/ml_predictor.py`)

提供犯罪趨勢預測功能：

```python
from src.utils.ml_predictor import CrimePredictionModel

model = CrimePredictionModel()

# 訓練模型
results = model.train_models(df)

# 預測趨勢
predictions = model.predict_crime_trends('台北市', [2024, 2025, 2026])
```

### 6. 通知系統 (`src/utils/notification_system.py`)

管理即時通知和訂閱：

```python
from src.utils.notification_system import NotificationSystem

notification_system = NotificationSystem(bot)

# 訂閱通知
notification_system.subscribe_user(
    user_id=12345,
    channel_id=67890,
    notification_types=['data_update', 'high_crime_alert'],
    areas=['台北市']
)
```

### 7. Web 介面 (`src/utils/web_interface.py`)

提供 Web 儀表板功能：

```python
from src.utils.web_interface import WebInterface

web_interface = WebInterface(data_processor)
web_interface.start_server(host='0.0.0.0', port=5000)
```

## 新增功能開發

### 1. 新增 Discord 指令

在 `src/bot/commands.py` 中新增指令：

```python
@bot.tree.command(name="new_command", description="新指令描述")
@app_commands.describe(param="參數描述")
async def new_command(interaction: discord.Interaction, param: str):
    try:
        # 指令邏輯
        await interaction.response.send_message("指令執行成功")
        logger.info(f"用戶 {interaction.user} 執行了新指令")
    except Exception as e:
        logger.error(f"執行新指令時發生錯誤: {e}")
        await interaction.response.send_message(f"❌ 錯誤：{str(e)}")
```

### 2. 新增圖表類型

在 `src/charts/generator.py` 中新增圖表生成方法：

```python
def generate_new_chart_type(self, df: pd.DataFrame, **kwargs) -> Optional[str]:
    """生成新類型圖表"""
    try:
        # 圖表生成邏輯
        fig, ax = plt.subplots(figsize=(12, 8))
        
        # 繪製圖表
        # ...
        
        filename = "new_chart.png"
        plt.savefig(filename, dpi=config.CHART_DPI, bbox_inches='tight')
        plt.close('all')
        
        return filename
    except Exception as e:
        logger.error(f"生成新圖表時發生錯誤: {e}")
        plt.close('all')
        return None
```

### 3. 新增 Web API 端點

在 `src/utils/web_interface.py` 中新增路由：

```python
@self.app.route('/api/new_endpoint')
def api_new_endpoint():
    """新的 API 端點"""
    try:
        # API 邏輯
        result = process_data()
        return jsonify({'success': True, 'data': result})
    except Exception as e:
        logger.error(f"API 處理時發生錯誤: {e}")
        return jsonify({'error': str(e)})
```

### 4. 新增通知類型

在 `src/utils/notification_system.py` 中新增通知處理：

```python
async def notify_new_event(self, event_data):
    """新事件通知"""
    try:
        message = f"新事件發生：{event_data}"
        
        for user_id, subscription in self.subscriptions.items():
            if 'new_event' in subscription['types']:
                await self.send_notification(
                    int(user_id),
                    subscription['channel_id'],
                    "🆕 新事件通知",
                    message,
                    discord.Color.blue()
                )
    except Exception as e:
        logger.error(f"發送新事件通知時發生錯誤: {e}")
```

## 測試

### 執行測試

```bash
# 執行所有測試
pytest

# 執行特定測試檔案
pytest tests/test_data_processor.py

# 執行測試並顯示覆蓋率
pytest --cov=src tests/

# 執行測試並生成 HTML 覆蓋率報告
pytest --cov=src --cov-report=html tests/
```

### 撰寫測試

在 `tests/` 目錄下創建測試檔案：

```python
import pytest
from src.your_module import YourClass

class TestYourClass:
    def setup_method(self):
        """設定測試方法"""
        self.instance = YourClass()
    
    def test_your_method(self):
        """測試您的方法"""
        result = self.instance.your_method("test_input")
        assert result == "expected_output"
    
    def test_error_handling(self):
        """測試錯誤處理"""
        with pytest.raises(ValueError):
            self.instance.your_method(None)
```

## 日誌管理

### 日誌配置

日誌系統會自動創建以下檔案：

- `logs/bot_YYYY-MM-DD.log`: 一般日誌
- `logs/error_YYYY-MM-DD.log`: 錯誤日誌

### 使用日誌

```python
import logging

logger = logging.getLogger(__name__)

# 不同等級的日誌
logger.debug("除錯資訊")
logger.info("一般資訊")
logger.warning("警告訊息")
logger.error("錯誤訊息")
logger.critical("嚴重錯誤")
```

## 效能優化

### 1. 資料處理優化

- 使用 pandas 的向量化操作
- 避免在迴圈中進行大量資料操作
- 適當使用資料索引

### 2. 圖表生成優化

- 及時關閉 matplotlib 圖形 (`plt.close('all')`)
- 使用適當的 DPI 設定
- 快取常用圖表

### 3. 記憶體管理

- 定期清理暫存檔案
- 使用 `del` 刪除不需要的大型物件
- 監控記憶體使用情況

## 部署指南

### 本地部署

```bash
# 啟動機器人
python bot.py

# 同時啟動 Web 介面（如果需要）
# Web 介面會在機器人啟動時自動啟動
```

### Docker 部署

```dockerfile
FROM python:3.9-slim

WORKDIR /app

COPY requirements.txt .
RUN pip install -r requirements.txt

COPY . .

CMD ["python", "bot.py"]
```

### 雲端部署

參考 `README.md` 中的部署指南，支援：

- Railway
- Render
- Heroku
- DigitalOcean

## 貢獻指南

### 1. Fork 專案

在 GitHub 上 fork 此專案到您的帳號。

### 2. 創建功能分支

```bash
git checkout -b feature/amazing-feature
```

### 3. 提交變更

```bash
git add .
git commit -m "Add amazing feature"
```

### 4. 推送分支

```bash
git push origin feature/amazing-feature
```

### 5. 創建 Pull Request

在 GitHub 上創建 Pull Request。

### 程式碼規範

- 使用中文註解
- 遵循 PEP 8 編碼規範
- 新增功能需包含單元測試
- 更新相關文檔

## 故障排除

### 常見問題

1. **中文字型顯示問題**
   - 確保系統已安裝中文字型
   - 檢查 `FONT_PATH` 環境變數設定

2. **CSV 檔案編碼問題**
   - 檢查檔案編碼格式
   - 確保檔案包含必要欄位

3. **圖表生成失敗**
   - 檢查資料格式是否正確
   - 確認 matplotlib 設定

4. **機器學習模型訓練失敗**
   - 檢查資料量是否足夠
   - 確認特徵欄位完整性

### 除錯技巧

1. **啟用除錯模式**
   ```env
   DEBUG=True
   ```

2. **查看詳細日誌**
   ```bash
   tail -f logs/bot_$(date +%Y-%m-%d).log
   ```

3. **使用 Python 除錯器**
   ```python
   import pdb; pdb.set_trace()
   ```

## 聯絡資訊

如有問題或建議，請：

1. 提交 [Issue](https://github.com/your-username/crime-statistics-discord-bot/issues)
2. 參與 [討論](https://github.com/your-username/crime-statistics-discord-bot/discussions)
3. 發送電子郵件至開發團隊
