from flask import Flask, render_template, request, redirect, url_for, session
from flask_wtf import FlaskForm
from wtforms import StringField, FileField, TextAreaField, SelectMultipleField
from wtforms.validators import DataRequired
from werkzeug.utils import secure_filename
import sqlite3
import os

app = Flask(__name__)
app.secret_key = 'supersecretkey'

UPLOAD_FOLDER = os.path.join('static', 'uploads')
os.makedirs(UPLOAD_FOLDER, exist_ok=True)
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER

# ---------- BASE DE DATOS ----------
def get_db():
    conn = sqlite3.connect('formulario.db')  # Cambiado a formulario.db
    return conn

# Crear tabla si no existe
def init_db():
    conn = get_db()
    cursor = conn.cursor()
    cursor.execute(''' 
        CREATE TABLE IF NOT EXISTS formularios (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            nombre TEXT,
            sitio TEXT,
            tamanio TEXT,
            disponibilidad TEXT,
            referencias_texto TEXT,
            fotos TEXT,
            forma_contacto TEXT
        )
    ''')
    conn.commit()
    conn.close()

init_db()

# ---------- FORMULARIO ----------
class FormularioTattoo(FlaskForm):
    nombre = StringField('Nombre y Apellidos', validators=[DataRequired()])
    sitio = StringField('Zona del cuerpo', validators=[DataRequired()])
    foto = FileField('Imagen de referencia', render_kw={"multiple": True})
    tamanio = StringField('Tamaño (cm)', validators=[DataRequired()])
    referencias_texto = TextAreaField('Ideas, referencias y estilo', validators=[DataRequired()])
    disponibilidad = SelectMultipleField('Días preferentes', choices=[ 
        ('Lunes', 'Lunes'), ('Martes', 'Martes'), ('Miércoles', 'Miércoles'),
        ('Jueves', 'Jueves'), ('Viernes', 'Viernes'), ('Sábado', 'Sábado')],
        validators=[DataRequired()])
    disponibilidad_horaria = SelectMultipleField('Disponibilidad horaria', choices=[ 
        ('Mañanas', 'Mañanas'), ('Tardes', 'Tardes')],
        validators=[DataRequired()])
    telefono_de_contacto = StringField('Número de teléfono', validators=[DataRequired()])

# ---------- RUTAS ----------
@app.route('/')
def index():
    return redirect(url_for('formulario'))

@app.route('/formulario', methods=['GET', 'POST'])
def formulario():
    form = FormularioTattoo()
    if form.validate_on_submit():
        nombre = form.nombre.data
        sitio = form.sitio.data
        tamanio = form.tamanio.data
        disponibilidad = ', '.join(form.disponibilidad.data)
        disponibilidad_horaria = ', '.join(form.disponibilidad_horaria.data)
        referencias_texto = form.referencias_texto.data
        telefono_de_contacto = form.telefono_de_contacto.data

        # Obtener múltiples archivos
        fotos = request.files.getlist("foto")
        filenames = []
        if fotos:
            for foto in fotos:
                if foto.filename:
                    filename = secure_filename(foto.filename)
                    foto.save(os.path.join(app.config['UPLOAD_FOLDER'], filename))
                    filenames.append(filename)

        # Guardar datos en la base de datos
        conn = get_db()
        c = conn.cursor()
        c.execute(""" 
            INSERT INTO formularios (nombre, sitio, tamanio, disponibilidad, referencias_texto, fotos, forma_contacto)
            VALUES (?, ?, ?, ?, ?, ?, ?)""",
            (nombre, sitio, tamanio, disponibilidad, referencias_texto, ','.join(filenames), telefono_de_contacto))
        conn.commit()
        conn.close()

        return redirect(url_for('formulario'))

    return render_template('formulario.html', form=form)
@app.route('/politica-de-privacidad')
def politica_privacidad():
    return render_template('politica_privacidad.html')

@app.route('/politica-de-cookies')
def politica_cookies():
    return render_template('politica_cookies.html')
@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        if request.form['username'] == 'La Nuit' and request.form['password'] == 'nuez+almendra15':
            session['logged_in'] = True
            return redirect(url_for('admin'))
        else:
            return 'Credenciales incorrectas'
    return render_template('login.html')

@app.route('/admin')
def admin():
    if not session.get('logged_in'):
        return redirect(url_for('login'))
    conn = get_db()
    c = conn.cursor()
    c.execute("SELECT * FROM formularios")
    formularios = c.fetchall()
    conn.close()
    return render_template('admin.html', formularios=formularios)

@app.route('/eliminar/<int:id>', methods=['GET'])
def eliminar(id):
    conn = get_db()
    c = conn.cursor()
    
    # Obtener el formulario para verificar si tiene imágenes
    c.execute("SELECT fotos FROM formularios WHERE id=?", (id,))
    formulario = c.fetchone()
    
    if formulario and formulario[0]:
        # Si tiene imágenes, eliminarlas de la carpeta de uploads
        fotos = formulario[0].split(',')
        for foto in fotos:
            foto_path = os.path.join(app.config['UPLOAD_FOLDER'], foto)
            if os.path.exists(foto_path):
                os.remove(foto_path)
    
    # Eliminar el formulario de la base de datos
    c.execute("DELETE FROM formularios WHERE id=?", (id,))
    conn.commit()
    conn.close()

    return redirect(url_for('admin'))

@app.route('/logout')
def logout():
    session.clear()
    return redirect(url_for('login'))

if __name__ == '__main__':
    app.run(debug=True)
