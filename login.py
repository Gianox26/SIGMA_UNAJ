"""
login.py
Autenticación para el Sistema de Reportes - Pabellón Académico UNAJ
Compatible con la base de datos MySQL reportes_unaj.

Tabla usada:
usuarios(
    id_usuario,
    nombre,
    apellido,
    correo,
    contraseña,
    rol,
    estado,
    fecha_registro
)
"""

from functools import wraps
import re

from flask import (
    Blueprint,
    render_template,
    request,
    redirect,
    url_for,
    session,
    flash,
    g
)

from werkzeug.security import check_password_hash
from conexion import obtener_conexion


login_bp = Blueprint("login", __name__)


INSTITUCION = {
    "nombre": "Universidad Nacional de Juliaca",
    "sigla": "UNAJ",
    "sede": "Sede La Capilla",
    "direccion": "Av. Nueva Zelandia N.° 631, Urb. La Capilla, Juliaca",
    "modulo": "Sistema estudiantil de reportes del Pabellón Académico"
}


EMAIL_REGEX = re.compile(r"^[^@\s]+@[^@\s]+\.[^@\s]+$")
PASSWORD_MINIMO = 8


def normalizar_correo(correo):
    return correo.strip().lower()


def correo_valido(correo):
    return bool(EMAIL_REGEX.match(correo))


def password_valido(password):
    return len(password) >= PASSWORD_MINIMO


def obtener_usuario_por_id(id_usuario):
    conexion = obtener_conexion()

    if conexion is None:
        return None

    cursor = conexion.cursor(dictionary=True)

    try:
        cursor.execute(
            """
            SELECT 
                id_usuario,
                nombre,
                apellido,
                correo,
                `contraseña`,
                rol,
                estado,
                fecha_registro
            FROM usuarios
            WHERE id_usuario = %s
            LIMIT 1
            """,
            (id_usuario,)
        )

        return cursor.fetchone()

    finally:
        cursor.close()
        conexion.close()


def obtener_usuario_por_correo(correo):
    conexion = obtener_conexion()

    if conexion is None:
        return None

    cursor = conexion.cursor(dictionary=True)

    try:
        cursor.execute(
            """
            SELECT 
                id_usuario,
                nombre,
                apellido,
                correo,
                `contraseña`,
                rol,
                estado,
                fecha_registro
            FROM usuarios
            WHERE correo = %s
            LIMIT 1
            """,
            (correo,)
        )

        return cursor.fetchone()

    finally:
        cursor.close()
        conexion.close()


def redireccionar_por_rol(rol):
    rol = (rol or "").strip().lower()

    if rol == "administrador":
        return redirect(url_for("reportes.panel_reportes"))

    if rol == "supervisor":
        return redirect(url_for("reportes.panel_reportes"))

    return redirect(url_for("dashboard.estudiante"))

@login_bp.before_app_request
def cargar_usuario_actual():
    id_usuario = session.get("id_usuario") or session.get("usuario_id")

    if id_usuario is None:
        g.usuario = None
        return

    usuario = obtener_usuario_por_id(id_usuario)

    if usuario is None:
        session.clear()
        g.usuario = None
        return

    g.usuario = usuario


def login_requerido(vista):
    @wraps(vista)
    def funcion_protegida(*args, **kwargs):
        if g.usuario is None:
            flash("Debes iniciar sesión para continuar.", "warning")
            return redirect(url_for("login.iniciar_sesion"))

        return vista(*args, **kwargs)

    return funcion_protegida


def administrador_requerido(vista):
    @wraps(vista)
    def funcion_protegida(*args, **kwargs):
        if g.usuario is None:
            flash("Debes iniciar sesión para continuar.", "warning")
            return redirect(url_for("login.iniciar_sesion"))

        rol = (g.usuario.get("rol") or "").strip().lower()

        if rol != "administrador":
            flash("No tienes permisos de administrador.", "danger")
            return redirect(url_for("dashboard.estudiante"))

        return vista(*args, **kwargs)

    return funcion_protegida


def supervisor_o_admin_requerido(vista):
    @wraps(vista)
    def funcion_protegida(*args, **kwargs):
        if g.usuario is None:
            flash("Debes iniciar sesión para continuar.", "warning")
            return redirect(url_for("login.iniciar_sesion"))

        rol = (g.usuario.get("rol") or "").strip().lower()

        if rol not in ["supervisor", "administrador"]:
            flash("No tienes permisos para esta sección.", "danger")
            return redirect(url_for("dashboard.estudiante"))

        return vista(*args, **kwargs)

    return funcion_protegida


@login_bp.route("/login", methods=["GET", "POST"])
def iniciar_sesion():
    if g.usuario is not None:
        return redireccionar_por_rol(g.usuario["rol"])

    if request.method == "POST":
        correo = normalizar_correo(request.form.get("correo", ""))
        password = request.form.get("password", "")

        if not correo or not password:
            flash("Completa tu correo y contraseña.", "warning")
            return render_template(
                "login.html",
                institucion=INSTITUCION
            )

        usuario = obtener_usuario_por_correo(correo)

        if usuario is None:
            flash("Correo o contraseña incorrectos.", "danger")
            return render_template(
                "login.html",
                institucion=INSTITUCION
            ), 401

        if not usuario["estado"]:
            flash("Tu cuenta está desactivada. Contacta con administración.", "danger")
            return render_template(
                "login.html",
                institucion=INSTITUCION
            ), 403

        password_bd = usuario["contraseña"]

        if not check_password_hash(password_bd, password):
            flash("Correo o contraseña incorrectos.", "danger")
            return render_template(
                "login.html",
                institucion=INSTITUCION
            ), 401

        session.clear()

        session["id_usuario"] = usuario["id_usuario"]
        session["usuario_id"] = usuario["id_usuario"]

        session["nombre"] = usuario["nombre"]
        session["apellido"] = usuario["apellido"]
        session["correo"] = usuario["correo"]
        session["rol"] = usuario["rol"]

        nombre_completo = f"{usuario['nombre']} {usuario['apellido']}"
        flash(f"Bienvenido, {nombre_completo}.", "success")

        return redireccionar_por_rol(usuario["rol"])

    return render_template(
        "login.html",
        institucion=INSTITUCION
    )


@login_bp.route("/registro", methods=["GET", "POST"])
def registrar_usuario():
    flash(
        "Las cuentas son asignadas por la universidad. No se permite registro público.",
        "warning"
    )
    return redirect(url_for("login.iniciar_sesion"))


@login_bp.route("/logout")
def cerrar_sesion():
    session.clear()
    flash("Sesión cerrada correctamente.", "info")
    return redirect(url_for("login.iniciar_sesion"))