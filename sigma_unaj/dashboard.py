"""
dashboard.py
Dashboard del estudiante para el Sistema de Reportes UNAJ.

Este archivo usa directamente la base de datos MySQL reportes_unaj
y respeta las tablas existentes:

- usuarios
- incidencias
- acciones
- historial
- notificaciones
"""

from flask import Blueprint, render_template, redirect, url_for, flash, g, abort
from mysql.connector import Error

from conexion import obtener_conexion
from login import login_requerido


dashboard_bp = Blueprint("dashboard", __name__)


ESTADOS_INCIDENCIA = {
    "nueva": "Nueva",
    "en_proceso": "En proceso",
    "resuelta": "Resuelta",
    "cerrada": "Cerrada",
    "reabierta": "Reabierta",
}


PRIORIDADES = {
    "baja": "Baja",
    "media": "Media",
    "alta": "Alta",
    "critica": "Crítica",
}


CATEGORIAS = {
    "calidad": "Calidad",
    "ambiental": "Ambiental",
}


def convertir_entero(valor):
    return int(valor or 0)


def cerrar_recursos(cursor=None, conexion=None):
    if cursor is not None:
        cursor.close()

    if conexion is not None:
        conexion.close()


def enriquecer_incidencia(incidencia):
    """
    Agrega textos limpios para mostrar en el HTML sin cambiar la base de datos.
    """
    incidencia["estado_texto"] = ESTADOS_INCIDENCIA.get(
        incidencia["estado"],
        incidencia["estado"]
    )

    incidencia["prioridad_texto"] = PRIORIDADES.get(
        incidencia["prioridad"],
        incidencia["prioridad"]
    )

    incidencia["categoria_texto"] = CATEGORIAS.get(
        incidencia["categoria"],
        incidencia["categoria"]
    )

    return incidencia


