from flask import Blueprint, render_template, request, redirect, url_for, session, flash
from app.base_datos import db
from app.modelos import Usuario, Rol
from config.constantes import RolEnum
from app.decoradores import requerir_autenticacion, requerir_miembro, requerir_admin

usuarios_bp = Blueprint('usuarios_bp', __name__, url_prefix='/usuarios')


@usuarios_bp.route('/')
@requerir_admin
def indice():
    usuarios = Usuario.query.all()
    return render_template('usuarios/indice.html', usuarios=usuarios)


@usuarios_bp.route('/<int:usuario_id>')
@requerir_autenticacion
def perfil(usuario_id):
    usuario = Usuario.query.get_or_404(usuario_id)
    usuario_actual_id = session.get('usuario_id')

    if usuario_id != usuario_actual_id:
        usuario_actual = Usuario.query.get(usuario_actual_id)
        es_admin = any(rol.nombre == RolEnum.ADMIN.value for rol in usuario_actual.roles)
        if not es_admin:
            flash('No tienes permiso para ver este perfil.', 'danger')
            return redirect(url_for('proyectos_bp.indice'))

    return render_template('usuarios/perfil.html', usuario=usuario)


@usuarios_bp.route('/nuevo', methods=['GET', 'POST'])
@requerir_admin
def crear():
    roles = Rol.query.all()

    if request.method == 'POST':
        nombre_usuario = request.form.get('nombre_usuario', '').strip()
        email = request.form.get('email', '').strip()
        contrasena = request.form.get('contrasena', '')
        roles_ids = request.form.getlist('roles')

        if not nombre_usuario or not email or not contrasena:
            flash('Nombre de usuario, email y contraseña son obligatorios.', 'danger')
            return redirect(url_for('usuarios_bp.crear'))

        usuario_existente = Usuario.query.filter_by(nombre_usuario=nombre_usuario).first()
        if usuario_existente:
            flash('El nombre de usuario ya existe.', 'danger')
            return redirect(url_for('usuarios_bp.crear'))

        usuario = Usuario(nombre_usuario=nombre_usuario, email=email)
        usuario.establecer_contrasena(contrasena)

        for rol_id in roles_ids:
            rol = Rol.query.get(rol_id)
            if rol:
                usuario.roles.append(rol)

        db.session.add(usuario)
        db.session.commit()

        flash(f'Usuario "{nombre_usuario}" creado exitosamente.', 'success')
        return redirect(url_for('usuarios_bp.perfil', usuario_id=usuario.id))

    return render_template('usuarios/crear.html', roles=roles)


@usuarios_bp.route('/<int:usuario_id>/editar', methods=['GET', 'POST'])
@requerir_autenticacion
def editar(usuario_id):
    usuario = Usuario.query.get_or_404(usuario_id)
    usuario_actual_id = session.get('usuario_id')

    usuario_actual = Usuario.query.get(usuario_actual_id)
    es_admin = any(rol.nombre == RolEnum.ADMIN.value for rol in usuario_actual.roles)

    if usuario_id != usuario_actual_id and not es_admin:
        flash('No tienes permiso para editar este usuario.', 'danger')
        return redirect(url_for('proyectos_bp.indice'))

    roles = Rol.query.all()

    if request.method == 'POST':
        usuario.nombre_usuario = request.form.get('nombre_usuario', usuario.nombre_usuario).strip()
        usuario.email = request.form.get('email', usuario.email).strip()

        nueva_contrasena = request.form.get('nueva_contrasena', '').strip()
        if nueva_contrasena:
            usuario.establecer_contrasena(nueva_contrasena)

        if es_admin:
            usuario.roles.clear()
            roles_ids = request.form.getlist('roles')
            for rol_id in roles_ids:
                rol = Rol.query.get(rol_id)
                if rol:
                    usuario.roles.append(rol)

        db.session.commit()
        flash('Usuario actualizado exitosamente.', 'success')
        return redirect(url_for('usuarios_bp.perfil', usuario_id=usuario_id))

    return render_template('usuarios/editar.html', usuario=usuario, roles=roles, es_admin=es_admin)


@usuarios_bp.route('/<int:usuario_id>/desactivar', methods=['POST'])
@requerir_admin
def desactivar(usuario_id):
    usuario = Usuario.query.get_or_404(usuario_id)

    if usuario_id == session.get('usuario_id'):
        flash('No puedes desactivar tu propia cuenta.', 'danger')
        return redirect(url_for('usuarios_bp.perfil', usuario_id=usuario_id))

    usuario.activo = False
    db.session.commit()

    flash(f'Usuario "{usuario.nombre_usuario}" desactivado.', 'success')
    return redirect(url_for('usuarios_bp.indice'))


@usuarios_bp.route('/<int:usuario_id>/activar', methods=['POST'])
@requerir_admin
def activar(usuario_id):
    usuario = Usuario.query.get_or_404(usuario_id)
    usuario.activo = True
    db.session.commit()

    flash(f'Usuario "{usuario.nombre_usuario}" activado.', 'success')
    return redirect(url_for('usuarios_bp.indice'))


@usuarios_bp.route('/<int:usuario_id>/eliminar', methods=['POST'])
@requerir_admin
def eliminar(usuario_id):
    usuario = Usuario.query.get_or_404(usuario_id)

    if usuario_id == session.get('usuario_id'):
        flash('No puedes eliminar tu propia cuenta.', 'danger')
        return redirect(url_for('usuarios_bp.perfil', usuario_id=usuario_id))

    nombre_usuario = usuario.nombre_usuario
    db.session.delete(usuario)
    db.session.commit()

    flash(f'Usuario "{nombre_usuario}" eliminado permanentemente.', 'success')
    return redirect(url_for('usuarios_bp.indice'))
