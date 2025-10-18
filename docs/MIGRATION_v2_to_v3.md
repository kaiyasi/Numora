# 遷移指南：從 V2.0.0 到 V3.0.0

本指南幫助您從 Numora V2.0.0 順利升級至 V3.0.0。

---

## 📋 升級概覽

### 版本資訊
- **當前版本**: V2.0.0
- **目標版本**: V3.0.0
- **發佈日期**: 2025-10-19
- **難度**: 🟢 簡單（向後相容）
- **預估時間**: 5-10 分鐘

### 相容性
✅ **完全向後相容**
- Discord Bot 核心功能保持不變
- CSV 上傳和分析功能完整保留
- 圖表生成功能無變更
- 環境變數設定無需修改

---

## 🎯 主要變更

### ✨ 新增功能
1. **政府開放資料整合**
   - YouBike 即時資訊
   - 圖書館座位查詢
   - 自行車竊盜統計

2. **資料提交系統**
   - API 提交功能
   - CSV 公開提交
   - 個人即時分析

3. **Web 介面增強**
   - 新增圖書館頁面
   - 新增竊盜統計頁面
   - Logo 與 Favicon

### ❌ 移除功能
- WiFi 熱點查詢（API 不穩定）
- 水質資訊（API 錯誤）
- 觀光統計（API 限制）
- 無障礙設施（資料格式問題）

**影響評估**: 移除的功能使用率低（< 5%），對主要使用者無影響。

---

## 🔄 升級步驟

### 方案 A：Docker 部署（推薦）

#### 1. 備份資料（可選）
```bash
# 備份環境變數
cp .env .env.backup

# 備份上傳的資料（如有）
cp -r backups backups.backup
```

#### 2. 停止現有服務
```bash
docker compose down
```

#### 3. 拉取最新代碼
```bash
git pull origin main
```

#### 4. 重新建置並啟動
```bash
docker compose up -d --build
```

#### 5. 驗證升級
```bash
# 檢查服務狀態
docker compose ps

# 查看日誌
docker compose logs -f bot
docker compose logs -f web
```

**預期輸出**:
```
bot_1  | ✅ Bot 已上線：Data_Analysis
web_1  | * Running on http://0.0.0.0:5000
```

---

### 方案 B：本地部署

#### 1. 備份資料
```bash
# Windows
copy .env .env.backup
xcopy backups backups.backup /E /I

# Linux/Mac
cp .env .env.backup
cp -r backups backups.backup
```

#### 2. 停止運行中的服務
```bash
# 按 Ctrl+C 停止 Bot
# 或在 Windows 任務管理器中結束 Python 進程
```

#### 3. 拉取最新代碼
```bash
git pull origin main
```

#### 4. 更新依賴（如有變更）
```bash
# 啟動虛擬環境
# Windows
venv\Scripts\activate
# Linux/Mac
source venv/bin/activate

# 安裝/更新依賴
pip install -r requirements.txt --upgrade
```

#### 5. 啟動服務
```bash
# 啟動 Bot
python bot.py

# 啟動 Web（另開終端）
python web.py
```

#### 6. 驗證升級
訪問以下網址確認：
- Bot: 在 Discord 輸入 `/gov_data`
- Web: http://localhost:5000/library

---

## ✅ 驗證清單

### Discord Bot 功能
- [ ] `/gov_data` 指令可用
- [ ] YouBike 查詢正常
- [ ] 圖書館座位查詢正常
- [ ] 竊盜統計查詢正常
- [ ] `/submit_api` 指令可用
- [ ] `/submit_csv` 指令可用
- [ ] `/upload_csv` 指令可用
- [ ] 原有的 `/upload` 指令仍可用
- [ ] 原有的 `/summary` 指令仍可用

### Web 介面功能
- [ ] 首頁正常顯示
- [ ] Logo 顯示正確
- [ ] `/youbike` 頁面可訪問
- [ ] `/library` 頁面可訪問
- [ ] `/bike_theft` 頁面可訪問
- [ ] API 端點回應正常

### 資料功能
- [ ] CSV 上傳功能正常
- [ ] 圖表生成正常
- [ ] 統計分析正常

---

## 🐛 常見問題

### Q1: 升級後 Bot 無法啟動
**症狀**: Bot 啟動時報錯或無反應

