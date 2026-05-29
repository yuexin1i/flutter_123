# transformers.py

def transform_bus_eta(raw_data: list) -> list:
    """轉換公車預估到站時間"""
    slim_data = []
    for item in raw_data:
        slim_data.append({
            # 左邊的字串請換成你 BusModels.dart 裡面的變數名稱
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
            # 左邊的字串請換成你 YouBikeModels.dart 裡面的變數名稱
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
            # 左邊的字串請換成你 TRAModels.dart 裡面的變數名稱
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
            # 左邊的字串請換成你 THSRModels.dart 裡面的變數名稱
            "trainNo": item.get("TrainNo", ""),
            "direction": item.get("Direction", 0), # 0:南下, 1:北上
            "startingStationName": item.get("StartingStationName", {}).get("Zh_tw", ""),
            "endingStationName": item.get("EndingStationName", {}).get("Zh_tw", ""),
            "arrivalTime": item.get("ArrivalTime", ""),
            "departureTime": item.get("DepartureTime", "")
        })
    return slim_data