from fastapi import FastAPI, HTTPException
from datetime import datetime
from typing import Optional
from pydantic import BaseModel
import db_connection as db

app = FastAPI(title="Device Registration API")

class Device(BaseModel):
    imei: str
    serial_number: str

@app.get("/registration/all")
async def get_all_registrations():
    data = db.get_all_registration_data()
    if data is None:
        raise HTTPException(status_code=500, detail="Failed to fetch registration data")
    return {"data": data}

@app.get("/devices")
async def get_devices():
    devices = db.get_all_devices()
    return {"devices": devices, "total": len(devices)}

@app.post("/devices")
async def add_device(device: Device):
    success = db.insert_device_data(device.imei, device.serial_number)
    if not success:
        raise HTTPException(status_code=500, detail="Failed to insert device")
    return {"message": "Device added successfully"}

@app.get("/devices/count")
async def get_devices_count():
    count = db.get_device_count()
    return {"total_devices": count}

@app.get("/registration/{imei}")
async def get_registration_by_imei(imei: str):
    data = db.get_registration_data_by_imei(imei)
    if data is None:
        raise HTTPException(status_code=404, detail="Data not found")
    return {"data": data}

@app.get("/registration/{imei}/date-range")
async def get_registration_by_date_range(
    imei: str,
    start_date: datetime,
    end_date: datetime
):
    # Validasi tanggal
    if end_date < start_date:
        raise HTTPException(
            status_code=400, 
            detail="Invalid date range: end_date cannot be earlier than start_date"
        )
    
    data = db.get_registration_data_by_date_range(imei, start_date, end_date)
    if data is None:
        raise HTTPException(status_code=404, detail="Data not found")
    
    return {
        "data": data,
        "meta": {
            "start_date": start_date.strftime('%Y-%m-%d %H:%M:%S'),
            "end_date": end_date.strftime('%Y-%m-%d %H:%M:%S'),
            "total_records": len(data) if data else 0
        }
    }

@app.get("/registration/{imei}/gps")
async def get_gps_data_range(
    imei: str,
    start_date: datetime,
    end_date: datetime
):
    if end_date < start_date:
        raise HTTPException(
            status_code=400, 
            detail="Invalid date range: end_date cannot be earlier than start_date"
        )
    
    data = db.get_gps_data_by_date_range(imei, start_date, end_date)
    if data is None:
        raise HTTPException(status_code=404, detail="GPS data not found")
    return {
        "data": data,
        "meta": {
            "start_date": start_date.strftime('%Y-%m-%d %H:%M:%S'),
            "end_date": end_date.strftime('%Y-%m-%d %H:%M:%S'),
            "total_records": len(data) if data else 0
        }
    }

@app.get("/registration/{imei}/non-gps")
async def get_non_gps_data_range(
    imei: str,
    start_date: datetime,
    end_date: datetime
):
    if end_date < start_date:
        raise HTTPException(
            status_code=400, 
            detail="Invalid date range: end_date cannot be earlier than start_date"
        )
    
    data = db.get_non_gps_data_by_date_range(imei, start_date, end_date)
    if data is None:
        raise HTTPException(status_code=404, detail="Non-GPS data not found")
    return {
        "data": data,
        "meta": {
            "start_date": start_date.strftime('%Y-%m-%d %H:%M:%S'),
            "end_date": end_date.strftime('%Y-%m-%d %H:%M:%S'),
            "total_records": len(data) if data else 0
        }
    }

@app.get("/gps/{imei}/latest")
async def get_latest_gps(imei: str):
    data = db.get_latest_gps_data(imei)
    if data is None:
        raise HTTPException(status_code=404, detail="GPS data not found")
    return {"data": data}

@app.get("/heartbeat/{imei}/latest")
async def get_latest_heartbeat(imei: str):
    data = db.get_latest_heartbeat(imei)
    if data is None:
        raise HTTPException(status_code=404, detail="Heartbeat data not found")
    return {
        "data": data,
        "meta": {
            "timestamp": data.get('timestamp'),
            "voltage": data.get('voltage'),
            "battery_percentage": data.get('persentase_baterai')
        }
    }

@app.get("/beacons")
async def get_beacons():
    data = db.get_all_beacon_data()
    if data is None:
        raise HTTPException(status_code=500, detail="Failed to fetch beacon data")
    return {"data": data, "total": len(data)}

@app.get("/beacon-location")
async def get_beacon_location(major: str, minor: str):
    data = db.get_beacon_location(major, minor)
    if data is None:
        raise HTTPException(status_code=404, detail="Beacon location not found")
    return {"data": data}

@app.get("/registration/beacon-data")
async def get_beacon_registrations(
    start_date: Optional[datetime] = None,
    end_date: Optional[datetime] = None,
    imei: Optional[str] = None
):
    """Get registration data filtered for beacon type only"""
    try:
        data = db.get_beacon_registration_data(imei, start_date, end_date)
        if data is None:
            raise HTTPException(status_code=404, detail="Beacon registration data not found")
        return {
            "data": data,
            "meta": {
                "total_records": len(data) if data else 0,
                "imei": imei,
                "start_date": start_date.strftime('%Y-%m-%d %H:%M:%S') if start_date else None,
                "end_date": end_date.strftime('%Y-%m-%d %H:%M:%S') if end_date else None
            }
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