def obtener_datos_dashboard_estudiante(id_usuario):
    conexion = obtener_conexion()

    if conexion is None:
        return None

    cursor = conexion.cursor(dictionary=True)

    try:
        # Resumen general de incidencias del estudiante
        cursor.execute(
            """
            SELECT
                COUNT(*) AS total,
                COALESCE(SUM(CASE WHEN estado = 'nueva' THEN 1 ELSE 0 END), 0) AS nuevas,
                COALESCE(SUM(CASE WHEN estado = 'en_proceso' THEN 1 ELSE 0 END), 0) AS en_proceso,
                COALESCE(SUM(CASE WHEN estado = 'resuelta' THEN 1 ELSE 0 END), 0) AS resueltas,
                COALESCE(SUM(CASE WHEN estado = 'cerrada' THEN 1 ELSE 0 END), 0) AS cerradas,
                COALESCE(SUM(CASE WHEN estado = 'reabierta' THEN 1 ELSE 0 END), 0) AS reabiertas,
                COALESCE(SUM(CASE WHEN prioridad = 'critica' THEN 1 ELSE 0 END), 0) AS criticas,
                COALESCE(SUM(CASE WHEN prioridad = 'alta' THEN 1 ELSE 0 END), 0) AS altas,
                COALESCE(SUM(CASE WHEN categoria = 'calidad' THEN 1 ELSE 0 END), 0) AS calidad,
                COALESCE(SUM(CASE WHEN categoria = 'ambiental' THEN 1 ELSE 0 END), 0) AS ambiental
            FROM incidencias
            WHERE id_usuario = %s
            """,
            (id_usuario,)
        )

        resumen = cursor.fetchone()

        if resumen is None:
            resumen = {}

        resumen = {
            "total": convertir_entero(resumen.get("total")),
            "nuevas": convertir_entero(resumen.get("nuevas")),
            "en_proceso": convertir_entero(resumen.get("en_proceso")),
            "resueltas": convertir_entero(resumen.get("resueltas")),
            "cerradas": convertir_entero(resumen.get("cerradas")),
            "reabiertas": convertir_entero(resumen.get("reabiertas")),
            "criticas": convertir_entero(resumen.get("criticas")),
            "altas": convertir_entero(resumen.get("altas")),
            "calidad": convertir_entero(resumen.get("calidad")),
            "ambiental": convertir_entero(resumen.get("ambiental")),
        }

        # Últimas incidencias registradas por el estudiante
        cursor.execute(
            """
            SELECT
                id_incidencia,
                titulo,
                descripcion,
                categoria,
                prioridad,
                estado,
                laboratorio,
                fecha_reporte,
                evidencia_url
            FROM incidencias
            WHERE id_usuario = %s
            ORDER BY fecha_reporte DESC
            LIMIT 6
            """,
            (id_usuario,)
        )

        ultimas_incidencias = cursor.fetchall()
        ultimas_incidencias = [
            enriquecer_incidencia(incidencia)
            for incidencia in ultimas_incidencias
        ]

        # Conteo por estado para gráficos o tarjetas
        cursor.execute(
            """
            SELECT estado, COUNT(*) AS total
            FROM incidencias
            WHERE id_usuario = %s
            GROUP BY estado
            ORDER BY total DESC
            """,
            (id_usuario,)
        )

        estados = cursor.fetchall()

        for item in estados:
            item["estado_texto"] = ESTADOS_INCIDENCIA.get(
                item["estado"],
                item["estado"]
            )
            item["total"] = convertir_entero(item["total"])

        # Conteo por prioridad
        cursor.execute(
            """
            SELECT prioridad, COUNT(*) AS total
            FROM incidencias
            WHERE id_usuario = %s
            GROUP BY prioridad
            ORDER BY FIELD(prioridad, 'critica', 'alta', 'media', 'baja')
            """,
            (id_usuario,)
        )

        prioridades = cursor.fetchall()

        for item in prioridades:
            item["prioridad_texto"] = PRIORIDADES.get(
                item["prioridad"],
                item["prioridad"]
            )
            item["total"] = convertir_entero(item["total"])

        # Acciones vinculadas a incidencias del estudiante
        cursor.execute(
            """
            SELECT
                a.id_accion,
                a.descripcion,
                a.fecha_inicio,
                a.fecha_fin,
                a.estado,
                i.id_incidencia,
                i.titulo AS incidencia_titulo,
                s.nombre AS supervisor_nombre,
                s.apellido AS supervisor_apellido,
                r.nombre AS responsable_nombre,
                r.apellido AS responsable_apellido
            FROM acciones a
            INNER JOIN incidencias i
                ON i.id_incidencia = a.id_incidencia
            INNER JOIN usuarios s
                ON s.id_usuario = a.id_supervisor
            LEFT JOIN usuarios r
                ON r.id_usuario = a.id_responsable
            WHERE i.id_usuario = %s
            ORDER BY a.fecha_inicio DESC
            LIMIT 5
            """,
            (id_usuario,)
        )

        acciones = cursor.fetchall()

        # Historial reciente de las incidencias del estudiante
        cursor.execute(
            """
            SELECT
                h.id_historial,
                h.tipo_evento,
                h.estado_anterior,
                h.estado_nuevo,
                h.descripcion,
                h.fecha,
                h.id_incidencia,
                i.titulo AS incidencia_titulo
            FROM historial h
            INNER JOIN incidencias i
                ON i.id_incidencia = h.id_incidencia
            WHERE i.id_usuario = %s
            ORDER BY h.fecha DESC
            LIMIT 8
            """,
            (id_usuario,)
        )

        historial = cursor.fetchall()

        # Notificaciones del estudiante
        cursor.execute(
            """
            SELECT
                id_notificacion,
                mensaje,
                leido,
                fecha
            FROM notificaciones
            WHERE id_usuario = %s
            ORDER BY fecha DESC
            LIMIT 6
            """,
            (id_usuario,)
        )

        notificaciones = cursor.fetchall()

        cursor.execute(
            """
            SELECT COUNT(*) AS total
            FROM notificaciones
            WHERE id_usuario = %s
            AND leido = FALSE
            """,
            (id_usuario,)
        )

        notificaciones_no_leidas = cursor.fetchone()
        total_no_leidas = convertir_entero(notificaciones_no_leidas["total"])

        return {
            "resumen": resumen,
            "ultimas_incidencias": ultimas_incidencias,
            "estados": estados,
            "prioridades": prioridades,
            "acciones": acciones,
            "historial": historial,
            "notificaciones": notificaciones,
            "total_no_leidas": total_no_leidas,
        }

    except Error as error:
        print("Error al obtener datos del dashboard del estudiante:", error)
        return None

    finally:
        cerrar_recursos(cursor, conexion)


