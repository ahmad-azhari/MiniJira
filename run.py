#!/usr/bin/env python
import os
from app.app import crear_app, db

app = crear_app(os.getenv('FLASK_ENV', 'development'))

with app.app_context():
    db.create_all()

if __name__ == '__main__':
    app.run(debug=app.config.get('DEBUG', False))
