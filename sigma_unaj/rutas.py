from functools import wraps
from flask import Blueprint, render_template, request, redirect, url_for, session, flash
from werkzeug.security import generate_password_hash, check_password_hash
from conexion import obtener_conexion

bp = Blueprint("main", __name__)

def login_requerido(vista):
    @wraps(vista)
    def envoltura(*args, **kwargs):
        if "usuario_id" not in session:
            flash("Debes iniciar sesión.", "warning")
            return redirect(url_for("main.login"))
        return vista(*args, **kwargs)
    return envoltura

def admin_requerido(vista):
    @wraps(vista)
    def envoltura(*args, **kwargs):
        if not session.get("es_admin"):
            flash("No tienes permisos de administrador.", "danger")
            return redirect(url_for("main.inicio"))
        return vista(*args, **kwargs)
    return envoltura

@bp.route("/")
def inicio():
    return render_template("inicio.html")

@bp.route("/login", methods=["GET", "POST"])
def login():
    if request.method == "POST":
        correo = request.form["correo"].strip().lower()
        password = request.form["password"]

        db = obtener_conexion()
        usuario = db.execute(
            "SELECT * FROM usuarios WHERE correo = ?",
            (correo,)
        ).fetchone()

        if usuario and check_password_hash(usuario["password"], password):
            session["usuario_id"] = usuario["id"]
            session["nombre"] = usuario["nombre"]
            session["es_admin"] = bool(usuario["es_admin"])
            flash("Inicio de sesión correcto.", "success")
            return redirect(url_for("main.incidencias"))

        flash("Correo o contraseña incorrectos.", "danger")

    return render_template("login.html")

@bp.route("/registro", methods=["GET", "POST"])
def registro():
    if request.method == "POST":
        nombre = request.form["nombre"].strip()
        correo = request.form["correo"].strip().lower()
        password = request.form["password"]

        if not nombre or not correo or not password:
            flash("Completa todos los campos.", "warning")
            return redirect(url_for("main.registro"))

        db = obtener_conexion()
        existe = db.execute(
            "SELECT id FROM usuarios WHERE correo = ?",
            (correo,)
        ).fetchone()

        if existe:
            flash("El correo ya está registrado.", "danger")
            return redirect(url_for("main.registro"))

        db.execute(
            "INSERT INTO usuarios (nombre, correo, password) VALUES (?, ?, ?)",
            (nombre, correo, generate_password_hash(password))
        )
        db.commit()

        flash("Usuario registrado. Ahora puedes iniciar sesión.", "success")
        return redirect(url_for("main.login"))

    return render_template("registro.html")

@bp.route("/logout")
def logout():
    session.clear()
    flash("Sesión cerrada.", "info")
    return redirect(url_for("main.inicio"))

@bp.route("/incidencias")
@login_requerido
def incidencias():
    db = obtener_conexion()

    if session.get("es_admin"):
        lista = db.execute("""
            SELECT i.*, u.nombre AS usuario
            FROM incidencias i
            JOIN usuarios u ON u.id = i.usuario_id
            ORDER BY i.fecha DESC
        """).fetchall()
    else:
        lista = db.execute("""
            SELECT i.*, u.nombre AS usuario
            FROM incidencias i
            JOIN usuarios u ON u.id = i.usuario_id
            WHERE i.usuario_id = ?
            ORDER BY i.fecha DESC
        """, (session["usuario_id"],)).fetchall()

    return render_template("incidencias.html", incidencias=lista)

@bp.route("/crear-incidencia", methods=["GET", "POST"])
@login_requerido
def crear_incidencia():
    if request.method == "POST":
        titulo = request.form["titulo"].strip()
        descripcion = request.form["descripcion"].strip()

        if not titulo or not descripcion:
            flash("Completa título y descripción.", "warning")
            return redirect(url_for("main.crear_incidencia"))

        db = obtener_conexion()
        db.execute(
            "INSERT INTO incidencias (titulo, descripcion, usuario_id) VALUES (?, ?, ?)",
            (titulo, descripcion, session["usuario_id"])
        )
        db.commit()

        flash("Incidencia creada correctamente.", "success")
        return redirect(url_for("main.incidencias"))

    return render_template("crear_incidencia.html")

@bp.route("/admin", methods=["GET", "POST"])
@login_requerido
@admin_requerido
def admin():
    db = obtener_conexion()

    if request.method == "POST":
        incidencia_id = request.form["incidencia_id"]
        estado = request.form["estado"]

        db.execute(
            "UPDATE incidencias SET estado = ? WHERE id = ?",
            (estado, incidencia_id)
        )
        db.commit()
        flash("Estado actualizado.", "success")
        return redirect(url_for("main.admin"))

    incidencias = db.execute("""
        SELECT i.*, u.nombre AS usuario
        FROM incidencias i
        JOIN usuarios u ON u.id = i.usuario_id
        ORDER BY i.fecha DESC
    """).fetchall()

    return render_template("admin.html", incidencias=incidencias)
