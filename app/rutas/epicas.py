from flask import Blueprint, render_template, request, redirect, url_for, session, flash
from app.base_datos import db
from app.modelos import Epica, Proyecto, Usuario, CasoPrueba
from config.constantes import TipoEnum, EstadoEnum, PrioridadEnum
from app.decoradores import requerir_autenticacion, requerir_miembro, requerir_admin
from functools import wraps

epicas_bp = Blueprint('epicas_bp', __name__, url_prefix='/epicas')


@epicas_bp.route('/')
@requerir_autenticacion
def indice():
    query = request.args.get('q', '').strip()
    base_query = Epica.query.filter_by(tipo=TipoEnum.EPIC, epica_padre_id=None)
    if query:
        base_query = base_query.filter(Epica.nombre.ilike(f'%{query}%'))
    epicas = base_query.all()

    epicas_con_proyecto = []
    for epica in epicas:
        proyecto = Proyecto.query.get(epica.proyecto_id)
        historias = Epica.query.filter_by(epica_padre_id=epica.id).all()
        epicas_con_proyecto.append({
            'epica': epica,
            'proyecto': proyecto,
            'historias_count': len(historias)
        })

    return render_template('epicas/indice.html', epicas_con_proyecto=epicas_con_proyecto)


@epicas_bp.route('/historias')
@requerir_autenticacion
def historias():
    query = request.args.get('q', '').strip()
    base_query = Epica.query.filter_by(tipo=TipoEnum.STORY)
    if query:
        base_query = base_query.filter(Epica.nombre.ilike(f'%{query}%'))
    historias = base_query.all()

    historias_con_epica = []
    for historia in historias:
        epica_padre = Epica.query.get(historia.epica_padre_id) if historia.epica_padre_id else None
        proyecto = Proyecto.query.get(historia.proyecto_id)
        casos = historia.casos_prueba
        historias_con_epica.append({
            'historia': historia,
            'epica_padre': epica_padre,
            'proyecto': proyecto,
            'casos_count': len(casos)
        })

    return render_template('epicas/historias.html', historias_con_epica=historias_con_epica)


@epicas_bp.route('/<int:epica_id>')
@requerir_autenticacion
def detalle(epica_id):
    epica = Epica.query.get_or_404(epica_id)
    casos_prueba_disponibles = CasoPrueba.query.all()
    return render_template('epicas/detalle.html', epica=epica, casos_prueba_disponibles=casos_prueba_disponibles)


@epicas_bp.route('/nuevo/<int:proyecto_id>', methods=['GET', 'POST'])
@requerir_miembro
def crear_epica(proyecto_id):
    proyecto = Proyecto.query.get_or_404(proyecto_id)
    usuario_id = session.get('usuario_id')

    if request.method == 'POST':
        nombre = request.form.get('nombre', '').strip()
        descripcion = request.form.get('descripcion', '').strip()
        prioridad = request.form.get('prioridad', PrioridadEnum.MEDIA.value)

        if not nombre:
            flash('El nombre es obligatorio.', 'danger')
            return redirect(url_for('epicas_bp.crear_epica', proyecto_id=proyecto_id))

        epica = Epica(
            nombre=nombre,
            descripcion=descripcion,
            prioridad=PrioridadEnum(prioridad),
            tipo=TipoEnum.EPIC,
            estado=EstadoEnum.NUEVO,
            proyecto_id=proyecto_id,
            usuario_creacion_id=usuario_id
        )
        db.session.add(epica)
        db.session.commit()

        flash(f'Épica "{nombre}" creada exitosamente.', 'success')
        return redirect(url_for('epicas_bp.detalle', epica_id=epica.id))

    return render_template('epicas/crear_epica.html', proyecto=proyecto)


@epicas_bp.route('/<int:epica_id>/historia/nuevo', methods=['GET', 'POST'])
@requerir_miembro
def crear_historia(epica_id):
    epica = Epica.query.get_or_404(epica_id)
    usuario_id = session.get('usuario_id')

    if epica.tipo != TipoEnum.EPIC:
        flash('Solo puedes crear historias dentro de una épica.', 'danger')
        return redirect(url_for('epicas_bp.detalle', epica_id=epica_id))

    if request.method == 'POST':
        nombre = request.form.get('nombre', '').strip()
        descripcion = request.form.get('descripcion', '').strip()
        prioridad = request.form.get('prioridad', PrioridadEnum.MEDIA.value)

        if not nombre:
            flash('El nombre es obligatorio.', 'danger')
            return redirect(url_for('epicas_bp.crear_historia', epica_id=epica_id))

        historia = Epica(
            nombre=nombre,
            descripcion=descripcion,
            prioridad=PrioridadEnum(prioridad),
            tipo=TipoEnum.STORY,
            estado=EstadoEnum.NUEVO,
            epica_padre_id=epica_id,
            proyecto_id=epica.proyecto_id,
            usuario_creacion_id=usuario_id
        )
        db.session.add(historia)
        db.session.commit()

        flash(f'Historia "{nombre}" creada exitosamente.', 'success')
        return redirect(url_for('epicas_bp.detalle', epica_id=epica_id))

    return render_template('epicas/crear_historia.html', epica=epica)


