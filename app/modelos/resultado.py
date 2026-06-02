from datetime import datetime
from app.base_datos import db
from config.constantes import EstadoResultadoEnum, ModoEjecucionEnum, EstadoEjecucionEnum


class Resultado(db.Model):
    __tablename__ = 'resultado'

    id = db.Column(db.Integer, primary_key=True)
    caso_prueba_id = db.Column(db.Integer, db.ForeignKey('caso_prueba.id'), nullable=False)
    ciclo_prueba_id = db.Column(db.Integer, db.ForeignKey('ciclo_prueba.id'), nullable=True)
    id_solicitud = db.Column(db.String(80), unique=True, nullable=True)

    estado = db.Column(db.Enum(EstadoResultadoEnum, values_callable=lambda x: [e.value for e in x]), default=EstadoResultadoEnum.PASADO)
    entorno = db.Column(db.String(100), nullable=True)
    resultado_obtenido = db.Column(db.Text)
    notas = db.Column(db.Text)
    archivo_adjunto = db.Column(db.String(255), nullable=True)

    modo_ejecucion = db.Column(db.Enum(ModoEjecucionEnum, values_callable=lambda x: [e.value for e in x]), default=ModoEjecucionEnum.MANUAL)
    estado_ejecucion = db.Column(db.Enum(EstadoEjecucionEnum, values_callable=lambda x: [e.value for e in x]), default=EstadoEjecucionEnum.COMPLETADO)
    jenkins_build_number = db.Column(db.Integer, nullable=True)
    jenkins_log_url = db.Column(db.String(500), nullable=True)
    tiempo_inicio_jenkins = db.Column(db.DateTime, nullable=True)
    tiempo_fin_jenkins = db.Column(db.DateTime, nullable=True)
    tiempo_ejecucion = db.Column(db.Integer, nullable=True)
    numero_intentos = db.Column(db.Integer, default=1)
    json_respuesta_jenkins = db.Column(db.JSON, nullable=True)
    output_jenkins = db.Column(db.Text, nullable=True)

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
