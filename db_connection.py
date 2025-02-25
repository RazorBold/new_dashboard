import pymysql
from datetime import datetime, timedelta
import json
from shapely.geometry import Point, Polygon

def create_connection():
    # Konfigurasi Database Lokal
    db_config = {
        'host': 'localhost',
        'port': 3306,
        'database': 'lansitec_cat1',
        'user': 'admin',
        'password': 'Wow0w0!2025'
    }

    try:
        connection = pymysql.connect(
            host=db_config['host'],
            port=db_config['port'],
            user=db_config['user'],
            password=db_config['password'],
            database=db_config['database']
        )
        return connection

    except Exception as e:
        print(f"Error saat membuat koneksi: {str(e)}")
        return None

def get_all_registration_data():
    connection = create_connection()
    if connection is None:
        return None
    
    try:
        with connection.cursor() as cursor:
            sql = """
                SELECT id, payload_id_1, payload_id_2, parsed_data,
                       longitude, latitude, timestamp, voltage,
                       persentase_baterai, alarm
                FROM registration 
                ORDER BY timestamp DESC
            """
            cursor.execute(sql)
            result = cursor.fetchall()
            column_names = [desc[0] for desc in cursor.description]
            formatted_result = []
            
            for row in result:
                row_dict = dict(zip(column_names, row))
                if row_dict.get('timestamp'):
                    row_dict['timestamp'] = row_dict['timestamp'].strftime('%Y-%m-%d %H:%M:%S')
                formatted_result.append(row_dict)
            
            return formatted_result
            
    except Exception as e:
        print(f"Error getting data: {str(e)}")
        return None
    finally:
        connection.close()

def insert_device_data(imei, serial_number):
    connection = create_connection()
    
    if connection is None:
        print("Failed to establish connection")
        return False
    
    try:
        with connection.cursor() as cursor:
            sql = "INSERT INTO device (imei, serial_number) VALUES (%s, %s)"
            cursor.execute(sql, (imei, serial_number))
            connection.commit()
            return True
            
    except Exception as e:
        print(f"Error inserting data: {str(e)}")
        return False
        
    finally:
        connection.close()

def get_device_count():
    connection = create_connection()
    
    if connection is None:
        print("Failed to establish connection")
        return 0
    
    try:
        with connection.cursor() as cursor:
            sql = "SELECT COUNT(*) FROM device"
            cursor.execute(sql)
            result = cursor.fetchone()
            return result[0] if result else 0
            
    except Exception as e:
        print(f"Error getting device count: {str(e)}")
        return 0
        
    finally:
        connection.close()

def get_all_devices():
    connection = create_connection()
    if connection is None:
        return []
    
    try:
        with connection.cursor() as cursor:
            sql = "SELECT imei, serial_number FROM device"
            cursor.execute(sql)
            result = cursor.fetchall()
            return [{'imei': row[0], 'serial_number': row[1]} for row in result]
    except Exception as e:
        print(f"Error getting devices: {str(e)}")
        return []
    finally:
        connection.close()

def get_registration_data_by_imei(imei=None):
    connection = create_connection()
    if connection is None:
        return None
    
    try:
        with connection.cursor() as cursor:
            if (imei):
                sql = "SELECT * FROM registration WHERE payload_id_1 = %s"
                cursor.execute(sql, (imei,))
            else:
                sql = "SELECT * FROM registration"
                cursor.execute(sql)
            
            result = cursor.fetchall()
            column_names = [desc[0] for desc in cursor.description]
    except Exception as e:
        print(f"Error getting registration data: {str(e)}")
        return None
    finally:
        connection.close()

