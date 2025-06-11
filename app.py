from flask import Flask, request, jsonify
from flask_cors import CORS  #  Importa CORS
import psycopg2

app = Flask(__name__)
CORS(app)  #  Habilita CORS para todas las rutas

DB_URL = "postgresql://requisitoriados_user:x0xLGMH3N71ZfUG9UX7rcBiujKiELzKY@dpg-d114ho2li9vc738covqg-a.oregon-postgres.render.com/requisitoriados"

def connect_db():
    return psycopg2.connect(DB_URL, sslmode='require')

def init_notificaciones_table():
    conn = connect_db()
    cur = conn.cursor()
    cur.execute("""
        CREATE TABLE IF NOT EXISTS notificaciones (
            id SERIAL PRIMARY KEY,
            usuario_id INTEGER NOT NULL,
            tipo VARCHAR(50) NOT NULL,
            mensaje TEXT NOT NULL,
            fecha TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        );
    """)
    conn.commit()
    cur.close()
    conn.close()

@app.route('/notificaciones', methods=['POST'])
def crear_notificacion():
    data = request.get_json()
    usuario_id = data.get('usuario_id')
    tipo = data.get('tipo')
    mensaje = data.get('mensaje')

    if not usuario_id or not tipo or not mensaje:
        return jsonify({"exito": False, "error": "Campos incompletos"}), 400

    conn = connect_db()
    cur = conn.cursor()
    cur.execute("""
        INSERT INTO notificaciones (usuario_id, tipo, mensaje)
        VALUES (%s, %s, %s)
        RETURNING id;
    """, (usuario_id, tipo, mensaje))
    notificacion_id = cur.fetchone()[0]
    conn.commit()
    cur.close()
    conn.close()

    return jsonify({"exito": True, "notificacion_id": notificacion_id})

@app.route('/notificaciones/<int:usuario_id>', methods=['GET'])
def obtener_notificaciones(usuario_id):
    conn = connect_db()
    cur = conn.cursor()
    cur.execute("""
        SELECT id, tipo, mensaje, fecha
        FROM notificaciones
        WHERE usuario_id = %s
        ORDER BY fecha DESC;
    """, (usuario_id,))
    rows = cur.fetchall()
    cur.close()
    conn.close()

    notificaciones = []
    for row in rows:
        notificaciones.append({
            "id": row[0],
            "tipo": row[1],
            "mensaje": row[2],
            "fecha": row[3].isoformat()
        })

    return jsonify({"exito": True, "notificaciones": notificaciones})

@app.route('/notificaciones/<int:notificacion_id>', methods=['DELETE'])
def eliminar_notificacion(notificacion_id):
    conn = connect_db()
    cur = conn.cursor()

    cur.execute("SELECT id FROM notificaciones WHERE id = %s;", (notificacion_id,))
    if not cur.fetchone():
        cur.close()
        conn.close()
        return jsonify({"exito": False, "error": "Notificación no encontrada"}), 404

    cur.execute("DELETE FROM notificaciones WHERE id = %s;", (notificacion_id,))
    conn.commit()
    cur.close()
    conn.close()

    return jsonify({"exito": True, "mensaje": "Notificación eliminada"})

@app.route('/notificaciones/usuario/<int:usuario_id>', methods=['DELETE'])
def eliminar_todas_notificaciones(usuario_id):
    conn = connect_db()
    cur = conn.cursor()

    cur.execute("SELECT id FROM notificaciones WHERE usuario_id = %s;", (usuario_id,))
    if cur.rowcount == 0:
        cur.close()
        conn.close()
        return jsonify({"exito": False, "error": "No hay notificaciones para este usuario"}), 404

    cur.execute("DELETE FROM notificaciones WHERE usuario_id = %s;", (usuario_id,))
    conn.commit()
    cur.close()
    conn.close()

    return jsonify({"exito": True, "mensaje": "Todas las notificaciones del usuario han sido eliminadas"})



if __name__ != '__main__':
    # Producción (Gunicorn, etc.)
    init_notificaciones_table()
else:
    # Desarrollo local
    init_notificaciones_table()
    app.run(debug=True)
