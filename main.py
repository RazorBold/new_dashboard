from fastapi import FastAPI, Request, Form
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from fastapi.responses import HTMLResponse, RedirectResponse
import db_connection as db
from math import ceil
import api
from datetime import datetime, timedelta
import os

app = api.app

# Ensure static directory exists
static_dir = os.path.join(os.path.dirname(__file__), "static")
if not os.path.exists(static_dir):
    os.makedirs(static_dir)

# Create a basic favicon if it doesn't exist
favicon_path = os.path.join(static_dir, "favicon.ico")
if not os.path.exists(favicon_path):
    # Create minimal 16x16 favicon
    from PIL import Image
    img = Image.new('RGB', (16, 16), color='blue')
    img.save(favicon_path, 'ICO')

# Mount static files with proper configuration
app.mount("/static", StaticFiles(directory=static_dir), name="static")

templates = Jinja2Templates(directory="templates")
templates.env.globals.update(min=min)

@app.get("/", response_class=HTMLResponse)
async def root(request: Request):
    """Redirect root to dashboard"""
    return templates.TemplateResponse("redirect.html", {
        "request": request,
        "url": "/dashboard"
    })

@app.get("/dashboard", response_class=HTMLResponse)
async def dashboard(
    request: Request, 
    page: int = 1,
    imei: str = None,
    start_date: str = None,
    end_date: str = None
):
    devices = db.get_all_devices()
    device_status = None
    data = None

    # Get default last update data
    default_device_data = []
    if not imei and not start_date and not end_date:
        for device in devices:
            device_imei = device['imei']
            last_data = db.get_latest_data_by_imei(device_imei)
            if last_data:
                default_device_data.append(last_data)
        data = default_device_data
    else:
        # Handle filtered data
        if imei:
            # Get device status if specific device selected
            last_data = db.get_latest_data_by_imei(imei)
            heartbeat = db.get_latest_heartbeat(imei)
            
            if last_data and heartbeat:
                device_status = {
                    'voltage': heartbeat.get('voltage'),
                    'persentase_baterai': heartbeat.get('persentase_baterai'),
                    'timestamp': last_data.get('timestamp'),
                    'is_online': (datetime.now() - datetime.strptime(last_data['timestamp'], '%Y-%m-%d %H:%M:%S')).total_seconds() < 3600
                }
            
            # Get filtered data by date range if specified
            if start_date and end_date:
                try:
                    start_dt = datetime.strptime(start_date, '%Y-%m-%dT%H:%M')
                    end_dt = datetime.strptime(end_date, '%Y-%m-%dT%H:%M')
                    data = db.get_registration_data_by_date_range(imei, start_dt, end_dt)
                except ValueError:
                    data = db.get_registration_data_by_imei(imei)
            else:
                data = db.get_registration_data_by_imei(imei)
        else:
            # Get all data with optional date filter
            if start_date and end_date:
                try:
                    start_dt = datetime.strptime(start_date, '%Y-%m-%dT%H:%M')
                    end_dt = datetime.strptime(end_date, '%Y-%m-%dT%H:%M')
                    data = db.get_all_registration_data_by_date_range(start_dt, end_dt)
                except ValueError:
                    data = db.get_all_registration_data()
            else:
                data = db.get_all_registration_data()

    if data:
        # Pagination logic
        ITEMS_PER_PAGE = 10
        total_items = len(data)
        total_pages = ceil(total_items / ITEMS_PER_PAGE)
        start_idx = (page - 1) * ITEMS_PER_PAGE
        end_idx = start_idx + ITEMS_PER_PAGE
        current_data = data[start_idx:end_idx]
        
        return templates.TemplateResponse(
            "index.html",
            {
                "request": request,
                "data": current_data,
                "page": page,
                "total_pages": total_pages,
                "total_items": total_items,
                "devices": devices,
                "selected_imei": imei or "",
                "start_date": start_date or "",
                "end_date": end_date or "",
                "now": datetime.now().strftime('%Y-%m-%dT%H:%M'),
                "device_status": device_status,
            }
        )
    
    return templates.TemplateResponse(
        "error.html",
        {
            "request": request,
            "message": "No data found"
        }
    )

@app.get("/insert", response_class=HTMLResponse)
async def insert_page(request: Request):
    """Render insert device page"""
    return templates.TemplateResponse("insert.html", {
        "request": request,
        "message": None
    })

@app.post("/insert", response_class=HTMLResponse)
async def insert_device(
    request: Request,
    imei: str = Form(...),
    serial_number: str = Form(...)
):
    """Handle device insertion"""
    success = db.insert_device_data(imei, serial_number)
    if success:
        # Redirect to dashboard with success message
        response = RedirectResponse(url="/dashboard", status_code=303)
        return response
    else:
        # Re-render form with error message
        return templates.TemplateResponse("insert.html", {
            "request": request,
            "message": "Failed to insert device. Please try again."
        })

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=5003)
