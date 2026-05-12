from flask import Blueprint, render_template, request, redirect, url_for, session, flash
from app.base_datos import db
from app.modelos import CicloPrueba, CasoPrueba
from config.constantes import EstadoEnum
from functools import wraps

ciclos_prueba_bp = Blueprint('ciclos_prueba_bp', __name__, url_prefix='/ciclos-prueba')


def requerir_autenticacion(f):
    @wraps(f)
    def wrapper(*args, **kwargs):
        if 'usuario_id' not in session:
            flash('Debes iniciar sesión.', 'warning')
            return redirect(url_for('auth_bp.login'))
        return f(*args, **kwargs)
    return wrapper


@ciclos_prueba_bp.route('/')
@requerir_autenticacion
def indice():
    ciclos = CicloPrueba.query.all()
    return render_template('ciclos_prueba/indice.html', ciclos=ciclos)


@ciclos_prueba_bp.route('/<int:ciclo_id>')
@requerir_autenticacion
def detalle(ciclo_id):
    ciclo = CicloPrueba.query.get_or_404(ciclo_id)
    return render_template('ciclos_prueba/detalle.html', ciclo=ciclo)


@ciclos_prueba_bp.route('/nuevo', methods=['GET', 'POST'])
@requerir_autenticacion
def crear():
    if request.method == 'POST':
        nombre = request.form.get('nombre', '').strip()
        descripcion = request.form.get('descripcion', '').strip()

        if not nombre:
            flash('El nombre es obligatorio.', 'danger')
            return redirect(url_for('ciclos_prueba_bp.crear'))

        ciclo = CicloPrueba(
            nombre=nombre,
            descripcion=descripcion,
            estado=EstadoEnum.NUEVO
        )
        db.session.add(ciclo)
        db.session.commit()

        flash(f'Ciclo de prueba "{nombre}" creado exitosamente.', 'success')
        return redirect(url_for('ciclos_prueba_bp.detalle', ciclo_id=ciclo.id))

    return render_template('ciclos_prueba/crear.html')


@ciclos_prueba_bp.route('/<int:ciclo_id>/editar', methods=['GET', 'POST'])
@requerir_autenticacion
def editar(ciclo_id):
    ciclo = CicloPrueba.query.get_or_404(ciclo_id)

    if request.method == 'POST':
        ciclo.nombre = request.form.get('nombre', ciclo.nombre).strip()
        ciclo.descripcion = request.form.get('descripcion', ciclo.descripcion).strip()

        nuevo_estado = EstadoEnum(request.form.get('estado', ciclo.estado.value))
        if not ciclo.puede_cambiar_a(nuevo_estado):
            flash(f'No se puede cambiar de {ciclo.estado.value} a {nuevo_estado.value}.', 'danger')
            return redirect(url_for('ciclos_prueba_bp.editar', ciclo_id=ciclo_id))

        ciclo.estado = nuevo_estado
        db.session.commit()

        flash('Ciclo de prueba actualizado exitosamente.', 'success')
        return redirect(url_for('ciclos_prueba_bp.detalle', ciclo_id=ciclo_id))

    return render_template('ciclos_prueba/editar.html', ciclo=ciclo)


@ciclos_prueba_bp.route('/<int:ciclo_id>/agregar-caso', methods=['POST'])
@requerir_autenticacion
def agregar_caso(ciclo_id):
    ciclo = CicloPrueba.query.get_or_404(ciclo_id)
    caso_id = request.form.get('caso_id')

    caso = CasoPrueba.query.get_or_404(caso_id)

    if caso not in ciclo.casos_prueba:
        ciclo.casos_prueba.append(caso)
        db.session.commit()
        flash(f'Caso "{caso.nombre}" agregado al ciclo.', 'success')
    else:
        flash('El caso ya está en este ciclo.', 'warning')

    return redirect(url_for('ciclos_prueba_bp.detalle', ciclo_id=ciclo_id))


@ciclos_prueba_bp.route('/<int:ciclo_id>/quitar-caso/<int:caso_id>', methods=['POST'])
@requerir_autenticacion
def quitar_caso(ciclo_id, caso_id):
    ciclo = CicloPrueba.query.get_or_404(ciclo_id)
    caso = CasoPrueba.query.get_or_404(caso_id)

    if caso in ciclo.casos_prueba:
        ciclo.casos_prueba.remove(caso)
        db.session.commit()
        flash(f'Caso "{caso.nombre}" removido del ciclo.', 'success')

    return redirect(url_for('ciclos_prueba_bp.detalle', ciclo_id=ciclo_id))


@ciclos_prueba_bp.route('/<int:ciclo_id>/eliminar', methods=['POST'])
@requerir_autenticacion
def eliminar(ciclo_id):
    ciclo = CicloPrueba.query.get_or_404(ciclo_id)
    nombre = ciclo.nombre

    db.session.delete(ciclo)
    db.session.commit()

    flash(f'Ciclo de prueba "{nombre}" eliminado exitosamente.', 'success')
    return redirect(url_for('ciclos_prueba_bp.indice'))
