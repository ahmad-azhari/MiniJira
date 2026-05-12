from datetime import datetime
from app.base_datos import db
from config.constantes import EstadoEnum, PrioridadEnum, TipoEnum


epica_caso_prueba = db.Table(
    'epica_caso_prueba',
    db.Column('epica_id', db.Integer, db.ForeignKey('epica.id'), primary_key=True),
    db.Column('caso_prueba_id', db.Integer, db.ForeignKey('caso_prueba.id'), primary_key=True)
)

epica_ciclo_prueba = db.Table(
    'epica_ciclo_prueba',
    db.Column('epica_id', db.Integer, db.ForeignKey('epica.id'), primary_key=True),
    db.Column('ciclo_prueba_id', db.Integer, db.ForeignKey('ciclo_prueba.id'), primary_key=True)
)


class Epica(db.Model):
    __tablename__ = 'epica'

    id = db.Column(db.Integer, primary_key=True)
    tipo = db.Column(db.Enum(TipoEnum), default=TipoEnum.EPIC, nullable=False)
    nombre = db.Column(db.String(255), nullable=False, index=True)
    descripcion = db.Column(db.Text)
    estado = db.Column(db.Enum(EstadoEnum), default=EstadoEnum.NUEVO)
    prioridad = db.Column(db.Enum(PrioridadEnum), default=PrioridadEnum.MEDIA)

    epica_padre_id = db.Column(db.Integer, db.ForeignKey('epica.id'), nullable=True)
    proyecto_id = db.Column(db.Integer, db.ForeignKey('proyecto.id'), nullable=False)
    usuario_asignado_id = db.Column(db.Integer, db.ForeignKey('usuario.id'), nullable=True)
    usuario_creacion_id = db.Column(db.Integer, db.ForeignKey('usuario.id'), nullable=True)

    fecha_creacion = db.Column(db.DateTime, default=datetime.utcnow)
    fecha_limite = db.Column(db.DateTime, nullable=True)
    fecha_cierre = db.Column(db.DateTime, nullable=True)

    horas_estimadas = db.Column(db.Numeric(10, 2), nullable=True)
    horas_reales = db.Column(db.Numeric(10, 2), nullable=True)
    puntos_historia = db.Column(db.Integer, nullable=True)

    historias_hijas = db.relationship(
        'Epica',
        remote_side=[epica_padre_id],
        back_populates='epica_padre',
        lazy=True,
        cascade='all, delete-orphan',
        foreign_keys=[epica_padre_id]
    )
    epica_padre = db.relationship(
        'Epica',
        remote_side=[id],
        back_populates='historias_hijas',
        uselist=False
    )

    proyecto = db.relationship('Proyecto', back_populates='epicas')
    asignado_a = db.relationship('Usuario', foreign_keys=[usuario_asignado_id])
    creado_por = db.relationship('Usuario', foreign_keys=[usuario_creacion_id])

    casos_prueba = db.relationship(
        'CasoPrueba',
        secondary=epica_caso_prueba,
        back_populates='epicas'
    )
    ciclos_prueba = db.relationship(
        'CicloPrueba',
        secondary=epica_ciclo_prueba,
        back_populates='epicas'
    )

    defectos = db.relationship('Defecto', back_populates='epica', lazy=True)
    historiales = db.relationship('Historial', back_populates='epica', lazy=True)

    TRANSICIONES_VALIDAS = {
        EstadoEnum.NUEVO: [EstadoEnum.EN_PROGRESO],
        EstadoEnum.EN_PROGRESO: [EstadoEnum.TERMINADO, EstadoEnum.NUEVO],
        EstadoEnum.TERMINADO: [EstadoEnum.EN_PROGRESO],
    }

    def puede_cambiar_a(self, nuevo_estado):
        transiciones = self.TRANSICIONES_VALIDAS.get(self.estado, [])
        return nuevo_estado in transiciones

    def es_epica(self):
        return self.tipo == TipoEnum.EPIC

    def es_historia(self):
        return self.tipo == TipoEnum.STORY

    def __repr__(self):
        tipo_str = 'Epic' if self.es_epica() else 'Story'
        return f'<{tipo_str} {self.nombre}>'
