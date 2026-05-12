from datetime import datetime
from app.base_datos import db
from config.constantes import EstadoDefectoEnum, PrioridadEnum


class Defecto(db.Model):
    __tablename__ = 'defecto'

    id = db.Column(db.Integer, primary_key=True)

    titulo = db.Column(db.String(255), nullable=False)
    descripcion = db.Column(db.Text)
    estado = db.Column(db.Enum(EstadoDefectoEnum), default=EstadoDefectoEnum.ABIERTO)
    prioridad = db.Column(db.Enum(PrioridadEnum), default=PrioridadEnum.MEDIA)
    verificado = db.Column(db.Boolean, default=False)

    epica_id = db.Column(db.Integer, db.ForeignKey('epica.id'), nullable=True)
    caso_prueba_id = db.Column(db.Integer, db.ForeignKey('caso_prueba.id'), nullable=True)
    resultado_id = db.Column(db.Integer, db.ForeignKey('resultado.id'), nullable=True)
    usuario_asignado_id = db.Column(db.Integer, db.ForeignKey('usuario.id'), nullable=True)
    usuario_creacion_id = db.Column(db.Integer, db.ForeignKey('usuario.id'), nullable=True)

    fecha_creacion = db.Column(db.DateTime, default=datetime.utcnow)
    fecha_actualizacion = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    fecha_cierre = db.Column(db.DateTime, nullable=True)

    epica = db.relationship('Epica', back_populates='defectos')
    caso_prueba = db.relationship('CasoPrueba', back_populates='defectos')
    resultado = db.relationship('Resultado', back_populates='defectos')
    asignado_a = db.relationship('Usuario', foreign_keys=[usuario_asignado_id], back_populates='defectos_asignados')
    creado_por = db.relationship('Usuario', foreign_keys=[usuario_creacion_id])

    historiales = db.relationship('Historial', back_populates='defecto', lazy=True)

    TRANSICIONES_VALIDAS = {
        EstadoDefectoEnum.ABIERTO: [EstadoDefectoEnum.EN_PROGRESO],
        EstadoDefectoEnum.EN_PROGRESO: [EstadoDefectoEnum.CERRADO, EstadoDefectoEnum.ABIERTO],
        EstadoDefectoEnum.CERRADO: [EstadoDefectoEnum.ABIERTO],
    }

    def puede_cambiar_a(self, nuevo_estado):
        transiciones = self.TRANSICIONES_VALIDAS.get(self.estado, [])
        return nuevo_estado in transiciones

    def __repr__(self):
        return f'<Defecto #{self.id} {self.titulo}>'
