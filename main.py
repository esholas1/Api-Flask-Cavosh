from flask import Flask, request, jsonify
from flask_cors import CORS
import mysql.connector
from mysql.connector import Error
from werkzeug.security import generate_password_hash, check_password_hash
from datetime import datetime, timedelta
import random

app = Flask(__name__)
CORS(app)

DB_CONFIG = {
    "host": "127.0.0.1",
    "port": 3306,
    "user": "root",
    "password": "",
    "database": "cavoshcafe",
}


def get_connection():
    """Crear una conexión nueva a MySQL."""
    return mysql.connector.connect(**DB_CONFIG)

@app.route("/api/cliente/registrar", methods=["POST"])
def registrar_cliente():
    data = request.get_json(silent=True) or {}

    nombres = data.get("nombres")
    correo = data.get("correo")
    passwordd = data.get("passwordd")

    if not nombres or not correo or not passwordd:
        return jsonify({"ok": False, "message": "Todos los campos son obligatorios"}), 400

    try:
        cnx = get_connection()
        cursor = cnx.cursor(dictionary=True)
        cursor.execute("SELECT id FROM clientes WHERE correo = %s", (correo,))
        existe = cursor.fetchone()
        if existe:
            cursor.close()
            cnx.close()
            return jsonify({"ok": False, "message": "Correo ya registrado"}), 400
        hashed = generate_password_hash(passwordd)

        cursor.execute(
            "INSERT INTO clientes (nombres, correo, passwordd) VALUES (%s, %s, %s)",
            (nombres, correo, hashed),
        )
        cnx.commit()
        nuevo_id = cursor.lastrowid

        cursor.close()
        cnx.close()

        return jsonify(
            {
                "ok": True,
                "message": "Cliente registrado correctamente",
                "cliente_id": nuevo_id,
            }
        ), 201

    except Error as e:
        print("Error MySQL en registrar_cliente:", e)
        return jsonify({"ok": False, "message": "Error interno en el servidor"}), 500

@app.route("/api/cliente/login", methods=["POST"])
def login_cliente():
    data = request.get_json(silent=True) or {}

    correo = data.get("correo")
    passwordd = data.get("passwordd")

    if not correo or not passwordd:
        return jsonify({"ok": False, "message": "Correo y contraseña son obligatorios"}), 400

    try:
        cnx = get_connection()
        cursor = cnx.cursor(dictionary=True)

        cursor.execute("SELECT * FROM clientes WHERE correo = %s", (correo,))
        cliente = cursor.fetchone()

        cursor.close()
        cnx.close()

        if not cliente:
            return jsonify({"ok": False, "message": "Correo incorrecto"}), 400

        if not check_password_hash(cliente["passwordd"], passwordd):
            return jsonify({"ok": False, "message": "Contraseña incorrecta"}), 400

        return jsonify(
            {
                "ok": True,
                "message": "Login correcto",
                "cliente_id": cliente["id"],
                "nombres": cliente["nombres"],
            }
        ), 200

    except Error as e:
        print("Error MySQL en login_cliente:", e)
        return jsonify({"ok": False, "message": "Error interno en el servidor"}), 500

@app.route("/api/cliente/enviar-codigo", methods=["POST"])
def enviar_codigo():
    data = request.get_json(silent=True) or {}
    correo = data.get("correo")

    if not correo:
        return jsonify({"ok": False, "message": "El correo es obligatorio"}), 400

    try:
        cnx = get_connection()
        cursor = cnx.cursor(dictionary=True)

        cursor.execute("SELECT id FROM clientes WHERE correo = %s", (correo,))
        cliente = cursor.fetchone()

        if not cliente:
            cursor.close()
            cnx.close()
            return jsonify({"ok": False, "message": "Correo no registrado"}), 400

        cliente_id = cliente["id"]

        codigo = random.randint(1000, 9999)
        fecha_caducidad = datetime.now() + timedelta(minutes=5)

        cursor.execute(
            """
            INSERT INTO codigo_verificaciones (cliente_id, codigo, fecha_caducidad)
            VALUES (%s, %s, %s)
            """,
            (cliente_id, codigo, fecha_caducidad),
        )
        cnx.commit()

        cursor.close()
        cnx.close()

        print(f"[SIMULADO] Código para cliente_id={cliente_id}, correo={correo}: {codigo}")

        return jsonify(
            {
                "ok": True,
                "message": "Código generado y guardado",
                "cliente_id": cliente_id,
            }
        ), 200

    except Error as e:
        print("Error MySQL en enviar_codigo:", e)
        return jsonify({"ok": False, "message": "Error interno en el servidor"}), 500

@app.route("/api/cliente/validar-codigo", methods=["POST"])
def validar_codigo():
    data = request.get_json(silent=True) or {}

    cliente_id = data.get("cliente_id")
    codigo = data.get("codigo")

    if not cliente_id or not codigo:
        return jsonify({"ok": False, "message": "cliente_id y codigo son obligatorios"}), 400

    try:
        cnx = get_connection()
        cursor = cnx.cursor(dictionary=True)

        cursor.execute(
            """
            SELECT * FROM codigo_verificaciones
            WHERE cliente_id = %s AND codigo = %s AND fecha_caducidad > NOW()
            ORDER BY id DESC
            LIMIT 1
            """,
            (cliente_id, codigo),
        )
        registro = cursor.fetchone()

        cursor.close()
        cnx.close()

        if not registro:
            return jsonify(
                {"ok": False, "message": "Código inválido o expirado"}
            ), 400

        return jsonify({"ok": True, "message": "Código validado correctamente"}), 200

    except Error as e:
        print("Error MySQL en validar_codigo:", e)
        return jsonify({"ok": False, "message": "Error interno en el servidor"}), 500

if __name__ == "__main__":
    app.run(debug=True)
