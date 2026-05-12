from flask import Blueprint, render_template, request, redirect, url_for, session, flash
from app.base_datos import db
from app.modelos import Proyecto, Epica
from config.constantes import TipoEnum

proyectos_bp = Blueprint('proyectos_bp', __name__, url_prefix='/proyectos')


def requerir_autenticacion(f):
    from functools import wraps
    @wraps(f)
    def wrapper(*args, **kwargs):
        if 'usuario_id' not in session:
            flash('Debes iniciar sesión.', 'warning')
            return redirect(url_for('auth_bp.login'))
        return f(*args, **kwargs)
    return wrapper


@proyectos_bp.route('/')
@requerir_autenticacion
def indice():
    proyectos = Proyecto.query.all()
    return render_template('proyectos/indice.html', proyectos=proyectos)


@proyectos_bp.route('/<int:proyecto_id>')
@requerir_autenticacion
def detalle(proyecto_id):
    proyecto = Proyecto.query.get_or_404(proyecto_id)

    epicas = Epica.query.filter_by(
        proyecto_id=proyecto_id,
        tipo=TipoEnum.EPIC,
        epica_padre_id=None
    ).all()

    epicas_con_historias = []
    for epica in epicas:
        historias = Epica.query.filter_by(
            epica_padre_id=epica.id
        ).all()
        epicas_con_historias.append({
            'epica': epica,
            'historias': historias
        })

    historias_sueltas = Epica.query.filter_by(
        proyecto_id=proyecto_id,
        tipo=TipoEnum.STORY,
        epica_padre_id=None
    ).all()

    return render_template(
        'proyectos/detalle.html',
        proyecto=proyecto,
        epicas_con_historias=epicas_con_historias,
        historias_sueltas=historias_sueltas
    )


@proyectos_bp.route('/nuevo', methods=['GET', 'POST'])
@requerir_autenticacion
def crear():
    if request.method == 'POST':
        nombre = request.form.get('nombre', '').strip()
        descripcion = request.form.get('descripcion', '').strip()
        usuario_id = session.get('usuario_id')

        if not nombre:
            flash('El nombre del proyecto es obligatorio.', 'danger')
            return redirect(url_for('proyectos_bp.crear'))

        proyecto_existente = Proyecto.query.filter_by(nombre=nombre).first()
        if proyecto_existente:
            flash('Ya existe un proyecto con ese nombre.', 'danger')
            return redirect(url_for('proyectos_bp.crear'))

        nuevo_proyecto = Proyecto(
            nombre=nombre,
            descripcion=descripcion,
            usuario_id=usuario_id
        )
        db.session.add(nuevo_proyecto)
        db.session.commit()

        flash(f'Proyecto "{nombre}" creado exitosamente.', 'success')
        return redirect(url_for('proyectos_bp.detalle', proyecto_id=nuevo_proyecto.id))

    return render_template('proyectos/crear.html')


@proyectos_bp.route('/<int:proyecto_id>/editar', methods=['GET', 'POST'])
@requerir_autenticacion
def editar(proyecto_id):
    proyecto = Proyecto.query.get_or_404(proyecto_id)

    if request.method == 'POST':
        nombre = request.form.get('nombre', '').strip()
        descripcion = request.form.get('descripcion', '').strip()
        estado = request.form.get('estado', proyecto.estado)

        if not nombre:
            flash('El nombre del proyecto es obligatorio.', 'danger')
            return redirect(url_for('proyectos_bp.editar', proyecto_id=proyecto_id))

        proyecto.nombre = nombre
        proyecto.descripcion = descripcion
        proyecto.estado = estado
        db.session.commit()

        flash('Proyecto actualizado exitosamente.', 'success')
        return redirect(url_for('proyectos_bp.detalle', proyecto_id=proyecto_id))

    return render_template('proyectos/editar.html', proyecto=proyecto)


@proyectos_bp.route('/<int:proyecto_id>/eliminar', methods=['POST'])
@requerir_autenticacion
def eliminar(proyecto_id):
    proyecto = Proyecto.query.get_or_404(proyecto_id)
    nombre = proyecto.nombre

    db.session.delete(proyecto)
    db.session.commit()

    flash(f'Proyecto "{nombre}" eliminado exitosamente.', 'success')
    return redirect(url_for('proyectos_bp.indice'))
