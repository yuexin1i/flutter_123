# transformer.py

def transform_bus_eta(raw_data: list) -> list:
    """轉換公車預估到站時間 (配合 Flutter 模型)"""
    slim_data = []
    for item in raw_data:
        slim_data.append({
            "stopUID": item.get("StopUID", ""),
            "routeUID": item.get("RouteUID", ""),
            "plateNumb": item.get("PlateNumb", ""),
            "direction": item.get("Direction", -1),
            "estimateTime": item.get("EstimateTime"), # 保持為 None (null)，讓前端判斷
            "stopStatus": item.get("StopStatus", -1),
            "nextBusTime": item.get("NextBusTime"),
            "isLastBus": item.get("IsLastBus", False)
        })
    return slim_data

def transform_bus_alert(data):
    """整理公車通阻資訊 (配合 Flutter 模型)"""
    alerts = []
    for item in data:
        scope = item.get("Scope", {})

        # 💡 在後端直接把複雜的字典解析成純字串 ID 清單
        affected_route_ids = [str(r.get("RouteID", "")) for r in scope.get("Routes", [])] if "Routes" in scope else []
        affected_stop_ids = [str(s.get("StopID", "")) for s in scope.get("Stops", [])] if "Stops" in scope else []

        alerts.append({
            "alertID": item.get("AlertID", ""),
            "title": item.get("Title", "營運通阻公告"),
            "description": item.get("Description", ""),
            "startTime": item.get("StartTime", ""), # 統一改為 camelCase
            "endTime": item.get("EndTime", ""),     # 統一改為 camelCase
            "affectedRouteIDs": affected_route_ids,
            "affectedStopIDs": affected_stop_ids
        })
    return alerts

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
    """轉換台鐵即時到離站看版 (配合 Flutter 模型)"""
    slim_data = []
    for item in raw_data:
        slim_data.append({
            "stationID": item.get("StationID", ""),
            "trainNo": item.get("TrainNo", ""),
            "direction": item.get("Direction", 0), # 0:順行, 1:逆行
            # 這裡幫你把多層的字典攤平，直接送出字串，方便 Flutter 解析
            "trainTypeNameZh": item.get("TrainTypeName", {}).get("Zh_tw", "未知車種"),
            "tripLine": item.get("TripLine", 0), # 山線/海線等
            "endingStationZh": item.get("EndingStationName", {}).get("Zh_tw", ""),
            "scheduledArrivalTime": item.get("ScheduledArrivalTime", ""),
            "scheduledDepartureTime": item.get("ScheduledDepartureTime", ""),
            "delayTime": item.get("DelayTime", 0), # 誤點幾分鐘，0代表準點
            "updateTime": item.get("UpdateTime", "")
        })
    return slim_data

def transform_tra_alert(data):
    """整理台鐵通阻資訊 (配合 Flutter 模型)"""
    alerts = []
    for item in data:
        # 注意：TDX 的台鐵 Alert 格式可能跟高鐵不太一樣
        # 這裡假設 TDX 傳來的欄位長得像你設定的 Model

        inbound = item.get("Inbound", {})
        outbound = item.get("Outbound", {})

        alerts.append({
            "serviceID": item.get("ServiceID", ""),
            "serviceName": item.get("ServiceName", ""),
            "inboundStatus": inbound.get("Status", 0),
            "inboundReason": inbound.get("Reason", ""),
            "outboundStatus": outbound.get("Status", 0),
            "outboundReason": outbound.get("Reason", "")
        })
    return alerts


def transform_thsr_timetable(raw_data: list) -> list:
    """轉換高鐵每日時刻表 (配合 Flutter 模型)"""
    slim_data = []
    for item in raw_data:
        slim_data.append({
            "trainNo": item.get("TrainNo", ""),
            "direction": item.get("Direction", 0), # 0:南下, 1:北上
            # 幫你把字典攤平，直接送出中文站名字串
            "startingStationName": item.get("StartingStationName", {}).get("Zh_tw", ""),
            "endingStationName": item.get("EndingStationName", {}).get("Zh_tw", ""),
            "arrivalTime": item.get("ArrivalTime", ""),
            "departureTime": item.get("DepartureTime", "")
        })
    return slim_data

def transform_thsr_alert(data):
    """整理高鐵通阻資訊 (配合 Flutter 模型)"""
    alerts = []
    for item in data:
        alerts.append({
            "alertID": item.get("AlertID", "0"),
            "title": item.get("Title", "全線營運正常"),
            "description": item.get("Description", ""),
            # 注意：TDX 回傳的 Status 可能是數字或字串，這裡統一轉字串配合你的型別
            "status": str(item.get("Status", "正常")),
            "alertURL": item.get("AlertURL", "")
        })
    return alerts

