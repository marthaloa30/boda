from flask import Flask, render_template, request, redirect, url_for, send_file, Response
import psycopg2
import csv
import io
from functools import wraps
import os

USUARIO_ADMIN = "novios"
CONTRASENA_ADMIN = "123bodita"

DATABASE_URL = os.getenv("DATABASE_URL")

app = Flask(__name__)

def autenticar():
    return Response(
        'Acceso restringido. Se requieren credenciales.', 401,
        {'WWW-Authenticate': 'Basic realm="Zona privada"'}
    )

def requiere_autenticacion(f):
    @wraps(f)
    def decorada(*args, **kwargs):
        auth = request.authorization
        if not auth or auth.username != USUARIO_ADMIN or auth.password != CONTRASENA_ADMIN:
            return autenticar()
        return f(*args, **kwargs)
    return decorada

def get_db_connection():
    conn = psycopg2.connect(DATABASE_URL)
    return conn

def init_db():
    conn = get_db_connection()
    c = conn.cursor()
    c.execute('''
        CREATE TABLE IF NOT EXISTS invitados (
            id SERIAL PRIMARY KEY,
            nombre TEXT NOT NULL,
            correo TEXT NOT NULL,
            ceremonia TEXT NOT NULL,
            comentarios TEXT,
            confirmacion TEXT NOT NULL DEFAULT 'No'
        )
    ''')
    conn.commit()
    c.close()
    conn.close()

init_db()

@app.route('/admin')
@requiere_autenticacion
def admin():
    conn = get_db_connection()
    c = conn.cursor()
    c.execute('SELECT nombre, correo, ceremonia, comentarios, confirmacion FROM invitados ORDER BY id DESC')
    datos = c.fetchall()
    c.close()
    conn.close()
    return render_template('admin.html', invitados=datos)

@app.route('/')
def formulario():
    return render_template('formulario.html')

@app.route('/registrar', methods=['POST'])
def registrar():
    nombre = request.form['nombre']
    correo = request.form['correo']
    ceremonia = request.form['ceremonia']
    comentarios = request.form.get('comentarios', '')
    confirmacion = request.form.get('confirmacion', 'No')

    conn = get_db_connection()
    c = conn.cursor()
    c.execute(
        "INSERT INTO invitados (nombre, correo, ceremonia, comentarios, confirmacion) VALUES (%s, %s, %s, %s, %s)",
        (nombre, correo, ceremonia, comentarios, confirmacion)
    )
    conn.commit()
    c.close()
    conn.close()
    return redirect(url_for('gracias'))

@app.route('/lista')
def ver_lista():
    conn = get_db_connection()
    c = conn.cursor()
    c.execute('SELECT nombre, correo, ceremonia, comentarios, confirmacion FROM invitados ORDER BY id DESC')
    invitados = c.fetchall()

    c.execute("SELECT COUNT(*) FROM invitados WHERE confirmacion = 'Sí'")
    si_count = c.fetchone()[0]

    c.execute("SELECT COUNT(*) FROM invitados WHERE confirmacion = 'No'")
    no_count = c.fetchone()[0]

    c.close()
    conn.close()
    return render_template('lista.html', invitados=invitados, si_count=si_count, no_count=no_count)

@app.route('/descargar')
@requiere_autenticacion
def descargar_csv():
    conn = get_db_connection()
    c = conn.cursor()
    c.execute('SELECT * FROM invitados ORDER BY id DESC')
    datos = c.fetchall()
    c.close()
    conn.close()

    output = io.StringIO()
    writer = csv.writer(output)
    writer.writerow(['ID', 'Nombre', 'Correo', 'Ceremonia', 'Comentarios', 'Confirmación'])
    writer.writerows(datos)
    output.seek(0)

    return send_file(
        io.BytesIO(output.read().encode('utf-8')),
        mimetype='text/csv',
        download_name='invitados.csv',
        as_attachment=True
    )

@app.route('/gracias')
def gracias():
    return render_template('gracias.html')

if __name__ == '__main__':
    app.run(debug=True)
