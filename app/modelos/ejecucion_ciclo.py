from datetime import datetime
from app.base_datos import db
from config.constantes import EstadoEjecucionEnum


class EjecucionCiclo(db.Model):
    __tablename__ = 'ejecucion_ciclo'

    id = db.Column(db.Integer, primary_key=True)
    ciclo_prueba_id = db.Column(db.Integer, db.ForeignKey('ciclo_prueba.id'), nullable=False)
    fecha_ejecucion = db.Column(db.DateTime, default=datetime.utcnow)
    total_pruebas = db.Column(db.Integer, default=0)
    pruebas_pasadas = db.Column(db.Integer, default=0)
    pruebas_fallidas = db.Column(db.Integer, default=0)
    pruebas_en_progreso = db.Column(db.Integer, default=0)
    estado_ejecucion = db.Column(db.Enum(EstadoEjecucionEnum), default=EstadoEjecucionEnum.COMPLETADO)
    jenkins_build_number = db.Column(db.Integer, nullable=True)
    id_solicitud = db.Column(db.String(255), nullable=True)

    ciclo_prueba = db.relationship('CicloPrueba', backref='ejecuciones_ciclo')

    def __repr__(self):
        return f'<EjecucionCiclo {self.id} - Ciclo {self.ciclo_prueba_id}>'
