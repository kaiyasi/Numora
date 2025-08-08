# 犯罪案件統計 Discord Bot

一個功能強大的 Discord 機器人，用於分析和視覺化犯罪案件統計數據。支援 CSV 檔案上傳、地區篩選、年份分析和圖表生成。

## 功能特色

### 📊 數據分析
- **CSV 檔案上傳**：支援上傳自定義犯罪數據
- **多格式支援**：自動檢測編碼（UTF-8、Big5、CP950等）
- **智能欄位映射**：自動識別日期、地點、案類等欄位

### 🗺️ 地區分析
- **精確地址解析**：智能提取市、縣、區、鄉、鎮資訊
- **多層級篩選**：支援台北市、新竹縣、台北市中山區等不同層級
- **避免誤判**：防止里名中的「市」字被誤認為行政區劃

### 📈 圖表生成
- **年度統計圖**：特定地區和年份的案件分佈
- **排名熱點圖**：前5/10/15/20名案件熱點地區
- **全年度統計**：跨年度的趨勢分析圖表
- **中文字型支援**：完美顯示繁體中文

### 🎯 互動介面
- **下拉選單**：直觀的地區和年份選擇
- **動態按鈕**：快速生成不同排名的統計圖
- **即時更新**：選擇變更時即時更新圖表

## 指令列表

| 指令 | 描述 | 用法 |
|------|------|------|
| `/upload` | 上傳 CSV 檔案 | 附加檔案上傳 |
| `/summary` | 顯示統計總覽 | 選擇地區和年份查看圖表 |
| `/rank` | 地區排名統計 | 選擇地區查看熱點排名 |
| `/stats` | 詳細統計資料 | 顯示完整數據概覽 |
| `/clear` | 清除上傳資料 | 返回使用預設資料 |
| `/search` | 查詢特定案件資料 | 提供關鍵字或條件進行查詢 |
| `/filter` | 篩選案件資料 | 按案件類型、時間段等進行篩選 |

## 安裝指南

### 前置需求
- Python 3.8+
- Discord 開發者帳號
- Bot Token

### 本地安裝

1. **克隆專案**
```bash
git clone https://github.com/your-username/discord-crime-bot.git
cd discord-crime-bot
```

2. **安裝依賴**
```bash
pip install -r requirements.txt
```

3. **設定環境變數**
建立 `.env` 檔案：
```env
DISCORD_TOKEN=your_discord_bot_token_here
```

4. **準備資料檔案**
將犯罪數據放在 `crime_data.txt`（可選）

5. **執行機器人**
```bash
python main.py
```

### 雲端部署

#### Railway（推薦）
1. Fork 此專案到你的 GitHub
2. 連接 Railway 到你的 GitHub 帳號
3. 選擇此專案進行部署
4. 設定環境變數 `DISCORD_TOKEN`
5. 部署完成！

#### Render
1. 連接 GitHub 專案到 Render
2. 選擇 Web Service
3. 設定環境變數
4. 部署啟動

## 檔案格式

### CSV 檔案要求
支援的欄位名稱：

| 必要欄位 | 可接受的欄位名稱 |
|----------|------------------|
| 編號 | 編號, ID, id, 序號, No, number |
| 案類 | 案類, 案件類型, 類型, Type, type |
| 日期 | 日期, 發生日期, 時間, Date, date |
| 時段 | 時段, 時間段, 發生時段, Time, time |
| 地點 | 地點, 發生地點, 位置, Location, location |

### 地址格式範例
```
臺北市中正區忠孝東路1段
新竹縣竹北市成功路
高雄市鳳山區建國路
```

## 技術架構

### 核心技術
- **Discord.py 2.3+**：Discord API 互動
- **Pandas 2.0+**：數據處理和分析
- **Matplotlib 3.7+**：圖表生成和視覺化
- **Chardet 5.0+**：字元編碼檢測

### 功能模組
- `extract_area_info()`：地區資訊提取
- `extract_district_by_area()`：行政區分析
- `generate_area_year_plot()`：年度統計圖
- `generate_area_rank_plot()`：排名圖表
- `generate_yearly_plot()`：全年度趨勢圖

## 專案結構

```
discord-crime-bot/
├── main.py                 # 主程式檔案
├── requirements.txt        # Python 依賴
├── Procfile                # 部署配置
├── .env.example           # 環境變數範例
├── crime_data.txt         # 預設數據檔案（可選）
├── README.md              # 說明文件
└── .gitignore             # Git 忽略檔案
```

## 貢獻指南

歡迎提交 Issue 和 Pull Request！

### 開發環境設定
1. Fork 此專案
2. 建立功能分支：`git checkout -b feature/amazing-feature`
3. 提交變更：`git commit -m 'Add amazing feature'`
4. 推送分支：`git push origin feature/amazing-feature`
5. 開啟 Pull Request

### 程式碼規範
- 使用中文註解
- 遵循 PEP 8 編碼規範
- 新增功能需包含錯誤處理

## 授權條款

此專案採用 MIT 授權條款 - 詳見 [LICENSE](LICENSE) 檔案

## 更新日誌

### v1.0.0
- ✅ 基本 Discord 指令功能
- ✅ CSV 檔案上傳和解析
- ✅ 地區智能識別
- ✅ 多種圖表生成
- ✅ 中文字型支援

## 支援

如果遇到問題或有建議，請：
1. 查看 [常見問題](#常見問題)
2. 提交 [Issue](https://github.com/your-username/discord-crime-bot/issues)
3. 參與 [討論](https://github.com/your-username/discord-crime-bot/discussions)

## 常見問題

**Q: 圖表顯示中文亂碼怎麼辦？**
A: 確保系統已安裝中文字型，如 Microsoft JhengHei 或 SimHei。

**Q: CSV 上傳失敗？**
A: 檢查檔案格式是否正確，確保包含必要欄位。

**Q: 地區識別不正確？**
A: 確保地址格式為「市區」或「縣市」的標準格式。

---

