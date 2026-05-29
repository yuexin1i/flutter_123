# main.py
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
import httpx
import os
import time

# 引入 transformer.py 中的所有資料瘦身函式
from transformer import (
    transform_bus_eta,
    transform_youbike_status,
    transform_tra_live,
    transform_thsr_timetable,
    transform_tra_alert,
    transform_thsr_alert,
    transform_bus_alert
)

app = FastAPI(title="Chiayi Transport Middleware API")

# 允許 Flutter 跨網域請求 (解決 CORS 錯誤)
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

# ==========================================
# TDX Token 管理機制
# ==========================================
# ⚠️ 請確保在環境變數 (Environment Variables) 中設定這兩個值
TDX_CLIENT_ID = os.getenv("TDX_CLIENT_ID", "YOUR_CLIENT_ID")
TDX_CLIENT_SECRET = os.getenv("TDX_CLIENT_SECRET", "YOUR_CLIENT_SECRET")

# 儲存 Token 及其過期時間 (快取機制)
_token_cache = {
    "access_token": None,
    "expires_at": 0
}

async def get_valid_token():
    """取得有效的 TDX Token，若過期則重新獲取"""
    current_time = time.time()

    # 提早 300 秒 (5分鐘) 視為過期，避免極端情況
    if _token_cache["access_token"] and current_time < _token_cache["expires_at"] - 300:
        return _token_cache["access_token"]

    token_url = 'https://tdx.transportdata.tw/auth/realms/TDXConnect/protocol/openid-connect/token'
    data = {
        'grant_type': 'client_credentials',
        'client_id': TDX_CLIENT_ID,
        'client_secret': TDX_CLIENT_SECRET
    }

    async with httpx.AsyncClient() as client:
        try:
            response = await client.post(token_url, data=data)
            response.raise_for_status()
            res_json = response.json()

            _token_cache["access_token"] = res_json.get("access_token")
            # 通常 expires_in 是一天 (86400 秒)
            _token_cache["expires_at"] = current_time + res_json.get("expires_in", 86400)

            return _token_cache["access_token"]
        except Exception as e:
            print(f"❌ TDX Token 獲取失敗: {e}")
            raise HTTPException(status_code=500, detail="無法取得 TDX 授權 Token")

# ==========================================
# API 路由區 (Endpoints)
# ==========================================

@app.get("/")
def health_check():
    return {"status": "Chiayi Transport Server is running smoothly!"}

# ------------------------------------------
# 🚌 1. 公車預估到站時間
# ------------------------------------------
@app.get("/api/bus/eta/{city}/{route_id}")
async def get_bus_eta(city: str, route_id: str):
    token = await get_valid_token()
    headers = {"authorization": f"Bearer {token}", "Accept-Encoding": "gzip"}
    url = f"https://tdx.transportdata.tw/api/basic/v2/Bus/EstimatedTimeOfArrival/City/{city}?$filter=RouteID eq '{route_id}'&$format=JSON"

    async with httpx.AsyncClient() as client:
        res = await client.get(url, headers=headers)
        if res.status_code != 200:
            raise HTTPException(status_code=res.status_code, detail="TDX Bus ETA API Error")

        clean_data = transform_bus_eta(res.json())
        return {"data": clean_data}

# ------------------------------------------
# 🚲 2. YouBike 即時車位
# ------------------------------------------
@app.get("/api/bike/status/{city}")
async def get_bike_status(city: str):
    token = await get_valid_token()
    headers = {"authorization": f"Bearer {token}", "Accept-Encoding": "gzip"}
    url = f"https://tdx.transportdata.tw/api/basic/v2/Bike/Availability/City/{city}?$format=JSON"

    async with httpx.AsyncClient() as client:
        res = await client.get(url, headers=headers)
        if res.status_code != 200:
            raise HTTPException(status_code=res.status_code, detail="TDX YouBike API Error")

        clean_data = transform_youbike_status(res.json())
        return {"data": clean_data}

