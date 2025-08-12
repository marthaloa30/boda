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

def init_db():
    conn = psycopg2.connect(DATABASE_URL)
    c = conn.cursor()
    c.execute('''
        CREATE TABLE IF NOT EXISTS invitados (
            id SERIAL PRIMARY KEY,
            nombre TEXT NOT NULL,
            correo TEXT NOT NULL,
            ceremonia TEXT NOT NULL,
            comentarios TEXT
        )
    ''')
    conn.commit()
    conn.close()

init_db()

@app.route('/admin')
@requiere_autenticacion
def admin():
    conn = psycopg2.connect(DATABASE_URL)
    c = conn.cursor()
    c.execute('SELECT nombre, correo, ceremonia, comentarios FROM invitados')
    datos = c.fetchall()
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
    comentarios = request.form['comentarios']

    conn = psycopg2.connect(DATABASE_URL)
    c = conn.cursor()
    c.execute("INSERT INTO invitados (nombre, correo, ceremonia, comentarios) VALUES (%s, %s, %s, %s)",
              (nombre, correo, ceremonia, comentarios))
    conn.commit()
    conn.close()
    return redirect(url_for('gracias'))

@app.route('/lista')
def ver_lista():
    conn = psycopg2.connect(DATABASE_URL)
    c = conn.cursor()
    c.execute('SELECT nombre, correo, ceremonia, comentarios FROM invitados')
    invitados = c.fetchall()

    # Contar cuantos dijeron Sí y No en ceremonia
    c.execute("SELECT COUNT(*) FROM invitados WHERE ceremonia = 'Sí'")
    si_ceremonia = c.fetchone()[0]

    c.execute("SELECT COUNT(*) FROM invitados WHERE ceremonia = 'No'")
    no_ceremonia = c.fetchone()[0]

    conn.close()
    return render_template('lista.html', invitados=invitados, si_ceremonia=si_ceremonia, no_ceremonia=no_ceremonia)


@app.route('/descargar')
@requiere_autenticacion
def descargar_csv():
    conn = psycopg2.connect(DATABASE_URL)
    c = conn.cursor()
    c.execute('SELECT * FROM invitados')
    datos = c.fetchall()
    conn.close()

    output = io.StringIO()
    writer = csv.writer(output)
    writer.writerow(['ID', 'Nombre', 'Correo', 'Ceremonia', 'Comentarios'])
    writer.writerows(datos)
    output.seek(0)

    return send_file(io.BytesIO(output.read().encode('utf-8')),
                     mimetype='text/csv',
                     download_name='invitados.csv',
                     as_attachment=True)

@app.route('/gracias')
def gracias():
    return render_template('gracias.html')

if __name__ == '__main__':
    app.run(debug=True)