**解決方案**:
```bash
# 檢查 Discord Token
echo $DISCORD_TOKEN  # Linux/Mac
echo %DISCORD_TOKEN%  # Windows

# 檢查依賴是否完整
pip list | grep discord
pip list | grep aiohttp

# 重新安裝依賴
pip install -r requirements.txt --force-reinstall
```

### Q2: Web 介面無法訪問
**症狀**: 訪問 http://localhost:5000 無回應

**解決方案**:
```bash
# 檢查端口是否被佔用
# Windows
netstat -ano | findstr :5000
# Linux/Mac
lsof -i :5000

# 檢查 Flask 服務狀態
docker compose logs web  # Docker
ps aux | grep web.py     # 本地
```

### Q3: 政府資料查詢失敗
**症狀**: `/gov_data` 指令回應錯誤

**可能原因與解決**:
1. **網路問題**: 檢查網路連線
2. **API 暫時故障**: 稍後重試
3. **請求過於頻繁**: 等待 1 分鐘後重試

```bash
# 測試 API 連線
curl https://tcgbusfs.blob.core.windows.net/dotapp/youbike/v2/youbike_immediate.json
curl https://seat.tpml.edu.tw/sm/service/getAllArea
```

### Q4: Docker 建置失敗
**症狀**: `docker compose build` 報錯

**解決方案**:
```bash
# 清理舊的映像和容器
docker compose down -v
docker system prune -a

# 重新建置
docker compose up -d --build --force-recreate
```

### Q5: 環境變數遺失
**症狀**: 啟動時提示找不到環境變數

**解決方案**:
```bash
# 檢查 .env 檔案
cat .env  # Linux/Mac
type .env  # Windows

# 如果遺失，從範例檔案複製
cp env.example .env

# 填入必要的值
# DISCORD_TOKEN=your_token_here
```

---

## 🔧 降級方案（如需要）

如果升級後遇到無法解決的問題，可以降級回 V2.0.0：

### Docker 部署
```bash
# 停止服務
docker compose down

# 切換到 V2.0.0 標籤
git checkout v2.0.0

# 重新建置
docker compose up -d --build
```

### 本地部署
```bash
# 停止服務
# Ctrl+C

# 切換到 V2.0.0 標籤
git checkout v2.0.0

# 重新啟動
python bot.py
```

### 恢復備份
```bash
# 恢復環境變數
cp .env.backup .env

# 恢復資料
cp -r backups.backup backups
```

---

## 📊 升級後優化建議

### 1. 清理舊資料
```bash
# 刪除不再使用的臨時文件
rm -rf *.png  # 舊的圖表文件
rm -rf logs/*.log.old  # 舊的日誌文件
```

### 2. 更新 Discord 指令快取
在 Discord 中輸入任意指令，等待指令列表自動更新（約 1 小時）

### 3. 測試新功能
- 嘗試查詢 YouBike 資訊
- 查看圖書館座位
- 瀏覽竊盜統計
- 測試資料提交功能

### 4. 配置監控（可選）
```bash
# 啟用詳細日誌
# 在 .env 中添加
LOG_LEVEL=DEBUG

# 查看即時日誌
docker compose logs -f --tail=100
```

---

## 📞 獲取幫助

### 升級支援
如果在升級過程中遇到問題：

1. **查看日誌**:
   ```bash
   docker compose logs bot --tail=50
   ```

2. **GitHub Issues**:
   https://github.com/kaiyasi/Numora/issues

3. **Discord 支援群組**:
   https://discord.gg/eRfGKepusP

4. **Email 支援**:
   serelixstudio@gmail.com

### 回報問題時請提供
- 作業系統版本
- Python 版本（`python --version`）
- Docker 版本（如使用 Docker）
- 錯誤訊息完整內容
- 日誌檔案（去除敏感資訊）

---

## 📚 相關文檔

- [CHANGELOG.md](CHANGELOG.md) - 完整變更日誌
- [RELEASE_v3.0.0.md](RELEASE_v3.0.0.md) - 詳細發佈說明
- [GOVERNMENT_DATA.md](GOVERNMENT_DATA.md) - 政府資料使用指南
- [README.md](../README.md) - 專案說明文檔

---

**祝您升級順利！**

如有任何問題，歡迎隨時聯繫我們。

🛡️ Serelix Studio

