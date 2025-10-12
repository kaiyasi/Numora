# API 文檔

## 概述

犯罪案件統計 Discord Bot 提供了完整的 RESTful API 和 Discord Slash Commands，用於處理犯罪案件資料分析和視覺化。

## Discord Slash Commands

### 基本指令

#### `/upload`
上傳 CSV 檔案進行分析

**參數：**
- `file` (attachment): 要上傳的 CSV 檔案

**支援格式：**
- 編碼：UTF-8, Big5, CP950, GBK 等
- 檔案大小：最大 50MB
- 必要欄位：編號、案類、日期、時段、地點

**回應：**
```json
{
  "status": "success",
  "message": "CSV 檔案上傳成功",
  "data": {
    "filename": "crime_data.csv",
    "total_records": 1000,
    "year_range": "2020 - 2023",
    "available_areas": ["台北市", "新北市", "台中市"]
  }
}
```

#### `/summary`
顯示統計總覽並提供互動式圖表選擇

**功能：**
- 基本統計資訊顯示
- 地區選擇下拉選單
- 年份選擇下拉選單
- 即時圖表生成

#### `/rank`
顯示地區排名統計

**功能：**
- 地區選擇
- 排名數量選擇（前5/10/15/20名）
- 熱點地區分析

#### `/stats`
顯示詳細統計資料

**回應包含：**
- 基本資訊統計
- 可用地區列表
- 前10大案件類型
- 年份分布統計

#### `/clear`
清除已上傳的資料，回復使用預設資料

### 進階指令

#### `/predict`
使用機器學習模型預測犯罪趨勢

**參數：**
- `area` (string): 預測地區
- `years` (string): 預測年份（逗號分隔）

**範例：**
```
/predict area:台北市 years:2024,2025,2026
```

#### `/subscribe`
訂閱即時通知

**參數：**
- `types` (string): 通知類型（逗號分隔）
- `areas` (string, optional): 關注地區（逗號分隔）

**通知類型：**
- `data_update`: 資料更新通知
- `high_crime_alert`: 高犯罪率警告
- `trend_analysis`: 趨勢分析通知
- `weekly_report`: 週報
- `monthly_report`: 月報

#### `/unsubscribe`
取消訂閱通知

**參數：**
- `types` (string, optional): 要取消的通知類型

## Web API 端點

### 基礎端點

#### `GET /`
首頁

#### `GET /dashboard`
儀表板頁面，顯示統計概覽和圖表

#### `GET /analysis`
分析頁面，提供進階分析工具

#### `GET /prediction`
預測頁面，提供機器學習預測功能

### API 端點

#### `GET /api/data`
取得統計資料

**回應：**
```json
{
  "總案件數": 5000,
  "年份範圍": "2020 - 2023",
  "可用地區": {
    "市區": ["台北市中山區", "台北市信義區"],
    "縣市": ["新竹縣竹北市", "彰化縣員林市"]
  },
  "年份統計": {
    "2020": 1200,
    "2021": 1300,
    "2022": 1250,
    "2023": 1250
  },
  "案類統計": {
    "竊盜": 2000,
    "詐欺": 1500,
    "傷害": 800
  }
}
```

#### `GET /api/charts/{chart_type}`
取得圖表資料

**支援的圖表類型：**
- `yearly_trend`: 年度趨勢圖
- `area_distribution`: 地區分布圖
- `case_type_pie`: 案件類型圓餅圖
- `time_heatmap`: 時段熱力圖

**查詢參數：**
- `area` (string, optional): 篩選地區
- `year` (int, optional): 篩選年份

**範例：**
```
GET /api/charts/yearly_trend?area=台北市&year=2023
```

**回應：**
```json
{
  "data": [{
    "x": [2020, 2021, 2022, 2023],
    "y": [1200, 1300, 1250, 1250],
    "type": "scatter",
    "mode": "lines+markers"
  }],
  "layout": {
    "title": "台北市 - 年度案件趨勢",
    "xaxis": {"title": "年份"},
    "yaxis": {"title": "案件數"}
  }
}
```

