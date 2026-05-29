# transformer.py

def transform_bus_eta(raw_data: list) -> list:
    """轉換公車預估到站時間"""
    slim_data = []
    for item in raw_data:
        slim_data.append({
            "plateNumb": item.get("PlateNumb", ""),
            "routeNameZh": item.get("RouteName", {}).get("Zh_tw", ""),
            "stopNameZh": item.get("StopName", {}).get("Zh_tw", ""),
            "direction": item.get("Direction", 0),
            "estimateTime": item.get("EstimateTime", -1), # 預估到站秒數，-1代表無資料
            "status": item.get("StopStatus", 0) # 0:正常, 1:尚未發車, 2:交管不停, 3:末班車已過, 4:今日未營運
        })
    return slim_data


def transform_youbike_status(raw_data: list) -> list:
    """轉換 YouBike 即時車位狀態"""
    slim_data = []
    for item in raw_data:
        slim_data.append({
            "stationUID": item.get("StationUID", ""),
            "status": item.get("ServiceStatus", 0), # 0:停止營運, 1:正常營運, 2:暫停營運
            "availableRentBikes": item.get("AvailableRentBikes", 0),
            "availableReturnBikes": item.get("AvailableReturnBikes", 0),
        })
    return slim_data


def transform_tra_live(raw_data: list) -> list:
    """轉換台鐵即時到離站看版"""
    slim_data = []
    for item in raw_data:
        slim_data.append({
            "trainNo": item.get("TrainNo", ""),
            "direction": item.get("Direction", 0), # 0:順行, 1:逆行
            "trainTypeName": item.get("TrainTypeName", {}).get("Zh_tw", ""),
            "endingStationName": item.get("EndingStationName", {}).get("Zh_tw", ""),
            "scheduledArrivalTime": item.get("ScheduledArrivalTime", ""),
            "delayTime": item.get("DelayTime", 0) # 誤點幾分鐘，0代表準點
        })
    return slim_data


def transform_thsr_timetable(raw_data: list) -> list:
    """轉換高鐵每日時刻表"""
    slim_data = []
    for item in raw_data:
        slim_data.append({
            "trainNo": item.get("TrainNo", ""),
            "direction": item.get("Direction", 0), # 0:南下, 1:北上
            "startingStationName": item.get("StartingStationName", {}).get("Zh_tw", ""),
            "endingStationName": item.get("EndingStationName", {}).get("Zh_tw", ""),
            "arrivalTime": item.get("ArrivalTime", ""),
            "departureTime": item.get("DepartureTime", "")
        })
    return slim_data

def transform_tra_alert(data):
    """整理台鐵通阻資訊"""
    alerts = []
    for item in data:
        alerts.append({
            "title": item.get("Title", "無標題"),
            "description": item.get("Description", ""),
            "status": item.get("Status", "1"), # 1: 預警, 2: 發生中, 3: 處理中, 4: 排除中, 5: 已排除
            "publish_time": item.get("PublishTime", ""),
            "update_time": item.get("UpdateTime", ""),
            "effect_lines": [line.get("LineID") for line in item.get("EffectLines", [])] if item.get("EffectLines") else []
        })
    return alerts

def transform_thsr_alert(data):
    """整理高鐵通阻資訊"""
    alerts = []
    for item in data:
        alerts.append({
            "title": item.get("Title", "全線營運正常"),
            "description": item.get("Description", ""),
            "status": item.get("Status", "1"),
            "publish_time": item.get("PublishTime", ""),
            "update_time": item.get("UpdateTime", ""),
            "direction": item.get("Direction", 0) # 0: 雙向, 1: 南下, 2: 北上
        })
    return alerts

def transform_bus_alert(data):
    """整理公車通阻資訊"""
    alerts = []
    for item in data:
        # TDX 公車的受影響路線通常包在 Scope 裡面，這裡做安全讀取
        effect_routes = []
        scope = item.get("Scope", {})
        if "Routes" in scope:
            effect_routes = [route.get("RouteName", {}).get("Zh_tw") for route in scope.get("Routes", [])]
        elif "EffectRoutes" in item:
            # 保留你原本的寫法作為備用，以防特定縣市的 JSON 結構不同
            effect_routes = [route.get("RouteName", {}).get("Zh_tw") for route in item.get("EffectRoutes", [])]

        alerts.append({
            "title": item.get("Title", "無標題"),
            "description": item.get("Description", ""),
            "start_time": item.get("StartTime", ""),
            "end_time": item.get("EndTime", ""),
            "effect_routes": effect_routes
        })
    return alerts