def get_registration_data_by_date_range(imei, start_date, end_date):
    connection = create_connection()
    if connection is None:
        return None
    
    try:
        with connection.cursor() as cursor:
            sql = """
                SELECT id, payload_id_1, payload_id_2, parsed_data, 
                       longitude, latitude, timestamp, voltage, 
                       persentase_baterai, alarm
                FROM registration 
                WHERE payload_id_1 = %s 
                AND timestamp BETWEEN %s AND %s 
                ORDER BY timestamp DESC
            """
            cursor.execute(sql, (imei, start_date, end_date))
            result = cursor.fetchall()
            column_names = [desc[0] for desc in cursor.description]
            formatted_result = []
            
            for row in result:
                row_dict = dict(zip(column_names, row))
                # Convert datetime objects to string
                if row_dict.get('timestamp'):
                    row_dict['timestamp'] = row_dict['timestamp'].strftime('%Y-%m-%d %H:%M:%S')
                formatted_result.append(row_dict)
            
            return formatted_result
            
    except Exception as e:
        print(f"Error getting data by date range: {str(e)}")
        return None
    finally:
        connection.close()

def get_latest_gps_data(imei):
    connection = create_connection()
    if connection is None:
        return None
    
    try:
        with connection.cursor() as cursor:
            sql = """
                SELECT * FROM registration 
                WHERE payload_id_1 = %s AND payload_id_2 = 'GNSS'
                ORDER BY timestamp DESC
                LIMIT 1
            """
            cursor.execute(sql, (imei,))
            result = cursor.fetchone()
            if result:
                column_names = [desc[0] for desc in cursor.description]
                return dict(zip(column_names, result))
            return None
    except Exception as e:
        print(f"Error getting latest GPS data: {str(e)}")
        return None
    finally:
        connection.close()

def get_gps_data_by_date_range(imei, start_date, end_date):
    connection = create_connection()
    if connection is None:
        return None
    
    try:
        with connection.cursor() as cursor:
            sql = """
                SELECT id, payload_id_1, parsed_data, 
                       longitude, latitude, timestamp
                FROM registration 
                WHERE payload_id_1 = %s 
                AND payload_id_2 = 'GNSS'
                AND timestamp BETWEEN %s AND %s 
                ORDER BY timestamp DESC
            """
            cursor.execute(sql, (imei, start_date, end_date))
            result = cursor.fetchall()
            column_names = [desc[0] for desc in cursor.description]
            formatted_result = []
            
            for row in result:
                row_dict = dict(zip(column_names, row))
                if row_dict.get('timestamp'):
                    row_dict['timestamp'] = row_dict['timestamp'].strftime('%Y-%m-%d %H:%M:%S')
                formatted_result.append(row_dict)
            
            return formatted_result
            
    except Exception as e:
        print(f"Error getting GPS data: {str(e)}")
        return None
    finally:
        connection.close()

def get_non_gps_data_by_date_range(imei, start_date, end_date):
    connection = create_connection()
    if connection is None:
        return None
    
    try:
        with connection.cursor() as cursor:
            sql = """
                SELECT id, payload_id_1, payload_id_2, parsed_data, 
                       voltage, persentase_baterai, alarm, timestamp
                FROM registration 
                WHERE payload_id_1 = %s 
                AND payload_id_2 != 'GNSS'
                AND timestamp BETWEEN %s AND %s 
                ORDER BY timestamp DESC
            """
            cursor.execute(sql, (imei, start_date, end_date))
            result = cursor.fetchall()
            column_names = [desc[0] for desc in cursor.description]
            formatted_result = []
            
            for row in result:
                row_dict = dict(zip(column_names, row))
                if row_dict.get('timestamp'):
                    row_dict['timestamp'] = row_dict['timestamp'].strftime('%Y-%m-%d %H:%M:%S')
                formatted_result.append(row_dict)
            
            return formatted_result
            
    except Exception as e:
        print(f"Error getting non-GPS data: {str(e)}")
        return None
    finally:
        connection.close()

def get_latest_heartbeat(imei):
    connection = create_connection()
    if connection is None:
        return None
    
    try:
        with connection.cursor() as cursor:
            sql = """
                SELECT id, payload_id_1, payload_id_2, parsed_data, 
                       voltage, persentase_baterai, timestamp
                FROM registration 
                WHERE payload_id_1 = %s 
                AND payload_id_2 = 'Heartbeat'
                ORDER BY timestamp DESC
                LIMIT 1
            """
            cursor.execute(sql, (imei,))
            result = cursor.fetchone()
            if result:
                column_names = [desc[0] for desc in cursor.description]
                data = dict(zip(column_names, result))
                if data.get('timestamp'):
                    data['timestamp'] = data['timestamp'].strftime('%Y-%m-%d %H:%M:%S')
                return data
            return None
    except Exception as e:
        print(f"Error getting latest heartbeat data: {str(e)}")
        return None
    finally:
        connection.close()

