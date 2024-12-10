from flask_wtf import FlaskForm
from wtforms import StringField, IntegerField, FloatField, SelectField, SubmitField
from wtforms.validators import DataRequired

class CategoriaForm(FlaskForm):
    nombre = StringField('Nombre de la Categoría', validators=[DataRequired()])
    submit = SubmitField('Guardar')

class ProductoForm(FlaskForm):
    nombre = StringField('Nombre del Producto', validators=[DataRequired()])
    cantidad = IntegerField('Cantidad', validators=[DataRequired()])
    precio = FloatField('Precio', validators=[DataRequired()])
    categoria_id = SelectField('Categoría', coerce=int, validators=[DataRequired()])
    submit = SubmitField('Guardar')
