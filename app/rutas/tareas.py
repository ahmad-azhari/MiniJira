from flask import Blueprint, jsonify, request, session

from app.base_datos import db
from app.modelos import Tarea


tareas_bp = Blueprint("tareas_bp", __name__, url_prefix="/api/tareas")


def _usuario_id():
    return session.get("usuario_id")


def _require_auth():
    uid = _usuario_id()
    if not uid:
        return None, (jsonify({"error": "No autenticado"}), 401)
    return uid, None


@tareas_bp.get("")
def listar_tareas():
    uid, err = _require_auth()
    if err:
        return err

    tareas = Tarea.query.filter_by(usuario_id=uid).order_by(Tarea.id.asc()).all()
    return jsonify([t.to_dict() for t in tareas]), 200


@tareas_bp.post("")
def crear_tarea():
    uid, err = _require_auth()
    if err:
        return err

    data = request.get_json(silent=True) or {}
    titulo = (data.get("titulo") or "").strip()
    if not titulo:
        return jsonify({"error": "titulo requerido"}), 400

    tarea = Tarea(
        titulo=titulo,
        descripcion=(data.get("descripcion") or "").strip(),
        estado=(data.get("estado") or "pendiente").strip() or "pendiente",
        usuario_id=uid,
    )
    db.session.add(tarea)
    db.session.commit()
    return jsonify(tarea.to_dict()), 201


@tareas_bp.get("/<int:tarea_id>")
def obtener_tarea(tarea_id: int):
    uid, err = _require_auth()
    if err:
        return err

    tarea = Tarea.query.get(tarea_id)
    if not tarea or tarea.usuario_id != uid:
        return jsonify({"error": "No encontrado"}), 404
    return jsonify(tarea.to_dict()), 200


@tareas_bp.put("/<int:tarea_id>")
def actualizar_tarea(tarea_id: int):
    uid, err = _require_auth()
    if err:
        return err

    tarea = Tarea.query.get(tarea_id)
    if not tarea:
        return jsonify({"error": "No encontrado"}), 404
    if tarea.usuario_id != uid:
        return jsonify({"error": "Prohibido"}), 403

    data = request.get_json(silent=True) or {}
    if "titulo" in data:
        titulo = (data.get("titulo") or "").strip()
        if not titulo:
            return jsonify({"error": "titulo requerido"}), 400
        tarea.titulo = titulo
    if "descripcion" in data:
        tarea.descripcion = (data.get("descripcion") or "").strip()
    if "estado" in data:
        tarea.estado = (data.get("estado") or "").strip()

    db.session.commit()
    return jsonify(tarea.to_dict()), 200


@tareas_bp.delete("/<int:tarea_id>")
def eliminar_tarea(tarea_id: int):
    uid, err = _require_auth()
    if err:
        return err

    tarea = Tarea.query.get(tarea_id)
    if not tarea:
        return jsonify({"error": "No encontrado"}), 404
    if tarea.usuario_id != uid:
        return jsonify({"error": "Prohibido"}), 403

    db.session.delete(tarea)
    db.session.commit()
    return ("", 204)