def get_latest_data_by_imei(imei):
    connection = create_connection()
    if connection is None:
        return None
    
    try:
        with connection.cursor() as cursor:
            sql = """
                SELECT * FROM registration 
                WHERE payload_id_1 = %s
                ORDER BY timestamp DESC
                LIMIT 1
            """
            cursor.execute(sql, (imei,))
            result = cursor.fetchone()
            if result:
                column_names = [desc[0] for desc in cursor.description]
                data = dict(zip(column_names, result))
                if data.get('timestamp'):
                    data['timestamp'] = data['timestamp'].strftime('%Y-%m-%d %H:%M:%S')
                return data
            return None
    except Exception as e:
        print(f"Error getting latest data: {str(e)}")
        return None
    finally:
        connection.close()

def get_registration_data_by_imei(imei):
    connection = create_connection()
    if connection is None:
        return None
    
    try:
        with connection.cursor() as cursor:
            sql = """
                SELECT id, payload_id_1, payload_id_2, parsed_data,
                       longitude, latitude, timestamp, voltage,
                       persentase_baterai, alarm
                FROM registration 
                WHERE payload_id_1 = %s
                ORDER BY timestamp DESC
            """
            cursor.execute(sql, (imei,))
            result = cursor.fetchall()
            column_names = [desc[0] for desc in cursor.description]
            formatted_result = []
            
            for row in result:
                row_dict = dict(zip(column_names, row))
                if row_dict.get('timestamp'):
                    row_dict['timestamp'] = row_dict['timestamp'].strftime('%Y-%m-%d %H:%M:%S')
                formatted_result.append(row_dict)
            
            return formatted_result
            
    except Exception as e:
        print(f"Error getting data by IMEI: {str(e)}")
        return None
    finally:
        connection.close()

def get_all_registration_data_by_date_range(start_date, end_date):
    connection = create_connection()
    if connection is None:
        return None
    
    try:
        with connection.cursor() as cursor:
            sql = """
                SELECT id, payload_id_1, payload_id_2, parsed_data,
                       longitude, latitude, timestamp, voltage,
                       persentase_baterai, alarm
                FROM registration 
                WHERE timestamp BETWEEN %s AND %s
                ORDER BY timestamp DESC
            """
            cursor.execute(sql, (start_date, end_date))
            result = cursor.fetchall()
            column_names = [desc[0] for desc in cursor.description]
            formatted_result = []
            
            for row in result:
                row_dict = dict(zip(column_names, row))
                if row_dict.get('timestamp'):
                    row_dict['timestamp'] = row_dict['timestamp'].strftime('%Y-%m-%d %H:%M:%S')
                formatted_result.append(row_dict)
            
            return formatted_result
            
    except Exception as e:
        print(f"Error getting data by date range: {str(e)}")
        return None
    finally:
        connection.close()

def get_all_beacon_data():
    connection = create_connection()
    if connection is None:
        return None
    
    try:
        with connection.cursor() as cursor:
            sql = """
                SELECT id, name, major, minor, longitude, latitude, location_name
                FROM data_beacon 
                ORDER BY id
            """
            cursor.execute(sql)
            result = cursor.fetchall()
            column_names = [desc[0] for desc in cursor.description]
            formatted_result = []
            
            for row in result:
                row_dict = dict(zip(column_names, row))
                formatted_result.append(row_dict)
            
            return formatted_result
            
    except Exception as e:
        print(f"Error getting beacon data: {str(e)}")
        return None
    finally:
        connection.close()

