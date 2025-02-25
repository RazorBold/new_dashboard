from fastapi import FastAPI, HTTPException
from datetime import datetime, timedelta
from typing import Optional
from pydantic import BaseModel
import db_connection as db
import requests

app = FastAPI(title="Device Registration API")

GOOGLE_MAPS_API_KEY = "AIzaSyAdidNhffYHTMN60gs6oiXcqpyrmE8vpf0"  # Ganti dengan API key Anda

class Device(BaseModel):
    imei: str
    serial_number: str

_device_cache = {}
_last_cache_update = None
_cache_duration = timedelta(minutes=5)

def get_cached_devices():
    global _device_cache, _last_cache_update
    now = datetime.now()
    
    if _last_cache_update is None or (now - _last_cache_update) > _cache_duration:
        devices = db.get_all_devices()
        _device_cache = {device['imei']: device['serial_number'] for device in devices}
        _last_cache_update = now
    
    return _device_cache

@app.get("/device-info/{imei}")
async def get_device_info(imei: str):
    """Get device serial number from cache"""
    devices = get_cached_devices()
    return {"serial_number": devices.get(imei)}

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
    
    processed_data = []
    for row in data:
        if row['payload_id_2'] == 'Beacon':
            major, minor = db.parse_beacon_data(row['parsed_data'])
            row['major'] = major
            row['minor'] = minor
        processed_data.append(row)
    
    return {"data": processed_data}

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

@app.get("/service-tanto")
async def get_service_tanto():
    """Get all service tanto data"""
    data = db.get_service_tanto_data()
    if data is None:
        raise HTTPException(status_code=500, detail="Failed to fetch service tanto data")
    return {
        "data": data,
        "total": len(data),
        "fields": {
            "id": "Record ID",
            "id_container": "Container ID",
            "last_activity": "Last Activity",
            "date": "Date",
            "created_time": "Created Time"
        },
        "timestamp": datetime.now().strftime('%Y-%m-%d %H:%M:%S')
    }

@app.get("/devices-with-activity")
async def get_devices_with_activity():
    """Get all devices with their latest container activity"""
    devices = db.get_all_devices_with_activity()
    return {
        "devices": devices,
        "total": len(devices),
        "timestamp": datetime.now().strftime('%Y-%m-%d %H:%M:%S')
    }

@app.get("/device-activity/{imei}")
async def get_device_activity(imei: str):
    """Get activity for a single device"""
    device = db.get_device_by_imei(imei)
    if device is None:
        raise HTTPException(status_code=404, detail="Device not found")
    
    activity = db.get_container_activity(device['serial_number'])
    return {
        "imei": imei,
        "serial_number": device['serial_number'],
        "last_activity": activity or "No Activity"
    }

@app.get("/all-device-activities")
async def get_all_device_activities():
    """Get activities for all devices"""
    data = db.get_all_devices_activities()
    return {
        "devices": data,
        "timestamp": datetime.now().strftime('%Y-%m-%d %H:%M:%S')
    }

@app.post("/api/geofence")
async def create_geofence(geofence: dict):
    """Create a new geofence area"""
    try:
        success = db.save_geofence(
            name=geofence['name'],
            coordinates=geofence['coordinates'],
            description=geofence.get('description')
        )
        
        if not success:
            raise HTTPException(status_code=500, detail="Failed to save geofence")
        
        return {"message": "Geofence saved successfully"}
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error saving geofence: {str(e)}")

@app.get("/api/geofence")
async def get_geofences():
    data = db.get_all_geofences()
    if data is None:
        raise HTTPException(status_code=500, detail="Failed to fetch geofences")
    return data

@app.get("/reverse-geocode")
async def get_address(lat: float, lng: float):
    """Get location name (geofence or street address) for coordinates"""
    try:
        # First check if point is in any geofence
        geofence_name = db.check_point_in_geofence(lat, lng)
        if (geofence_name):
            return {
                "street_name": geofence_name,
                "full_address": f"Inside {geofence_name} Area"
            }
        
        # If not in geofence, get street address from Google Maps
        url = f"https://maps.googleapis.com/maps/api/geocode/json?latlng={lat},{lng}&key={GOOGLE_MAPS_API_KEY}"
        response = requests.get(url)
        data = response.json()
        
        if data["status"] == "OK":
            address_components = data["results"][0]["address_components"]
            street_name = None
            city = None
            
            # Extract street name and city
            for component in address_components:
                if "route" in component["types"]:
                    street_name = component["long_name"]
                if "administrative_area_level_2" in component["types"]:
                    city = component["long_name"]
            
            # If no specific street found, use formatted address
            if not street_name:
                street_name = data["results"][0]["formatted_address"].split(',')[0]
            
            location_text = f"{street_name}"
            if city:
                location_text += f", {city}"
            
            return {
                "street_name": location_text,
                "full_address": data["results"][0]["formatted_address"]
            }
        else:
            return {"error": "No results found"}
            
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Geocoding error: {str(e)}")

@app.get("/beacon/registration")
async def get_beacon_registrations(
    imei: Optional[str] = None,
    start_date: Optional[str] = None,
    end_date: Optional[str] = None
):
    """Get beacon registration data with optional IMEI and date filters"""
    try:
        data = db.get_beacon_registration_data(imei, start_date, end_date)
        if data is None:
            raise HTTPException(status_code=500, detail="Failed to fetch beacon registration data")
        
        processed_data = []
        for row in data:
            major, minor = db.parse_beacon_data(row['parsed_data'])
            row['major'] = major
            row['minor'] = minor
            processed_data.append(row)
        
        return {
            "status": "success",
            "data": processed_data,
            "count": len(processed_data)
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/beacon/locations")
async def get_beacon_locations():
    """Get all beacon location data"""
    try:
        data = db.get_all_beacon_locations()
        if data is None:
            raise HTTPException(status_code=500, detail="Failed to fetch beacon locations")
        
        return {
            "status": "success",
            "data": data,
            "count": len(data)
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/beacon/location/{major}/{minor}")
async def get_beacon_location_by_id(
    major: str,
    minor: str
):
    """Get beacon location by major and minor IDs"""
    try:
        data = db.get_beacon_location_by_id(major, minor)
        if data is None:
            return {
                "status": "error",
                "message": "Beacon location not found"
            }
        
        return {
            "status": "success",
            "data": data
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
