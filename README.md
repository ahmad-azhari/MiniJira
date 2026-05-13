# Mini Jira - Sistema de Gestión de Pruebas

Sistema completo de gestión de pruebas de software construido con Flask y SQLAlchemy.

## 📋 Características

- **Gestión de Proyectos**: Crear y administrar múltiples proyectos
- **Épicas e Historias**: Organizar trabajo en épicas y historias de usuario
- **Casos de Prueba**: Definir y gestionar casos de prueba manuales y automatizados
- **Ciclos de Prueba**: Agrupar casos en ciclos de prueba
- **Resultados**: Registrar resultados de ejecución de pruebas
- **Defectos**: Reportar y rastrear defectos encontrados
- **Reportes**: Dashboard y reportes de calidad
- **Gestión de Usuarios**: Sistema de roles y permisos

## 🚀 Instalación

### Requisitos Previos
- Python 3.9+
- pip
- virtualenv (recomendado)

### Pasos de Instalación

1. **Clonar el repositorio**
```bash
git clone https://github.com/tu_usuario/Mini-Jira.git
cd Mini-Jira
```

2. **Crear entorno virtual**
```bash
python -m venv venv
# En Windows:
venv\Scripts\activate
# En Linux/Mac:
source venv/bin/activate
```

3. **Instalar dependencias**
```bash
pip install -r requirements.txt
```

4. **Configurar variables de entorno**
```bash
cp .env.example .env
# Editar .env con tus valores
```

5. **Inicializar la base de datos**
```bash
python scripts/init_db.py
```

6. **Ejecutar la aplicación**
```bash
python run.py
```

La aplicación estará disponible en `http://localhost:5000`


## 🔐 Sistemas de Seguridad

### Autenticación
- Sesiones Flask con almacenamiento en filesystem
- Contraseñas hasheadas con bcrypt
- CSRF protection en formularios

### Autorización
- Sistema basado en roles
- Decoradores para proteger rutas
- Verificación de permisos en operaciones

### Validación
- Validación de entrada en todas las rutas
- Validación de estado en transiciones
- Checks de integridad relacional

## 🧪 Testing

```bash
# Ejecutar tests
python -m pytest

# Con coverage
python -m pytest --cov=app tests/
```

## 📝 Configuración

### Ambientes

La aplicación soporta tres ambientes:

- **development**: Modo debug activado, BD SQLite local
- **testing**: BD en memoria, sin debug
- **production**: Sin debug, requiere BD externa

Cambiar ambiente:
```bash
export FLASK_ENV=production  # Linux/Mac
set FLASK_ENV=production     # Windows
```

## 🤝 Contribuir

1. Fork el repositorio
2. Crear rama de feature (`git checkout -b feature/AmazingFeature`)
3. Commit cambios (`git commit -m 'Add AmazingFeature'`)
4. Push a la rama (`git push origin feature/AmazingFeature`)
5. Abrir Pull Request

## 📜 Licencia

Distribuido bajo licencia MIT. Ver `LICENSE` para más información.

## 📧 Contacto

Autor: Ahmad El Azhari  
Email: ahmadk18elazhari@gmail.com
