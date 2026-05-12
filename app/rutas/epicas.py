from flask import Blueprint, render_template, request, redirect, url_for, session, flash
from app.base_datos import db
from app.modelos import Epica, Proyecto, Usuario
from config.constantes import TipoEnum, EstadoEnum, PrioridadEnum
from functools import wraps

epicas_bp = Blueprint('epicas_bp', __name__, url_prefix='/epicas')


def requerir_autenticacion(f):
    @wraps(f)
    def wrapper(*args, **kwargs):
        if 'usuario_id' not in session:
            flash('Debes iniciar sesión.', 'warning')
            return redirect(url_for('auth_bp.login'))
        return f(*args, **kwargs)
    return wrapper


@epicas_bp.route('/<int:epica_id>')
@requerir_autenticacion
def detalle(epica_id):
    epica = Epica.query.get_or_404(epica_id)
    return render_template('epicas/detalle.html', epica=epica)


@epicas_bp.route('/nuevo/<int:proyecto_id>', methods=['GET', 'POST'])
@requerir_autenticacion
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
@requerir_autenticacion
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


@epicas_bp.route('/<int:epica_id>/editar', methods=['GET', 'POST'])
@requerir_autenticacion
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


@epicas_bp.route('/<int:epica_id>/eliminar', methods=['POST'])
@requerir_autenticacion
def eliminar(epica_id):
    epica = Epica.query.get_or_404(epica_id)
    nombre = epica.nombre
    proyecto_id = epica.proyecto_id

    db.session.delete(epica)
    db.session.commit()

    flash(f'Épica "{nombre}" eliminada exitosamente.', 'success')
    return redirect(url_for('proyectos_bp.detalle', proyecto_id=proyecto_id))