def get_beacon_location(major, minor):
    connection = create_connection()
    if connection is None:
        return None
    
    try:
        with connection.cursor() as cursor:
            sql = """
                SELECT id, name, major, minor, longitude, latitude, location_name
                FROM data_beacon 
                WHERE major = %s AND minor = %s
                LIMIT 1
            """
            cursor.execute(sql, (major, minor))
            result = cursor.fetchone()
            if result:
                column_names = [desc[0] for desc in cursor.description]
                return dict(zip(column_names, result))
            return None
            
    except Exception as e:
        print(f"Error getting beacon location: {str(e)}")
        return None
    finally:
        connection.close()

def get_beacon_registration_data(imei=None, start_date=None, end_date=None):
    """Get beacon registration data with optional IMEI and date filters"""
    connection = create_connection()
    if connection is None:
        return None
    
    try:
        with connection.cursor() as cursor:
            sql = """
                SELECT id, payload_id_1, payload_id_2, parsed_data,
                       timestamp, voltage, persentase_baterai
                FROM registration 
                WHERE payload_id_2 = 'Beacon'
            """
            params = []
            
            if imei:
                sql += " AND payload_id_1 = %s"
                params.append(imei)
                
            if start_date and end_date:
                sql += " AND timestamp BETWEEN %s AND %s"
                params.extend([start_date, end_date])
                
            sql += " ORDER BY timestamp DESC"
            
            cursor.execute(sql, params)
            result = cursor.fetchall()
            column_names = [desc[0] for desc in cursor.description]
            formatted_result = []
            
            for row in result:
                row_dict = dict(zip(column_names, row))
                if row_dict.get('timestamp'):
                    row_dict['timestamp'] = row_dict['timestamp'].strftime('%Y-%m-%d %H:%M:%S')
                formatted_result.append(row_dict)
            
            return formatted_result
            
    except Exception as e:
        print(f"Error getting beacon registration data: {str(e)}")
        return None
    finally:
        connection.close()

def get_all_beacon_locations():
    connection = create_connection()
    if connection is None:
        return None
    
    try:
        with connection.cursor() as cursor:
            sql = """
                SELECT id, name, major, minor, 
                       longitude, latitude, location_name
                FROM data_beacon
                ORDER BY id
            """
            cursor.execute(sql)
            result = cursor.fetchall()
            column_names = [desc[0] for desc in cursor.description]
            formatted_result = []
            
            for row in result:
                row_dict = dict(zip(column_names, row))
                formatted_result.append(row_dict)
            
            return formatted_result
            
    except Exception as e:
        print(f"Error getting beacon locations: {str(e)}")
        return None
    finally:
        connection.close()

def get_beacon_location_by_id(major, minor):
    connection = create_connection()
    if connection is None:
        return None
    
    try:
        with connection.cursor() as cursor:
            sql = """
                SELECT longitude, latitude, location_name, name
                FROM data_beacon
                WHERE major = %s AND minor = %s
                LIMIT 1
            """
            cursor.execute(sql, (major, minor))
            result = cursor.fetchone()
            if result:
                return {
                    "longitude": result[0],
                    "latitude": result[1],
                    "location_name": result[2],
                    "beacon_name": result[3]
                }
            return None
            
    except Exception as e:
        print(f"Error getting beacon location by ID: {str(e)}")
        return None
    finally:
        connection.close()

def parse_beacon_data(parsed_data):
    """Parse beacon data to extract major and minor values"""
    try:
        # Handle string that looks like a dict
        if isinstance(parsed_data, str):
            # Replace single quotes with double quotes for valid JSON
            parsed_data = parsed_data.replace("'", '"')
            data = json.loads(parsed_data)
        else:
            data = parsed_data

        beacons = data.get('beacons', [])
        if beacons and isinstance(beacons, list) and len(beacons) > 0:
            major = str(beacons[0].get('major'))
            minor = str(beacons[0].get('minor'))
            if major and minor:
                return major, minor
        return None, None
    except Exception as e:
        print(f"Error parsing beacon data: {str(e)}")
        print(f"Raw data: {parsed_data}")
        return None, None

