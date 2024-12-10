from reportlab.lib.pagesizes import letter
from reportlab.pdfgen import canvas
from flask import Flask, render_template, redirect, url_for, flash,send_file, request
import io
from io import BytesIO
from datetime import datetime
import pdfkit 
from config import Config
from models import db, Categoria, Producto
from forms import CategoriaForm, ProductoForm

app = Flask(__name__)
app.config.from_object(Config)
db.init_app(app)

# Inicializar la base de datos
with app.app_context():
    db.create_all()

@app.route('/')
def index():
    categorias = Categoria.query.all()
    productos = Producto.query.all()
    return render_template('index.html', categorias=categorias, productos=productos)

@app.route('/categoria/nueva', methods=['GET', 'POST'])
def nueva_categoria():
    form = CategoriaForm()
    if form.validate_on_submit():
        nueva_categoria = Categoria(nombre=form.nombre.data)
        db.session.add(nueva_categoria)
        db.session.commit()
        flash('Categoría creada con éxito.')
        return redirect(url_for('index'))
    return render_template('categoria.html', form=form)

@app.route('/producto/nuevo', methods=['GET', 'POST'])
def nuevo_producto():
    form = ProductoForm()
    form.categoria_id.choices = [(c.id, c.nombre) for c in Categoria.query.all()]
    if form.validate_on_submit():
        nuevo_producto = Producto(
            nombre=form.nombre.data,
            cantidad=form.cantidad.data,
            precio=form.precio.data,
            fecha=datetime.now(),
            categoria_id=form.categoria_id.data
        )
        db.session.add(nuevo_producto)
        db.session.commit()
        flash('Producto creado con éxito.')
        return redirect(url_for('index'))
    return render_template('inventario.html', form=form)

@app.route('/eliminar/<int:id>', methods=['GET'])
def eliminar_producto(id):
    # Buscar el producto por ID en la base de datos
    producto = Producto.query.get(id)
    if producto:
        db.session.delete(producto)  # Eliminar el producto de la base de datos
        db.session.commit()  # Guardar los cambios en la base de datos
        flash('Producto eliminado con éxito.')
    else:
        flash('Producto no encontrado.')
    return redirect(url_for('index'))  # Redirige a la página principal después de eliminar

@app.route('/editar/<int:id>', methods=['GET', 'POST'])
def editar_producto(id):
    # Obtener el producto de la base de datos
    producto = Producto.query.get(id)
    if not producto:
        flash('Producto no encontrado.')
        return redirect(url_for('index'))  # Si no se encuentra el producto, redirigir al índice

    # Crear el formulario de ProductoForm
    form = ProductoForm()

    # Cargar las categorías desde la base de datos
    categorias = Categoria.query.all()
    form.categoria_id.choices = [(categoria.id, categoria.nombre) for categoria in categorias]

    # Si es un GET, mostrar el formulario con los datos actuales del producto
    if request.method == 'GET':
        form.nombre.data = producto.nombre
        form.cantidad.data = producto.cantidad
        form.precio.data = producto.precio
        form.categoria_id.data = producto.categoria_id  # Pre-seleccionar la categoría actual

    # Si es un POST, procesar los datos del formulario
    if request.method == 'POST':
        if form.validate_on_submit():
            try:
                # Actualizar los campos del producto con los nuevos valores del formulario
                producto.nombre = form.nombre.data
                producto.cantidad = form.cantidad.data
                producto.precio = form.precio.data
                producto.categoria_id = form.categoria_id.data

                # Guardar los cambios en la base de datos
                db.session.commit()  # Guardar cambios en la base de datos
                flash('Producto actualizado con éxito.')
                return redirect(url_for('index'))  # Redirige a la página principal después de editar
            except Exception as e:
                db.session.rollback()  # Si ocurre un error, hacer rollback
                flash(f'Hubo un error al actualizar el producto. {e}')
                print(f"Error al guardar: {e}")
        else:
            flash('Por favor, completa todos los campos correctamente.')

    return render_template('editar_producto.html', form=form, producto=producto)


@app.route('/descargar_reporte_pdf', methods=['GET'])
def descargar_reporte_pdf():
    # Crear un objeto en memoria para el archivo PDF
    buffer = io.BytesIO()

    # Crear el objeto PDF con la librería reportlab
    c = canvas.Canvas(buffer, pagesize=letter)
    c.setFont("Helvetica-Bold", 16)
    c.drawCentredString(300, 780, 'INVENTARIADO DE TIENDA')

    # Encabezados del reporte (fuentes y formato)
    c.setFont("Helvetica-Bold", 12)
    c.drawString(30, 750, 'ID')
    c.drawString(60, 750, 'Nombre')
    c.drawString(200, 750, 'Cantidad')
    c.drawString(280, 750, 'Precio')
    c.drawString(370, 750, 'Categoría')
    c.drawString(480, 750, 'Fecha')  # Agregar encabezado de fecha
    
    # Cambiar el color de la fuente para los datos
    c.setFont("Helvetica", 10)

    # Obtener todos los productos desde la base de datos
    productos = Producto.query.all()

    # Ajustes de posición en la página para los datos
    y_position = 730  # Posición inicial en Y para los datos de los productos

    # Iterar sobre todos los productos
    for producto in productos:
        categoria_nombre = producto.categoria.nombre  # Obtener el nombre de la categoría
        
        # Escribir los datos en la página
        c.drawString(30, y_position, str(producto.id))
        c.drawString(60, y_position, producto.nombre)
        c.drawString(200, y_position, str(producto.cantidad))
        c.drawString(280, y_position, f"Bs{producto.precio:.2f}")
        c.drawString(370, y_position, categoria_nombre)
        c.drawString(480, y_position, producto.fecha.strftime('%Y-%m-%d %H:%M:%S'))  # Mostrar la fecha
        
        y_position -= 20  # Moverse hacia abajo para el siguiente producto
        
        # Si nos acercamos al final de la página, agregar una nueva página
        if y_position < 50:  # Si estamos demasiado cerca del borde inferior
            c.showPage()  # Añadir una nueva página
            c.setFont("Helvetica-Bold", 12)
            c.drawString(30, 750, 'ID')
            c.drawString(60, 750, 'Nombre')
            c.drawString(200, 750, 'Cantidad')
            c.drawString(280, 750, 'Precio')
            c.drawString(370, 750, 'Categoría')
            c.drawString(480, 750, 'Fecha')  # Agregar encabezado de fecha
            c.setFont("Helvetica", 10)
            y_position = 730  # Restablecer la posición Y al inicio de la página

    # Finalizar el PDF y guardarlo en el buffer
    c.save()

    # Mover el puntero al inicio del archivo para la descarga
    buffer.seek(0)

    # Enviar el archivo PDF como respuesta de descarga
    return send_file(buffer, as_attachment=True, download_name="reporte.pdf", mimetype='application/pdf')

if __name__ == '__main__':
    app.run(debug=True)
    
