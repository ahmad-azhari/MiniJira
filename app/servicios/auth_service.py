from app.modelos import Usuario
from app.base_datos import db


class AuthService:
    @staticmethod
    def autenticar(nombre_usuario: str, contrasena: str) -> Usuario | None:
        usuario = Usuario.query.filter_by(nombre_usuario=nombre_usuario).first()
        if usuario and usuario.verificar_contrasena(contrasena) and usuario.activo:
            return usuario
        return None

    @staticmethod
    def crear_usuario(nombre_usuario: str, email: str, contrasena: str) -> Usuario:
        usuario = Usuario(nombre_usuario=nombre_usuario, email=email)
        usuario.establecer_contrasena(contrasena)
        db.session.add(usuario)
        db.session.commit()
        return usuario

    @staticmethod
    def usuario_existe(nombre_usuario: str) -> bool:
        return Usuario.query.filter_by(nombre_usuario=nombre_usuario).first() is not None

    @staticmethod
    def obtener_usuario(usuario_id: int) -> Usuario | None:
        return Usuario.query.get(usuario_id)

    @staticmethod
    def cambiar_contrasena(usuario: Usuario, contrasena_nueva: str) -> bool:
        usuario.establecer_contrasena(contrasena_nueva)
        db.session.commit()
        return True
