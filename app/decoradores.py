from flask import session, redirect, url_for, flash
from functools import wraps
from config.constantes import RolEnum


def requerir_autenticacion(f):
    """Requiere estar autenticado (todos los roles)"""
    @wraps(f)
    def wrapper(*args, **kwargs):
        if 'usuario_id' not in session:
            flash('Debes iniciar sesión.', 'warning')
            return redirect(url_for('auth_bp.login'))
        return f(*args, **kwargs)
    return wrapper


def requerir_miembro(f):
    """Solo ADMIN y MIEMBRO pueden acceder (creación/edición)"""
    @wraps(f)
    def wrapper(*args, **kwargs):
        if 'usuario_id' not in session:
            flash('Debes iniciar sesión.', 'warning')
            return redirect(url_for('auth_bp.login'))

        roles = session.get('roles', [])
        if RolEnum.ADMIN.value not in roles and RolEnum.MIEMBRO.value not in roles:
            flash('No tienes permiso para realizar esta acción.', 'danger')
            return redirect(url_for('proyectos_bp.indice'))

        return f(*args, **kwargs)
    return wrapper


def requerir_admin(f):
    """Solo ADMIN puede acceder (eliminación y gestión)"""
    @wraps(f)
    def wrapper(*args, **kwargs):
        if 'usuario_id' not in session:
            flash('Debes iniciar sesión.', 'warning')
            return redirect(url_for('auth_bp.login'))

        roles = session.get('roles', [])
        if RolEnum.ADMIN.value not in roles:
            flash('No tienes permiso para realizar esta acción. Solo administradores.', 'danger')
            return redirect(url_for('proyectos_bp.indice'))

        return f(*args, **kwargs)
    return wrapper