def get_service_tanto_data():
    connection = create_connection()
    if connection is None:
        return None
    
    try:
        with connection.cursor() as cursor:
            sql = """
                WITH RankedData AS (
                    SELECT id, id_container, last_activity, 
                           date,  -- Remove DATE_FORMAT since it's already a string
                           DATE_FORMAT(created_time, '%Y-%m-%d %H:%i:%s') as created_time,
                           ROW_NUMBER() OVER (PARTITION BY id_container ORDER BY created_time DESC) as rn
                    FROM service_tanto
                )
                SELECT id, id_container, last_activity, date, created_time
                FROM RankedData
                WHERE rn = 1
                ORDER BY created_time DESC
            """
            cursor.execute(sql)
            result = cursor.fetchall()
            column_names = [desc[0] for desc in cursor.description]
            formatted_result = []
            
            for row in result:
                row_dict = dict(zip(column_names, row))
                # Don't try to format the date field since it's already a string
                formatted_result.append(row_dict)
            
            return formatted_result
            
    except Exception as e:
        print(f"Error getting service tanto data: {str(e)}")
        return None
    finally:
        connection.close()

def get_latest_container_activities():
    connection = create_connection()
    if connection is None:
        return None
    
    try:
        with connection.cursor() as cursor:
            sql = """
                WITH RankedData AS (
                    SELECT id_container, last_activity, created_time,
                           ROW_NUMBER() OVER (PARTITION BY id_container ORDER BY created_time DESC) as rn
                    FROM service_tanto
                )
                SELECT id_container, 
                       COALESCE(last_activity, 'No Activity') as last_activity,
                       created_time
                FROM RankedData
                WHERE rn = 1
                ORDER BY created_time DESC
            """
            cursor.execute(sql)
            result = cursor.fetchall()
            column_names = [desc[0] for desc in cursor.description]
            
            # Create a dictionary with container ID as key
            container_activities = {}
            for row in result:
                row_dict = dict(zip(column_names, row))
                container_activities[row_dict['id_container']] = row_dict['last_activity']
            
            return container_activities
            
    except Exception as e:
        print(f"Error getting container activities: {str(e)}")
        return None
    finally:
        connection.close()

def get_all_devices_with_activity():
    connection = create_connection()
    if connection is None:
        return []
    
    try:
        # Get all devices
        devices = get_all_devices()
        if not devices:
            return []
            
        # Get container activities
        container_activities = get_latest_container_activities()
        if not container_activities:
            container_activities = {}
        
        # Merge device info with container activity
        for device in devices:
            device['last_activity'] = container_activities.get(device['serial_number'], 'No Activity')
            
        return devices
            
    except Exception as e:
        print(f"Error getting devices with activities: {str(e)}")
        return []

def get_device_by_imei(imei):
    connection = create_connection()
    if connection is None:
        return None
    
    try:
        with connection.cursor() as cursor:
            sql = "SELECT imei, serial_number FROM device WHERE imei = %s"
            cursor.execute(sql, (imei,))
            result = cursor.fetchone()
            if result:
                return {'imei': result[0], 'serial_number': result[1]}
            return None
    except Exception as e:
        print(f"Error getting device: {str(e)}")
        return None
    finally:
        connection.close()

def get_container_activity(serial_number):
    connection = create_connection()
    if connection is None:
        return None
    
    try:
        with connection.cursor() as cursor:
            sql = """
                SELECT last_activity 
                FROM service_tanto 
                WHERE id_container = %s 
                ORDER BY created_time DESC 
                LIMIT 1
            """
            cursor.execute(sql, (serial_number,))
            result = cursor.fetchone()
            return result[0] if result else None
    except Exception as e:
        print(f"Error getting container activity: {str(e)}")
        return None
    finally:
        connection.close()

