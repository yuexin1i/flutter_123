# main.py
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
import httpx
import os
import time
import asyncio

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

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

# ==========================================
# TDX Token 管理機制
# ==========================================
TDX_CLIENT_ID = os.getenv("TDX_CLIENT_ID", "YOUR_CLIENT_ID")
TDX_CLIENT_SECRET = os.getenv("TDX_CLIENT_SECRET", "YOUR_CLIENT_SECRET")

_token_cache = {
    "access_token": None,
    "expires_at": 0
}

async def get_valid_token():
    current_time = time.time()
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
            _token_cache["expires_at"] = current_time + res_json.get("expires_in", 86400)
            return _token_cache["access_token"]
        except Exception as e:
            print(f"❌ TDX Token 獲取失敗: {e}")
            raise HTTPException(status_code=500, detail="無法取得 TDX 授權 Token")


# ==========================================
# ⚡ Server-Side API 快取機制
# ==========================================
# 結構：{ cache_key: { "data": ..., "expires_at": float, "lock": asyncio.Lock } }
_api_cache: dict = {}
CACHE_TTL_SECONDS = 60  # 60 秒快取，避免重複打 TDX


async def get_cached(cache_key: str, fetcher, ttl: int = CACHE_TTL_SECONDS):
    """
    通用快取包裝器。
    - 若快取有效，直接回傳快取資料（不打 TDX）
    - 若快取過期或不存在，呼叫 fetcher() 取得新資料並存入快取
    - 使用 asyncio.Lock 防止同一瞬間多個請求同時打 TDX（stampede 問題）
    """
    now = time.time()

    # 初始化快取槽（含鎖）
    if cache_key not in _api_cache:
        _api_cache[cache_key] = {
            "data": None,
            "expires_at": 0,
            "lock": asyncio.Lock()
        }

    slot = _api_cache[cache_key]

    # 快取有效 → 直接回傳（不需要鎖）
    if slot["data"] is not None and now < slot["expires_at"]:
        return slot["data"], True  # (data, from_cache)

    # 快取過期 → 加鎖後再次確認（雙重檢查，避免多個 coroutine 同時刷新）
    async with slot["lock"]:
        now = time.time()
        if slot["data"] is not None and now < slot["expires_at"]:
            return slot["data"], True

        # 真正呼叫 TDX
        fresh_data = await fetcher()
        slot["data"] = fresh_data
        slot["expires_at"] = now + ttl
        return fresh_data, False  # (data, from_cache)


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
    cache_key = f"bus_eta:{city}:{route_id}"

    async def fetcher():
        token = await get_valid_token()
        headers = {"authorization": f"Bearer {token}", "Accept-Encoding": "gzip"}
        url = f"https://tdx.transportdata.tw/api/basic/v2/Bus/EstimatedTimeOfArrival/City/{city}?$filter=RouteID eq '{route_id}'&$format=JSON"
        async with httpx.AsyncClient() as client:
            res = await client.get(url, headers=headers)
            if res.status_code != 200:
                raise HTTPException(status_code=res.status_code, detail="TDX Bus ETA API Error")
            return transform_bus_eta(res.json())

    data, from_cache = await get_cached(cache_key, fetcher)
    return {"data": data, "from_cache": from_cache}


# ------------------------------------------
# 🚲 2. YouBike 即時車位
# ------------------------------------------
@app.get("/api/bike/status/{city}")
async def get_bike_status(city: str):
    cache_key = f"bike_status:{city}"

    async def fetcher():
        token = await get_valid_token()
        headers = {"authorization": f"Bearer {token}", "Accept-Encoding": "gzip"}
        url = f"https://tdx.transportdata.tw/api/basic/v2/Bike/Availability/City/{city}?$format=JSON"
        async with httpx.AsyncClient() as client:
            res = await client.get(url, headers=headers)
            if res.status_code != 200:
                raise HTTPException(status_code=res.status_code, detail="TDX YouBike API Error")
            return transform_youbike_status(res.json())

    data, from_cache = await get_cached(cache_key, fetcher)
    return {"data": data, "from_cache": from_cache}


