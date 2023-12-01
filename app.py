
#--------------------------------------------------------------------
from flask import Flask, request, jsonify, render_template
from flask import redirect, url_for

# Instalar con pip install flask-cors
from flask_cors import CORS

# Instalar con pip install mysql-connector-python
import mysql.connector

# Si es necesario, pip install Werkzeug
from werkzeug.utils import secure_filename

# No es necesario instalar, es parte del sistema standard de Python
import os
import time
#--------------------------------------------------------------------



app = Flask(__name__)
CORS(app)  # Esto habilitará CORS para todas las rutas



class Catalogo:
    
    # Constructor de la clase
    def __init__(self, host, user, password, database):
        # Primero, establecemos una conexión sin especificar la base de datos
        self.conn = mysql.connector.connect(
            host=host,
            user=user,
            password=password
        )
        self.cursor = self.conn.cursor()

        # Intentamos seleccionar la base de datos
        try:
            self.cursor.execute(f"USE {database};")
        except mysql.connector.Error as err:
            # Si la base de datos no existe, la creamos
            if err.errno == mysql.connector.errorcode.ER_BAD_DB_ERROR:
                self.cursor.execute(f"CREATE DATABASE {database};")
                self.conn.database = database
            else:
                raise err

        # Una vez que la base de datos está establecida, creamos la tabla si no existe
        self.cursor.execute('''CREATE TABLE IF NOT EXISTS productos (
            codigo INT PRIMARY KEY AUTO_INCREMENT,
            descripcion VARCHAR(255) NOT NULL,
            cantidad INT NOT NULL,
            precio DECIMAL(10, 2) NOT NULL,
            imagen_url VARCHAR(255),
            proveedor INT);''')
        self.conn.commit()

        # Cerrar el cursor inicial y abrir uno nuevo con el parámetro dictionary=True
        self.cursor.close()
        self.cursor = self.conn.cursor(dictionary=True)
        
    #----------------------------------------------------------------
    def agregar_producto(self, codigo, descripcion, cantidad, precio, proveedor):
        # Verificamos si ya existe un producto con el mismo código
        self.cursor.execute(f"SELECT * FROM productos WHERE codigo = {codigo};")
        producto_existe = self.cursor.fetchone()
        if producto_existe:
            return False

        sql = "INSERT INTO productos (codigo, descripcion, cantidad, precio, proveedor) VALUES (%s, %s, %s, %s, %s);"
        valores = (codigo, descripcion, cantidad, precio, proveedor)

        self.cursor.execute(sql, valores)        
        self.conn.commit()
        return self.cursor.rowcount > 0

    #----------------------------------------------------------------

    def consultar_producto(self, codigo):
        # Consultamos un producto a partir de su código
        self.cursor.execute(f"SELECT * FROM productos WHERE codigo = {codigo};")
        return self.cursor.fetchone()

    #----------------------------------------------------------------
    def modificar_producto(self, codigo, nueva_descripcion, nueva_cantidad, nuevo_precio, nuevo_proveedor):
        sql = "UPDATE productos SET descripcion = %s, cantidad = %s, precio = %s, proveedor = %s WHERE codigo = %s;"
        valores = (nueva_descripcion, nueva_cantidad, nuevo_precio, nuevo_proveedor, codigo)
        self.cursor.execute(sql, valores)
        self.conn.commit()
        
        return self.cursor.rowcount > 0
    
    
    #----------------------------------------------------------------
    def listar_productos(self):
        self.cursor.execute("SELECT * FROM productos;")
        productos = self.cursor.fetchall()
        return productos

    #----------------------------------------------------------------
    def eliminar_producto(self, codigo):
        # Eliminamos un producto de la tabla a partir de su código
        
        self.cursor.execute(f"DELETE FROM productos WHERE codigo = {codigo};")
        self.conn.commit()
        return True

    #----------------------------------------------------------------
    def mostrar_producto(self, codigo):
        # Mostramos los datos de un producto a partir de su código
        producto = self.consultar_producto(codigo)
        if producto:
            print("-" * 40)
            print(f"Código.....: {producto['codigo']}")
            print(f"Descripción: {producto['descripcion']}")
            print(f"Cantidad...: {producto['cantidad']}")
            print(f"Precio.....: {producto['precio']}")
            
            print(f"Proveedor..: {producto['proveedor']}")
            print("-" * 40)
        else:
            print("Producto no encontrado.")

