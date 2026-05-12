from datetime import datetime
from app.base_datos import db
from config.constantes import EstadoEnum


class CicloPrueba(db.Model):
    __tablename__ = 'ciclo_prueba'

    id = db.Column(db.Integer, primary_key=True)
    nombre = db.Column(db.String(255), nullable=False, index=True)
    descripcion = db.Column(db.Text)
    estado = db.Column(db.Enum(EstadoEnum), default=EstadoEnum.NUEVO)

    fecha_inicio = db.Column(db.DateTime, nullable=True)
    fecha_fin = db.Column(db.DateTime, nullable=True)
    fecha_creacion = db.Column(db.DateTime, default=datetime.utcnow)

    casos_prueba = db.relationship(
        'CasoPrueba',
        secondary='caso_prueba_ciclo',
        back_populates='ciclos_prueba'
    )

    epicas = db.relationship(
        'Epica',
        secondary='epica_ciclo_prueba',
        back_populates='ciclos_prueba'
    )

    resultados = db.relationship('Resultado', back_populates='ciclo_prueba', lazy=True, cascade='all, delete-orphan')
    historiales = db.relationship('Historial', back_populates='ciclo_prueba', lazy=True)

    TRANSICIONES_VALIDAS = {
        EstadoEnum.NUEVO: [EstadoEnum.EN_PROGRESO],
        EstadoEnum.EN_PROGRESO: [EstadoEnum.TERMINADO, EstadoEnum.NUEVO],
        EstadoEnum.TERMINADO: [EstadoEnum.EN_PROGRESO],
    }

    def puede_cambiar_a(self, nuevo_estado):
        transiciones = self.TRANSICIONES_VALIDAS.get(self.estado, [])
        return nuevo_estado in transiciones

    def __repr__(self):
        return f'<CicloPrueba {self.nombre}>'
