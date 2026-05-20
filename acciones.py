"""
acciones.py
Módulo administrativo para visualizar, filtrar y actualizar acciones realizadas
frente a incidencias del Sistema de Reportes UNAJ.

Usa las tablas:
- acciones
- incidencias
- usuarios
- historial
- notificaciones
"""

from flask import (
    Blueprint,
    render_template,
    request,
    redirect,
    url_for,
    flash,
    g,
    abort
)

from mysql.connector import Error

from conexion import obtener_conexion
from login import login_requerido


acciones_bp = Blueprint("acciones", __name__)


ESTADOS_ACCION = {
    "pendiente": "Pendiente",
    "en_proceso": "En proceso",
    "finalizada": "Finalizada",
}


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


def cerrar_recursos(cursor=None, conexion=None):
    if cursor is not None:
        cursor.close()

    if conexion is not None:
        conexion.close()


def solo_admin():
    if g.usuario is None:
        abort(403)

    rol = (g.usuario.get("rol") or "").strip().lower()

    if rol != "administrador":
        abort(403)


def convertir_entero(valor):
    return int(valor or 0)


def enriquecer_accion(accion):
    accion["estado_texto"] = ESTADOS_ACCION.get(
        accion.get("estado"),
        accion.get("estado")
    )

    accion["incidencia_estado_texto"] = ESTADOS_INCIDENCIA.get(
        accion.get("incidencia_estado"),
        accion.get("incidencia_estado")
    )

    accion["prioridad_texto"] = PRIORIDADES.get(
        accion.get("prioridad"),
        accion.get("prioridad")
    )

    accion["categoria_texto"] = CATEGORIAS.get(
        accion.get("categoria"),
        accion.get("categoria")
    )

    return accion


