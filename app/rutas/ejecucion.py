from datetime import datetime, timedelta
from flask import Blueprint, render_template, request, session, flash, redirect, url_for
from app.base_datos import db
from app.modelos import CicloPrueba, CasoPrueba, Resultado
from config.constantes import EstadoResultadoEnum, EstadoEjecucionEnum
from app.decoradores import requerir_autenticacion

ejecucion_bp = Blueprint('ejecucion_bp', __name__, url_prefix='/ejecucion')
VENTANA_EJECUCION_ACTIVA = timedelta(minutes=30)


def _es_ejecucion_activa(resultado):
    if not resultado or not resultado.estado_ejecucion:
        return False
    if resultado.estado_ejecucion.value not in ('pendiente', 'en_progreso'):
        return False
    if not resultado.fecha_creacion:
        return False
    return datetime.utcnow() - resultado.fecha_creacion <= VENTANA_EJECUCION_ACTIVA


@ejecucion_bp.route('/')
@requerir_autenticacion
def indice():
    ciclos = CicloPrueba.query.all()
    casos = CasoPrueba.query.all()
    
    stats_ciclos = []
    for c in ciclos:
        c.actualizar_estado_desde_resultados()
        total = len(c.casos_prueba)
        resultados_map = {}
        for res in c.resultados:
            if res.caso_prueba_id not in resultados_map or res.fecha_creacion > resultados_map[res.caso_prueba_id].fecha_creacion:
                resultados_map[res.caso_prueba_id] = res
        
        pasados = sum(1 for res in resultados_map.values() if res.estado == EstadoResultadoEnum.PASADO)
        fallidos = sum(1 for res in resultados_map.values() if res.estado == EstadoResultadoEnum.FALLIDO)
        en_progreso = sum(1 for res in resultados_map.values() if res.estado == EstadoResultadoEnum.EN_PROGRESO or _es_ejecucion_activa(res))
        pendientes = total - len(resultados_map)
        
        stats_ciclos.append({
            'nombre': c.nombre,
            'total': total,
            'pasados': pasados,
            'fallidos': fallidos,
            'en_progreso': en_progreso,
            'pendientes': max(0, pendientes)
        })

    pasados_ind = 0
    fallidos_ind = 0
    en_progreso_ind = 0
    pendientes_ind = 0
    
    for caso in casos:
        ultimo_resultado = Resultado.query.filter_by(caso_prueba_id=caso.id).order_by(Resultado.fecha_creacion.desc()).first()
        if not ultimo_resultado:
            pendientes_ind += 1
        elif ultimo_resultado.estado == EstadoResultadoEnum.PASADO:
            pasados_ind += 1
        elif ultimo_resultado.estado == EstadoResultadoEnum.FALLIDO:
            fallidos_ind += 1
        else:
            en_progreso_ind += 1

    stats_casos = {
        'total': len(casos),
        'pasados': pasados_ind,
        'fallidos': fallidos_ind,
        'en_progreso': en_progreso_ind,
        'pendientes': pendientes_ind
    }
    
    return render_template('ejecucion/indice.html', 
                           stats_ciclos=stats_ciclos,
                           stats_casos=stats_casos)