#### `GET /api/prediction`
機器學習預測

**查詢參數：**
- `area` (string): 預測地區
- `years` (array): 預測年份列表

**範例：**
```
GET /api/prediction?area=台北市&years=2024&years=2025&years=2026
```

**回應：**
```json
{
  "area": "台北市",
  "predictions": {
    "2024": 1280,
    "2025": 1300,
    "2026": 1320
  },
  "feature_importance": {
    "年份": 0.6,
    "地區_encoded": 0.4
  },
  "model_accuracy": {
    "mae": 45.2,
    "r2": 0.85
  }
}
```

#### `GET /api/areas`
取得可用地區列表

**回應：**
```json
{
  "市區": ["台北市中山區", "台北市信義區", "台北市大安區"],
  "縣市": ["新竹縣竹北市", "彰化縣員林市"],
  "縣鄉": ["南投縣埔里鄉", "苗栗縣頭份鄉"],
  "縣鎮": ["彰化縣員林鎮", "雲林縣斗六鎮"]
}
```

## 資料格式

### CSV 檔案格式

支援的欄位名稱映射：

| 標準欄位 | 可接受的欄位名稱 |
|----------|------------------|
| 編號 | 編號, ID, id, 序號, No, number |
| 案類 | 案類, 案件類型, 類型, Type, type, 案件類別 |
| 日期 | 日期, 發生日期, 時間, Date, date, 發生(現)日期 |
| 時段 | 時段, 時間段, 發生時段, Time, time |
| 地點 | 地點, 發生地點, 位置, Location, location, 地址 |

### 日期格式

支援多種日期格式：
- 民國年：`1120101` (112年1月1日)
- 西元年：`2023-01-01`, `20230101`
- ISO 格式：`2023-01-01T00:00:00`

### 地址格式

支援的地址格式：
- 市區：`台北市中山區民權東路`
- 縣市：`新竹縣竹北市成功路`
- 縣鄉：`南投縣埔里鄉中山路`
- 縣鎮：`彰化縣員林鎮民權路`

## 錯誤處理

### 錯誤代碼

| 代碼 | 描述 |
|------|------|
| 400 | 請求參數錯誤 |
| 404 | 資源不存在 |
| 413 | 檔案過大 |
| 422 | 資料格式錯誤 |
| 500 | 伺服器內部錯誤 |

### 錯誤回應格式

```json
{
  "error": {
    "code": 400,
    "message": "請求參數錯誤",
    "details": "缺少必要欄位：編號"
  }
}
```

## 限制

- 檔案大小：最大 50MB
- API 請求頻率：每分鐘 60 次
- 同時處理的圖表：最多 5 個
- 預測年份範圍：最多未來 10 年

## 驗證

目前 API 不需要驗證，但建議在生產環境中實施適當的驗證機制。

## 範例程式碼

### Python 範例

```python
import requests
import json

# 取得統計資料
response = requests.get('http://localhost:5000/api/data')
data = response.json()
print(f"總案件數: {data['總案件數']}")

# 取得年度趨勢圖表
chart_response = requests.get(
    'http://localhost:5000/api/charts/yearly_trend',
    params={'area': '台北市'}
)
chart_data = chart_response.json()

# 預測犯罪趨勢
prediction_response = requests.get(
    'http://localhost:5000/api/prediction',
    params={
        'area': '台北市',
        'years': [2024, 2025, 2026]
    }
)
predictions = prediction_response.json()
```

### JavaScript 範例

```javascript
// 取得統計資料
fetch('/api/data')
  .then(response => response.json())
  .then(data => {
    console.log('總案件數:', data.總案件數);
  });

// 載入圖表
fetch('/api/charts/yearly_trend?area=台北市')
  .then(response => response.json())
  .then(chartData => {
    Plotly.newPlot('chart-div', chartData.data, chartData.layout);
  });
```
