import pymysql
from sshtunnel import SSHTunnelForwarder
from datetime import datetime, timedelta

def create_ssh_tunnel():
    # Konfigurasi SSH
    ssh_config = {
        'ssh_host': '36.92.168.182',
        'ssh_port': 22,
        'ssh_username': 'nociot',
        'ssh_password': 'telkom!@#321',
    }

    # Konfigurasi Database
    db_config = {
        'db_host': 'localhost',
        'db_port': 3306,
        'db_name': 'lansitec_cat1',
        'db_user': 'admin',
        'db_password': 'Wow0w0!2025'
    }

    try:
        # Membuat SSH tunnel
        tunnel = SSHTunnelForwarder(
            (ssh_config['ssh_host'], ssh_config['ssh_port']),
            ssh_username=ssh_config['ssh_username'],
            ssh_password=ssh_config['ssh_password'],
            remote_bind_address=('127.0.0.1', db_config['db_port'])
        )
        
        # Memulai tunnel
        tunnel.start()

        # Membuat koneksi database melalui tunnel
        connection = pymysql.connect(
            host=db_config['db_host'],
            port=tunnel.local_bind_port,
            user=db_config['db_user'],
            password=db_config['db_password'],
            database=db_config['db_name']
        )

        return tunnel, connection

    except Exception as e:
        print(f"Error saat membuat koneksi: {str(e)}")
        return None, None

def get_all_registration_data():
    tunnel, connection = create_ssh_tunnel()
    if tunnel is None or connection is None:
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
        tunnel.close()

def insert_device_data(imei, serial_number):
    tunnel, connection = create_ssh_tunnel()
    
    if tunnel is None or connection is None:
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
        tunnel.close()

def get_device_count():
    tunnel, connection = create_ssh_tunnel()
    
    if tunnel is None or connection is None:
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
        tunnel.close()

def get_all_devices():
    tunnel, connection = create_ssh_tunnel()
    if tunnel is None or connection is None:
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
        tunnel.close()

def get_registration_data_by_imei(imei=None):
    tunnel, connection = create_ssh_tunnel()
    if tunnel is None or connection is None:
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
        tunnel.close()

def get_registration_data_by_date_range(imei, start_date, end_date):
    tunnel, connection = create_ssh_tunnel()
    if tunnel is None or connection is None:
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
        tunnel.close()

def get_latest_gps_data(imei):
    tunnel, connection = create_ssh_tunnel()
    if tunnel is None or connection is None:
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
        tunnel.close()

def get_gps_data_by_date_range(imei, start_date, end_date):
    tunnel, connection = create_ssh_tunnel()
    if tunnel is None or connection is None:
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
        tunnel.close()

def get_non_gps_data_by_date_range(imei, start_date, end_date):
    tunnel, connection = create_ssh_tunnel()
    if tunnel is None or connection is None:
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
        tunnel.close()

def get_latest_heartbeat(imei):
    tunnel, connection = create_ssh_tunnel()
    if tunnel is None or connection is None:
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
        tunnel.close()

def get_latest_data_by_imei(imei):
    tunnel, connection = create_ssh_tunnel()
    if tunnel is None or connection is None:
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
        tunnel.close()

def get_registration_data_by_imei(imei):
    tunnel, connection = create_ssh_tunnel()
    if tunnel is None or connection is None:
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
        tunnel.close()

def get_all_registration_data_by_date_range(start_date, end_date):
    tunnel, connection = create_ssh_tunnel()
    if tunnel is None or connection is None:
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
        tunnel.close()

if __name__ == "__main__":
    # Mengambil dan menampilkan data
    data = get_all_registration_data()
    if data:
        print(f"Total data yang ditemukan: {len(data)}")
        for row in data:
            print(row)

