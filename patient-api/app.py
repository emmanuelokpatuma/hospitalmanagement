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
    'driver': '{ODBC Driver 17 for SQL Server}'
}

# Helper function to get DB connection
def get_db_connection():
    conn_str = f"DRIVER={DB_CONFIG['driver']};SERVER={DB_CONFIG['server']};DATABASE={DB_CONFIG['database']};UID={DB_CONFIG['username']};PWD={DB_CONFIG['password']}"
    return pyodbc.connect(conn_str)

# Create patients table if not exists
with get_db_connection() as conn:
    cursor = conn.cursor()
    cursor.execute("""
        IF NOT EXISTS (SELECT * FROM sysobjects WHERE name='patients' AND xtype='U')
        CREATE TABLE patients (
            id INT IDENTITY(1,1) PRIMARY KEY,
            name VARCHAR(255),
            age INT
        )
    """)
    conn.commit()

# Get all patients
@app.route('/patients', methods=['GET'])
def get_patients():
    with get_db_connection() as conn:
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM patients")
        patients = cursor.fetchall()
        # Convert to dict
        result = [{'id': row[0], 'name': row[1], 'age': row[2]} for row in patients]
    return jsonify(result)

# Add a patient
@app.route('/patients', methods=['POST'])
def add_patient():
    data = request.json
    name = data.get('name')
    age = data.get('age')
    with get_db_connection() as conn:
        cursor = conn.cursor()
        cursor.execute("INSERT INTO patients (name, age) VALUES (?, ?)", (name, age))
        conn.commit()
        cursor.execute("SELECT @@IDENTITY")
        patient_id = cursor.fetchone()[0]
    return jsonify({'id': patient_id, 'name': name, 'age': age})

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=3000)