@acciones_bp.route("/admin/acciones")
@login_requerido
def panel_acciones():
    """
    Lista general de acciones administrativas.
    Permite filtrar por búsqueda, estado de acción, responsable y estado de incidencia.
    """
    solo_admin()

    busqueda = request.args.get("q", "").strip()
    estado_accion = request.args.get("estado", "").strip()
    responsable = request.args.get("responsable", "").strip()
    estado_incidencia = request.args.get("estado_incidencia", "").strip()

    conexion = obtener_conexion()

    if conexion is None:
        flash("No se pudo conectar con la base de datos.", "danger")

        return render_template(
            "acciones_admin.html",
            acciones=[],
            resumen={},
            responsables=[],
            filtros={
                "q": busqueda,
                "estado": estado_accion,
                "responsable": responsable,
                "estado_incidencia": estado_incidencia,
            },
            estados_accion=ESTADOS_ACCION,
            estados_incidencia=ESTADOS_INCIDENCIA,
        )

    cursor = conexion.cursor(dictionary=True)

    try:
        condiciones = []
        valores = []

        if busqueda:
            condiciones.append(
                """
                (
                    a.descripcion LIKE %s
                    OR i.titulo LIKE %s
                    OR i.descripcion LIKE %s
                    OR i.laboratorio LIKE %s
                    OR estudiante.nombre LIKE %s
                    OR estudiante.apellido LIKE %s
                    OR estudiante.correo LIKE %s
                    OR supervisor.nombre LIKE %s
                    OR supervisor.apellido LIKE %s
                    OR responsable.nombre LIKE %s
                    OR responsable.apellido LIKE %s
                )
                """
            )

            texto = f"%{busqueda}%"
            valores.extend([
                texto, texto, texto, texto, texto,
                texto, texto, texto, texto, texto, texto
            ])

        if estado_accion:
            condiciones.append("a.estado = %s")
            valores.append(estado_accion)

        if responsable:
            condiciones.append("a.id_responsable = %s")
            valores.append(responsable)

        if estado_incidencia:
            condiciones.append("i.estado = %s")
            valores.append(estado_incidencia)

        where_sql = ""

        if condiciones:
            where_sql = "WHERE " + " AND ".join(condiciones)

        consulta = f"""
            SELECT
                a.id_accion,
                a.descripcion,
                a.fecha_inicio,
                a.fecha_fin,
                a.estado,

                i.id_incidencia,
                i.titulo AS incidencia_titulo,
                i.descripcion AS incidencia_descripcion,
                i.categoria,
                i.prioridad,
                i.estado AS incidencia_estado,
                i.laboratorio,
                i.fecha_reporte,

                estudiante.id_usuario AS estudiante_id,
                estudiante.nombre AS estudiante_nombre,
                estudiante.apellido AS estudiante_apellido,
                estudiante.correo AS estudiante_correo,

                supervisor.id_usuario AS supervisor_id,
                supervisor.nombre AS supervisor_nombre,
                supervisor.apellido AS supervisor_apellido,
                supervisor.rol AS supervisor_rol,

                responsable.id_usuario AS responsable_id,
                responsable.nombre AS responsable_nombre,
                responsable.apellido AS responsable_apellido,
                responsable.rol AS responsable_rol

            FROM acciones a
            INNER JOIN incidencias i
                ON i.id_incidencia = a.id_incidencia

            INNER JOIN usuarios estudiante
                ON estudiante.id_usuario = i.id_usuario

            INNER JOIN usuarios supervisor
                ON supervisor.id_usuario = a.id_supervisor

            LEFT JOIN usuarios responsable
                ON responsable.id_usuario = a.id_responsable

            {where_sql}

            ORDER BY a.fecha_inicio DESC
        """

        cursor.execute(consulta, valores)
        acciones = cursor.fetchall()

        acciones = [
            enriquecer_accion(accion)
            for accion in acciones
        ]

        cursor.execute(
            """
            SELECT
                COUNT(*) AS total,
                COALESCE(SUM(CASE WHEN estado = 'pendiente' THEN 1 ELSE 0 END), 0) AS pendientes,
                COALESCE(SUM(CASE WHEN estado = 'en_proceso' THEN 1 ELSE 0 END), 0) AS en_proceso,
                COALESCE(SUM(CASE WHEN estado = 'finalizada' THEN 1 ELSE 0 END), 0) AS finalizadas
            FROM acciones
            """
        )

        resumen = cursor.fetchone() or {}

        resumen = {
            "total": convertir_entero(resumen.get("total")),
            "pendientes": convertir_entero(resumen.get("pendientes")),
            "en_proceso": convertir_entero(resumen.get("en_proceso")),
            "finalizadas": convertir_entero(resumen.get("finalizadas")),
        }

        cursor.execute(
            """
            SELECT
                id_usuario,
                nombre,
                apellido,
                correo,
                rol
            FROM usuarios
            WHERE rol IN ('administrador', 'supervisor')
            AND estado = TRUE
            ORDER BY rol, apellido, nombre
            """
        )

        responsables = cursor.fetchall()

        return render_template(
            "acciones_admin.html",
            acciones=acciones,
            resumen=resumen,
            responsables=responsables,
            filtros={
                "q": busqueda,
                "estado": estado_accion,
                "responsable": responsable,
                "estado_incidencia": estado_incidencia,
            },
            estados_accion=ESTADOS_ACCION,
            estados_incidencia=ESTADOS_INCIDENCIA,
        )

    except Error as error:
        print("Error al cargar acciones:", error)
        flash("No se pudieron cargar las acciones.", "danger")

        return render_template(
            "acciones_admin.html",
            acciones=[],
            resumen={},
            responsables=[],
            filtros={
                "q": busqueda,
                "estado": estado_accion,
                "responsable": responsable,
                "estado_incidencia": estado_incidencia,
            },
            estados_accion=ESTADOS_ACCION,
            estados_incidencia=ESTADOS_INCIDENCIA,
        )

    finally:
        cerrar_recursos(cursor, conexion)


