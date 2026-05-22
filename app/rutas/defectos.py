from flask import Blueprint, render_template, request, redirect, url_for, session, flash
from app.base_datos import db
from app.modelos import Defecto, CasoPrueba, Usuario
from config.constantes import EstadoDefectoEnum, PrioridadEnum
from app.decoradores import requerir_autenticacion, requerir_miembro, requerir_admin

defectos_bp = Blueprint('defectos_bp', __name__, url_prefix='/defectos')


@defectos_bp.route('/')
@requerir_autenticacion
def indice():
    query = request.args.get('q', '').strip()
    if query:
        defectos = Defecto.query.filter(Defecto.titulo.ilike(f'%{query}%')).all()
    else:
        defectos = Defecto.query.all()
    return render_template('defectos/indice.html', defectos=defectos)


@defectos_bp.route('/<int:defecto_id>')
@requerir_autenticacion
def detalle(defecto_id):
    defecto = Defecto.query.get_or_404(defecto_id)
    return render_template('defectos/detalle.html', defecto=defecto)


@defectos_bp.route('/nuevo/<int:caso_id>', methods=['GET', 'POST'])
@requerir_miembro
def crear(caso_id):
    caso = CasoPrueba.query.get_or_404(caso_id)
    usuario_id = session.get('usuario_id')
    usuarios = Usuario.query.all()

    if request.method == 'POST':
        titulo = request.form.get('titulo', '').strip()
        descripcion = request.form.get('descripcion', '').strip()
        prioridad = request.form.get('prioridad', PrioridadEnum.MEDIA.value)
        asignado_a_id = request.form.get('usuario_asignado_id')

        if not titulo or not descripcion:
            flash('Título y descripción son obligatorios.', 'danger')
            return redirect(url_for('defectos_bp.crear', caso_id=caso_id))

        defecto = Defecto(
            titulo=titulo,
            descripcion=descripcion,
            prioridad=PrioridadEnum(prioridad),
            estado=EstadoDefectoEnum.ABIERTO,
            caso_prueba_id=caso_id,
            usuario_creacion_id=usuario_id,
            usuario_asignado_id=asignado_a_id if asignado_a_id else None
        )
        db.session.add(defecto)
        db.session.commit()

        flash(f'Defecto "{titulo}" reportado exitosamente.', 'success')
        return redirect(url_for('defectos_bp.detalle', defecto_id=defecto.id))

    return render_template('defectos/crear.html', caso=caso, usuarios=usuarios)


@defectos_bp.route('/<int:defecto_id>/editar', methods=['GET', 'POST'])
@requerir_miembro
def editar(defecto_id):
    defecto = Defecto.query.get_or_404(defecto_id)
    usuarios = Usuario.query.all()

    if request.method == 'POST':
        defecto.titulo = request.form.get('titulo', defecto.titulo).strip()
        defecto.descripcion = request.form.get('descripcion', defecto.descripcion).strip()
        defecto.prioridad = PrioridadEnum(request.form.get('prioridad', defecto.prioridad.value))

        nuevo_estado = EstadoDefectoEnum(request.form.get('estado', defecto.estado.value))
        if not defecto.puede_cambiar_a(nuevo_estado):
            flash(f'No se puede cambiar de {defecto.estado.value} a {nuevo_estado.value}.', 'danger')
            return redirect(url_for('defectos_bp.editar', defecto_id=defecto_id))

        defecto.estado = nuevo_estado
        asignado_a_id = request.form.get('usuario_asignado_id')
        defecto.usuario_asignado_id = asignado_a_id if asignado_a_id else None

        db.session.commit()

        flash('Defecto actualizado exitosamente.', 'success')
        return redirect(url_for('defectos_bp.detalle', defecto_id=defecto_id))

    return render_template('defectos/editar.html', defecto=defecto, usuarios=usuarios)


@defectos_bp.route('/<int:defecto_id>/eliminar', methods=['POST'])
@requerir_admin
def eliminar(defecto_id):
    defecto = Defecto.query.get_or_404(defecto_id)
    titulo = defecto.titulo

    db.session.delete(defecto)
    db.session.commit()

    flash(f'Defecto "{titulo}" eliminado exitosamente.', 'success')
    return redirect(url_for('defectos_bp.indice'))
