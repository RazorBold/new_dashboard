from flask import Flask, render_template, request
import requests
from math import ceil

app = Flask(__name__)

API_BASE_URL = "http://localhost:5003"
ITEMS_PER_PAGE = 10

@app.route('/')
def index():
    page = request.args.get('page', 1, type=int)
    
    # Fetch data from API
    response = requests.get(f"{API_BASE_URL}/registration/all")
    if response.status_code == 200:
        all_data = response.json()['data']
        
        # Calculate pagination
        total_items = len(all_data)
        total_pages = ceil(total_items / ITEMS_PER_PAGE)
        
        # Slice data for current page
        start_idx = (page - 1) * ITEMS_PER_PAGE
        end_idx = start_idx + ITEMS_PER_PAGE
        current_data = all_data[start_idx:end_idx]
        
        return render_template(
            'index.html',
            data=current_data,
            page=page,
            total_pages=total_pages,
            total_items=total_items
        )
    else:
        return render_template('error.html', message="Failed to fetch data")

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5004, debug=True)