# ------------------------------------------
# 🚂 3. 台鐵即時到離站資訊 (動態前後30分鐘)
# ------------------------------------------
@app.get("/api/rail/tra/live/{station_id}")
async def get_tra_live(station_id: str):
    token = await get_valid_token()
    headers = {"authorization": f"Bearer {token}", "Accept-Encoding": "gzip"}
    url = f"https://tdx.transportdata.tw/api/basic/v2/Rail/TRA/LiveBoard/Station/{station_id}?$format=JSON"

    async with httpx.AsyncClient() as client:
        res = await client.get(url, headers=headers)
        if res.status_code != 200:
            raise HTTPException(status_code=res.status_code, detail="TDX TRA Live API Error")

        clean_data = transform_tra_live(res.json())
        return {"data": clean_data}

# ------------------------------------------
# 🚄 4. 高鐵特定日期時刻表
# ------------------------------------------
@app.get("/api/rail/thsr/timetable/{station_id}/{train_date}")
async def get_thsr_timetable(station_id: str, train_date: str):
    token = await get_valid_token()
    headers = {"authorization": f"Bearer {token}", "Accept-Encoding": "gzip"}
    # train_date 格式需為 YYYY-MM-DD
    url = f"https://tdx.transportdata.tw/api/basic/v2/Rail/THSR/DailyTimetable/Station/{station_id}/{train_date}?$format=JSON"

    async with httpx.AsyncClient() as client:
        res = await client.get(url, headers=headers)
        if res.status_code != 200:
            raise HTTPException(status_code=res.status_code, detail="TDX THSR Timetable API Error")

        clean_data = transform_thsr_timetable(res.json())
        return {"data": clean_data}

# ------------------------------------------
# ⚠️ 5. 台鐵即時營運通阻資訊
# ------------------------------------------
@app.get("/api/rail/tra/alert")
async def get_tra_alert():
    token = await get_valid_token()
    headers = {"authorization": f"Bearer {token}", "Accept-Encoding": "gzip"}
    url = "https://tdx.transportdata.tw/api/basic/v2/Rail/TRA/Alert?$format=JSON"

    async with httpx.AsyncClient() as client:
        res = await client.get(url, headers=headers)
        if res.status_code != 200:
            raise HTTPException(status_code=res.status_code, detail="TDX TRA Alert API Error")

        clean_data = transform_tra_alert(res.json())
        return {"data": clean_data}

# ------------------------------------------
# ⚠️ 6. 高鐵即時營運通阻資訊
# ------------------------------------------
@app.get("/api/rail/thsr/alert")
async def get_thsr_alert():
    token = await get_valid_token()
    headers = {"authorization": f"Bearer {token}", "Accept-Encoding": "gzip"}
    url = "https://tdx.transportdata.tw/api/basic/v2/Rail/THSR/Alert?$format=JSON"

    async with httpx.AsyncClient() as client:
        res = await client.get(url, headers=headers)
        if res.status_code != 200:
            raise HTTPException(status_code=res.status_code, detail="TDX THSR Alert API Error")

        clean_data = transform_thsr_alert(res.json())
        return {"data": clean_data}

# ------------------------------------------
# ⚠️ 7. 公車即時營運通阻資訊
# ------------------------------------------
@app.get("/api/bus/alert/{city}")
async def get_bus_alert(city: str):
    token = await get_valid_token()
    headers = {"authorization": f"Bearer {token}", "Accept-Encoding": "gzip"}
    url = f"https://tdx.transportdata.tw/api/basic/v2/Bus/Alert/City/{city}?$format=JSON"

    async with httpx.AsyncClient() as client:
        res = await client.get(url, headers=headers)
        if res.status_code != 200:
            raise HTTPException(status_code=res.status_code, detail="TDX Bus Alert API Error")

        clean_data = transform_bus_alert(res.json())
        return {"data": clean_data}