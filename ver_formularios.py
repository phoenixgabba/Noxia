import sqlite3

# Conexión a la base de datos
conn = sqlite3.connect('formulario.db')
cursor = conn.cursor()

# Consulta los formularios
cursor.execute("SELECT * FROM formularios")
formularios = cursor.fetchall()

# Muestra los resultados de manera legible
for f in formularios:
    print(f)

# Cierra la conexión
conn.close()
