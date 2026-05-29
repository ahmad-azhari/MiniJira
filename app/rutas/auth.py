from flask import Blueprint, render_template, request, redirect, url_for, session, flash
from app.base_datos import db
from app.modelos import Usuario
import logging

auth_bp = Blueprint('auth_bp', __name__, url_prefix='/auth')
logger = logging.getLogger(__name__)


@auth_bp.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        nombre_usuario = request.form.get('nombre_usuario', '').strip()
        contrasena = request.form.get('contrasena', '')

        usuario = Usuario.query.filter_by(nombre_usuario=nombre_usuario).first()

        if usuario and usuario.verificar_contrasena(contrasena):
            if not usuario.activo:
                logger.warning(f'Intento de login de usuario desactivado: {nombre_usuario}')
                flash('Usuario desactivado. Contacta al administrador.', 'warning')
                return redirect(url_for('auth_bp.login'))

            session['usuario_id'] = usuario.id
            session['nombre_usuario'] = usuario.nombre_usuario
            session['roles'] = [rol.nombre for rol in usuario.roles] if usuario.roles else ['viewer']

            logger.info(f'✓ Login exitoso: {nombre_usuario} ({", ".join(session["roles"])})')
            flash(f'¡Bienvenido {usuario.nombre_usuario}!', 'success')
            return redirect(url_for('proyectos_bp.indice'))
        else:
            logger.warning(f'✗ Intento de login fallido: {nombre_usuario}')
            flash('Usuario o contraseña incorrectos.', 'danger')

    return render_template('auth/login.html')


@auth_bp.route('/logout')
def logout():
    usuario = session.get('nombre_usuario', 'desconocido')
    logger.info(f'✗ Logout: {usuario}')
    session.clear()
    flash('Sesión cerrada exitosamente.', 'info')
    return redirect(url_for('auth_bp.login'))
