from datetime import datetime
from app.base_datos import db


class Historial(db.Model):
    __tablename__ = 'historial'

    id = db.Column(db.Integer, primary_key=True)

    tipo_entidad = db.Column(db.String(50), nullable=False)
    id_entidad = db.Column(db.Integer, nullable=False)
    nombre_campo = db.Column(db.String(100), nullable=False)
    valor_anterior = db.Column(db.Text)
    valor_nuevo = db.Column(db.Text)

    usuario_cambio_id = db.Column(db.Integer, db.ForeignKey('usuario.id'), nullable=True)
    fecha_cambio = db.Column(db.DateTime, default=datetime.utcnow, index=True)

    proyecto_id = db.Column(db.Integer, db.ForeignKey('proyecto.id'), nullable=True)
    epica_id = db.Column(db.Integer, db.ForeignKey('epica.id'), nullable=True)
    caso_prueba_id = db.Column(db.Integer, db.ForeignKey('caso_prueba.id'), nullable=True)
    ciclo_prueba_id = db.Column(db.Integer, db.ForeignKey('ciclo_prueba.id'), nullable=True)
    resultado_id = db.Column(db.Integer, db.ForeignKey('resultado.id'), nullable=True)
    defecto_id = db.Column(db.Integer, db.ForeignKey('defecto.id'), nullable=True)

    cambio_por = db.relationship('Usuario', back_populates='cambios_historial')
    proyecto = db.relationship('Proyecto', back_populates='historiales')
    epica = db.relationship('Epica', back_populates='historiales')
    caso_prueba = db.relationship('CasoPrueba', back_populates='historiales')
    ciclo_prueba = db.relationship('CicloPrueba', back_populates='historiales')
    resultado = db.relationship('Resultado', back_populates='historiales')
    defecto = db.relationship('Defecto', back_populates='historiales')

    def __repr__(self):
        return f'<Historial {self.tipo_entidad}#{self.id_entidad} Campo={self.nombre_campo}>'
