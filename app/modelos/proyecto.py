from datetime import datetime
from app.base_datos import db
from config.constantes import EstadoProyectoEnum


class Proyecto(db.Model):
    __tablename__ = 'proyecto'

    id = db.Column(db.Integer, primary_key=True)
    nombre = db.Column(db.String(100), nullable=False, unique=True, index=True)
    descripcion = db.Column(db.Text)
    estado = db.Column(
        db.Enum(EstadoProyectoEnum),
        default=EstadoProyectoEnum.ACTIVO
    )
    fecha_creacion = db.Column(db.DateTime, default=datetime.utcnow)
    fecha_fin = db.Column(db.DateTime, nullable=True)

    usuario_id = db.Column(db.Integer, db.ForeignKey('usuario.id'), nullable=False)
    creador = db.relationship('Usuario', back_populates='proyectos_creados')

    epicas = db.relationship('Epica', back_populates='proyecto', lazy=True, cascade='all, delete-orphan')
    historiales = db.relationship('Historial', back_populates='proyecto', lazy=True)

    def __repr__(self):
        return f'<Proyecto {self.nombre}>'
