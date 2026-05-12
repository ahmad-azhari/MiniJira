from flask import Blueprint, render_template, request, redirect, url_for, session, flash
from app.base_datos import db
from app.modelos import Defecto, CasoPrueba, Usuario
from config.constantes import EstadoDefectoEnum, PrioridadEnum
from functools import wraps

defectos_bp = Blueprint('defectos_bp', __name__, url_prefix='/defectos')


def requerir_autenticacion(f):
    @wraps(f)
    def wrapper(*args, **kwargs):
        if 'usuario_id' not in session:
            flash('Debes iniciar sesión.', 'warning')
            return redirect(url_for('auth_bp.login'))
        return f(*args, **kwargs)
    return wrapper


@defectos_bp.route('/')
@requerir_autenticacion
def indice():
    defectos = Defecto.query.all()
    return render_template('defectos/indice.html', defectos=defectos)


@defectos_bp.route('/<int:defecto_id>')
@requerir_autenticacion
def detalle(defecto_id):
    defecto = Defecto.query.get_or_404(defecto_id)
    return render_template('defectos/detalle.html', defecto=defecto)


@defectos_bp.route('/nuevo/<int:caso_id>', methods=['GET', 'POST'])
@requerir_autenticacion
def crear(caso_id):
    caso = CasoPrueba.query.get_or_404(caso_id)
    usuario_id = session.get('usuario_id')
    usuarios = Usuario.query.all()

    if request.method == 'POST':
        titulo = request.form.get('titulo', '').strip()
        descripcion = request.form.get('descripcion', '').strip()
        pasos_reproduccion = request.form.get('pasos_reproduccion', '').strip()
        resultado_esperado = request.form.get('resultado_esperado', '').strip()
        resultado_actual = request.form.get('resultado_actual', '').strip()
        prioridad = request.form.get('prioridad', PrioridadEnum.MEDIA.value)
        asignado_a_id = request.form.get('asignado_a_id')

        if not titulo or not descripcion:
            flash('Título y descripción son obligatorios.', 'danger')
            return redirect(url_for('defectos_bp.crear', caso_id=caso_id))

        defecto = Defecto(
            titulo=titulo,
            descripcion=descripcion,
            pasos_reproduccion=pasos_reproduccion,
            resultado_esperado=resultado_esperado,
            resultado_actual=resultado_actual,
            prioridad=PrioridadEnum(prioridad),
            estado=EstadoDefectoEnum.NUEVO,
            caso_prueba_id=caso_id,
            reportado_por_id=usuario_id,
            asignado_a_id=asignado_a_id if asignado_a_id else None
        )
        db.session.add(defecto)
        db.session.commit()

        flash(f'Defecto "{titulo}" reportado exitosamente.', 'success')
        return redirect(url_for('defectos_bp.detalle', defecto_id=defecto.id))

    return render_template('defectos/crear.html', caso=caso, usuarios=usuarios)


@defectos_bp.route('/<int:defecto_id>/editar', methods=['GET', 'POST'])
@requerir_autenticacion
def editar(defecto_id):
    defecto = Defecto.query.get_or_404(defecto_id)
    usuarios = Usuario.query.all()

    if request.method == 'POST':
        defecto.titulo = request.form.get('titulo', defecto.titulo).strip()
        defecto.descripcion = request.form.get('descripcion', defecto.descripcion).strip()
        defecto.pasos_reproduccion = request.form.get('pasos_reproduccion', defecto.pasos_reproduccion).strip()
        defecto.resultado_esperado = request.form.get('resultado_esperado', defecto.resultado_esperado).strip()
        defecto.resultado_actual = request.form.get('resultado_actual', defecto.resultado_actual).strip()
        defecto.prioridad = PrioridadEnum(request.form.get('prioridad', defecto.prioridad.value))

        nuevo_estado = EstadoDefectoEnum(request.form.get('estado', defecto.estado.value))
        if not defecto.puede_cambiar_a(nuevo_estado):
            flash(f'No se puede cambiar de {defecto.estado.value} a {nuevo_estado.value}.', 'danger')
            return redirect(url_for('defectos_bp.editar', defecto_id=defecto_id))

        defecto.estado = nuevo_estado
        asignado_a_id = request.form.get('asignado_a_id')
        defecto.asignado_a_id = asignado_a_id if asignado_a_id else None

        db.session.commit()

        flash('Defecto actualizado exitosamente.', 'success')
        return redirect(url_for('defectos_bp.detalle', defecto_id=defecto_id))

    return render_template('defectos/editar.html', defecto=defecto, usuarios=usuarios)


@defectos_bp.route('/<int:defecto_id>/eliminar', methods=['POST'])
@requerir_autenticacion
def eliminar(defecto_id):
    defecto = Defecto.query.get_or_404(defecto_id)
    titulo = defecto.titulo

    db.session.delete(defecto)
    db.session.commit()

    flash(f'Defecto "{titulo}" eliminado exitosamente.', 'success')
    return redirect(url_for('defectos_bp.indice'))
