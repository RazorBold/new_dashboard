from fastapi import FastAPI, Request, Form, HTTPException
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from fastapi.responses import HTMLResponse, RedirectResponse, StreamingResponse
from typing import Optional
import db_connection as db
from math import ceil
import api
from datetime import datetime, timedelta
import os
import pandas as pd
from io import BytesIO

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
                    'is_online': (datetime.now() - datetime.strptime(last_data['timestamp'], '%Y-%m-%d %H:%M:%S')).total_seconds() < 86400  # 24 hours
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

@app.get("/export-excel")
async def export_excel(
    imei: Optional[str] = None,
    start_date: Optional[str] = None,
    end_date: Optional[str] = None
):
    """Export table data to Excel"""
    try:
        # Get data based on filters
        if imei:
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
            if start_date and end_date:
                try:
                    start_dt = datetime.strptime(start_date, '%Y-%m-%dT%H:%M')
                    end_dt = datetime.strptime(end_date, '%Y-%m-%dT%H:%M')
                    data = db.get_all_registration_data_by_date_range(start_dt, end_dt)
                except ValueError:
                    data = db.get_all_registration_data()
            else:
                data = db.get_all_registration_data()

        if not data:
            raise HTTPException(status_code=404, detail="No data found to export")

        # Convert to DataFrame
        df = pd.DataFrame(data)
        
        # Reorder and rename columns for better readability
        columns_order = [
            'payload_id_1', 'payload_id_2', 'timestamp', 
            'latitude', 'longitude', 'voltage', 
            'persentase_baterai', 'alarm', 'parsed_data'
        ]
        
        column_names = {
            'payload_id_1': 'IMEI',
            'payload_id_2': 'Type',
            'timestamp': 'Timestamp',
            'latitude': 'Latitude',
            'longitude': 'Longitude',
            'voltage': 'Voltage',
            'persentase_baterai': 'Battery (%)',
            'alarm': 'Alarm',
            'parsed_data': 'Raw Data'
        }

        # Select and rename columns
        df = df.reindex(columns=[col for col in columns_order if col in df.columns])
        df = df.rename(columns=column_names)

        # Create Excel file in memory
        output = BytesIO()
        with pd.ExcelWriter(output, engine='xlsxwriter') as writer:
            # Write DataFrame to Excel starting from row 4 (after headers)
            df.to_excel(writer, sheet_name='Device Data', index=False, startrow=5)
            
            workbook = writer.book
            worksheet = writer.sheets['Device Data']
            
            # Define formats
            title_format = workbook.add_format({
                'bold': True,
                'font_size': 12,
                'align': 'left'
            })
            
            header_format = workbook.add_format({
                'bold': True,
                'font_color': 'white',
                'bg_color': '#0d6efd',
                'align': 'center',
                'valign': 'vcenter',
                'border': 1
            })

            subheader_format = workbook.add_format({
                'bold': True,
                'font_color': 'black',
                'bg_color': '#e9ecef',
                'align': 'center',
                'valign': 'vcenter',
                'border': 1
            })
            
            cell_format = workbook.add_format({
                'align': 'left',
                'valign': 'vcenter'
            })

            # Write report information (first 3 rows)
            row = 0
            if imei:
                worksheet.write(row, 0, f'Device IMEI: {imei}', title_format)
                row += 1
            if start_date and end_date:
                worksheet.write(row, 0, f'Period: {start_date} to {end_date}', title_format)
                row += 1
            worksheet.write(row, 0, f'Generated: {datetime.now().strftime("%Y-%m-%d %H:%M:%S")}', title_format)

            # Write main headers (row 4)
            row = 4
            headers = ['Device Information', 'Location Data', 'Status', '', '', 'System', '', '', '']
            header_spans = [2, 2, 2, 0, 0, 3, 0, 0, 0]  # 0 means merge into previous
            
            current_col = 0
            for header, span in zip(headers, header_spans):
                if span > 0:
                    worksheet.merge_range(row, current_col, row, current_col + span - 1, header, header_format)
                    current_col += span

            # Write subheaders (row 5)
            row = 5
            for col_num, value in enumerate(df.columns.values):
                worksheet.write(row, col_num, value, subheader_format)

            # Format the data
            data_rows = len(df) + 6  # +6 because data starts at row 6
            for col_num, value in enumerate(df.columns.values):
                # Calculate column width
                max_length = max(
                    df[value].astype(str).str.len().max(),
                    len(str(value))
                )
                worksheet.set_column(col_num, col_num, max_length + 2, cell_format)

        # Reset buffer position
        output.seek(0)
        
        # Generate filename with filter info
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        filename = f"device_data_{imei or 'all'}"
        if start_date and end_date:
            filename += f"_{start_date.split('T')[0]}_{end_date.split('T')[0]}"
        filename += f"_{timestamp}.xlsx"
        
        return StreamingResponse(
            output,
            media_type='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet',
            headers={'            curl "http://127.0.0.1:5003/registrati            curl "http://127.0.0.1:5003/registration/beacon-data?imei=860137071625429"-Disposition': f'attachment; filename="{filename}"'}
        )
        
    except Exception as e:
        print(f"Export error: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Export failed: {str(e)}")

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=5003)
