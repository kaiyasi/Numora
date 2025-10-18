"""
政府公開資料 API 配置
包含各政府機關的 API 端點和資料集資訊
"""

# 政府資料開放平臺主要端點（注意：這是資料集頁面前綴，不是機器可直接讀取的 API）
GOV_DATA_BASE_URL = "https://data.gov.tw/dataset/"

# 各縣市政府 API 端點 - 已校正為實際可用的入口
CITY_APIS = {
    "taipei": {
        "name": "台北市政府",
        "base_url": "https://data.taipei/",  # 台北多為資料資源直鏈；若要 CKAN action 再自行接 /api/3/action/
        "description": "台北市政府資料開放平臺（以資源直鏈為主，部分提供 CKAN action）",
        "verified": True
    },
    "new_taipei": {
        "name": "新北市政府",
        "base_url": "https://data.ntpc.gov.tw",  # 官方入口；實際資源依 OpenAPI/資源路徑呼叫
        "description": "新北市政府資料開放平臺（提供 OpenAPI 與資料資源直取）",
        "verified": True
    },
    "taichung": {
        "name": "台中市政府",
        "base_url": "https://datacenter.taichung.gov.tw/swagger/api-docs/",
        "description": "台中市資料中心 OpenAPI 文件入口",
        "verified": True
    },
    "kaohsiung": {
        "name": "高雄市政府",
        "base_url": "https://data.kcg.gov.tw/",  # CKAN 站台根；如需 CKAN Action：/api/3/action/...
        "description": "高雄市政府資料開放平臺（CKAN）",
        "verified": True
    },
    "taoyuan": {
        "name": "桃園市政府",
        "base_url": "https://opendata.tycg.gov.tw/api-docs",  # 新版 OpenAPI 文件入口
        "description": "桃園市政府資料開放平臺（OpenAPI 文件）",
        "verified": True
    }
}

# 中央政府機關 API - 實際可用的端點
CENTRAL_APIS = {
    "weather": {
        "name": "中央氣象署",
        "base_url": "https://opendata.cwb.gov.tw/api/v1/rest/datastore/",
        "description": "中央氣象署開放資料平臺",
        "auth_required": True,
        "verified": True
    },
    "transport": {
        "name": "交通部運研所",
        "base_url": "https://tisvcloud.freeway.gov.tw/",
        "description": "交通資訊服務雲（歷史 TDCS 為 CSV 目錄）",
        "auth_required": False,
        "verified": True
    },
    "health": {
        "name": "衛生福利部",
        "base_url": "https://data.gov.tw/dataset/",
        "description": "衛生福利部資料（透過政府開放平臺索引）",
        "verified": True
    }
}

# 實際可用的資料集 - 經過校正
VERIFIED_DATASETS = {
    # 台北市實際可用資料集
    "taipei_youbike": {
        "id": "ddb80380-f1b3-4f8e-8c47-7b0eb6a44132",
        "name": "YouBike 2.0 即時資訊",
        "agency": "台北市政府",
        "update_frequency": "即時",
        "description": "YouBike 2.0 各站點即時車輛數量",
        # 實際可直接 GET 的 JSON 資源（Azure Blob）
        "api_url": "https://tcgbusfs.blob.core.windows.net/dotapp/youbike/v2/youbike_immediate.json",
        "format": "JSON",
        "verified": True
    },
    "taipei_wifi": {
        "id": "f37de02a-623d-4f72-bca9-7c7aad2f0e10",
        "resource_id": None,  # 保留自動搜尋資源流程；不要硬拚 dataset UUID 當 API
        "name": "Taipei Free WiFi 熱點",
        "agency": "台北市政府",
        "update_frequency": "不定期",
        "description": "台北市免費無線網路熱點位置",
        "api_url": None,       # 待以資料集頁面解析出實際資源 URL 後填入
        "format": "JSON",
        "verified": False,
        "fallback_keywords": ["wifi", "hotspot", "無線網路", "iTaiwan"]
    },
    "taipei_garbage_truck": {
        "id": "5a5b36e0-f870-4b7f-8378-c91ac5f57941",
        "name": "垃圾車即時位置",
        "agency": "台北市政府",
        "update_frequency": "即時",
        "description": "台北市垃圾車即時位置資訊",
        "api_url": None,       # 需以資料集頁解析取得實際資源（CSV/JSON/GeoJSON）直鏈
        "format": "JSON",
        "verified": False
    },

    # 中央氣象署資料（需要 API Key）
    "weather_forecast": {
        "id": "F-C0032-001",
        "name": "一般天氣預報",
        "agency": "中央氣象署",
        "update_frequency": "每3小時",
        "description": "36小時天氣預報",
        "api_url": "https://opendata.cwb.gov.tw/api/v1/rest/datastore/F-C0032-001",
        "format": "JSON",
        "auth_required": True,
        "verified": True
    },

    # 交通資訊（TDCS 歷史資料為 CSV 目錄）
    "freeway_info": {
        "id": "freeway",
        "name": "高速公路即時路況（歷史 TDCS）",
        "agency": "交通部高速公路局",
        "update_frequency": "即時/歷史分檔",
        "description": "國道車流 TDCS 歷史檔案（CSV 目錄）",
        "api_url": "https://tisvcloud.freeway.gov.tw/history/TDCS/M03A/",
        "format": "CSV",       # 更正：此為 CSV 目錄，不是 JSON
        "verified": True
    }
}

