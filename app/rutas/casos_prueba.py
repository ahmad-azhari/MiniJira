from flask import Blueprint, render_template, request, redirect, url_for, session, flash, jsonify
from app.base_datos import db
from app.modelos import CasoPrueba, Epica, Usuario
from config.constantes import TipoTestEnum, EstadoEnum, PrioridadEnum
from app.decoradores import requerir_autenticacion, requerir_miembro, requerir_admin

casos_prueba_bp = Blueprint('casos_prueba_bp', __name__, url_prefix='/casos-prueba')


@casos_prueba_bp.route('/')
@requerir_autenticacion
def indice():
    query = request.args.get('q', '').strip()
    if query:
        casos = CasoPrueba.query.filter(CasoPrueba.nombre.ilike(f'%{query}%')).all()
    else:
        casos = CasoPrueba.query.all()
    return render_template('casos_prueba/indice.html', casos=casos)


@casos_prueba_bp.route('/<int:caso_id>')
@requerir_autenticacion
def detalle(caso_id):
    caso = CasoPrueba.query.get_or_404(caso_id)
    ciclos_del_caso = caso.ciclos_prueba if caso.ciclos_prueba else []
    return render_template('casos_prueba/detalle.html', caso=caso, ciclos_del_caso=ciclos_del_caso)


@casos_prueba_bp.route('/nuevo', methods=['GET', 'POST'])
@requerir_miembro
def crear():
    usuario_id = session.get('usuario_id')

    if request.method == 'POST':
        nombre = request.form.get('nombre', '').strip()
        objetivo = request.form.get('objetivo', '').strip()
        precondicion = request.form.get('precondicion', '').strip()
        descripcion = request.form.get('descripcion', '').strip()
        resultado_esperado = request.form.get('resultado_esperado', '').strip()
        tipo = request.form.get('tipo', TipoTestEnum.MANUAL.value)
        prioridad = request.form.get('prioridad', PrioridadEnum.MEDIA.value)

        if not nombre or not objetivo:
            flash('Nombre y objetivo son obligatorios.', 'danger')
            return redirect(url_for('casos_prueba_bp.crear'))

        caso = CasoPrueba(
            nombre=nombre,
            objetivo=objetivo,
            precondicion=precondicion,
            descripcion=descripcion,
            resultado_esperado=resultado_esperado,
            tipo=TipoTestEnum(tipo),
            prioridad=PrioridadEnum(prioridad),
            estado=EstadoEnum.NUEVO,
            usuario_creacion_id=usuario_id
        )
        db.session.add(caso)
        db.session.commit()

        flash(f'Caso de prueba "{nombre}" creado exitosamente.', 'success')
        return redirect(url_for('casos_prueba_bp.detalle', caso_id=caso.id))

    return render_template('casos_prueba/crear.html')


@casos_prueba_bp.route('/<int:caso_id>/editar', methods=['GET', 'POST'])
@requerir_miembro
def editar(caso_id):
    caso = CasoPrueba.query.get_or_404(caso_id)

    if request.method == 'POST':
        caso.nombre = request.form.get('nombre', caso.nombre).strip()
        caso.objetivo = request.form.get('objetivo', caso.objetivo).strip()
        caso.precondicion = request.form.get('precondicion', caso.precondicion).strip()
        caso.descripcion = request.form.get('descripcion', caso.descripcion).strip()
        caso.resultado_esperado = request.form.get('resultado_esperado', caso.resultado_esperado).strip()
        caso.tipo = TipoTestEnum(request.form.get('tipo', caso.tipo.value))
        caso.prioridad = PrioridadEnum(request.form.get('prioridad', caso.prioridad.value))

        nuevo_estado = EstadoEnum(request.form.get('estado', caso.estado.value))
        if not caso.puede_cambiar_a(nuevo_estado):
            flash(f'No se puede cambiar de {caso.estado.value} a {nuevo_estado.value}.', 'danger')
            return redirect(url_for('casos_prueba_bp.editar', caso_id=caso_id))

        caso.estado = nuevo_estado
        db.session.commit()

        flash('Caso de prueba actualizado exitosamente.', 'success')
        return redirect(url_for('casos_prueba_bp.detalle', caso_id=caso_id))

    return render_template('casos_prueba/editar.html', caso=caso)


@casos_prueba_bp.route('/<int:caso_id>/eliminar', methods=['POST'])
@requerir_admin
def eliminar(caso_id):
    caso = CasoPrueba.query.get_or_404(caso_id)
    nombre = caso.nombre

    db.session.delete(caso)
    db.session.commit()

    flash(f'Caso de prueba "{nombre}" eliminado exitosamente.', 'success')
    return redirect(url_for('casos_prueba_bp.indice'))


@casos_prueba_bp.route('/<int:caso_id>/api/detalles')
@requerir_autenticacion
def obtener_detalles_api(caso_id):
    caso = CasoPrueba.query.get_or_404(caso_id)
    
    resultado_obtenido = None
    notas = None
    if caso.resultados:
        resultado_mas_reciente = max(caso.resultados, key=lambda r: r.fecha_creacion)
        resultado_obtenido = resultado_mas_reciente.resultado_obtenido
        notas = resultado_mas_reciente.notas
    
    historias = [epica.nombre for epica in caso.epicas] if caso.epicas else []
    
    return jsonify({
        'id': caso.id,
        'nombre': caso.nombre,
        'objetivo': caso.objetivo or '',
        'precondicion': caso.precondicion or '',
        'pasos_reproduccion': caso.pasos_reproduccion or '',
        'resultado_esperado': caso.resultado_esperado or '',
        'estado': caso.estado.value if caso.estado else '',
        'prioridad': caso.prioridad.value if caso.prioridad else '',
        'tipo': caso.tipo.value if caso.tipo else '',
        'fecha_creacion': caso.fecha_creacion.isoformat() if caso.fecha_creacion else None,
        'historias': historias,
        'resultado_obtenido': resultado_obtenido or '',
        'notas': notas or '',
    }), 200
