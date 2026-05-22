from flask import Blueprint, render_template, request, redirect, url_for, session, flash
from app.base_datos import db
from app.modelos import Resultado, CasoPrueba, CicloPrueba
from config.constantes import EstadoResultadoEnum
from app.decoradores import requerir_autenticacion, requerir_miembro, requerir_admin

resultados_bp = Blueprint('resultados_bp', __name__, url_prefix='/resultados')


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
@requerir_miembro
def crear(caso_id):
    caso = CasoPrueba.query.get_or_404(caso_id)
    usuario_id = session.get('usuario_id')

    if request.method == 'POST':
        estado = request.form.get('estado', EstadoResultadoEnum.PASADO.value)
        notas = request.form.get('notas', '').strip()
        ciclo_id = request.form.get('ciclo_id')
        entorno = request.form.get('entorno', '').strip()
        resultado_obtenido = request.form.get('resultado_obtenido', '').strip()

        if not ciclo_id:
            flash('Debe seleccionar un ciclo de prueba.', 'danger')
            return redirect(url_for('resultados_bp.crear', caso_id=caso_id))

        resultado = Resultado(
            caso_prueba_id=caso_id,
            ciclo_prueba_id=ciclo_id,
            estado=EstadoResultadoEnum(estado),
            notas=notas,
            entorno=entorno,
            resultado_obtenido=resultado_obtenido,
            usuario_creacion_id=usuario_id
        )
        db.session.add(resultado)
        db.session.commit()

        flash('Resultado de prueba registrado exitosamente.', 'success')
        return redirect(url_for('resultados_bp.detalle', resultado_id=resultado.id))

    ciclos = CicloPrueba.query.all()
    ciclo_id_preseleccionado = request.args.get('ciclo_id', type=int)
    return render_template('resultados/crear.html', caso=caso, ciclos=ciclos, ciclo_id_preseleccionado=ciclo_id_preseleccionado)


@resultados_bp.route('/<int:resultado_id>/editar', methods=['GET', 'POST'])
@requerir_miembro
def editar(resultado_id):
    resultado = Resultado.query.get_or_404(resultado_id)

    if request.method == 'POST':
        resultado.estado = EstadoResultadoEnum(request.form.get('estado', resultado.estado.value))
        resultado.notas = request.form.get('notas', resultado.notas).strip()
        db.session.commit()

        flash('Resultado actualizado exitosamente.', 'success')
        return redirect(url_for('resultados_bp.detalle', resultado_id=resultado_id))

    return render_template('resultados/editar.html', resultado=resultado)


@resultados_bp.route('/<int:resultado_id>/eliminar', methods=['POST'])
@requerir_admin
def eliminar(resultado_id):
    resultado = Resultado.query.get_or_404(resultado_id)
    caso_id = resultado.caso_prueba_id

    db.session.delete(resultado)
    db.session.commit()

    flash('Resultado eliminado exitosamente.', 'success')
    return redirect(url_for('casos_prueba_bp.detalle', caso_id=caso_id))
