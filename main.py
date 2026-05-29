# main.py
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
import httpx
import os
from transformers import transform_bus_eta, transform_youbike_status, transform_tra_live, transform_thsr_timetable

app = FastAPI(title="Chiayi Transport Middleware API")

# 允許 Flutter (特別是 Web 版) 跨網域請求
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

# ⚠️ 這裡要放入你取得 TDX Token 的邏輯
TDX_TOKEN = os.getenv("TDX_TOKEN", "YOUR_TEMP_TOKEN")
HEADERS = {"authorization": f"Bearer {TDX_TOKEN}", "Accept-Encoding": "gzip"}

@app.get("/")
def health_check():
    return {"status": "Server is running smoothly!"}

@app.get("/api/bus/eta/{city}/{route_id}")
async def get_bus_eta(city: str, route_id: str):
    url = f"https://tdx.transportdata.tw/api/basic/v2/Bus/EstimatedTimeOfArrival/City/{city}?$filter=RouteID eq '{route_id}'&$format=JSON"
    async with httpx.AsyncClient() as client:
        res = await client.get(url, headers=HEADERS)
        if res.status_code != 200:
            raise HTTPException(status_code=500, detail="TDX API Error")

        # 呼叫轉換器瘦身
        clean_data = transform_bus_eta(res.json())
        return {"data": clean_data}

@app.get("/api/bike/status/{city}")
async def get_bike_status(city: str):
    url = f"https://tdx.transportdata.tw/api/basic/v2/Bike/Availability/City/{city}?$format=JSON"
    async with httpx.AsyncClient() as client:
        res = await client.get(url, headers=HEADERS)
        if res.status_code != 200:
            raise HTTPException(status_code=500, detail="TDX API Error")

        clean_data = transform_youbike_status(res.json())
        return {"data": clean_data}

# ... (台鐵與高鐵的路由寫法皆以此類推) ...