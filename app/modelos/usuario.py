from datetime import datetime
from werkzeug.security import generate_password_hash, check_password_hash
from app.base_datos import db


usuario_rol = db.Table(
    'usuario_rol',
    db.Column('usuario_id', db.Integer, db.ForeignKey('usuario.id'), primary_key=True),
    db.Column('rol_id', db.Integer, db.ForeignKey('rol.id'), primary_key=True)
)


class Usuario(db.Model):
    __tablename__ = 'usuario'

    id = db.Column(db.Integer, primary_key=True)
    nombre_usuario = db.Column(db.String(100), unique=True, nullable=False)
    email = db.Column(db.String(150), unique=True, nullable=False)
    contrasena_hash = db.Column(db.String(255), nullable=False)
    activo = db.Column(db.Boolean, default=True)
    fecha_creacion = db.Column(db.DateTime, default=datetime.utcnow)

    roles = db.relationship('Rol', secondary=usuario_rol, back_populates='usuarios')
    proyectos_creados = db.relationship('Proyecto', back_populates='creador', lazy=True)
    defectos_asignados = db.relationship('Defecto', foreign_keys='Defecto.usuario_asignado_id', back_populates='asignado_a', lazy=True)
    cambios_historial = db.relationship('Historial', back_populates='cambio_por', lazy=True)

    def establecer_contrasena(self, contrasena):
        self.contrasena_hash = generate_password_hash(contrasena)

    def verificar_contrasena(self, contrasena):
        return check_password_hash(self.contrasena_hash, contrasena)

    def __repr__(self):
        return f'<Usuario {self.nombre_usuario}>'


class Rol(db.Model):
    __tablename__ = 'rol'

    id = db.Column(db.Integer, primary_key=True)
    nombre = db.Column(db.String(50), unique=True, nullable=False)
    descripcion = db.Column(db.Text)

    usuarios = db.relationship('Usuario', secondary=usuario_rol, back_populates='roles')

    def __repr__(self):
        return f'<Rol {self.nombre}>'
