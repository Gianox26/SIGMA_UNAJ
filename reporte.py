"""
reporte.py
Módulo para crear reportes/incidencias del estudiante.

Funciona con la base de datos reportes_unaj:

- usuarios
- incidencias
- historial
- notificaciones

Incluye un endpoint para "Generar con IA".
Por ahora es un asistente de redacción local basado en reglas.
No usa una API externa, así que no inventa datos: solo ordena y mejora
la descripción que escribe el estudiante.
"""

from flask import (
    Blueprint,
    render_template,
    request,
    redirect,
    url_for,
    flash,
    jsonify,
    g,
    abort
)

from mysql.connector import Error

from conexion import obtener_conexion
from login import login_requerido


reporte_bp = Blueprint("reporte", __name__, url_prefix="/reporte")


CATEGORIAS_VALIDAS = ["calidad", "ambiental"]
PRIORIDADES_VALIDAS = ["baja", "media", "alta", "critica"]


def cerrar_recursos(cursor=None, conexion=None):
    if cursor is not None:
        cursor.close()

    if conexion is not None:
        conexion.close()


def limpiar_texto(texto):
    if texto is None:
        return ""

    return " ".join(texto.strip().split())


def detectar_categoria(descripcion):
    texto = descripcion.lower()

    palabras_ambiental = [
        "agua",
        "filtración",
        "filtracion",
        "lluvia",
        "humedad",
        "techo",
        "residuo",
        "basura",
        "olor",
        "contaminación",
        "contaminacion",
        "humo",
        "desagüe",
        "desague",
        "inundación",
        "inundacion",
        "moho",
        "polvo",
        "ventilación",
        "ventilacion"
    ]

    for palabra in palabras_ambiental:
        if palabra in texto:
            return "ambiental"

    return "calidad"


def detectar_prioridad(descripcion):
    texto = descripcion.lower()

    palabras_criticas = [
        "cortocircuito",
        "riesgo eléctrico",
        "riesgo electrico",
        "incendio",
        "chispa",
        "electrocución",
        "electrocucion",
        "inundación",
        "inundacion",
        "accidente",
        "peligro grave",
        "cable pelado",
        "humo",
        "fuga de gas",
        "urgente"
    ]

    palabras_altas = [
        "riesgo",
        "peligro",
        "filtración",
        "filtracion",
        "no funciona",
        "malogrado",
        "dañado",
        "danado",
        "afecta la clase",
        "interrumpe",
        "equipos eléctricos",
        "equipos electricos"
    ]

    palabras_medias = [
        "dificulta",
        "molestia",
        "falla",
        "problema",
        "demora",
        "mantenimiento",
        "reparación",
        "reparacion"
    ]

    for palabra in palabras_criticas:
        if palabra in texto:
            return "critica"

    for palabra in palabras_altas:
        if palabra in texto:
            return "alta"

    for palabra in palabras_medias:
        if palabra in texto:
            return "media"

    return "baja"


def generar_titulo(descripcion, laboratorio, categoria):
    texto = limpiar_texto(descripcion)

    if not laboratorio:
        laboratorio = "Pabellón Académico"

    if len(texto) <= 80:
        return texto.capitalize()

    if categoria == "ambiental":
        return f"Incidencia ambiental en {laboratorio}"

    return f"Incidencia de calidad en {laboratorio}"


def mejorar_descripcion(descripcion, laboratorio, categoria, prioridad):
    descripcion = limpiar_texto(descripcion)

    if not laboratorio:
        laboratorio = "el Pabellón Académico"

    categoria_texto = "ambiental" if categoria == "ambiental" else "de calidad"
    prioridad_texto = {
        "baja": "baja",
        "media": "media",
        "alta": "alta",
        "critica": "crítica"
    }.get(prioridad, prioridad)

    descripcion_mejorada = (
        f"Se reporta una incidencia {categoria_texto} en {laboratorio}. "
        f"Descripción del estudiante: {descripcion}. "
        f"De acuerdo con la información registrada, la prioridad sugerida es {prioridad_texto}. "
        f"Se solicita la revisión del caso por el área responsable para evaluar la situación, "
        f"definir las acciones correspondientes y realizar el seguimiento dentro del sistema."
    )

    return descripcion_mejorada


def validar_reporte(titulo, descripcion, categoria, prioridad, laboratorio):
    errores = []

    if len(titulo) < 5:
        errores.append("El título debe tener al menos 5 caracteres.")

    if len(descripcion) < 15:
        errores.append("La descripción debe tener al menos 15 caracteres.")

    if categoria not in CATEGORIAS_VALIDAS:
        errores.append("Selecciona una categoría válida.")

    if prioridad not in PRIORIDADES_VALIDAS:
        errores.append("Selecciona una prioridad válida.")

    if len(laboratorio) < 3:
        errores.append("Indica el ambiente, laboratorio o zona donde ocurre la incidencia.")

    return errores