@acciones_bp.route("/admin/acciones/<int:id_accion>")
@login_requerido
def detalle_accion(id_accion):
    """
    Detalle de una acción registrada frente a una incidencia.
    """
    solo_admin()

    conexion = obtener_conexion()

    if conexion is None:
        flash("No se pudo conectar con la base de datos.", "danger")
        return redirect(url_for("acciones.panel_acciones"))

    cursor = conexion.cursor(dictionary=True)

    try:
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
                i.descripcion AS incidencia_descripcion,
                i.categoria,
                i.prioridad,
                i.estado AS incidencia_estado,
                i.laboratorio,
                i.fecha_reporte,
                i.evidencia_url,

                estudiante.id_usuario AS estudiante_id,
                estudiante.nombre AS estudiante_nombre,
                estudiante.apellido AS estudiante_apellido,
                estudiante.correo AS estudiante_correo,

                supervisor.id_usuario AS supervisor_id,
                supervisor.nombre AS supervisor_nombre,
                supervisor.apellido AS supervisor_apellido,
                supervisor.rol AS supervisor_rol,

                responsable.id_usuario AS responsable_id,
                responsable.nombre AS responsable_nombre,
                responsable.apellido AS responsable_apellido,
                responsable.rol AS responsable_rol

            FROM acciones a
            INNER JOIN incidencias i
                ON i.id_incidencia = a.id_incidencia

            INNER JOIN usuarios estudiante
                ON estudiante.id_usuario = i.id_usuario

            INNER JOIN usuarios supervisor
                ON supervisor.id_usuario = a.id_supervisor

            LEFT JOIN usuarios responsable
                ON responsable.id_usuario = a.id_responsable

            WHERE a.id_accion = %s
            LIMIT 1
            """,
            (id_accion,)
        )

        accion = cursor.fetchone()

        if accion is None:
            abort(404)

        accion = enriquecer_accion(accion)

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
            (accion["id_incidencia"],)
        )

        historial = cursor.fetchall()

        cursor.execute(
            """
            SELECT
                id_usuario,
                nombre,
                apellido,
                correo,
                rol
            FROM usuarios
            WHERE rol IN ('administrador', 'supervisor')
            AND estado = TRUE
            ORDER BY rol, apellido, nombre
            """
        )

        responsables = cursor.fetchall()

        return render_template(
            "detalle_accion_admin.html",
            accion=accion,
            historial=historial,
            responsables=responsables,
            estados_accion=ESTADOS_ACCION,
            estados_incidencia=ESTADOS_INCIDENCIA,
        )

    except Error as error:
        print("Error al cargar detalle de acción:", error)
        flash("No se pudo cargar el detalle de la acción.", "danger")
        return redirect(url_for("acciones.panel_acciones"))

    finally:
        cerrar_recursos(cursor, conexion)


@acciones_bp.route("/admin/acciones/<int:id_accion>/estado", methods=["POST"])
@login_requerido
def actualizar_estado_accion(id_accion):
    """
    Actualiza el estado de una acción.
    Si la acción pasa a finalizada, registra fecha_fin.
    También crea historial y notificación para el estudiante.
    """
    solo_admin()

    nuevo_estado = request.form.get("estado", "").strip()

    if nuevo_estado not in ESTADOS_ACCION:
        flash("Estado de acción no válido.", "warning")
        return redirect(url_for("acciones.detalle_accion", id_accion=id_accion))

    conexion = obtener_conexion()

    if conexion is None:
        flash("No se pudo conectar con la base de datos.", "danger")
        return redirect(url_for("acciones.detalle_accion", id_accion=id_accion))

    cursor = conexion.cursor(dictionary=True)

    try:
        cursor.execute(
            """
            SELECT
                a.id_accion,
                a.descripcion,
                a.estado,
                a.id_incidencia,

                i.titulo AS incidencia_titulo,
                i.id_usuario AS estudiante_id

            FROM acciones a
            INNER JOIN incidencias i
                ON i.id_incidencia = a.id_incidencia

            WHERE a.id_accion = %s
            LIMIT 1
            """,
            (id_accion,)
        )

        accion = cursor.fetchone()

        if accion is None:
            abort(404)

        estado_anterior = accion["estado"]

        if estado_anterior == nuevo_estado:
            flash("La acción ya tiene ese estado.", "warning")
            return redirect(url_for("acciones.detalle_accion", id_accion=id_accion))

        if nuevo_estado == "finalizada":
            cursor.execute(
                """
                UPDATE acciones
                SET estado = %s,
                    fecha_fin = NOW()
                WHERE id_accion = %s
                """,
                (nuevo_estado, id_accion)
            )
        else:
            cursor.execute(
                """
                UPDATE acciones
                SET estado = %s,
                    fecha_fin = NULL
                WHERE id_accion = %s
                """,
                (nuevo_estado, id_accion)
            )

        descripcion_historial = (
            f"El administrador {g.usuario['nombre']} {g.usuario['apellido']} "
            f"actualizó la acción de {estado_anterior} a {nuevo_estado}."
        )

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
                "actualizacion_accion",
                estado_anterior,
                nuevo_estado,
                descripcion_historial,
                g.usuario["id_usuario"],
                accion["id_incidencia"],
            )
        )

        mensaje = (
            f"Una acción asociada a tu reporte "
            f"'{accion['incidencia_titulo']}' cambió a: "
            f"{ESTADOS_ACCION.get(nuevo_estado, nuevo_estado)}."
        )

        cursor.execute(
            """
            INSERT INTO notificaciones
            (
                mensaje,
                leido,
                id_usuario
            )
            VALUES (%s, FALSE, %s)
            """,
            (
                mensaje,
                accion["estudiante_id"],
            )
        )

        conexion.commit()

        flash("Estado de la acción actualizado correctamente.", "success")

    except Error as error:
        conexion.rollback()
        print("Error al actualizar estado de acción:", error)
        flash("No se pudo actualizar el estado de la acción.", "danger")

    finally:
        cerrar_recursos(cursor, conexion)

    return redirect(url_for("acciones.detalle_accion", id_accion=id_accion))


@acciones_bp.route("/admin/acciones/<int:id_accion>/responsable", methods=["POST"])
@login_requerido
def actualizar_responsable_accion(id_accion):
    """
    Cambia o asigna responsable a una acción.
    """
    solo_admin()

    id_responsable = request.form.get("id_responsable", "").strip()

    if not id_responsable:
        flash("Selecciona un responsable válido.", "warning")
        return redirect(url_for("acciones.detalle_accion", id_accion=id_accion))

    try:
        id_responsable = int(id_responsable)
    except ValueError:
        flash("Responsable no válido.", "warning")
        return redirect(url_for("acciones.detalle_accion", id_accion=id_accion))

    conexion = obtener_conexion()

    if conexion is None:
        flash("No se pudo conectar con la base de datos.", "danger")
        return redirect(url_for("acciones.detalle_accion", id_accion=id_accion))

    cursor = conexion.cursor(dictionary=True)

    try:
        cursor.execute(
            """
            SELECT
                a.id_accion,
                a.id_incidencia,
                i.titulo AS incidencia_titulo,
                i.id_usuario AS estudiante_id
            FROM acciones a
            INNER JOIN incidencias i
                ON i.id_incidencia = a.id_incidencia
            WHERE a.id_accion = %s
            LIMIT 1
            """,
            (id_accion,)
        )

        accion = cursor.fetchone()

        if accion is None:
            abort(404)

        cursor.execute(
            """
            SELECT
                id_usuario,
                nombre,
                apellido,
                rol
            FROM usuarios
            WHERE id_usuario = %s
            AND rol IN ('administrador', 'supervisor')
            AND estado = TRUE
            LIMIT 1
            """,
            (id_responsable,)
        )

        responsable = cursor.fetchone()

        if responsable is None:
            flash("El responsable seleccionado no existe o no está activo.", "warning")
            return redirect(url_for("acciones.detalle_accion", id_accion=id_accion))

        cursor.execute(
            """
            UPDATE acciones
            SET id_responsable = %s
            WHERE id_accion = %s
            """,
            (
                id_responsable,
                id_accion,
            )
        )

        descripcion_historial = (
            f"El administrador {g.usuario['nombre']} {g.usuario['apellido']} "
            f"asignó como responsable a "
            f"{responsable['nombre']} {responsable['apellido']}."
        )

        cursor.execute(
            """
            INSERT INTO historial
            (
                tipo_evento,
                descripcion,
                id_usuario,
                id_incidencia
            )
            VALUES (%s, %s, %s, %s)
            """,
            (
                "asignacion_responsable",
                descripcion_historial,
                g.usuario["id_usuario"],
                accion["id_incidencia"],
            )
        )

        mensaje = (
            f"Se asignó un responsable a una acción de tu reporte "
            f"'{accion['incidencia_titulo']}'."
        )

        cursor.execute(
            """
            INSERT INTO notificaciones
            (
                mensaje,
                leido,
                id_usuario
            )
            VALUES (%s, FALSE, %s)
            """,
            (
                mensaje,
                accion["estudiante_id"],
            )
        )

        conexion.commit()

        flash("Responsable actualizado correctamente.", "success")

    except Error as error:
        conexion.rollback()
        print("Error al actualizar responsable:", error)
        flash("No se pudo actualizar el responsable.", "danger")

    finally:
        cerrar_recursos(cursor, conexion)

    return redirect(url_for("acciones.detalle_accion", id_accion=id_accion))