---
# SECURITY.md

Serelix Studio 安全性政策（Security Policy）

---

## 一、目的

本文件說明 Serelix Studio 專案的安全性報告與處理流程。  
我們致力於確保所有使用者與貢獻者能在安全、可信賴的環境中開發與部署本專案。  
若您發現潛在漏洞、弱點或風險，請依以下方式通報。

---

## 二、支援版本（Supported Versions）

| 版本 | 支援狀態 |
|------|-----------|
| 最新主要版本 (main branch) | :white_check_mark: 仍在積極維護 |
| 過往穩定版本 (stable / legacy) | ⚠ 僅針對關鍵安全性問題提供修補 |
| 已終止維護版本 (EOL) | :x: 不再提供更新或支援 |

若不確定版本狀態，請參考各專案的 `README.md` 或發行頁面。

---

## 三、回報漏洞（Reporting a Vulnerability）

### 私下通報
若您發現安全性漏洞，請 **勿公開發佈或建立 Issue／Pull Request**。  
請透過以下安全通道私下通報：

- :e_mail: **電子郵件**：serelixstudio@gmail.com  
  請在標題中註明 `[SECURITY]`，並包含以下內容：  
  - 問題描述與影響範圍  
  - 重現步驟（如適用）  
  - 受影響的版本與環境  
  - 是否已有公開利用方式（若有，請詳細說明）

- 💬 **Discord 私訊回報**：  
  您也可直接在官方社群中以私訊方式聯絡維護團隊：  
  - 官方社群伺服器：[Serelix Studio Discord](https://discord.gg/eRfGKepusP)  
  - 工作室首席工程師：[kaiyasi](https://discord.com/users/kaiyasi)

> **提醒：** 請勿於公開頻道或討論串張貼漏洞細節，  
> 以避免潛在攻擊者利用尚未修補的弱點。

---

## 四、回應流程（Response Process）

1. **確認與回覆**：在收到通報後 48 小時內回覆，並確認漏洞細節。  
2. **評估與重現**：由維護團隊進行技術驗證與風險評估。  
3. **修補與測試**：在內部修正並進行驗證測試。  
4. **協調發布**：視情況與通報者協調公開時間。  
5. **正式公告**：於發行版本說明與安全公告中公開修補資訊。  

若問題屬於高嚴重度漏洞，我們將：
- 優先修補並於最短時間內釋出更新；
- 向所有主要用戶及部署者發出安全提醒；
- 感謝並註明通報者（除非對方要求匿名）。

---

## 五、責任揭露（Responsible Disclosure）

Serelix Studio 採取「負責任揭露」原則：
- 在漏洞修補前，請勿公開、散布或利用漏洞資訊。  
- 若漏洞已被公開利用，請即時通知我們以便緊急應對。  
- 維護團隊將在修補完成後於公告中感謝通報者的貢獻。

---

## 六、聯繫資訊

- :e_mail: **安全通報信箱**：serelixstudio@gmail.com  
- :speech_balloon: **官方社群**：[Serelix Studio Discord](https://discord.gg/eRfGKepusP)  
- :technologist: **工作室首席工程師**：[kaiyasi](https://discord.com/users/kaiyasi)

所有通報與溝通將保密處理。  
我們重視每一份回報，並感謝您協助維護專案安全。

---

## 七、法律與授權聲明

- 所有安全性通報均受 Serelix Studio 專案授權條款與貢獻政策約束。  
- 我們不對非官方修改版本或衍生專案提供安全保證。  
- 本文件改編自 OpenSSF 與 OWASP 社群安全通報範例，並依 Serelix Studio 組織政策在地化。

---

## 八、感謝

感謝所有主動回報漏洞、協助測試與改善安全性的開發者與使用者。  
您的參與讓 Serelix Studio 的專案更加可靠與安全。

---