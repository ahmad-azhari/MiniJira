from flask import Blueprint, render_template, session, request
from app.modelos import (
    Proyecto, Epica, CasoPrueba, Resultado, Defecto,
    CicloPrueba, Usuario
)
from config.constantes import (
    EstadoEnum, EstadoResultadoEnum, EstadoDefectoEnum, TipoEnum, PrioridadEnum
)
from functools import wraps
from flask import flash, redirect, url_for

reportes_bp = Blueprint('reportes_bp', __name__, url_prefix='/reportes')


def requerir_autenticacion(f):
    @wraps(f)
    def wrapper(*args, **kwargs):
        if 'usuario_id' not in session:
            flash('Debes iniciar sesión.', 'warning')
            return redirect(url_for('auth_bp.login'))
        return f(*args, **kwargs)
    return wrapper


@reportes_bp.route('/dashboard')
@requerir_autenticacion
def dashboard():
    total_proyectos = Proyecto.query.count()
    total_epicas = Epica.query.count()
    total_casos = CasoPrueba.query.count()
    total_ciclos = CicloPrueba.query.count()

    epicas_nuevas = Epica.query.filter_by(estado=EstadoEnum.NUEVO).count()
    epicas_en_progreso = Epica.query.filter_by(estado=EstadoEnum.EN_PROGRESO).count()
    epicas_completadas = Epica.query.filter_by(estado=EstadoEnum.TERMINADO).count()

    resultados_pasados = Resultado.query.filter_by(estado=EstadoResultadoEnum.PASADO).count()
    resultados_fallidos = Resultado.query.filter_by(estado=EstadoResultadoEnum.FALLIDO).count()

    defectos_nuevos = Defecto.query.filter_by(estado=EstadoDefectoEnum.ABIERTO).count()
    defectos_resueltos = Defecto.query.filter_by(estado=EstadoDefectoEnum.CERRADO).count()

    ultimas_epicas = Epica.query.order_by(Epica.fecha_creacion.desc()).limit(5).all()
    ultimos_defectos = Defecto.query.order_by(Defecto.fecha_creacion.desc()).limit(5).all()

    stats = {
        'proyectos': total_proyectos,
        'epicas': total_epicas,
        'casos': total_casos,
        'ciclos': total_ciclos,
        'epicas_nuevas': epicas_nuevas,
        'epicas_en_progreso': epicas_en_progreso,
        'epicas_completadas': epicas_completadas,
        'resultados_pasados': resultados_pasados,
        'resultados_fallidos': resultados_fallidos,
        'defectos_nuevos': defectos_nuevos,
        'defectos_resueltos': defectos_resueltos,
    }

    return render_template('reportes/dashboard.html',
                         stats=stats,
                         ultimas_epicas=ultimas_epicas,
                         ultimos_defectos=ultimos_defectos)


@reportes_bp.route('/proyectos')
@requerir_autenticacion
def reporte_proyectos():
    query = request.args.get('q', '').strip()
    if query:
        proyectos = Proyecto.query.filter(Proyecto.nombre.ilike(f'%{query}%')).all()
    else:
        proyectos = Proyecto.query.all()

    data = []
    for proyecto in proyectos:
        epicas = Epica.query.filter(Epica.proyecto_id == proyecto.id, Epica.tipo != TipoEnum.STORY).count()
        historias = Epica.query.filter(Epica.proyecto_id == proyecto.id, Epica.tipo == TipoEnum.STORY).count()
        casos = CasoPrueba.query.join(CasoPrueba.epicas).filter(Epica.proyecto_id == proyecto.id).count()

        data.append({
            'proyecto': proyecto,
            'epicas': epicas,
            'historias': historias,
            'casos': casos,
        })

    return render_template('reportes/proyectos.html', data=data)


@reportes_bp.route('/calidad')
@requerir_autenticacion
def reporte_calidad():
    total_casos = CasoPrueba.query.count()
    total_resultados = Resultado.query.count()

    if total_resultados > 0:
        tasa_exito = (Resultado.query.filter_by(estado=EstadoResultadoEnum.PASADO).count() / total_resultados) * 100
    else:
        tasa_exito = 0

    total_defectos = Defecto.query.count()
    defectos_abiertos = Defecto.query.filter(
        Defecto.estado.in_([EstadoDefectoEnum.ABIERTO, EstadoDefectoEnum.EN_PROGRESO])
    ).count()

    ciclos = CicloPrueba.query.all()
    ciclo_stats = []

    for ciclo in ciclos:
        total = len(ciclo.casos_prueba)
        resultados = Resultado.query.filter_by(ciclo_prueba_id=ciclo.id).all()
        pasados = sum(1 for r in resultados if r.estado == EstadoResultadoEnum.PASADO)

        ciclo_stats.append({
            'ciclo': ciclo,
            'total_casos': total,
            'total_resultados': len(resultados),
            'pasados': pasados,
            'tasa': (pasados / len(resultados) * 100) if resultados else 0
        })

    return render_template('reportes/calidad.html',
                         total_casos=total_casos,
                         tasa_exito=tasa_exito,
                         total_defectos=total_defectos,
                         defectos_abiertos=defectos_abiertos,
                         ciclo_stats=ciclo_stats)


@reportes_bp.route('/defectos')
@requerir_autenticacion
def reporte_defectos():
    defectos_por_estado = {}
    for estado in EstadoDefectoEnum:
        count = Defecto.query.filter_by(estado=estado).count()
        defectos_por_estado[estado.value] = count

    defectos_por_prioridad = {}
    for prioridad in PrioridadEnum:
        count = Defecto.query.filter_by(prioridad=prioridad).count()
        defectos_por_prioridad[prioridad.value] = count

    defectos_asignados = Defecto.query.filter(Defecto.usuario_asignado_id.isnot(None)).all()

    usuarios_asignacion = {}
    for defecto in defectos_asignados:
        usuario = defecto.asignado_a
        if usuario:
            if usuario.nombre_usuario not in usuarios_asignacion:
                usuarios_asignacion[usuario.nombre_usuario] = 0
            usuarios_asignacion[usuario.nombre_usuario] += 1

    return render_template('reportes/defectos.html',
                         defectos_por_estado=defectos_por_estado,
                         defectos_por_prioridad=defectos_por_prioridad,
                         usuarios_asignacion=usuarios_asignacion)
