#!/usr/bin/env python
import os
import logging
from app.app import crear_app, db

app = crear_app(os.getenv('FLASK_ENV', 'development'))
logger = logging.getLogger(__name__)

with app.app_context():
    db.create_all()

if __name__ == '__main__':
    host = os.getenv('FLASK_HOST', '127.0.0.1')
    port = int(os.getenv('FLASK_PORT', 5000))
    logger.info(f'🚀 Servidor corriendo en http://{host}:{port}')
    app.run(host=host, port=port, debug=app.config.get('DEBUG', False))

