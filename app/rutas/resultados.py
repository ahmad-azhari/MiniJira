from flask import Blueprint, render_template, request, redirect, url_for, session, flash
from app.base_datos import db
from app.modelos import Resultado, CasoPrueba, CicloPrueba
from config.constantes import EstadoResultadoEnum
from functools import wraps

resultados_bp = Blueprint('resultados_bp', __name__, url_prefix='/resultados')


def requerir_autenticacion(f):
    @wraps(f)
    def wrapper(*args, **kwargs):
        if 'usuario_id' not in session:
            flash('Debes iniciar sesión.', 'warning')
            return redirect(url_for('auth_bp.login'))
        return f(*args, **kwargs)
    return wrapper


@resultados_bp.route('/')
@requerir_autenticacion
def indice():
    resultados = Resultado.query.all()
    return render_template('resultados/indice.html', resultados=resultados)


@resultados_bp.route('/<int:resultado_id>')
@requerir_autenticacion
def detalle(resultado_id):
    resultado = Resultado.query.get_or_404(resultado_id)
    return render_template('resultados/detalle.html', resultado=resultado)


@resultados_bp.route('/nuevo/<int:caso_id>', methods=['GET', 'POST'])
@requerir_autenticacion
def crear(caso_id):
    caso = CasoPrueba.query.get_or_404(caso_id)
    usuario_id = session.get('usuario_id')

    if request.method == 'POST':
        estado = request.form.get('estado', EstadoResultadoEnum.PASADO.value)
        observaciones = request.form.get('observaciones', '').strip()
        ciclo_id = request.form.get('ciclo_id')

        resultado = Resultado(
            caso_prueba_id=caso_id,
            estado=EstadoResultadoEnum(estado),
            observaciones=observaciones,
            usuario_ejecucion_id=usuario_id,
            ciclo_prueba_id=ciclo_id if ciclo_id else None
        )
        db.session.add(resultado)
        db.session.commit()

        flash('Resultado de prueba registrado exitosamente.', 'success')
        return redirect(url_for('resultados_bp.detalle', resultado_id=resultado.id))

    ciclos = CicloPrueba.query.all()
    return render_template('resultados/crear.html', caso=caso, ciclos=ciclos)


@resultados_bp.route('/<int:resultado_id>/editar', methods=['GET', 'POST'])
@requerir_autenticacion
def editar(resultado_id):
    resultado = Resultado.query.get_or_404(resultado_id)

    if request.method == 'POST':
        resultado.estado = EstadoResultadoEnum(request.form.get('estado', resultado.estado.value))
        resultado.observaciones = request.form.get('observaciones', resultado.observaciones).strip()
        db.session.commit()

        flash('Resultado actualizado exitosamente.', 'success')
        return redirect(url_for('resultados_bp.detalle', resultado_id=resultado_id))

    return render_template('resultados/editar.html', resultado=resultado)


@resultados_bp.route('/<int:resultado_id>/eliminar', methods=['POST'])
@requerir_autenticacion
def eliminar(resultado_id):
    resultado = Resultado.query.get_or_404(resultado_id)
    caso_id = resultado.caso_prueba_id

    db.session.delete(resultado)
    db.session.commit()

    flash('Resultado eliminado exitosamente.', 'success')
    return redirect(url_for('casos_prueba_bp.detalle', caso_id=caso_id))