@epicas_bp.route('/historias/nuevo', methods=['GET', 'POST'])
@requerir_miembro
def crear_historia_suelta():
    usuario_id = session.get('usuario_id')
    epicas = Epica.query.filter_by(tipo=TipoEnum.EPIC).all()
    proyectos = Proyecto.query.all()

    if request.method == 'POST':
        nombre = request.form.get('nombre', '').strip()
        descripcion = request.form.get('descripcion', '').strip()
        prioridad = request.form.get('prioridad', PrioridadEnum.MEDIA.value)
        epica_id = request.form.get('epica_id') or None
        proyecto_id = request.form.get('proyecto_id')

        if not nombre:
            flash('El nombre es obligatorio.', 'danger')
            return redirect(url_for('epicas_bp.crear_historia_suelta'))

        if epica_id:
            epica = Epica.query.get(epica_id)
            proyecto_id = epica.proyecto_id if epica else proyecto_id
        
        if not proyecto_id:
            flash('Debes seleccionar un proyecto o una épica.', 'danger')
            return redirect(url_for('epicas_bp.crear_historia_suelta'))

        historia = Epica(
            nombre=nombre,
            descripcion=descripcion,
            prioridad=PrioridadEnum(prioridad),
            tipo=TipoEnum.STORY,
            estado=EstadoEnum.NUEVO,
            epica_padre_id=epica_id,
            proyecto_id=proyecto_id,
            usuario_creacion_id=usuario_id
        )
        db.session.add(historia)
        db.session.commit()

        flash(f'Historia "{nombre}" creada exitosamente.', 'success')
        return redirect(url_for('epicas_bp.historias'))

    return render_template('epicas/crear_historia_suelta.html', epicas=epicas, proyectos=proyectos)


@epicas_bp.route('/<int:epica_id>/editar', methods=['GET', 'POST'])
@requerir_miembro
def editar(epica_id):
    epica = Epica.query.get_or_404(epica_id)

    if request.method == 'POST':
        nombre = request.form.get('nombre', '').strip()
        descripcion = request.form.get('descripcion', '').strip()
        prioridad = request.form.get('prioridad', epica.prioridad.value)
        estado = request.form.get('estado', epica.estado.value)

        if not nombre:
            flash('El nombre es obligatorio.', 'danger')
            return redirect(url_for('epicas_bp.editar', epica_id=epica_id))

        epica.nombre = nombre
        epica.descripcion = descripcion
        epica.prioridad = PrioridadEnum(prioridad)
        nuevo_estado = EstadoEnum(estado)

        if not epica.puede_cambiar_a(nuevo_estado):
            flash(f'No se puede cambiar de {epica.estado.value} a {estado}.', 'danger')
            return redirect(url_for('epicas_bp.editar', epica_id=epica_id))

        epica.estado = nuevo_estado
        db.session.commit()

        flash('Épica actualizada exitosamente.', 'success')
        return redirect(url_for('epicas_bp.detalle', epica_id=epica_id))

    return render_template('epicas/editar.html', epica=epica)


@epicas_bp.route('/<int:epica_id>/agregar-caso', methods=['POST'])
@requerir_miembro
def agregar_caso(epica_id):
    epica = Epica.query.get_or_404(epica_id)
    caso_id = request.form.get('caso_id')

    caso = CasoPrueba.query.get_or_404(caso_id)

    if caso not in epica.casos_prueba:
        epica.casos_prueba.append(caso)
        db.session.commit()
        flash(f'Caso "{caso.nombre}" agregado a la épica.', 'success')
    else:
        flash('El caso ya está asociado a esta épica.', 'warning')

    return redirect(url_for('epicas_bp.detalle', epica_id=epica_id))


@epicas_bp.route('/<int:epica_id>/quitar-caso/<int:caso_id>', methods=['POST'])
@requerir_miembro
def quitar_caso(epica_id, caso_id):
    epica = Epica.query.get_or_404(epica_id)
    caso = CasoPrueba.query.get_or_404(caso_id)

    if caso in epica.casos_prueba:
        epica.casos_prueba.remove(caso)
        db.session.commit()
        flash(f'Caso "{caso.nombre}" removido de la épica.', 'success')

    return redirect(url_for('epicas_bp.detalle', epica_id=epica_id))


@epicas_bp.route('/<int:historia_id>/agregar-caso-historia', methods=['POST'])
@requerir_miembro
def agregar_caso_historia(historia_id):
    historia = Epica.query.get_or_404(historia_id)
    caso_id = request.form.get('caso_id')

    caso = CasoPrueba.query.get_or_404(caso_id)

    if caso not in historia.casos_prueba:
        historia.casos_prueba.append(caso)
        db.session.commit()
        flash(f'Caso "{caso.nombre}" agregado a la historia.', 'success')
    else:
        flash('El caso ya está asociado a esta historia.', 'warning')

    return redirect(url_for('epicas_bp.detalle', epica_id=historia_id))


@epicas_bp.route('/<int:historia_id>/quitar-caso-historia/<int:caso_id>', methods=['POST'])
@requerir_miembro
def quitar_caso_historia(historia_id, caso_id):
    historia = Epica.query.get_or_404(historia_id)
    caso = CasoPrueba.query.get_or_404(caso_id)

    if caso in historia.casos_prueba:
        historia.casos_prueba.remove(caso)
        db.session.commit()
        flash(f'Caso "{caso.nombre}" removido de la historia.', 'success')

    return redirect(url_for('epicas_bp.detalle', epica_id=historia_id))



@epicas_bp.route('/<int:epica_id>/eliminar', methods=['POST'])
@requerir_admin
def eliminar(epica_id):
    epica = Epica.query.get_or_404(epica_id)
    nombre = epica.nombre
    proyecto_id = epica.proyecto_id

    db.session.delete(epica)
    db.session.commit()

    flash(f'Épica "{nombre}" eliminada exitosamente.', 'success')
    return redirect(url_for('proyectos_bp.detalle', proyecto_id=proyecto_id))
