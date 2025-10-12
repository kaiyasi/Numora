# Serelix Studio 貢獻指南（Contributing Guidelines）

感謝您對 Serelix Studio 專案的關注與支持。
為確保所有貢獻能順利整合並維持高品質，我們制定以下貢獻流程與準則。

---

一、參與方式

您可以透過以下方式貢獻本專案：
- 提交程式碼改進（新增功能、修正錯誤、效能優化等）
- 改善文件內容（README、教學文件、註解等）
- 回報問題與提出改進建議
- 協助測試、驗證或翻譯

在提交前，請先閱讀本文件與專案的 CODE_OF_CONDUCT.md。

---

二、回報問題（Issues）

若發現錯誤、漏洞或使用疑慮，請先確認以下事項：
1. 已搜尋過現有討論，確定問題尚未被提出。
2. 提供明確的重現步驟、環境資訊與錯誤訊息。
3. 若為安全性問題，**請勿公開發佈**，改以電子郵件方式通報（見下方聯繫方式）。

建議格式（如需貼上請將內部反引號符號替換為正常程式區段）：
```
### 問題描述
（清楚描述遇到的問題）

### 重現步驟
1. …
2. …
3. …

### 預期結果
（說明您認為應該出現的正確行為）

### 實際結果
（附上錯誤訊息或截圖）
```

---

三、提交變更（Pull Requests）

1. Fork 與分支
- 請先 Fork 本專案至您的帳號。
- 建立新分支進行開發： feature/<描述> 或 fix/<描述>
  例： feature/forum-post-editor 或 fix/socket-timeout-bug

2. Commit 規範
每次提交訊息應簡潔且具描述性，建議格式如下：
```
add: 實作文章編輯模組
fix: 修正登入時 Token 驗證錯誤
docs: 更新 API 說明文件
refactor: 重構使用者資料處理流程
```
請避免使用「update」「change」等無意義訊息。

3. Pull Request 說明
開啟 PR 時，請於描述中包含：
- 變更目的與背景
- 主要修改項目
- 驗證方式或測試結果
- 影響範圍（是否改動核心功能）

---

四、程式風格

為保持一致性，請遵循以下格式規範：

| 語言 | 標準 |
|------|------|
| Python | PEP8、Black 自動格式化 |
| JavaScript / TypeScript | ESLint、Prettier |
| Markdown / 文件 | 使用 UTF-8、每行寬度 ≤ 100 字元 |

在提交前請確保所有檔案皆通過自動化檢查或 Linter。

---

五、測試與驗證

- 若您的變更涉及邏輯或功能修改，請新增或更新對應的測試案例。
- 所有測試應能通過 CI/CD 或本地環境測試指令。
- 若修改影響外部 API，請於文件中同步更新介面說明與參數格式。

---

六、授權與貢獻歸屬

所有貢獻皆將遵循專案主要授權條款（見 LICENSE）。
提交 Pull Request 即代表您同意授予 Serelix Studio 使用與再發佈該內容的權利。
我們會在貢獻記錄與發布說明中感謝所有貢獻者。

---

七、聯繫與支援

若您有任何疑問、建議或需要私下通報問題，請聯繫：
- :e_mail: 電子郵件：serelixstudio@gmail.com
- :speech_balloon: 官方社群：Serelix Studio Discord — https://discord.gg/eRfGKepusP
- :technologist: 工作室首席工程師：kaiyasi — https://discord.com/users/kaiyasi

---

八、感謝您的貢獻

每一位貢獻者都是 Serelix Studio 成長的一部分。
感謝您願意投入時間與心力，讓這個專案更好。
---