#--------------------------------------------------------------------
# Cuerpo del programa
#--------------------------------------------------------------------
@app.route('/')
def index():
    return render_template('index.html')



@app.route('/productos')
def productos_html():
    return render_template('productos.html')

@app.route('/modificar_producto')
def modificar_producto_html():
    return render_template('modificar_producto.html')

@app.route('/borrar_producto')
def borrar_producto_html():
    return render_template('borrar_producto.html')

#print(catalogo.modificar_producto(2, 'osito', 10, 2332, 5))




# Carpeta para guardar las imagenes.
ruta_destino = './static/img/'
#--------------------------------------------------------------------
@app.route("/productos", methods=["GET"])
def listar_productos():
    productos = catalogo.listar_productos()
    return jsonify(productos)

#--------------------------------------------------------------------
@app.route("/productos/<int:codigo>", methods=["GET"])
def mostrar_producto(codigo):
    producto = catalogo.consultar_producto(codigo)
    if producto:
        return jsonify(producto)
    else:
        return "Producto no encontrado", 404

#--------------------------------------------------------------------

@app.route("/productos", methods=["POST"])
def agregar_producto():
    
    codigo = request.form.get('codigo')
    descripcion = request.form.get('descripcion')
    cantidad = request.form.get('cantidad')
    precio = request.form.get('precio')
    proveedor = request.form.get('proveedor')  
    
    if catalogo.agregar_producto(codigo, descripcion, cantidad, precio, proveedor):
        return jsonify({"mensaje": "Producto agregado"}), 201
    else:
        return jsonify({"mensaje": "Producto ya existe"}), 400

#--------------------------------------------------------------------
@app.route("/modificar_producto", methods=["PUT"])
def modificar_producto():
    try:
        
        codigo = request.form.get('codigo_modificar')
        print(codigo)
        nueva_descripcion = request.form.get('nueva_descripcion')
        nueva_cantidad = request.form.get('nueva_cantidad')
        nuevo_precio = request.form.get('nuevo_precio')
        nuevo_proveedor = request.form.get('nuevo_proveedor')

        # Validar los datos de entrada
        if not codigo or not nueva_cantidad or not nuevo_precio or not nuevo_proveedor:
            return jsonify({"mensaje": "Datos de entrada incompletos"}), 400

        

        if catalogo.modificar_producto(codigo, nueva_descripcion, nueva_cantidad, nuevo_precio, nuevo_proveedor):
            return jsonify({"mensaje": "Producto modificado"}), 200
        else:
            return jsonify({"mensaje": "Producto no encontrado"}), 404
    except mysql.connector.Error as err:
        print(f"Error de MySQL: {err}")
        return jsonify({"mensaje": "Error de MySQL"}), 500
    except Exception as e:
        print(f"Error interno: {e}")
        return jsonify({"mensaje": f"Error interno: {str(e)}"}), 500

#--------------------------------------------------------------------

@app.route("/borrar_producto/<int:codigo>", methods=["POST"])
def borrar_producto(codigo):
    producto_existente = catalogo.consultar_producto(codigo)

    if producto_existente:
        catalogo.borrar_producto(codigo)
        return jsonify({"mensaje": "Producto eliminado"}), 200
    else:
        return jsonify({"mensaje": "Producto no encontrado"}), 404

    #jsonify({"mensaje": "Error al eliminar el producto"}), 404
   
#--------------------------------------------------------------------

catalogo = Catalogo(host='localhost', user='root', password='Rodrigo2023', database='miapp')

if __name__ == "__main__":
    app.run(debug=True)