@ejecucion_bp.route('/ciclos')
@requerir_autenticacion
def ciclos():
    ciclos = CicloPrueba.query.all()
    ciclo_id = request.args.get('ciclo_id', type=int)
    
    ciclo_seleccionado = None
    casos_con_estado = []
    ciclo_tiene_resumen_auto = False
    
    if ciclos:
        if ciclo_id:
            ciclo_seleccionado = next((c for c in ciclos if c.id == ciclo_id), None)
        if not ciclo_seleccionado:
            ciclo_seleccionado = ciclos[0]
            ciclo_id = ciclo_seleccionado.id
        
        ciclo_seleccionado.actualizar_estado_desde_resultados()
        db.session.commit()
        
        for caso in ciclo_seleccionado.casos_prueba:
            ultimo_resultado = Resultado.query.filter_by(
                ciclo_prueba_id=ciclo_seleccionado.id,
                caso_prueba_id=caso.id
            ).order_by(Resultado.fecha_creacion.desc()).first()
            
            if ultimo_resultado and ultimo_resultado.estado_ejecucion in (EstadoEjecucionEnum.PENDIENTE, EstadoEjecucionEnum.EN_PROGRESO):
                if not ultimo_resultado.fecha_creacion or datetime.utcnow() - ultimo_resultado.fecha_creacion > VENTANA_EJECUCION_ACTIVA:
                    ultimo_resultado.estado_ejecucion = EstadoEjecucionEnum.ERROR
                    db.session.commit()
            
            ejecucion_activa = False
            if caso.tipo.value == 'automatizado':
                ejecucion_activa = _es_ejecucion_activa(ultimo_resultado)
            
            casos_con_estado.append({
                'caso': caso,
                'ultimo_resultado': ultimo_resultado,
                'ejecucion_activa': ejecucion_activa,
            })
            if (
                ultimo_resultado
                and ultimo_resultado.modo_ejecucion
                and ultimo_resultado.modo_ejecucion.value == 'automatizado'
                and ultimo_resultado.estado_ejecucion
                and ultimo_resultado.estado_ejecucion.value == 'completado'
            ):
                ciclo_tiene_resumen_auto = True
            
    stats_ciclos = []
    for c in ciclos:
        c.actualizar_estado_desde_resultados()
        
        total_casos = len(c.casos_prueba)
        resultados_map = {}
        for res in c.resultados:
            if res.caso_prueba_id not in resultados_map or res.fecha_creacion > resultados_map[res.caso_prueba_id].fecha_creacion:
                resultados_map[res.caso_prueba_id] = res
                
        pasados = sum(1 for res in resultados_map.values() if res.estado == EstadoResultadoEnum.PASADO)
        fallidos = sum(1 for res in resultados_map.values() if res.estado == EstadoResultadoEnum.FALLIDO)
        en_progreso = sum(
            1 for res in resultados_map.values()
            if res.estado == EstadoResultadoEnum.EN_PROGRESO
            or _es_ejecucion_activa(res)
        )
        pendientes = total_casos - len(resultados_map)
        
        stats_ciclos.append({
            'id': c.id,
            'nombre': c.nombre,
            'total': total_casos,
            'pasados': pasados,
            'fallidos': fallidos,
            'en_progreso': en_progreso,
            'pendientes': max(0, pendientes)
        })
    
    db.session.commit()
        
    return render_template('ejecucion/ciclos.html', 
                           ciclos=ciclos, 
                           ciclo_seleccionado=ciclo_seleccionado,
                           casos_con_estado=casos_con_estado,
                           stats_ciclos=stats_ciclos,
                           ciclo_tiene_resumen_auto=ciclo_tiene_resumen_auto)

@ejecucion_bp.route('/casos')
@requerir_autenticacion
def casos():
    casos_db = CasoPrueba.query.all()
    
    casos_automaticos = []
    casos_manuales = []
    
    pasados_ind = 0
    fallidos_ind = 0
    en_progreso_ind = 0
    pendientes_ind = 0
    
    for caso in casos_db:
        ultimo_resultado = Resultado.query.filter_by(
            caso_prueba_id=caso.id
        ).order_by(Resultado.fecha_creacion.desc()).first()
        
        ejecucion_activa = False
        if caso.tipo.value == 'automatizado':
            ejecucion_activa = _es_ejecucion_activa(ultimo_resultado)
        
        if not ultimo_resultado:
            pendientes_ind += 1
        elif ultimo_resultado.estado == EstadoResultadoEnum.PASADO:
            pasados_ind += 1
        elif ultimo_resultado.estado == EstadoResultadoEnum.FALLIDO:
            fallidos_ind += 1
        else:
            en_progreso_ind += 1
            
        info = {
            'caso': caso,
            'ultimo_resultado': ultimo_resultado,
            'ejecucion_activa': ejecucion_activa
        }
        
        if caso.tipo.value == 'automatizado':
            casos_automaticos.append(info)
        else:
            casos_manuales.append(info)
            
    stats_casos = {
        'total': len(casos_db),
        'pasados': pasados_ind,
        'fallidos': fallidos_ind,
        'en_progreso': en_progreso_ind,
        'pendientes': pendientes_ind
    }
            
    return render_template('ejecucion/casos.html',
                           casos_automaticos=casos_automaticos,
                           casos_manuales=casos_manuales,
                           stats_casos=stats_casos)
