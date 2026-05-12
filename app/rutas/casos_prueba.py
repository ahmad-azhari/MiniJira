from flask import Blueprint, render_template, request, redirect, url_for, session, flash
from app.base_datos import db
from app.modelos import CasoPrueba, Epica, Usuario
from config.constantes import TipoTestEnum, EstadoEnum, PrioridadEnum
from functools import wraps

casos_prueba_bp = Blueprint('casos_prueba_bp', __name__, url_prefix='/casos-prueba')


def requerir_autenticacion(f):
    @wraps(f)
    def wrapper(*args, **kwargs):
        if 'usuario_id' not in session:
            flash('Debes iniciar sesión.', 'warning')
            return redirect(url_for('auth_bp.login'))
        return f(*args, **kwargs)
    return wrapper


@casos_prueba_bp.route('/')
@requerir_autenticacion
def indice():
    casos = CasoPrueba.query.all()
    return render_template('casos_prueba/indice.html', casos=casos)


@casos_prueba_bp.route('/<int:caso_id>')
@requerir_autenticacion
def detalle(caso_id):
    caso = CasoPrueba.query.get_or_404(caso_id)
    return render_template('casos_prueba/detalle.html', caso=caso)


@casos_prueba_bp.route('/nuevo', methods=['GET', 'POST'])
@requerir_autenticacion
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
@requerir_autenticacion
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
@requerir_autenticacion
def eliminar(caso_id):
    caso = CasoPrueba.query.get_or_404(caso_id)
    nombre = caso.nombre

    db.session.delete(caso)
    db.session.commit()

    flash(f'Caso de prueba "{nombre}" eliminado exitosamente.', 'success')
    return redirect(url_for('casos_prueba_bp.indice'))
