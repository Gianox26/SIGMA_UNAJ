from flask import Flask, render_template, session, redirect, url_for

from conexion import obtener_conexion
from login import login_bp
from dashboard import dashboard_bp
from reporte import reporte_bp
from adminDashboard import admin_bp
from reportes import reportes_bp
from acciones import acciones_bp

app = Flask(__name__, template_folder="plantillas", static_folder="estaticos")
app.secret_key = "unaj_capilla_2024_secret_key_brutal"

app.register_blueprint(login_bp)
app.register_blueprint(dashboard_bp)
app.register_blueprint(reportes_bp)
app.register_blueprint(acciones_bp)
app.register_blueprint(reporte_bp)
app.register_blueprint(admin_bp)

@app.route("/")
def inicio():
    if "id_usuario" not in session and "usuario_id" not in session:
        return redirect(url_for("login.iniciar_sesion"))

    rol = (session.get("rol") or "").strip().lower()

    if rol == "administrador":
        return redirect(url_for("admin.dashboard"))

    return redirect(url_for("dashboard.estudiante"))


@app.route("/favicon.ico")
def favicon():
    return "", 204


@app.errorhandler(404)
def pagina_no_encontrada(e):
    return "Página no encontrada", 404


@app.errorhandler(500)
def error_servidor(e):
    return "Error interno del servidor", 500


if __name__ == "__main__":
    conexion = obtener_conexion()

    if conexion:
        conexion.close()
        app.run(debug=True, host="0.0.0.0", port=5000)
    else:
        print("No se pudo conectar a la base de datos")