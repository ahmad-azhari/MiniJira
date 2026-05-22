from flask import Blueprint, render_template, request, session, flash, redirect, url_for
from app.base_datos import db
from app.modelos import CicloPrueba, CasoPrueba, Resultado
from config.constantes import EstadoResultadoEnum
from app.decoradores import requerir_autenticacion

ejecucion_bp = Blueprint('ejecucion_bp', __name__, url_prefix='/ejecucion')


@ejecucion_bp.route('/')
@requerir_autenticacion
def indice():
    ciclos = CicloPrueba.query.all()
    ciclo_id = request.args.get('ciclo_id', type=int)
    
    ciclo_seleccionado = None
    casos_con_estado = []
    
    if ciclos:
        if ciclo_id:
            ciclo_seleccionado = next((c for c in ciclos if c.id == ciclo_id), None)
        if not ciclo_seleccionado:
            ciclo_seleccionado = ciclos[0]
            ciclo_id = ciclo_seleccionado.id
        for caso in ciclo_seleccionado.casos_prueba:
            ultimo_resultado = Resultado.query.filter_by(
                ciclo_prueba_id=ciclo_seleccionado.id,
                caso_prueba_id=caso.id
            ).order_by(Resultado.fecha_creacion.desc()).first()
            
            casos_con_estado.append({
                'caso': caso,
                'ultimo_resultado': ultimo_resultado
            })
            
    stats_ciclos = []
    for c in ciclos:
        total_casos = len(c.casos_prueba)
        resultados_map = {}
        for res in c.resultados:
            if res.caso_prueba_id not in resultados_map or res.fecha_creacion > resultados_map[res.caso_prueba_id].fecha_creacion:
                resultados_map[res.caso_prueba_id] = res
                
        pasados = sum(1 for res in resultados_map.values() if res.estado == EstadoResultadoEnum.PASADO)
        fallidos = sum(1 for res in resultados_map.values() if res.estado == EstadoResultadoEnum.FALLIDO)
        bloqueados = sum(1 for res in resultados_map.values() if res.estado == EstadoResultadoEnum.BLOQUEADO)
        en_progreso = sum(1 for res in resultados_map.values() if res.estado == EstadoResultadoEnum.EN_PROGRESO)
        pendientes = total_casos - len(resultados_map)
        
        stats_ciclos.append({
            'id': c.id,
            'nombre': c.nombre,
            'total': total_casos,
            'pasados': pasados,
            'fallidos': fallidos,
            'bloqueados': bloqueados,
            'en_progreso': en_progreso,
            'pendientes': max(0, pendientes)
        })
        
    return render_template(
        'ejecucion/indice.html',
        ciclos=ciclos,
        ciclo_seleccionado=ciclo_seleccionado,
        casos_con_estado=casos_con_estado,
        stats_ciclos=stats_ciclos
    )