@reporte_bp.route("/nuevo", methods=["GET", "POST"])
@login_requerido
def nuevo_reporte():
    """
    Permite al estudiante crear un nuevo reporte.
    """
    if g.usuario["rol"] != "usuario":
        abort(403)

    if request.method == "POST":
        titulo = limpiar_texto(request.form.get("titulo", ""))
        descripcion = limpiar_texto(request.form.get("descripcion", ""))
        categoria = limpiar_texto(request.form.get("categoria", ""))
        prioridad = limpiar_texto(request.form.get("prioridad", ""))
        laboratorio = limpiar_texto(request.form.get("laboratorio", ""))
        evidencia_url = limpiar_texto(request.form.get("evidencia_url", ""))

        errores = validar_reporte(
            titulo=titulo,
            descripcion=descripcion,
            categoria=categoria,
            prioridad=prioridad,
            laboratorio=laboratorio
        )

        if errores:
            for error in errores:
                flash(error, "warning")

            return render_template(
                "reporte.html",
                usuario=g.usuario,
                categorias=CATEGORIAS_VALIDAS,
                prioridades=PRIORIDADES_VALIDAS,
                form=request.form
            ), 400

        conexion = obtener_conexion()

        if conexion is None:
            flash("No se pudo conectar con la base de datos.", "danger")
            return redirect(url_for("dashboard.estudiante"))

        cursor = conexion.cursor(dictionary=True)

        try:
            cursor.execute(
                """
                INSERT INTO incidencias
                (
                    titulo,
                    descripcion,
                    categoria,
                    prioridad,
                    laboratorio,
                    evidencia_url,
                    id_usuario
                )
                VALUES (%s, %s, %s, %s, %s, %s, %s)
                """,
                (
                    titulo,
                    descripcion,
                    categoria,
                    prioridad,
                    laboratorio,
                    evidencia_url if evidencia_url else None,
                    g.usuario["id_usuario"]
                )
            )

            id_incidencia = cursor.lastrowid

            cursor.execute(
                """
                INSERT INTO historial
                (
                    tipo_evento,
                    estado_anterior,
                    estado_nuevo,
                    descripcion,
                    id_usuario,
                    id_incidencia
                )
                VALUES (%s, %s, %s, %s, %s, %s)
                """,
                (
                    "creacion",
                    None,
                    "nueva",
                    "El estudiante registró una nueva incidencia en el sistema.",
                    g.usuario["id_usuario"],
                    id_incidencia
                )
            )

            cursor.execute(
                """
                INSERT INTO notificaciones
                (
                    mensaje,
                    leido,
                    id_usuario
                )
                VALUES (%s, %s, %s)
                """,
                (
                    f"Tu reporte #{id_incidencia} fue registrado correctamente y quedó en estado nueva.",
                    False,
                    g.usuario["id_usuario"]
                )
            )

            conexion.commit()

            flash("Reporte registrado correctamente.", "success")
            return redirect(url_for("dashboard.estudiante"))

        except Error as error:
            conexion.rollback()
            print("Error al registrar reporte:", error)
            flash("No se pudo registrar el reporte. Revisa los datos e inténtalo nuevamente.", "danger")

        finally:
            cerrar_recursos(cursor, conexion)

    return render_template(
        "reporte.html",
        usuario=g.usuario,
        categorias=CATEGORIAS_VALIDAS,
        prioridades=PRIORIDADES_VALIDAS,
        form={}
    )


@reporte_bp.route("/generar-ia", methods=["POST"])
@login_requerido
def generar_con_ia():
    """
    Genera una versión mejor redactada del reporte.

    Este endpoint no inventa datos. Toma la descripción escrita por el estudiante
    y sugiere título, categoría, prioridad y descripción formal.
    """
    if g.usuario["rol"] != "usuario":
        abort(403)

    datos = request.get_json(silent=True) or {}

    descripcion_original = limpiar_texto(datos.get("descripcion", ""))
    laboratorio = limpiar_texto(datos.get("laboratorio", ""))

    if len(descripcion_original) < 15:
        return jsonify({
            "ok": False,
            "mensaje": "Escribe una descripción más detallada para poder generar el reporte."
        }), 400

    categoria = limpiar_texto(datos.get("categoria", ""))

    if categoria not in CATEGORIAS_VALIDAS:
        categoria = detectar_categoria(descripcion_original)

    prioridad = limpiar_texto(datos.get("prioridad", ""))

    if prioridad not in PRIORIDADES_VALIDAS:
        prioridad = detectar_prioridad(descripcion_original)

    titulo = generar_titulo(
        descripcion=descripcion_original,
        laboratorio=laboratorio,
        categoria=categoria
    )

    descripcion_mejorada = mejorar_descripcion(
        descripcion=descripcion_original,
        laboratorio=laboratorio,
        categoria=categoria,
        prioridad=prioridad
    )

    return jsonify({
        "ok": True,
        "titulo": titulo,
        "descripcion": descripcion_mejorada,
        "categoria": categoria,
        "prioridad": prioridad,
        "laboratorio": laboratorio
    })