# 政府資料開放平臺的資料集（使用資料集頁面而非 API）
GOV_PLATFORM_DATASETS = {
    "population_stats": {
        "id": "8410",
        "name": "人口統計資料",
        "agency": "內政部戶政司",
        "update_frequency": "每月",
        "description": "各縣市人口統計資料",
        "download_url": "https://data.gov.tw/dataset/8410",
        "format": ["CSV", "JSON", "XML"],
        "note": "需要手動下載或自動化擷取資源連結，無統一 API"
    },
    "crime_stats": {
        "id": "25793",
        "name": "刑案統計",
        "agency": "內政部警政署",
        "update_frequency": "每月",
        "description": "各縣市刑事案件統計資料",
        "download_url": "https://data.gov.tw/dataset/25793",
        "format": ["CSV", "ODS"],
        "note": "需要手動下載或自動化擷取資源連結，無統一 API"
    }
}

# 熱門資料集 ID 對照表（保持原樣；實際取用請對應到各資源 URL）
POPULAR_DATASETS = {
    # 治安相關
    "crime_statistics": {
        "id": "25793",
        "name": "刑案統計",
        "agency": "內政部警政署",
        "update_frequency": "每月",
        "description": "各縣市刑事案件統計資料"
    },
    "police_stations": {
        "id": "25962",
        "name": "警察機關通訊資料",
        "agency": "內政部警政署",
        "update_frequency": "不定期",
        "description": "全國警察機關聯絡資訊"
    },
    "traffic_accidents": {
        "id": "12818",
        "name": "道路交通事故統計",
        "agency": "交通部",
        "update_frequency": "每月",
        "description": "道路交通事故統計資料"
    },

    # 人口統計
    "population_stats": {
        "id": "8410",
        "name": "人口統計資料",
        "agency": "內政部戶政司",
        "update_frequency": "每月",
        "description": "各縣市人口統計資料"
    },
    "household_stats": {
        "id": "8411",
        "name": "戶數統計資料",
        "agency": "內政部戶政司",
        "update_frequency": "每月",
        "description": "各縣市戶數統計資料"
    },

    # 經濟指標
    "unemployment_rate": {
        "id": "6564",
        "name": "失業率統計",
        "agency": "勞動部",
        "update_frequency": "每月",
        "description": "各縣市失業率統計"
    },
    "consumer_price_index": {
        "id": "5961",
        "name": "消費者物價指數",
        "agency": "行政院主計總處",
        "update_frequency": "每月",
        "description": "消費者物價指數統計"
    },

    # 教育資源
    "school_directory": {
        "id": "6289",
        "name": "各級學校名錄",
        "agency": "教育部",
        "update_frequency": "每學期",
        "description": "全國各級學校基本資料"
    },
    "student_statistics": {
        "id": "6290",
        "name": "學生數統計",
        "agency": "教育部",
        "update_frequency": "每學年",
        "description": "各級學校學生人數統計"
    },

    # 醫療資源
    "medical_institutions": {
        "id": "24432",
        "name": "醫療機構基本資料",
        "agency": "衛生福利部",
        "update_frequency": "每月",
        "description": "全國醫療機構基本資料"
    },
    "pharmacies": {
        "id": "39292",
        "name": "藥局基本資料",
        "agency": "衛生福利部",
        "update_frequency": "每月",
        "description": "全國藥局基本資料"
    },

    # 交通資訊
    "parking_lots": {
        "id": "128435",
        "name": "停車場資訊",
        "agency": "交通部",
        "update_frequency": "不定期",
        "description": "公有停車場基本資料"
    },
    "bus_stops": {
        "id": "128436",
        "name": "公車站牌資訊",
        "agency": "交通部",
        "update_frequency": "不定期",
        "description": "公車站牌位置資料"
    },

    # 環境資料
    "air_quality": {
        "id": "40448",
        "name": "空氣品質監測",
        "agency": "環境部",
        "update_frequency": "每小時",
        "description": "空氣品質監測站資料"
    },
    "weather_stations": {
        "id": "32289",
        "name": "氣象站資料",
        "agency": "中央氣象署",
        "update_frequency": "即時",
        "description": "氣象觀測站基本資料"
    },

    # 社會福利
    "elderly_care": {
        "id": "25840",
        "name": "長期照顧機構",
        "agency": "衛生福利部",
        "update_frequency": "每月",
        "description": "長期照顧服務機構資料"
    },
    "social_welfare": {
        "id": "25841",
        "name": "社會福利機構",
        "agency": "衛生福利部",
        "update_frequency": "每月",
        "description": "社會福利機構基本資料"
    }
}