def get_all_devices_activities():
    connection = create_connection()
    if connection is None:
        return []
    
    try:
        # Get all devices first
        devices = get_all_devices()
        if not devices:
            return []
        
        # Get all container activities in one query
        with connection.cursor() as cursor:
            placeholders = ', '.join(['%s'] * len(devices))
            serial_numbers = [d['serial_number'] for d in devices]
            
            sql = f"""
                WITH RankedActivities AS (
                    SELECT id_container, last_activity,
                           ROW_NUMBER() OVER (PARTITION BY id_container ORDER BY created_time DESC) as rn
                    FROM service_tanto
                    WHERE id_container IN ({placeholders})
                )
                SELECT id_container, last_activity
                FROM RankedActivities
                WHERE rn = 1
            """
            cursor.execute(sql, serial_numbers)
            activities = {row[0]: row[1] for row in cursor.fetchall()}
        
        # Merge device info with activities
        for device in devices:
            device['last_activity'] = activities.get(device['serial_number'], 'No Activity')
        
        return devices
            
    except Exception as e:
        print(f"Error getting all device activities: {str(e)}")
        return []
    finally:
        connection.close()

def save_geofence(name: str, coordinates: list, description: str = None):
    connection = create_connection()
    if connection is None:
        return False  # Changed from None to False for consistency
    
    try:
        with connection.cursor() as cursor:
            sql = """
                INSERT INTO geofence (name, coordinates, description)
                VALUES (%s, %s, %s)
            """
            cursor.execute(sql, (
                name,
                json.dumps(coordinates),  # Convert list to JSON string
                description
            ))
            connection.commit()
            return True
    except Exception as e:
        print(f"Error saving geofence: {str(e)}")
        return False
    finally:
        connection.close()

def get_all_geofences():
    connection = create_connection()
    if connection is None:
        return None
    
    try:
        with connection.cursor() as cursor:
            sql = "SELECT id, name, coordinates, description FROM geofence"
            cursor.execute(sql)
            result = cursor.fetchall()
            return [
                {
                    'id': row[0],
                    'name': row[1],
                    'coordinates': json.loads(row[2]),
                    'description': row[3]
                }
                for row in result
            ]
    except Exception as e:
        print(f"Error getting geofences: {str(e)}")
        return None
    finally:
        connection.close()

def check_point_in_geofence(lat: float, lng: float):
    """Check if a point is inside any geofence and return the geofence name if found"""
    geofences = get_all_geofences()
    if not geofences:
        return None
        
    try:
        point = Point([lng, lat])  # Create point
        
        for fence in geofences:
            coords = fence['coordinates']
            # Convert coordinates to proper format for Polygon
            polygon_coords = [[p['lng'], p['lat']] for p in coords]
            polygon = Polygon(polygon_coords)
            
            if point.within(polygon):
                print(f"Point {lat}, {lng} is within geofence {fence['name']}")  # Debug line
                return fence['name']
        
        print(f"Point {lat}, {lng} is not within any geofence")  # Debug line
        return None
            
    except Exception as e:
        print(f"Error checking point in geofence: {str(e)}")
        return None

def get_beacon_registration_data(imei=None, start_date=None, end_date=None, limit=None):
    connection = create_connection()
    if connection is None:
        return None
    
    try:
        with connection.cursor() as cursor:
            sql = """
                SELECT id, payload_id_1, payload_id_2, parsed_data,
                       timestamp, voltage, persentase_baterai
                FROM registration 
                WHERE payload_id_2 = 'Beacon'
            """
            params = []
            
            if imei:
                sql += " AND payload_id_1 = %s"
                params.append(imei)
                
            if start_date and end_date:
                sql += " AND timestamp BETWEEN %s AND %s"
                params.extend([start_date, end_date])
                
            sql += " ORDER BY timestamp DESC"
            
            if limit:
                sql += " LIMIT %s"
                params.append(limit)
            
            cursor.execute(sql, params)
            result = cursor.fetchall()
            column_names = [desc[0] for desc in cursor.description]
            formatted_result = []
            
            for row in result:
                row_dict = dict(zip(column_names, row))
                if row_dict.get('timestamp'):
                    row_dict['timestamp'] = row_dict['timestamp'].strftime('%Y-%m-%d %H:%M:%S')
                formatted_result.append(row_dict)
            
            return formatted_result
            
    except Exception as e:
        print(f"Error getting beacon registration data: {str(e)}")
        return None
    finally:
        connection.close()

if __name__ == "__main__":
    # Mengambil dan menampilkan data
    data = get_all_registration_data()
    if data:
        print(f"Total data yang ditemukan: {len(data)}")
        for row in data:
            print(row)
