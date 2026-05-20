"""
reportes.py
Módulo para que el administrador visualice reportes/incidencias
y registre acciones realizadas frente a cada incidencia.

Usa las tablas existentes:
- incidencias
- usuarios
- acciones
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


reportes_bp = Blueprint("reportes", __name__)


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


ESTADOS_ACCION = {
    "pendiente": "Pendiente",
    "en_proceso": "En proceso",
    "finalizada": "Finalizada",
}


def cerrar_recursos(cursor=None, conexion=None):
    if cursor is not None:
        cursor.close()

    if conexion is not None:
        conexion.close()


def solo_admin():
    """
    Permite acceso solo a usuarios administradores.
    """
    if g.usuario is None:
        abort(403)

    if g.usuario["rol"] != "administrador":
        abort(403)


def enriquecer_incidencia(incidencia):
    """
    Agrega textos legibles sin modificar la base de datos.
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


def enriquecer_accion(accion):
    accion["estado_texto"] = ESTADOS_ACCION.get(
        accion["estado"],
        accion["estado"]
    )

    return accion


@reportes_bp.route("/admin/reportes")
@login_requerido
def panel_reportes():
    """
    Lista general de reportes para el administrador.
    Permite filtrar por búsqueda, estado, prioridad y categoría.
    """
    solo_admin()

    busqueda = request.args.get("q", "").strip()
    estado = request.args.get("estado", "").strip()
    prioridad = request.args.get("prioridad", "").strip()
    categoria = request.args.get("categoria", "").strip()

    conexion = obtener_conexion()

    if conexion is None:
        flash("No se pudo conectar con la base de datos.", "danger")
        return render_template(
            "reportes_admin.html",
            reportes=[],
            resumen={},
            filtros={
                "q": busqueda,
                "estado": estado,
                "prioridad": prioridad,
                "categoria": categoria,
            },
            estados=ESTADOS_INCIDENCIA,
            prioridades=PRIORIDADES,
            categorias=CATEGORIAS,
        )

    cursor = conexion.cursor(dictionary=True)

    try:
        condiciones = []
        valores = []

        if busqueda:
            condiciones.append(
                """
                (
                    i.titulo LIKE %s
                    OR i.descripcion LIKE %s
                    OR i.laboratorio LIKE %s
                    OR u.nombre LIKE %s
                    OR u.apellido LIKE %s
                    OR u.correo LIKE %s
                )
                """
            )

            texto = f"%{busqueda}%"
            valores.extend([texto, texto, texto, texto, texto, texto])

        if estado:
            condiciones.append("i.estado = %s")
            valores.append(estado)

        if prioridad:
            condiciones.append("i.prioridad = %s")
            valores.append(prioridad)

        if categoria:
            condiciones.append("i.categoria = %s")
            valores.append(categoria)

        where_sql = ""

        if condiciones:
            where_sql = "WHERE " + " AND ".join(condiciones)

        consulta = f"""
            SELECT
                i.id_incidencia,
                i.titulo,
                i.descripcion,
                i.categoria,
                i.prioridad,
                i.estado,
                i.laboratorio,
                i.fecha_reporte,
                i.evidencia_url,
                i.id_usuario,

                u.nombre AS estudiante_nombre,
                u.apellido AS estudiante_apellido,
                u.correo AS estudiante_correo,

                COUNT(a.id_accion) AS total_acciones,

                COALESCE(
                    SUM(CASE WHEN a.estado = 'pendiente' THEN 1 ELSE 0 END),
                    0
                ) AS acciones_pendientes,

                COALESCE(
                    SUM(CASE WHEN a.estado = 'en_proceso' THEN 1 ELSE 0 END),
                    0
                ) AS acciones_en_proceso,

                COALESCE(
                    SUM(CASE WHEN a.estado = 'finalizada' THEN 1 ELSE 0 END),
                    0
                ) AS acciones_finalizadas

            FROM incidencias i
            INNER JOIN usuarios u
                ON u.id_usuario = i.id_usuario
            LEFT JOIN acciones a
                ON a.id_incidencia = i.id_incidencia

            {where_sql}

            GROUP BY
                i.id_incidencia,
                i.titulo,
                i.descripcion,
                i.categoria,
                i.prioridad,
                i.estado,
                i.laboratorio,
                i.fecha_reporte,
                i.evidencia_url,
                i.id_usuario,
                u.nombre,
                u.apellido,
                u.correo

            ORDER BY i.fecha_reporte DESC
        """

        cursor.execute(consulta, valores)
        reportes = cursor.fetchall()

        reportes = [
            enriquecer_incidencia(reporte)
            for reporte in reportes
        ]

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
            """
        )

        resumen = cursor.fetchone()

        return render_template(
            "reportes_admin.html",
            reportes=reportes,
            resumen=resumen,
            filtros={
                "q": busqueda,
                "estado": estado,
                "prioridad": prioridad,
                "categoria": categoria,
            },
            estados=ESTADOS_INCIDENCIA,
            prioridades=PRIORIDADES,
            categorias=CATEGORIAS,
        )

    except Error as error:
        print("Error al cargar reportes:", error)
        flash("No se pudieron cargar los reportes.", "danger")

        return render_template(
            "reportes_admin.html",
            reportes=[],
            resumen={},
            filtros={
                "q": busqueda,
                "estado": estado,
                "prioridad": prioridad,
                "categoria": categoria,
            },
            estados=ESTADOS_INCIDENCIA,
            prioridades=PRIORIDADES,
            categorias=CATEGORIAS,
        )

    finally:
        cerrar_recursos(cursor, conexion)


@reportes_bp.route("/admin/reportes/<int:id_incidencia>")
@login_requerido
def detalle_reporte(id_incidencia):
    """
    Muestra el detalle de una incidencia y las acciones tomadas.
    """
    solo_admin()

    conexion = obtener_conexion()

    if conexion is None:
        flash("No se pudo conectar con la base de datos.", "danger")
        return redirect(url_for("reportes.panel_reportes"))

    cursor = conexion.cursor(dictionary=True)

    try:
        cursor.execute(
            """
            SELECT
                i.id_incidencia,
                i.titulo,
                i.descripcion,
                i.categoria,
                i.prioridad,
                i.estado,
                i.laboratorio,
                i.fecha_reporte,
                i.evidencia_url,
                i.id_usuario,

                u.nombre AS estudiante_nombre,
                u.apellido AS estudiante_apellido,
                u.correo AS estudiante_correo

            FROM incidencias i
            INNER JOIN usuarios u
                ON u.id_usuario = i.id_usuario
            WHERE i.id_incidencia = %s
            LIMIT 1
            """,
            (id_incidencia,)
        )

        reporte = cursor.fetchone()

        if reporte is None:
            abort(404)

        reporte = enriquecer_incidencia(reporte)

        cursor.execute(
            """
            SELECT
                a.id_accion,
                a.descripcion,
                a.fecha_inicio,
                a.fecha_fin,
                a.estado,
                a.id_supervisor,
                a.id_responsable,

                s.nombre AS supervisor_nombre,
                s.apellido AS supervisor_apellido,
                s.rol AS supervisor_rol,

                r.nombre AS responsable_nombre,
                r.apellido AS responsable_apellido,
                r.rol AS responsable_rol

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
        acciones = [
            enriquecer_accion(accion)
            for accion in acciones
        ]

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
                id_usuario,
                nombre,
                apellido,
                correo,
                rol
            FROM usuarios
            WHERE rol IN ('supervisor', 'administrador')
            AND estado = TRUE
            ORDER BY rol, apellido, nombre
            """
        )

        responsables = cursor.fetchall()

        return render_template(
            "detalle_reporte_admin.html",
            reporte=reporte,
            acciones=acciones,
            historial=historial,
            responsables=responsables,
            estados=ESTADOS_INCIDENCIA,
            estados_accion=ESTADOS_ACCION,
        )

    except Error as error:
        print("Error al cargar detalle del reporte:", error)
        flash("No se pudo cargar el detalle del reporte.", "danger")
        return redirect(url_for("reportes.panel_reportes"))

    finally:
        cerrar_recursos(cursor, conexion)


@reportes_bp.route("/admin/reportes/<int:id_incidencia>/accion", methods=["POST"])
@login_requerido
def registrar_accion(id_incidencia):
    """
    Registra una acción administrativa frente a una incidencia.

    También puede cambiar el estado de la incidencia y registrar historial.
    """
    solo_admin()

    descripcion = request.form.get("descripcion", "").strip()
    estado_accion = request.form.get("estado_accion", "pendiente").strip()
    nuevo_estado_incidencia = request.form.get("nuevo_estado", "").strip()
    id_responsable = request.form.get("id_responsable", "").strip()

    if not descripcion:
        flash("Describe la acción realizada.", "warning")
        return redirect(url_for("reportes.detalle_reporte", id_incidencia=id_incidencia))

    if estado_accion not in ESTADOS_ACCION:
        flash("Estado de acción no válido.", "warning")
        return redirect(url_for("reportes.detalle_reporte", id_incidencia=id_incidencia))

    if nuevo_estado_incidencia and nuevo_estado_incidencia not in ESTADOS_INCIDENCIA:
        flash("Estado de incidencia no válido.", "warning")
        return redirect(url_for("reportes.detalle_reporte", id_incidencia=id_incidencia))

    id_responsable_valor = None

    if id_responsable:
        try:
            id_responsable_valor = int(id_responsable)
        except ValueError:
            id_responsable_valor = None

    conexion = obtener_conexion()

    if conexion is None:
        flash("No se pudo conectar con la base de datos.", "danger")
        return redirect(url_for("reportes.detalle_reporte", id_incidencia=id_incidencia))

    cursor = conexion.cursor(dictionary=True)

    try:
        cursor.execute(
            """
            SELECT
                id_incidencia,
                titulo,
                estado,
                id_usuario
            FROM incidencias
            WHERE id_incidencia = %s
            LIMIT 1
            """,
            (id_incidencia,)
        )

        incidencia = cursor.fetchone()

        if incidencia is None:
            abort(404)

        estado_anterior = incidencia["estado"]

        cursor.execute(
            """
            INSERT INTO acciones
            (
                descripcion,
                estado,
                id_incidencia,
                id_supervisor,
                id_responsable
            )
            VALUES (%s, %s, %s, %s, %s)
            """,
            (
                descripcion,
                estado_accion,
                id_incidencia,
                g.usuario["id_usuario"],
                id_responsable_valor,
            )
        )

        if nuevo_estado_incidencia and nuevo_estado_incidencia != estado_anterior:
            cursor.execute(
                """
                UPDATE incidencias
                SET estado = %s
                WHERE id_incidencia = %s
                """,
                (
                    nuevo_estado_incidencia,
                    id_incidencia,
                )
            )

            tipo_evento = "cambio_estado"
            descripcion_historial = (
                f"El administrador {g.usuario['nombre']} {g.usuario['apellido']} "
                f"registró una acción y cambió el estado de "
                f"{estado_anterior} a {nuevo_estado_incidencia}."
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
                    tipo_evento,
                    estado_anterior,
                    nuevo_estado_incidencia,
                    descripcion_historial,
                    g.usuario["id_usuario"],
                    id_incidencia,
                )
            )

            mensaje_notificacion = (
                f"Tu reporte '{incidencia['titulo']}' cambió de estado: "
                f"{ESTADOS_INCIDENCIA.get(nuevo_estado_incidencia, nuevo_estado_incidencia)}."
            )

        else:
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
                    "comentario",
                    f"El administrador registró una acción: {descripcion}",
                    g.usuario["id_usuario"],
                    id_incidencia,
                )
            )

            mensaje_notificacion = (
                f"Se registró una nueva acción administrativa en tu reporte "
                f"'{incidencia['titulo']}'."
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
                mensaje_notificacion,
                incidencia["id_usuario"],
            )
        )

        conexion.commit()

        flash("Acción registrada correctamente.", "success")

    except Error as error:
        conexion.rollback()
        print("Error al registrar acción:", error)
        flash("No se pudo registrar la acción.", "danger")

    finally:
        cerrar_recursos(cursor, conexion)

    return redirect(url_for("reportes.detalle_reporte", id_incidencia=id_incidencia))


@reportes_bp.route("/admin/reportes/<int:id_incidencia>/estado", methods=["POST"])
@login_requerido
def cambiar_estado_reporte(id_incidencia):
    """
    Cambia únicamente el estado de la incidencia.
    """
    solo_admin()

    nuevo_estado = request.form.get("estado", "").strip()

    if nuevo_estado not in ESTADOS_INCIDENCIA:
        flash("Estado no válido.", "warning")
        return redirect(url_for("reportes.detalle_reporte", id_incidencia=id_incidencia))

    conexion = obtener_conexion()

    if conexion is None:
        flash("No se pudo conectar con la base de datos.", "danger")
        return redirect(url_for("reportes.detalle_reporte", id_incidencia=id_incidencia))

    cursor = conexion.cursor(dictionary=True)

    try:
        cursor.execute(
            """
            SELECT
                id_incidencia,
                titulo,
                estado,
                id_usuario
            FROM incidencias
            WHERE id_incidencia = %s
            LIMIT 1
            """,
            (id_incidencia,)
        )

        incidencia = cursor.fetchone()

        if incidencia is None:
            abort(404)

        estado_anterior = incidencia["estado"]

        if estado_anterior == nuevo_estado:
            flash("El reporte ya tiene ese estado.", "warning")
            return redirect(url_for("reportes.detalle_reporte", id_incidencia=id_incidencia))

        cursor.execute(
            """
            UPDATE incidencias
            SET estado = %s
            WHERE id_incidencia = %s
            """,
            (
                nuevo_estado,
                id_incidencia,
            )
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
                "cambio_estado",
                estado_anterior,
                nuevo_estado,
                (
                    f"El administrador {g.usuario['nombre']} {g.usuario['apellido']} "
                    f"cambió el estado del reporte."
                ),
                g.usuario["id_usuario"],
                id_incidencia,
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
            VALUES (%s, FALSE, %s)
            """,
            (
                (
                    f"Tu reporte '{incidencia['titulo']}' cambió de estado: "
                    f"{ESTADOS_INCIDENCIA.get(nuevo_estado, nuevo_estado)}."
                ),
                incidencia["id_usuario"],
            )
        )

        conexion.commit()

        flash("Estado del reporte actualizado.", "success")

    except Error as error:
        conexion.rollback()
        print("Error al cambiar estado:", error)
        flash("No se pudo cambiar el estado del reporte.", "danger")

    finally:
        cerrar_recursos(cursor, conexion)

    return redirect(url_for("reportes.detalle_reporte", id_incidencia=id_incidencia))