from datetime import datetime
from app.base_datos import db
from config.constantes import EstadoResultadoEnum


class Resultado(db.Model):
    __tablename__ = 'resultado'

    id = db.Column(db.Integer, primary_key=True)
    caso_prueba_id = db.Column(db.Integer, db.ForeignKey('caso_prueba.id'), nullable=False)
    ciclo_prueba_id = db.Column(db.Integer, db.ForeignKey('ciclo_prueba.id'), nullable=False)

    estado = db.Column(db.Enum(EstadoResultadoEnum), default=EstadoResultadoEnum.EN_PROGRESO)
    entorno = db.Column(db.String(100), nullable=True)
    resultado_obtenido = db.Column(db.Text)
    notas = db.Column(db.Text)
    archivo_adjunto = db.Column(db.String(255), nullable=True)

    usuario_creacion_id = db.Column(db.Integer, db.ForeignKey('usuario.id'), nullable=True)
    fecha_creacion = db.Column(db.DateTime, default=datetime.utcnow)
    fecha_actualizacion = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    caso_prueba = db.relationship('CasoPrueba', back_populates='resultados')
    ciclo_prueba = db.relationship('CicloPrueba', back_populates='resultados')
    creado_por = db.relationship('Usuario', foreign_keys=[usuario_creacion_id])

    defectos = db.relationship('Defecto', back_populates='resultado', lazy=True)
    historiales = db.relationship('Historial', back_populates='resultado', lazy=True)

    def __repr__(self):
        return f'<Resultado Caso={self.caso_prueba_id} Estado={self.estado.value}>'
