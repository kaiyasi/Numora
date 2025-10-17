# Numora - 智能犯罪案件統計分析平台

> **由 Serelix Studio 開發的犯罪案件數據分析與視覺化系統，集成 Discord Bot 與 Web 儀表板**

[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)
[![Python](https://img.shields.io/badge/python-v3.8+-blue.svg)](https://www.python.org/downloads/)
[![Discord.py](https://img.shields.io/badge/discord.py-v2.3+-blue.svg)](https://discordpy.readthedocs.io/)
[![Docker](https://img.shields.io/badge/docker-%230db7ed.svg?style=flat&logo=docker&logoColor=white)](https://www.docker.com/)

---

## :dart: 專案特色

Numora 是一個**企業級的犯罪案件統計分析平台**，提供深度數據洞察與 AI 預測功能。

### :sparkles: 核心概念

* **:brain: AI 驅動**: 機器學習預測犯罪趨勢，提供數據洞察
* **:globe_with_meridians: 多平台整合**: Discord Bot + Web 儀表板雙重體驗
* **:chart_with_upwards_trend: 智能分析**: 自動化地區識別、趨勢分析與視覺化
* **:bell: 即時通知**: 智能警報系統，重要變化即時推送
* **:shield: 數據安全**: 完整的輸入驗證與錯誤處理機制

### :rocket: 技術架構

* **後端**: Discord.py + Flask + SQLite/PostgreSQL
* **前端**: 互動式 Web 儀表板 (Bootstrap 5 + Plotly)
* **AI/ML**: scikit-learn 機器學習預測模型
* **部署**: Docker + Docker Compose + GitHub Actions CI/CD
* **監控**: 結構化日誌 + 效能監控

---

## :zap: 功能亮點

### :chart_with_upwards_trend: **智能數據分析**
- **:file_folder: 多格式支援**: CSV, Excel, JSON 自動編碼檢測 (UTF-8, Big5, CP950)
- **:brain: 智能映射**: 自動識別欄位結構，支援中英文欄位名稱
- **:mag: 精準解析**: 智能地址解析，支援市/縣/區/鄉/鎮多層級篩選

### :robot: **AI 預測引擎**
- **:crystal_ball: 趨勢預測**: 使用隨機森林與線性回歸預測犯罪趨勢
- **:dart: 熱點分析**: 自動識別高風險地區與時段
- **:chart_with_upwards_trend: 特徵重要性**: 分析影響犯罪率的關鍵因素

### :desktop_computer: **雙平台體驗**
- **:speech_balloon: Discord Bot**: 直觀的斜線指令與互動式選單
- **:globe_with_meridians: Web 儀表板**: 現代化的響應式介面與即時圖表
- **:bell: 智能通知**: 資料更新、異常警報、定期報告推送

### :art: **視覺化圖表**
- **:bar_chart: 互動式圖表**: Plotly 支援的縮放、篩選、匯出功能
- **:world_map: 地理分析**: 地區熱力圖與分布統計
- **:calendar: 時序分析**: 年度趨勢、季節性模式、時段分析

### :classical_building: **政府資料整合**
- **:open_file_folder: 多源資料**: 整合中央與地方政府公開資料
- **:mag: 智能搜尋**: 快速搜尋相關政府資料集
- **:chart_with_upwards_trend: 綜合分析**: 跨資料源的關聯性分析
- **:globe_with_meridians: 即時更新**: 自動獲取最新政府公開資料

---

## :video_game: Discord 指令

### :beginner: 基礎指令

| 指令 | 功能描述 | 使用方式 |
|------|----------|----------|
| :inbox_tray: `/upload` | 上傳分析檔案 | 拖拽 CSV/Excel 檔案 |
| :bar_chart: `/summary` | 統計總覽 | 互動式地區年份選擇 |
| :trophy: `/rank` | 排名分析 | 熱點地區前 N 名統計 |
| :clipboard: `/stats` | 詳細數據 | 完整統計資訊展示 |
| :wastebasket: `/clear` | 清除資料 | 重置為預設數據 |

### :rocket: 進階指令

| 指令 | 功能描述 | 使用方式 |
|------|----------|----------|
| :crystal_ball: `/predict` | AI 趨勢預測 | 指定地區與預測年份 |
| :bell: `/subscribe` | 訂閱通知 | 選擇通知類型與關注地區 |
| :no_bell: `/unsubscribe` | 取消訂閱 | 管理通知偏好設定 |
| :question: `/help` | 使用說明 | 完整功能與指令介紹 |

### :classical_building: 政府資料指令

| 指令 | 功能描述 | 使用方式 |
|------|----------|----------|
| :open_file_folder: `/gov_data` | 政府資料查詢 | 互動式選單查詢各類政府資料 |
| :mag: `/gov_search` | 搜尋資料集 | 關鍵字搜尋相關政府資料集 |
| :chart_with_upwards_trend: `/gov_analysis` | 綜合分析 | 指定地區進行多資料源分析 |
| :bookmark_tabs: `/gov_datasets` | 資料集列表 | 查看所有可用的政府資料集 |

---

## :rocket: 快速開始

### :clipboard: 前置要求

* **Docker & Docker Compose** (推薦)
* 或 **Python 3.8+** + **Discord 開發者帳號**

### :whale: Docker 部署 (推薦)

1. **複製專案並進入目錄**
   ```bash
   git clone https://github.com/kaiyasi/Numora.git
   cd Numora
   ```

   2. **設定環境變數**
   ```bash
   cp env.example .env
   # 編輯 .env 檔案，填入 Discord Token
   ```

3. **啟動所有服務**
   ```bash
   docker compose up -d --build
   ```

4. **存取服務**
   - **Discord Bot**: 自動上線
   - **Web 儀表板**: http://localhost:5000
   - **API 文檔**: http://localhost:5000/docs

### :computer: 本地開發

1. **建立虛擬環境**
   ```bash
   python -m venv venv
   source venv/bin/activate  # Linux/Mac
   venv\Scripts\activate     # Windows
   ```

2. **安裝依賴套件**
   ```bash
   pip install -r requirements.txt
   ```

3. **設定環境變數**
   ```bash
   cp env.example .env
   # 填入必要的環境變數
   ```

4. **啟動應用程式**
   ```bash
   # 啟動 Discord Bot
   python bot.py
   
   # 或使用原版 (向後相容)
   python main.py
   ```

### :cloud: 雲端部署

#### Render
[![Deploy to Render](https://render.com/images/deploy-to-render-button.svg)](https://render.com/deploy?repo=https://github.com/kaiyasi/Numora)

#### Docker Hub
```bash
docker pull kaiyasi/numora:latest
docker run -e DISCORD_TOKEN=your_token kaiyasi/numora
```

2. **安裝依賴套件**

## :file_folder: 資料格式支援

### :page_facing_up: 支援的檔案格式

3. **設定環境變數**
| 格式 | 編碼支援 | 大小限制 | 特殊功能 |
|------|----------|----------|----------|
| **CSV** | UTF-8, Big5, CP950, GBK | 50MB | 自動編碼檢測 |
| **Excel** | .xlsx, .xls | 50MB | 多工作表支援 |
| **JSON** | UTF-8 | 50MB | 巢狀結構解析 |

4. **啟動應用程式**
### :label: 欄位映射規則

| 標準欄位 | 可接受的欄位名稱 |
|----------|------------------|
| **編號** | 編號, ID, id, 序號, No, number |
| **案類** | 案類, 案件類型, 類型, Type, type, 案件類別 |
| **日期** | 日期, 發生日期, 時間, Date, date, 發生(現)日期 |
| **時段** | 時段, 時間段, 發生時段, Time, time |
| **地點** | 地點, 發生地點, 位置, Location, location, 地址 |

### :round_pushpin: 地址格式範例

```
✅ 正確格式:
臺北市中正區忠孝東路1段100號
docker pull kaiyasi/numora:latest
docker run -e DISCORD_TOKEN=your_token kaiyasi/numora

❌ 不建議格式:
中正區忠孝東路 (缺少市級資訊)
*Numora by Serelix Studio - 智能犯罪案件統計分析平台* :shield: *讓數據說話，讓分析更簡單*
```
## :books: 詳細文檔

### :page_with_curl: 核心文檔
* **:gear: [API 文檔](docs/API.md)**: 完整的 API 端點說明
* **:hammer_and_wrench: [開發者指南](docs/DEVELOPMENT.md)**: 開發環境設定與貢獻指南
* **:handshake: [貢獻指南](docs/CONTRIBUTING.md)**: 如何參與專案開發
* **:shield: [安全政策](docs/SECURITY.md)**: 安全問題回報流程

### :chart_with_upwards_trend: 專案資訊
* **:memo: [更新日誌](docs/CHANGELOG.md)**: 版本變更記錄
* **:scroll: [行為準則](docs/CODE_OF_CONDUCT.md)**: 社群行為準則
* **:test_tube: [測試報告](tests/)**: 單元測試與覆蓋率報告

---

## :building_construction: 專案架構

### :file_folder: 目錄結構
```
Numora/
├── 📁 src/                     # 源碼模組
│   ├── 🤖 bot/                 # Discord 機器人
│   ├── 📊 data/                # 資料處理
│   ├── 📈 charts/              # 圖表生成  
│   └── 🛠️ utils/               # 工具模組
├── 📚 docs/                    # 完整文檔
│   ├── 📖 README.md            # 文檔索引
│   ├── ⚙️ API.md               # API 文檔
│   ├── 🛠️ DEVELOPMENT.md       # 開發指南
│   ├── 🤝 CONTRIBUTING.md      # 貢獻指南
│   ├── 🛡️ SECURITY.md          # 安全政策
│   ├── 📋 CODE_OF_CONDUCT.md   # 行為準則
│   └── 📝 CHANGELOG.md         # 更新日誌
├── 🧪 tests/                   # 測試套件
├── 🐳 docker-compose.yml       # 容器編排
├── 🚀 bot.py                   # 主程式入口
└── 📋 requirements.txt         # 依賴清單
```
### :gear: 核心技術棧

| 類別 | 技術選擇 | 版本要求 | 用途說明 |
|------|----------|----------|----------|
| **Discord** | discord.py | 2.3+ | Discord API 互動 |
| **數據處理** | pandas, numpy | 2.0+ | 資料分析與處理 |
| **機器學習** | scikit-learn | 1.3+ | AI 預測模型 |
| **視覺化** | matplotlib, plotly | 3.7+ | 圖表生成 |
| **Web 框架** | Flask | 2.3+ | Web 儀表板 |
| **資料庫** | SQLite/PostgreSQL | - | 資料儲存 |
| **HTTP 客戶端** | aiohttp | 3.8+ | 政府 API 串接 |
| **資料解析** | beautifulsoup4, lxml | 4.12+ | 網頁資料解析 |

---

## :page_facing_up: 授權條款

此專案採用 **MIT 授權條款** - 詳見 [LICENSE](LICENSE) 檔案

---

## :telephone_receiver: 支援與聯繫

### :bug: 問題回報與建議
* **:octocat: GitHub Issues**: [問題回報](https://github.com/kaiyasi/Numora/issues)
* **:speech_balloon: GitHub Discussions**: [功能討論](https://github.com/kaiyasi/Numora/discussions)
* **:shield: 安全問題**: 請參考 [安全政策](docs/SECURITY.md) 私下回報

### :busts_in_silhouette: 社群交流
* **:loudspeaker: 官方 Discord 群組**: [SerelixStudio_Discord](https://discord.gg/eRfGKepusP)
* **:camera_with_flash: 官方 IG**: [SerelixStudio_IG](https://www.instagram.com/serelix_studio?igsh=eGM1anl3em1xaHZ6&utm_source=qr)
* **:e_mail: 官方 Gmail**: [serelixstudio@gmail.com](mailto:serelixstudio@gmail.com)

### :star: 專案連結
* **:octocat: GitHub 專案**: [https://github.com/kaiyasi/Numora](https://github.com/kaiyasi/Numora)
* **:globe_with_meridians: 專案網站**: [https://kaiyasi.github.io/Numora](https://kaiyasi.github.io/Numora)
* **:book: 線上文檔**: [https://kaiyasi.github.io/Numora/docs](https://kaiyasi.github.io/Numora/docs)

---

## :trophy: 貢獻者

感謝所有為此專案做出貢獻的開發者！

[![Contributors](https://contrib.rocks/image?repo=kaiyasi/Numora)](https://github.com/kaiyasi/Numora/graphs/contributors)

### :handshake: 如何貢獻

我們歡迎各種形式的貢獻！請查看我們的 [貢獻指南](docs/CONTRIBUTING.md) 了解詳細資訊。

1. :fork_and_knife: **Fork 專案**
2. :herb: **創建功能分支**: `git checkout -b feature/amazing-feature`
3. :white_check_mark: **提交變更**: `git commit -m 'Add amazing feature'`
4. :arrow_up: **推送分支**: `git push origin feature/amazing-feature`
5. :arrow_right: **開啟 Pull Request**

---

## :memo: 版本資訊

### :rocket: 最新版本: v2.0.0

**主要更新：**
- :brain: 新增 AI 預測功能
- :globe_with_meridians: 全新 Web 儀表板
- :bell: 即時通知系統
- :test_tube: 完整測試框架
- :whale: Docker 容器化支援

查看完整 [更新日誌](docs/CHANGELOG.md) 了解所有變更。

### :chart_with_upwards_trend: 專案統計

![GitHub stars](https://img.shields.io/github/stars/kaiyasi/Numora?style=social)
![GitHub forks](https://img.shields.io/github/forks/kaiyasi/Numora?style=social)
![GitHub issues](https://img.shields.io/github/issues/kaiyasi/Numora)
![GitHub pull requests](https://img.shields.io/github/issues-pr/kaiyasi/Numora)

---

*Numora by Serelix Studio - 智能犯罪案件統計分析平台* :shield: *讓數據說話，讓分析更簡單*

