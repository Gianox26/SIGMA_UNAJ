import mysql.connector

# Datos de conexión
MYSQL_HOST = "localhost"
MYSQL_USER = "root"
MYSQL_PASSWORD = ""
MYSQL_DB = "reportes_unaj"

# Clave secreta (para Flask)
SECRET_KEY = "clave_secreta_segura"

def obtener_conexion():
    try:
        conexion = mysql.connector.connect(
            host=MYSQL_HOST,
            user=MYSQL_USER,
            password=MYSQL_PASSWORD,
            database=MYSQL_DB,
            buffered=True  # ✅ CORRECTO: dentro de connect()
        )
        print("✅ Conexión exitosa a la base de datos")
        return conexion
    except mysql.connector.Error as err:
        print("❌ Error al conectar a la base de datos:", err)
        return None