@dashboard_bp.route("/dashboard")
@login_requerido
def estudiante():
    """
    Dashboard principal del estudiante.
    Solo permite acceso a usuarios con rol 'usuario'.
    """
    if g.usuario["rol"] != "usuario":
        abort(403)

    datos = obtener_datos_dashboard_estudiante(g.usuario["id_usuario"])

    if datos is None:
        flash("No se pudieron cargar los datos del dashboard.", "danger")

        return render_template(
            "dashboard.html",
            usuario=g.usuario,
            resumen={
                "total": 0,
                "nuevas": 0,
                "en_proceso": 0,
                "resueltas": 0,
                "cerradas": 0,
                "reabiertas": 0,
                "criticas": 0,
                "altas": 0,
                "calidad": 0,
                "ambiental": 0,
            },
            ultimas_incidencias=[],
            estados=[],
            prioridades=[],
            acciones=[],
            historial=[],
            notificaciones=[],
            total_no_leidas=0,
        )

    return render_template(
        "dashboard.html",
        usuario=g.usuario,
        resumen=datos["resumen"],
        ultimas_incidencias=datos["ultimas_incidencias"],
        estados=datos["estados"],
        prioridades=datos["prioridades"],
        acciones=datos["acciones"],
        historial=datos["historial"],
        notificaciones=datos["notificaciones"],
        total_no_leidas=datos["total_no_leidas"],
    )


@dashboard_bp.route("/dashboard/notificacion/<int:id_notificacion>/leer", methods=["POST"])
@login_requerido
def marcar_notificacion_leida(id_notificacion):
    """
    Marca como leída una notificación del estudiante autenticado.
    """
    if g.usuario["rol"] != "usuario":
        abort(403)

    conexion = obtener_conexion()

    if conexion is None:
        flash("No se pudo conectar con la base de datos.", "danger")
        return redirect(url_for("dashboard.estudiante"))

    cursor = conexion.cursor(dictionary=True)

    try:
        cursor.execute(
            """
            UPDATE notificaciones
            SET leido = TRUE
            WHERE id_notificacion = %s
            AND id_usuario = %s
            """,
            (
                id_notificacion,
                g.usuario["id_usuario"],
            )
        )

        conexion.commit()
        flash("Notificación marcada como leída.", "success")

    except Error as error:
        print("Error al marcar notificación como leída:", error)
        flash("No se pudo actualizar la notificación.", "danger")

    finally:
        cerrar_recursos(cursor, conexion)

    return redirect(url_for("dashboard.estudiante"))


@dashboard_bp.route("/dashboard/incidencia/<int:id_incidencia>")
@login_requerido
def detalle_incidencia_estudiante(id_incidencia):
    """
    Detalle de una incidencia perteneciente al estudiante autenticado.
    """
    if g.usuario["rol"] != "usuario":
        abort(403)

    conexion = obtener_conexion()

    if conexion is None:
        flash("No se pudo conectar con la base de datos.", "danger")
        return redirect(url_for("dashboard.estudiante"))

    cursor = conexion.cursor(dictionary=True)

    try:
        cursor.execute(
            """
            SELECT
                id_incidencia,
                titulo,
                descripcion,
                categoria,
                prioridad,
                estado,
                laboratorio,
                fecha_reporte,
                evidencia_url,
                id_usuario
            FROM incidencias
            WHERE id_incidencia = %s
            AND id_usuario = %s
            LIMIT 1
            """,
            (
                id_incidencia,
                g.usuario["id_usuario"],
            )
        )

        incidencia = cursor.fetchone()

        if incidencia is None:
            abort(404)

        incidencia = enriquecer_incidencia(incidencia)

        cursor.execute(
            """
            SELECT
                h.id_historial,
                h.tipo_evento,
                h.estado_anterior,
                h.estado_nuevo,
                h.descripcion,
                h.fecha,
                u.nombre,
                u.apellido,
                u.rol
            FROM historial h
            INNER JOIN usuarios u
                ON u.id_usuario = h.id_usuario
            WHERE h.id_incidencia = %s
            ORDER BY h.fecha DESC
            """,
            (id_incidencia,)
        )

        historial = cursor.fetchall()

        cursor.execute(
            """
            SELECT
                a.id_accion,
                a.descripcion,
                a.fecha_inicio,
                a.fecha_fin,
                a.estado,
                s.nombre AS supervisor_nombre,
                s.apellido AS supervisor_apellido,
                r.nombre AS responsable_nombre,
                r.apellido AS responsable_apellido
            FROM acciones a
            INNER JOIN usuarios s
                ON s.id_usuario = a.id_supervisor
            LEFT JOIN usuarios r
                ON r.id_usuario = a.id_responsable
            WHERE a.id_incidencia = %s
            ORDER BY a.fecha_inicio DESC
            """,
            (id_incidencia,)
        )

        acciones = cursor.fetchall()

        return render_template(
            "detalle_incidencia_estudiante.html",
            usuario=g.usuario,
            incidencia=incidencia,
            historial=historial,
            acciones=acciones,
        )

    except Error as error:
        print("Error al cargar detalle de incidencia:", error)
        flash("No se pudo cargar el detalle de la incidencia.", "danger")
        return redirect(url_for("dashboard.estudiante"))

    finally:
        cerrar_recursos(cursor, conexion)