# ------------------------------------------
# 🚂 3. 台鐵即時到離站資訊
# ------------------------------------------
@app.get("/api/rail/tra/live/{station_id}")
async def get_tra_live(station_id: str):
    cache_key = f"tra_live:{station_id}"

    async def fetcher():
        token = await get_valid_token()
        headers = {"authorization": f"Bearer {token}", "Accept-Encoding": "gzip"}
        url = f"https://tdx.transportdata.tw/api/basic/v2/Rail/TRA/LiveBoard/Station/{station_id}?$format=JSON"
        async with httpx.AsyncClient() as client:
            res = await client.get(url, headers=headers)
            if res.status_code != 200:
                raise HTTPException(status_code=res.status_code, detail="TDX TRA Live API Error")
            return transform_tra_live(res.json())

    data, from_cache = await get_cached(cache_key, fetcher)
    return {"data": data, "from_cache": from_cache}


# ------------------------------------------
# 🚄 4. 高鐵特定日期時刻表（TTL 延長至 10 分鐘，時刻表變化極少）
# ------------------------------------------
@app.get("/api/rail/thsr/timetable/{station_id}/{train_date}")
async def get_thsr_timetable(station_id: str, train_date: str):
    cache_key = f"thsr_timetable:{station_id}:{train_date}"

    async def fetcher():
        token = await get_valid_token()
        headers = {"authorization": f"Bearer {token}", "Accept-Encoding": "gzip"}
        url = f"https://tdx.transportdata.tw/api/basic/v2/Rail/THSR/DailyTimetable/Station/{station_id}/{train_date}?$format=JSON"
        async with httpx.AsyncClient() as client:
            res = await client.get(url, headers=headers)
            if res.status_code != 200:
                raise HTTPException(status_code=res.status_code, detail="TDX THSR Timetable API Error")
            return transform_thsr_timetable(res.json())

    data, from_cache = await get_cached(cache_key, fetcher, ttl=600)  # 時刻表 10 分鐘快取
    return {"data": data, "from_cache": from_cache}


# ------------------------------------------
# ⚠️ 5. 台鐵即時營運通阻資訊
# ------------------------------------------
@app.get("/api/rail/tra/alert")
async def get_tra_alert():
    cache_key = "tra_alert"

    async def fetcher():
        token = await get_valid_token()
        headers = {"authorization": f"Bearer {token}", "Accept-Encoding": "gzip"}
        url = "https://tdx.transportdata.tw/api/basic/v2/Rail/TRA/Alert?$format=JSON"
        async with httpx.AsyncClient() as client:
            res = await client.get(url, headers=headers)
            if res.status_code != 200:
                raise HTTPException(status_code=res.status_code, detail="TDX TRA Alert API Error")
            return transform_tra_alert(res.json())

    data, from_cache = await get_cached(cache_key, fetcher)
    return {"data": data, "from_cache": from_cache}


# ------------------------------------------
# ⚠️ 6. 高鐵即時營運通阻資訊
# ------------------------------------------
@app.get("/api/rail/thsr/alert")
async def get_thsr_alert():
    cache_key = "thsr_alert"

    async def fetcher():
        token = await get_valid_token()
        headers = {"authorization": f"Bearer {token}", "Accept-Encoding": "gzip"}
        url = "https://tdx.transportdata.tw/api/basic/v2/Rail/THSR/Alert?$format=JSON"
        async with httpx.AsyncClient() as client:
            res = await client.get(url, headers=headers)
            if res.status_code != 200:
                raise HTTPException(status_code=res.status_code, detail="TDX THSR Alert API Error")
            return transform_thsr_alert(res.json())

    data, from_cache = await get_cached(cache_key, fetcher)
    return {"data": data, "from_cache": from_cache}


# ------------------------------------------
# ⚠️ 7. 公車即時營運通阻資訊
# ------------------------------------------
@app.get("/api/bus/alert/{city}")
async def get_bus_alert(city: str):
    cache_key = f"bus_alert:{city}"

    async def fetcher():
        token = await get_valid_token()
        headers = {"authorization": f"Bearer {token}", "Accept-Encoding": "gzip"}
        url = f"https://tdx.transportdata.tw/api/basic/v2/Bus/Alert/City/{city}?$format=JSON"
        async with httpx.AsyncClient() as client:
            res = await client.get(url, headers=headers)
            if res.status_code != 200:
                raise HTTPException(status_code=res.status_code, detail="TDX Bus Alert API Error")
            return transform_bus_alert(res.json())

    data, from_cache = await get_cached(cache_key, fetcher)
    return {"data": data, "from_cache": from_cache}