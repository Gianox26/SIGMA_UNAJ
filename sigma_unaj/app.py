from flask import Flask, render_template, session, redirect, url_for

from conexion import obtener_conexion
from login import login_bp
from dashboard import dashboard_bp
from reporte import reporte_bp


app = Flask(
    __name__,
    template_folder="plantillas",
    static_folder="estaticos"
)

app.secret_key = "unaj_capilla_2024_secret_key_brutal"


# Blueprints del sistema
app.register_blueprint(login_bp)
app.register_blueprint(dashboard_bp)
app.register_blueprint(reporte_bp)


@app.route("/")
def inicio():
    if "id_usuario" in session:
        return redirect(url_for("dashboard.estudiante"))

    return redirect(url_for("login.iniciar_sesion"))


@app.route("/incidencias")
def incidencias():
    if "id_usuario" not in session:
        return redirect(url_for("login.iniciar_sesion"))

    return redirect(url_for("dashboard.estudiante"))


@app.route("/crear-incidencia")
def crear_incidencia():
    if "id_usuario" not in session:
        return redirect(url_for("login.iniciar_sesion"))

    return redirect(url_for("reporte.nuevo_reporte"))


@app.errorhandler(404)
def pagina_no_encontrada(e):
    return render_template("404.html"), 404


@app.errorhandler(500)
def error_servidor(e):
    return render_template("500.html"), 500


if __name__ == "__main__":
    conexion = obtener_conexion()

    if conexion:
        conexion.close()
        print("Servidor iniciado en http://localhost:5000")
        app.run(debug=True, host="0.0.0.0", port=5000)
    else:
        print("No se pudo conectar a la base de datos")