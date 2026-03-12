"""
Modelos de la base de datos
"""
from flask_sqlalchemy import SQLAlchemy

db = SQLAlchemy()


class Persona(db.Model):
    __tablename__ = 'personas'

    id = db.Column(db.Integer, primary_key=True)
    nombre = db.Column(db.String(100), nullable=False, unique=True)
    activo = db.Column(db.Boolean, default=True)
    acumulado = db.Column(db.Integer, default=0)
    guardias_asignadas = db.relationship('Guardia', backref='persona', lazy=True, foreign_keys='Guardia.persona_id')
    novedades = db.relationship('Novedad', backref='persona', lazy=True)

    def __repr__(self):
        return f'<Persona {self.nombre}>'


class Guardia(db.Model):
    __tablename__ = 'guardias'

    id = db.Column(db.Integer, primary_key=True)
    fecha = db.Column(db.Date, nullable=False, index=True)
    persona_id = db.Column(db.Integer, db.ForeignKey('personas.id'), nullable=False)
    tipo = db.Column(db.String(20), default='normal')
    es_suplencia = db.Column(db.Boolean, default=False)
    persona_original_id = db.Column(db.Integer, db.ForeignKey('personas.id'), nullable=True)

    __table_args__ = (db.UniqueConstraint('fecha', 'persona_id', name='unique_fecha_persona'),)

    def __repr__(self):
        return f'<Guardia {self.fecha} - {self.persona_id}>'


class Novedad(db.Model):
    __tablename__ = 'novedades'

    id = db.Column(db.Integer, primary_key=True)
    persona_id = db.Column(db.Integer, db.ForeignKey('personas.id'), nullable=False)
    fecha_inicio = db.Column(db.Date, nullable=False)
    fecha_fin = db.Column(db.Date, nullable=False)
    tipo = db.Column(db.String(50), nullable=False)
    descripcion = db.Column(db.String(200))

    def __repr__(self):
        return f'<Novedad {self.persona_id} - {self.fecha_inicio} a {self.fecha_fin}>'


class HistoricoAcumulado(db.Model):
    __tablename__ = 'historico_acumulado'

    id = db.Column(db.Integer, primary_key=True)
    persona_id = db.Column(db.Integer, db.ForeignKey('personas.id'), nullable=False)
    mes = db.Column(db.Integer, nullable=False)
    anio = db.Column(db.Integer, nullable=False)
    acumulado = db.Column(db.Integer, default=0)

    __table_args__ = (db.UniqueConstraint('persona_id', 'mes', 'anio', name='unique_persona_mes_anio'),)
