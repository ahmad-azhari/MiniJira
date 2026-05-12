from datetime import datetime
from app.base_datos import db
from config.constantes import EstadoEnum, PrioridadEnum, TipoTestEnum


caso_prueba_ciclo = db.Table(
    'caso_prueba_ciclo',
    db.Column('caso_prueba_id', db.Integer, db.ForeignKey('caso_prueba.id'), primary_key=True),
    db.Column('ciclo_prueba_id', db.Integer, db.ForeignKey('ciclo_prueba.id'), primary_key=True)
)


class CasoPrueba(db.Model):
    __tablename__ = 'caso_prueba'

    id = db.Column(db.Integer, primary_key=True)
    nombre = db.Column(db.String(255), nullable=False, index=True)
    objetivo = db.Column(db.Text)
    precondicion = db.Column(db.Text)
    descripcion = db.Column(db.Text)
    pasos_reproduccion = db.Column(db.Text)
    resultado_esperado = db.Column(db.Text)

    estado = db.Column(db.Enum(EstadoEnum), default=EstadoEnum.NUEVO)
    prioridad = db.Column(db.Enum(PrioridadEnum), default=PrioridadEnum.MEDIA)
    tipo = db.Column(db.Enum(TipoTestEnum), default=TipoTestEnum.MANUAL)

    url = db.Column(db.String(500), nullable=True)
    script_prueba = db.Column(db.Text, nullable=True)
    archivo_adjunto = db.Column(db.String(255), nullable=True)

    usuario_creacion_id = db.Column(db.Integer, db.ForeignKey('usuario.id'), nullable=True)
    fecha_creacion = db.Column(db.DateTime, default=datetime.utcnow)
    fecha_actualizacion = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    creado_por = db.relationship('Usuario', foreign_keys=[usuario_creacion_id])

    epicas = db.relationship(
        'Epica',
        secondary='epica_caso_prueba',
        back_populates='casos_prueba'
    )
    ciclos_prueba = db.relationship(
        'CicloPrueba',
        secondary=caso_prueba_ciclo,
        back_populates='casos_prueba'
    )

    resultados = db.relationship('Resultado', back_populates='caso_prueba', lazy=True, cascade='all, delete-orphan')
    defectos = db.relationship('Defecto', back_populates='caso_prueba', lazy=True)
    historiales = db.relationship('Historial', back_populates='caso_prueba', lazy=True)

    TRANSICIONES_VALIDAS = {
        EstadoEnum.NUEVO: [EstadoEnum.EN_PROGRESO],
        EstadoEnum.EN_PROGRESO: [EstadoEnum.TERMINADO, EstadoEnum.NUEVO],
        EstadoEnum.TERMINADO: [EstadoEnum.EN_PROGRESO],
    }

    def puede_cambiar_a(self, nuevo_estado):
        transiciones = self.TRANSICIONES_VALIDAS.get(self.estado, [])
        return nuevo_estado in transiciones

    def es_automatizado(self):
        return self.tipo == TipoTestEnum.AUTOMATIZADO

    def __repr__(self):
        return f'<CasoPrueba {self.nombre}>'
