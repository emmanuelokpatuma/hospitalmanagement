from flask import Flask, request, jsonify
from flask_cors import CORS
import pyodbc
import os

app = Flask(__name__)
CORS(app)

# SQL Server configuration
DB_CONFIG = {
    'server': os.environ.get('DB_SERVER', 'sqlserver'),
    'database': 'hospital',
    'username': 'sa',
    'password': 'YourStrong!Passw0rd',
    'driver': '{ODBC Driver 18 for SQL Server}'
}

def get_db_connection():
    conn_str = f"DRIVER={DB_CONFIG['driver']};SERVER={DB_CONFIG['server']};DATABASE={DB_CONFIG['database']};UID={DB_CONFIG['username']};PWD={DB_CONFIG['password']};TrustServerCertificate=yes;"
    return pyodbc.connect(conn_str)

# Create appointments table
with get_db_connection() as conn:
    cursor = conn.cursor()
    cursor.execute("""
        IF NOT EXISTS (SELECT * FROM sysobjects WHERE name='appointments' AND xtype='U')
        CREATE TABLE appointments (
            id INT IDENTITY(1,1) PRIMARY KEY,
            patient_id INT,
            doctor VARCHAR(255),
            date DATE,
            time TIME
        )
    """)
    conn.commit()

# Get all appointments (FIXED)
@app.route('/appointments', methods=['GET'])
def get_appointments():
    with get_db_connection() as conn:
        cursor = conn.cursor()
        cursor.execute("""
            SELECT
                id,
                patient_id,
                doctor,
                CONVERT(VARCHAR(10), date, 120) AS date,
                CONVERT(VARCHAR(5), time, 108) AS time
            FROM appointments
        """)
        appointments = cursor.fetchall()
        # Convert to dict
        result = [{'id': row[0], 'patient_id': row[1], 'doctor': row[2], 'date': row[3], 'time': row[4]} for row in appointments]

    return jsonify(result)

# Health check endpoint
@app.route('/health', methods=['GET'])
def health():
    return jsonify({'status': 'healthy'}), 200

# Add appointment
@app.route('/appointments', methods=['POST'])
def add_appointment():
    data = request.json
    patient_id = data.get('patient_id')
    doctor = data.get('doctor')
    date = data.get('date')
    time = data.get('time')

    with get_db_connection() as conn:
        cursor = conn.cursor()
        cursor.execute(
            "INSERT INTO appointments (patient_id, doctor, date, time) VALUES (?, ?, ?, ?)",
            (patient_id, doctor, date, time)
        )
        conn.commit()
        cursor.execute("SELECT @@IDENTITY")
        appointment_id = cursor.fetchone()[0]

    return jsonify({
        'id': appointment_id,
        'patient_id': patient_id,
        'doctor': doctor,
        'date': date,
        'time': time
    })

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=3001)
