import pymysql
from datetime import datetime, timedelta

def get_db_connection():
    try:
        # Konfigurasi Database
        connection = pymysql.connect(
            host='127.0.0.1',
            port=3306,
            database='lansitec_cat1',
            user='admin',
            password='Wow0w0!2025'
        )
        return connection
    except Exception as e:
        print(f"Error connecting to database: {str(e)}")
        return None

def get_all_registration_data():
    connection = get_db_connection()
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
    connection = get_db_connection()
    
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
    connection = get_db_connection()
    
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
    connection = get_db_connection()
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
    connection = get_db_connection()
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
    connection = get_db_connection()
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
    connection = get_db_connection()
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
    connection = get_db_connection()
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
    connection = get_db_connection()
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
    connection = get_db_connection()
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
    connection = get_db_connection()
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
    connection = get_db_connection()
    if connection is None:
        return None
    
    try:
        with connection.cursor() as cursor:
            sql = """
                SELECT id, payload_id_1, payload_id_2, timestamp,
                       longitude, latitude, voltage, persentase_baterai,
                       Major, Minor, alarm
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
                
                # Get beacon location info if it's a beacon record
                if row_dict.get('payload_id_2') == 'Beacon' and row_dict.get('Major') and row_dict.get('Minor'):
                    beacon_info = get_beacon_location(row_dict['Major'], row_dict['Minor'])
                    if beacon_info:
                        row_dict['beacon_name'] = beacon_info.get('name')
                        row_dict['location_name'] = beacon_info.get('location_name')
                
                formatted_result.append(row_dict)
            
            return formatted_result
            
    except Exception as e:
        print(f"Error getting data by IMEI: {str(e)}")
        return None
    finally:
        connection.close()

def get_all_registration_data_by_date_range(start_date, end_date):
    connection = get_db_connection()
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
    connection = get_db_connection()
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
    connection = get_db_connection()
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

def extract_major_minor(parsed_data):
    try:
        if not parsed_data:
            return None, None
        
        # Common patterns for beacon data
        if "Major:" in parsed_data and "Minor:" in parsed_data:
            parts = parsed_data.split(',')
            for part in parts:
                if "Major:" in part and "Minor:" in part:
                    # Example format: "Major:1234/Minor:5678"
                    major_minor = part.strip().split('/')
                    major = major_minor[0].split(':')[1].strip()
                    minor = major_minor[1].split(':')[1].strip()
                    return major, minor
                    
        return None, None
    except Exception as e:
        print(f"Error parsing Major/Minor: {str(e)}")
        return None, None

def get_beacon_registration_data(imei=None, start_date=None, end_date=None):
    connection = get_db_connection()
    if connection is None:
        return None
    
    try:
        with connection.cursor() as cursor:
            sql = """
                SELECT id, payload_id_1, payload_id_2, timestamp, 
                       Major, Minor, voltage, persentase_baterai,
                       alarm, latitude, longitude
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
                
                # Get beacon location info if available
                if row_dict.get('Major') and row_dict.get('Minor'):
                    beacon_info = get_beacon_location(row_dict['Major'], row_dict['Minor'])
                    if beacon_info:
                        row_dict['beacon_name'] = beacon_info.get('name')
                        row_dict['location_name'] = beacon_info.get('location_name')
                
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

