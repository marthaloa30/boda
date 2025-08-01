from flask import Flask, render_template, request, redirect, url_for, send_file
import sqlite3
import csv
import io
from functools import wraps
from flask import Response, request

USUARIO_ADMIN = "novios"
CONTRASENA_ADMIN = "123bodita"


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


# Crear tabla si no existe
def init_db():
    conn = sqlite3.connect('invitados.db')
    c = conn.cursor()
    c.execute('''
        CREATE TABLE IF NOT EXISTS invitados (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
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
    conn = sqlite3.connect('invitados.db')
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

    conn = sqlite3.connect('invitados.db')
    c = conn.cursor()
    c.execute("INSERT INTO invitados (nombre, correo, ceremonia,  comentarios) VALUES (?, ?, ?, ?)",
              (nombre, correo, ceremonia, comentarios))
    conn.commit()
    conn.close()
    return redirect(url_for('gracias'))

@app.route('/lista')
def ver_lista():
    conn = sqlite3.connect('invitados.db')
    c = conn.cursor()
    c.execute('SELECT nombre, correo, ceremonia, comentarios FROM invitados')
    datos = c.fetchall()
    conn.close()
    return render_template('lista.html', invitados=datos)

@app.route('/descargar')
@requiere_autenticacion
def descargar_csv():
    conn = sqlite3.connect('invitados.db')
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