# 台北市特色資料集（僅供顯示；實際取用請接對資源 URL）
TAIPEI_DATASETS = {
    "youbike": {
        "id": "ddb80380-f1b3-4f8e-8c47-7b0eb6a44132",
        "name": "YouBike 站點資訊",
        "description": "YouBike 微笑單車即時資訊",
        "api_url": "https://tcgbusfs.blob.core.windows.net/dotapp/youbike/v2/youbike_immediate.json",
        "verified": True
    },
    "library_seats": {
        "id": "library",
        "name": "圖書館座位資訊",
        "description": "台北市立圖書館即時座位資訊",
        "api_url": "https://seat.tpml.edu.tw/sm/service/getAllArea",
        "verified": True
    },
    "bike_theft": {
        "id": "adf80a2b-b29d-4fca-888c-bcd26ae314e0",
        "name": "自行車竊盜統計",
        "description": "台北市自行車竊盜案件統計資料",
        "api_url": "https://data.taipei/api/v1/dataset/adf80a2b-b29d-4fca-888c-bcd26ae314e0?scope=resourceAquire",
        "verified": True
    }
}

# 資料格式說明（內部規格，非各平臺官方上限）
DATA_FORMATS = {
    "json": {
        "description": "JSON 格式",
        "mime_type": "application/json",
        "recommended": True
    },
    "csv": {
        "description": "CSV 格式",
        "mime_type": "text/csv",
        "recommended": False
    },
    "xml": {
        "description": "XML 格式",
        "mime_type": "application/xml",
        "recommended": False
    }
}

# API 請求參數說明（內部預設；實際以各平臺文件為準）
API_PARAMETERS = {
    "format": {
        "description": "資料格式",
        "values": ["json", "csv", "xml"],
        "default": "json"
    },
    "limit": {
        "description": "資料筆數限制",
        "type": "integer",
        "default": 100,
        "max": 1000
    },
    "offset": {
        "description": "資料起始位置",
        "type": "integer",
        "default": 0
    },
    "q": {
        "description": "搜尋關鍵字",
        "type": "string"
    },
    "sort": {
        "description": "排序欄位",
        "type": "string"
    }
}

# 錯誤代碼說明（一般常見 HTTP 狀態；實際以各平臺為準）
ERROR_CODES = {
    200: "請求成功",
    400: "請求參數錯誤",
    401: "未授權存取",
    403: "禁止存取",
    404: "資源不存在",
    429: "請求頻率過高",
    500: "伺服器內部錯誤",
    503: "服務暫時無法使用"
}

# 使用限制（你的系統內部節流建議值，非官方配額）
USAGE_LIMITS = {
    "requests_per_minute": 60,
    "requests_per_hour": 1000,
    "requests_per_day": 10000,
    "max_records_per_request": 1000
}
