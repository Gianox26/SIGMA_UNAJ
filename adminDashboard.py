from functools import wraps
from datetime import datetime
from flask import Blueprint, render_template, session, redirect, url_for, flash
from conexion import obtener_conexion


admin_bp = Blueprint("admin", __name__, url_prefix="/admin")


def admin_requerido(vista):
    @wraps(vista)
    def funcion_protegida(*args, **kwargs):
        if "usuario_id" not in session:
            flash("Primero inicia sesión para continuar.", "warning")
            return redirect(url_for("login.iniciar_sesion"))

        if session.get("rol") != "administrador":
            flash("No tienes permisos para acceder al panel administrador.", "danger")
            return redirect(url_for("dashboard.estudiante"))

        return vista(*args, **kwargs)

    return funcion_protegida


def obtener_usuario_actual(cursor):
    id_usuario = session.get("usuario_id")

    cursor.execute(
        """
        SELECT 
            id_usuario,
            nombre,
            apellido,
            correo,
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

    if not usuario:
        session.clear()
        return None

    return usuario


def ejecutar_scalar(cursor, consulta, parametros=None):
    cursor.execute(consulta, parametros or ())
    fila = cursor.fetchone()

    if not fila:
        return 0

    valor = list(fila.values())[0]
    return valor or 0


def calcular_variacion(actual, anterior):
    actual = actual or 0
    anterior = anterior or 0

    if anterior == 0:
        if actual == 0:
            return 0
        return 100

    return round(((actual - anterior) / anterior) * 100, 1)


def obtener_kpis(cursor):
    total_reportes = ejecutar_scalar(
        cursor,
        "SELECT COUNT(*) AS total FROM incidencias"
    )

    reportes_criticos = ejecutar_scalar(
        cursor,
        """
        SELECT COUNT(*) AS total
        FROM incidencias
        WHERE prioridad = 'critica'
        """
    )

    reportes_en_proceso = ejecutar_scalar(
        cursor,
        """
        SELECT COUNT(*) AS total
        FROM incidencias
        WHERE estado = 'en_proceso'
        """
    )

    reportes_resueltos = ejecutar_scalar(
        cursor,
        """
        SELECT COUNT(*) AS total
        FROM incidencias
        WHERE estado IN ('resuelta', 'cerrada')
        """
    )

    total_mes_actual = ejecutar_scalar(
        cursor,
        """
        SELECT COUNT(*) AS total
        FROM incidencias
        WHERE YEAR(fecha_reporte) = YEAR(CURDATE())
          AND MONTH(fecha_reporte) = MONTH(CURDATE())
        """
    )

    total_mes_anterior = ejecutar_scalar(
        cursor,
        """
        SELECT COUNT(*) AS total
        FROM incidencias
        WHERE YEAR(fecha_reporte) = YEAR(DATE_SUB(CURDATE(), INTERVAL 1 MONTH))
          AND MONTH(fecha_reporte) = MONTH(DATE_SUB(CURDATE(), INTERVAL 1 MONTH))
        """
    )

    criticos_mes_actual = ejecutar_scalar(
        cursor,
        """
        SELECT COUNT(*) AS total
        FROM incidencias
        WHERE prioridad = 'critica'
          AND YEAR(fecha_reporte) = YEAR(CURDATE())
          AND MONTH(fecha_reporte) = MONTH(CURDATE())
        """
    )

    criticos_mes_anterior = ejecutar_scalar(
        cursor,
        """
        SELECT COUNT(*) AS total
        FROM incidencias
        WHERE prioridad = 'critica'
          AND YEAR(fecha_reporte) = YEAR(DATE_SUB(CURDATE(), INTERVAL 1 MONTH))
          AND MONTH(fecha_reporte) = MONTH(DATE_SUB(CURDATE(), INTERVAL 1 MONTH))
        """
    )

    proceso_mes_actual = ejecutar_scalar(
        cursor,
        """
        SELECT COUNT(*) AS total
        FROM incidencias
        WHERE estado = 'en_proceso'
          AND YEAR(fecha_reporte) = YEAR(CURDATE())
          AND MONTH(fecha_reporte) = MONTH(CURDATE())
        """
    )

    proceso_mes_anterior = ejecutar_scalar(
        cursor,
        """
        SELECT COUNT(*) AS total
        FROM incidencias
        WHERE estado = 'en_proceso'
          AND YEAR(fecha_reporte) = YEAR(DATE_SUB(CURDATE(), INTERVAL 1 MONTH))
          AND MONTH(fecha_reporte) = MONTH(DATE_SUB(CURDATE(), INTERVAL 1 MONTH))
        """
    )

    resueltos_mes_actual = ejecutar_scalar(
        cursor,
        """
        SELECT COUNT(*) AS total
        FROM incidencias
        WHERE estado IN ('resuelta', 'cerrada')
          AND YEAR(fecha_reporte) = YEAR(CURDATE())
          AND MONTH(fecha_reporte) = MONTH(CURDATE())
        """
    )

    resueltos_mes_anterior = ejecutar_scalar(
        cursor,
        """
        SELECT COUNT(*) AS total
        FROM incidencias
        WHERE estado IN ('resuelta', 'cerrada')
          AND YEAR(fecha_reporte) = YEAR(DATE_SUB(CURDATE(), INTERVAL 1 MONTH))
          AND MONTH(fecha_reporte) = MONTH(DATE_SUB(CURDATE(), INTERVAL 1 MONTH))
        """
    )

    return {
        "total_reportes": total_reportes,
        "reportes_criticos": reportes_criticos,
        "reportes_en_proceso": reportes_en_proceso,
        "reportes_resueltos": reportes_resueltos,

        "variacion_total": calcular_variacion(total_mes_actual, total_mes_anterior),
        "variacion_criticos": calcular_variacion(criticos_mes_actual, criticos_mes_anterior),
        "variacion_proceso": calcular_variacion(proceso_mes_actual, proceso_mes_anterior),
        "variacion_resueltos": calcular_variacion(resueltos_mes_actual, resueltos_mes_anterior),
    }


def obtener_reportes_por_mes(cursor):
    cursor.execute(
        """
        SELECT 
            MONTH(fecha_reporte) AS mes,
            COUNT(*) AS total
        FROM incidencias
        WHERE YEAR(fecha_reporte) = YEAR(CURDATE())
        GROUP BY MONTH(fecha_reporte)
        ORDER BY mes
        """
    )

    filas = cursor.fetchall()

    meses = [
        "Ene", "Feb", "Mar", "Abr", "May", "Jun",
        "Jul", "Ago", "Sep", "Oct", "Nov", "Dic"
    ]

    datos = {fila["mes"]: fila["total"] for fila in filas}

    resultado = []

    for indice, nombre_mes in enumerate(meses, start=1):
        resultado.append({
            "mes": nombre_mes,
            "total": datos.get(indice, 0)
        })

    maximo = max([item["total"] for item in resultado], default=1)

    if maximo <= 0:
        maximo = 1

    for item in resultado:
        item["altura"] = round((item["total"] / maximo) * 100, 1)

    return resultado


def obtener_incidencias_recientes(cursor):
    cursor.execute(
        """
        SELECT 
            i.id_incidencia,
            CONCAT('INC-', YEAR(i.fecha_reporte), '-', LPAD(i.id_incidencia, 4, '0')) AS codigo,
            i.titulo,
            i.descripcion,
            i.categoria,
            i.prioridad,
            i.estado,
            i.laboratorio,
            DATE_FORMAT(i.fecha_reporte, '%d/%m/%Y %H:%i') AS fecha_reporte,
            u.nombre AS estudiante_nombre,
            u.apellido AS estudiante_apellido,
            (
                SELECT CONCAT(us.nombre, ' ', us.apellido)
                FROM acciones a
                INNER JOIN usuarios us ON us.id_usuario = a.id_supervisor
                WHERE a.id_incidencia = i.id_incidencia
                ORDER BY a.fecha_inicio DESC
                LIMIT 1
            ) AS asignado_a
        FROM incidencias i
        INNER JOIN usuarios u ON u.id_usuario = i.id_usuario
        ORDER BY i.fecha_reporte DESC
        LIMIT 8
        """
    )

    incidencias = cursor.fetchall()

    for item in incidencias:
        item["categoria_texto"] = texto_categoria(item["categoria"])
        item["prioridad_texto"] = texto_prioridad(item["prioridad"])
        item["estado_texto"] = texto_estado(item["estado"])

        if not item.get("asignado_a"):
            item["asignado_a"] = "Sin asignar"

    return incidencias


def obtener_notificaciones_admin(cursor):
    cursor.execute(
        """
        SELECT 
            n.id_notificacion,
            n.mensaje,
            n.leido,
            DATE_FORMAT(n.fecha, '%d/%m/%Y %H:%i') AS fecha,
            TIMESTAMPDIFF(MINUTE, n.fecha, NOW()) AS minutos
        FROM notificaciones n
        ORDER BY n.fecha DESC
        LIMIT 6
        """
    )

    notificaciones = cursor.fetchall()

    for item in notificaciones:
        item["tiempo"] = formatear_tiempo(item.get("minutos"))
        item["tipo"] = clasificar_notificacion(item.get("mensaje", ""))

    return notificaciones


def obtener_usuarios_recientes(cursor):
    cursor.execute(
        """
        SELECT 
            id_usuario,
            nombre,
            apellido,
            correo,
            rol,
            estado,
            DATE_FORMAT(fecha_registro, '%d/%m/%Y %H:%i') AS fecha_registro,
            TIMESTAMPDIFF(MINUTE, fecha_registro, NOW()) AS minutos
        FROM usuarios
        ORDER BY fecha_registro DESC
        LIMIT 6
        """
    )

    usuarios = cursor.fetchall()

    for item in usuarios:
        item["tiempo"] = formatear_tiempo(item.get("minutos"))
        item["rol_texto"] = texto_rol(item["rol"])

    return usuarios


def obtener_resumen_usuarios(cursor):
    total_usuarios = ejecutar_scalar(
        cursor,
        "SELECT COUNT(*) AS total FROM usuarios"
    )

    total_estudiantes = ejecutar_scalar(
        cursor,
        """
        SELECT COUNT(*) AS total
        FROM usuarios
        WHERE rol = 'usuario'
        """
    )

    total_supervisores = ejecutar_scalar(
        cursor,
        """
        SELECT COUNT(*) AS total
        FROM usuarios
        WHERE rol = 'supervisor'
        """
    )

    total_administradores = ejecutar_scalar(
        cursor,
        """
        SELECT COUNT(*) AS total
        FROM usuarios
        WHERE rol = 'administrador'
        """
    )

    return {
        "total_usuarios": total_usuarios,
        "total_estudiantes": total_estudiantes,
        "total_supervisores": total_supervisores,
        "total_administradores": total_administradores
    }


def obtener_distribucion_estado(cursor):
    cursor.execute(
        """
        SELECT estado, COUNT(*) AS total
        FROM incidencias
        GROUP BY estado
        """
    )

    filas = cursor.fetchall()

    estados_base = {
        "nueva": 0,
        "en_proceso": 0,
        "resuelta": 0,
        "cerrada": 0,
        "reabierta": 0
    }

    for fila in filas:
        estados_base[fila["estado"]] = fila["total"]

    return estados_base


def obtener_distribucion_prioridad(cursor):
    cursor.execute(
        """
        SELECT prioridad, COUNT(*) AS total
        FROM incidencias
        GROUP BY prioridad
        """
    )

    filas = cursor.fetchall()

    prioridades_base = {
        "baja": 0,
        "media": 0,
        "alta": 0,
        "critica": 0
    }

    for fila in filas:
        prioridades_base[fila["prioridad"]] = fila["total"]

    return prioridades_base


def texto_categoria(valor):
    categorias = {
        "calidad": "Calidad",
        "ambiental": "Ambiental"
    }

    return categorias.get(valor, valor)


def texto_prioridad(valor):
    prioridades = {
        "baja": "Baja",
        "media": "Media",
        "alta": "Alta",
        "critica": "Crítica"
    }

    return prioridades.get(valor, valor)


def texto_estado(valor):
    estados = {
        "nueva": "Nueva",
        "en_proceso": "En proceso",
        "resuelta": "Resuelta",
        "cerrada": "Cerrada",
        "reabierta": "Reabierta"
    }

    return estados.get(valor, valor)


def texto_rol(valor):
    roles = {
        "usuario": "Estudiante",
        "supervisor": "Supervisor",
        "administrador": "Administrador"
    }

    return roles.get(valor, valor)


def clasificar_notificacion(mensaje):
    mensaje = mensaje.lower()

    if "crític" in mensaje or "critic" in mensaje:
        return "danger"

    if "resuelto" in mensaje or "resuelta" in mensaje:
        return "success"

    if "usuario" in mensaje:
        return "user"

    if "asignado" in mensaje or "asignada" in mensaje:
        return "info"

    return "info"


def formatear_tiempo(minutos):
    if minutos is None:
        return "Hace unos minutos"

    if minutos < 1:
        return "Ahora"

    if minutos < 60:
        return f"Hace {minutos} min"

    horas = minutos // 60

    if horas < 24:
        if horas == 1:
            return "Hace 1 hora"
        return f"Hace {horas} horas"

    dias = horas // 24

    if dias == 1:
        return "Hace 1 día"

    return f"Hace {dias} días"


@admin_bp.route("/dashboard")
@admin_requerido
def dashboard():
    conexion = obtener_conexion()

    if conexion is None:
        flash("No se pudo conectar con la base de datos.", "danger")
        return redirect(url_for("dashboard.estudiante"))

    cursor = None

    try:
        cursor = conexion.cursor(dictionary=True)

        usuario = obtener_usuario_actual(cursor)

        if usuario is None:
            flash("Tu sesión no es válida. Inicia sesión nuevamente.", "warning")
            return redirect(url_for("login.iniciar_sesion"))

        kpis = obtener_kpis(cursor)
        reportes_por_mes = obtener_reportes_por_mes(cursor)
        incidencias_recientes = obtener_incidencias_recientes(cursor)
        notificaciones = obtener_notificaciones_admin(cursor)
        usuarios_recientes = obtener_usuarios_recientes(cursor)
        resumen_usuarios = obtener_resumen_usuarios(cursor)
        estados = obtener_distribucion_estado(cursor)
        prioridades = obtener_distribucion_prioridad(cursor)

        return render_template(
            "admin_dashboard.html",
            usuario=usuario,
            kpis=kpis,
            reportes_por_mes=reportes_por_mes,
            incidencias_recientes=incidencias_recientes,
            notificaciones=notificaciones,
            usuarios_recientes=usuarios_recientes,
            resumen_usuarios=resumen_usuarios,
            estados=estados,
            prioridades=prioridades,
            fecha_actual=datetime.now()
        )

    except Exception as error:
        print("Error en admin dashboard:", error)
        flash("Ocurrió un error al cargar el dashboard administrador.", "danger")
        return redirect(url_for("dashboard.estudiante"))

    finally:
        if cursor:
            cursor.close()

        conexion.close()


@admin_bp.route("/reportes")
@admin_requerido
def reportes():
    return redirect(url_for("admin.dashboard"))


@admin_bp.route("/usuarios")
@admin_requerido
def usuarios():
    return redirect(url_for("admin.dashboard"))


@admin_bp.route("/supervisores")
@admin_requerido
def supervisores():
    return redirect(url_for("admin.dashboard"))


@admin_bp.route("/estadisticas")
@admin_requerido
def estadisticas():
    return redirect(url_for("admin.dashboard"))


@admin_bp.route("/configuracion")
@admin_requerido
def configuracion():
    return redirect(url_for("admin.dashboard"))