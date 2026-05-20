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

from werkzeug.security import generate_password_hash, check_password_hash
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

    usuario = cursor.fetchone()

    cursor.close()
    conexion.close()

    return usuario


def obtener_usuario_por_correo(correo):
    conexion = obtener_conexion()

    if conexion is None:
        return None

    cursor = conexion.cursor(dictionary=True)

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

    usuario = cursor.fetchone()

    cursor.close()
    conexion.close()

    return usuario


@login_bp.before_app_request
def cargar_usuario_actual():
    id_usuario = session.get("id_usuario")

    if id_usuario is None:
        g.usuario = None
        return

    g.usuario = obtener_usuario_por_id(id_usuario)


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

        if g.usuario["rol"] != "administrador":
            flash("No tienes permisos de administrador.", "danger")
            return redirect(url_for("main.inicio"))

        return vista(*args, **kwargs)

    return funcion_protegida


def supervisor_o_admin_requerido(vista):
    @wraps(vista)
    def funcion_protegida(*args, **kwargs):
        if g.usuario is None:
            flash("Debes iniciar sesión para continuar.", "warning")
            return redirect(url_for("login.iniciar_sesion"))

        if g.usuario["rol"] not in ["supervisor", "administrador"]:
            flash("No tienes permisos para esta sección.", "danger")
            return redirect(url_for("main.inicio"))

        return vista(*args, **kwargs)

    return funcion_protegida


@login_bp.route("/login", methods=["GET", "POST"])
def iniciar_sesion():
    if g.usuario is not None:
        return redirect(url_for("main.inicio"))

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
        session["nombre"] = usuario["nombre"]
        session["apellido"] = usuario["apellido"]
        session["correo"] = usuario["correo"]
        session["rol"] = usuario["rol"]

        nombre_completo = f"{usuario['nombre']} {usuario['apellido']}"

        flash(f"Bienvenido, {nombre_completo}.", "success")

        if usuario["rol"] == "usuario":
            return redirect(url_for("dashboard.estudiante"))

        return redirect(url_for("dashboard.estudiante"))

    return render_template(
        "login.html",
        institucion=INSTITUCION
    )


@login_bp.route("/registro", methods=["GET", "POST"])
def registrar_usuario():
    if g.usuario is not None:
        return redirect(url_for("main.inicio"))

    if request.method == "POST":
        nombre = request.form.get("nombre", "").strip()
        apellido = request.form.get("apellido", "").strip()
        correo = normalizar_correo(request.form.get("correo", ""))
        password = request.form.get("password", "")
        confirmar_password = request.form.get("confirmar_password", "")

        errores = []

        if len(nombre) < 2:
            errores.append("Ingresa tu nombre.")

        if len(apellido) < 2:
            errores.append("Ingresa tu apellido.")

        if not correo_valido(correo):
            errores.append("Ingresa un correo válido.")

        if not password_valido(password):
            errores.append(
                f"La contraseña debe tener al menos {PASSWORD_MINIMO} caracteres."
            )

        if password != confirmar_password:
            errores.append("Las contraseñas no coinciden.")

        if errores:
            for error in errores:
                flash(error, "warning")

            return render_template(
                "registro.html",
                institucion=INSTITUCION
            ), 400

        conexion = obtener_conexion()

        if conexion is None:
            flash("No se pudo conectar con la base de datos.", "danger")
            return render_template(
                "registro.html",
                institucion=INSTITUCION
            ), 500

        cursor = conexion.cursor(dictionary=True)

        cursor.execute(
            """
            SELECT id_usuario
            FROM usuarios
            WHERE correo = %s
            LIMIT 1
            """,
            (correo,)
        )

        usuario_existente = cursor.fetchone()

        if usuario_existente:
            cursor.close()
            conexion.close()

            flash("Ya existe una cuenta registrada con ese correo.", "danger")
            return render_template(
                "registro.html",
                institucion=INSTITUCION
            ), 409

        password_encriptado = generate_password_hash(password)

        cursor.execute(
            """
            INSERT INTO usuarios
            (
                nombre,
                apellido,
                correo,
                `contraseña`,
                rol,
                estado
            )
            VALUES (%s, %s, %s, %s, %s, %s)
            """,
            (
                nombre,
                apellido,
                correo,
                password_encriptado,
                "usuario",
                True
            )
        )

        conexion.commit()

        cursor.close()
        conexion.close()

        flash("Cuenta creada correctamente. Ahora inicia sesión.", "success")
        return redirect(url_for("login.dashboard"))

    return render_template(
        "registro.html",
        institucion=INSTITUCION
    )


@login_bp.route("/logout")
@login_requerido
def cerrar_sesion():
    session.clear()
    flash("Sesión cerrada correctamente.", "info")
    return redirect(url_for("login.iniciar_sesion"))