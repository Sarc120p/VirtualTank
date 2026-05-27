"""
PyHMI - Central Server.
Reads data from the Modbus simulator and provides a REST API for the dashboard.
Includes persistent history in SQLite, bidirectional commands, and recipe management.
"""
import os
import csv
import time
import threading
from datetime import datetime
from flask import Flask, jsonify, render_template, request
from flask_sqlalchemy import SQLAlchemy
from pymodbus.client.sync import ModbusTcpClient

app = Flask(__name__)

MODBUS_HOST = "127.0.0.1"
MODBUS_PORT = 5020

# Database configuration
basedir = os.path.abspath(os.path.dirname(__file__))
db_path = os.path.join(basedir, 'database', 'history.db')
os.makedirs(os.path.dirname(db_path), exist_ok=True)
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///' + db_path
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
db = SQLAlchemy(app)

# Recipes directory
RECEITAS_DIR = os.path.join(basedir, 'receitas')


# ------------------------------------------------------------
# Database model
# ------------------------------------------------------------
class Leitura(db.Model):
    __tablename__ = 'leitura'
    id = db.Column(db.Integer, primary_key=True)
    timestamp = db.Column(db.DateTime, default=datetime.utcnow)
    temperatura = db.Column(db.Float)
    pressao = db.Column(db.Float)
    nivel = db.Column(db.Float)
    velocidade = db.Column(db.Float)
    valvula = db.Column(db.Integer)
    alarme_temp = db.Column(db.Integer)
    alarme_pressao_baixa = db.Column(db.Integer)
    alarme_pressao_alta = db.Column(db.Integer)
    arrefecimento = db.Column(db.Integer)
    lotes = db.Column(db.Integer)
    tempo = db.Column(db.Integer)


# ------------------------------------------------------------
# Modbus register mapping
# ------------------------------------------------------------
REGISTOS = {
    0: ("Temperature", "C", 10),
    1: ("Pressure", "kPa", 10),
    2: ("Level", "%", 10),
    3: ("Agitator", "RPM", 1),
    4: ("Drain Valve", "", 1),
    5: ("Temp Alarm", "", 1),
    6: ("Low Pressure Alarm", "", 1),
    7: ("Batches", "", 1),
    8: ("Elapsed Time", "min", 1),
    9: ("High Pressure Alarm", "", 1),
    10: ("Cooling", "", 1),
    11: ("State", "", 1),
    12: ("PRV", "", 1),
}


# ------------------------------------------------------------
# Modbus communication
# ------------------------------------------------------------
def criar_cliente():
    return ModbusTcpClient(MODBUS_HOST, port=MODBUS_PORT)


def ler_registos():
    client = criar_cliente()
    try:
        if not client.connect():
            return None
        result = client.read_holding_registers(0, count=13)
        if result.isError():
            return None

        data = {}
        for i, raw_value in enumerate(result.registers):
            name, unit, scale = REGISTOS.get(i, (f"Register {i}", "", 1))
            data[name] = {
                "value": round(raw_value / scale, 1),
                "unit": unit,
                "raw": raw_value,
                "alarm": bool(raw_value) if i in (5, 6, 9) else False,
            }
        return data
    finally:
        client.close()


# ------------------------------------------------------------
# History thread
# ------------------------------------------------------------
def salvar_leitura():
    with app.app_context():
        while True:
            data = ler_registos()
            if data:
                reading = Leitura(
                    temperatura=data["Temperature"]["value"],
                    pressao=data["Pressure"]["value"],
                    nivel=data["Level"]["value"],
                    velocidade=data["Agitator"]["value"],
                    valvula=data["Drain Valve"]["value"],
                    alarme_temp=data["Temp Alarm"]["value"],
                    alarme_pressao_baixa=data["Low Pressure Alarm"]["value"],
                    alarme_pressao_alta=data["High Pressure Alarm"]["value"],
                    arrefecimento=data["Cooling"]["value"],
                    lotes=data["Batches"]["value"],
                    tempo=data["Elapsed Time"]["value"],
                )
                db.session.add(reading)
                db.session.commit()
            time.sleep(5)


# ------------------------------------------------------------
# Application routes
# ------------------------------------------------------------
@app.route("/")
def dashboard():
    return render_template("dashboard.html")


@app.route("/api/data")
def api_data():
    data = ler_registos()
    if data is None:
        return jsonify({"error": "PLC communication failure", "connected": False}), 503
    return jsonify({**data, "connected": True})


@app.route("/api/command", methods=["POST"])
def api_command():
    req = request.get_json()
    command = req.get("command")
    value = req.get("value", 0)

    client = criar_cliente()
    if not client.connect():
        return jsonify({"error": "PLC offline"}), 503

    if command == "valve":
        client.write_register(4, int(value))
    elif command == "agitator":
        client.write_register(3, int(value))
    elif command == "cooling":
        client.write_register(10, int(value))
    elif command == "set_state":
        client.write_register(11, int(value))
    elif command == "prv":
        client.write_register(12, int(value))
    else:
        client.close()
        return jsonify({"error": "Invalid command"}), 400

    client.close()
    return jsonify({"success": True})


@app.route("/api/history")
def api_history():
    limit = request.args.get("limit", 50, type=int)
    readings = Leitura.query.order_by(Leitura.timestamp.desc()).limit(limit).all()
    return jsonify([{
        "timestamp": r.timestamp.isoformat(),
        "temperature": r.temperatura,
    } for r in readings[::-1]])


# ------------------------------------------------------------
# Recipe routes
# ------------------------------------------------------------
@app.route("/api/recipes")
def api_recipes():
    try:
        files = [f for f in os.listdir(RECEITAS_DIR) if f.lower().endswith('.csv')]
        return jsonify({"recipes": sorted(files)})
    except FileNotFoundError:
        return jsonify({"recipes": []})


@app.route("/api/recipe/<name>")
def api_recipe(name):
    path = os.path.join(RECEITAS_DIR, name)
    if not os.path.exists(path):
        return jsonify({"error": "Recipe not found"}), 404

    phases = []
    with open(path, 'r', encoding='utf-8') as f:
        reader = csv.DictReader(f)
        for row in reader:
            phases.append({
                "phase": int(row["phase"]),
                "target_temp": float(row["target_temp"]),
                "duration_min": int(row["duration_min"]),
                "agitation_rpm": int(row["agitation_rpm"])
            })
    return jsonify({"name": name, "phases": phases})


@app.route("/api/recipe/activate", methods=["POST"])
def api_activate_recipe():
    req = request.get_json()
    name = req.get("name")
    if not name:
        return jsonify({"error": "Recipe name required"}), 400

    path = os.path.join(RECEITAS_DIR, name)
    if not os.path.exists(path):
        return jsonify({"error": "Recipe not found"}), 404

    return jsonify({"success": True, "message": f"Recipe '{name}' selected. (Feature under development)"})


# ------------------------------------------------------------
# Application startup
# ------------------------------------------------------------
if __name__ == "__main__":
    with app.app_context():
        db.create_all()

    history_thread = threading.Thread(target=salvar_leitura, daemon=True)
    history_thread.start()

    print("[PyHMI] Testing Modbus simulator connection...")
    client = criar_cliente()
    if client.connect():
        print("[OK] Simulator connection established.")
        client.close()
    else:
        print("[WARNING] Simulator not found. Start simulador_clp.py first.")

    print("[PyHMI] Flask server running at http://localhost:5000")
    app.run(debug=False)