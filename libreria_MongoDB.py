"""
Gestor de biblioteca con MongoDB y pymongo.

Requisitos:
    pip install pymongo

Configuración (variables de entorno, con valores por defecto para desarrollo local):
    MONGO_URI         (por defecto: mongodb://localhost:27017)
    MONGO_DB          (por defecto: biblioteca)
    MONGO_COLECCION   (por defecto: libros)

Ejemplos de MONGO_URI:
    Local sin autenticación : mongodb://localhost:27017
    Local con autenticación : mongodb://usuario:clave@localhost:27017/?authSource=admin
    MongoDB Atlas           : mongodb+srv://usuario:clave@cluster0.xxxxx.mongodb.net/?retryWrites=true&w=majority

Estructura de cada documento de la colección:
    {
        "_id": ObjectId("..."),
        "titulo": "Cien años de soledad",
        "autor": "Gabriel García Márquez",
        "genero": "Novela",
        "estado": "leído"
    }
"""

import os
import re
import sys

from bson import ObjectId
from pymongo import ASCENDING, MongoClient
from pymongo.errors import (
    ConfigurationError,
    ConnectionFailure,
    DuplicateKeyError,
    InvalidURI,
    OperationFailure,
    PyMongoError,
    ServerSelectionTimeoutError,
)

# ---------------------------------------------------------------------------
# Configuración
# ---------------------------------------------------------------------------

MONGO_URI = os.getenv("MONGO_URI", "mongodb://localhost:27017")
MONGO_DB = os.getenv("MONGO_DB", "biblioteca")
MONGO_COLECCION = os.getenv("MONGO_COLECCION", "libros")

ESTADOS_VALIDOS = ("leído", "no leído")

CAMPOS_EDITABLES = {
    "1": ("titulo", "Título"),
    "2": ("autor", "Autor"),
    "3": ("genero", "Género"),
    "4": ("estado", "Estado de lectura"),
}


def conectar():
    """
    Crea el cliente, verifica la conexión y devuelve (cliente, colección).
    Lanza una excepción de pymongo si no se puede conectar.
    """
    cliente = MongoClient(MONGO_URI, serverSelectionTimeoutMS=5000)
    # MongoClient es "perezoso": el ping fuerza una conexión real.
    cliente.admin.command("ping")

    coleccion = cliente[MONGO_DB][MONGO_COLECCION]

    # Índice único (título + autor), sin distinguir mayúsculas/minúsculas.
    coleccion.create_index(
        [("titulo", ASCENDING), ("autor", ASCENDING)],
        unique=True,
        name="uq_libro_titulo_autor",
        collation={"locale": "es", "strength": 2},
    )
    return cliente, coleccion


# ---------------------------------------------------------------------------
# Utilidades de entrada / salida
# ---------------------------------------------------------------------------

def mostrar_libro(libro):
    """Imprime un documento (libro) en una sola línea."""
    print(
        f"ID: {libro['_id']} | Título: {libro['titulo']} | "
        f"Autor: {libro['autor']} | Género: {libro['genero']} | "
        f"Estado: {libro['estado']}"
    )


def pedir_texto(mensaje):
    """Pide un texto y repite la pregunta hasta que no esté vacío."""
    while True:
        texto = input(mensaje).strip()
        if texto:
            return texto
        print("El valor no puede estar vacío.")


def pedir_estado(mensaje):
    """Pide el estado de lectura y repite hasta que sea válido."""
    while True:
        estado = input(mensaje).strip().lower()
        # Aceptamos también la versión sin tilde
        estado = estado.replace("leido", "leído")
        if estado in ESTADOS_VALIDOS:
            return estado
        print("Estado no válido. Escribe 'leído' o 'no leído'.")


def pedir_id(mensaje):
    """Pide un ID (ObjectId de 24 caracteres hexadecimales). Devuelve None si no es válido."""
    texto = input(mensaje).strip()
    if not ObjectId.is_valid(texto):
        print("ID no válido. Copia el ID completo (24 caracteres) del listado.")
        return None
    return ObjectId(texto)


# ---------------------------------------------------------------------------
# Operaciones CRUD
# ---------------------------------------------------------------------------

def agregar_libro(coleccion):
    print("\n--- AGREGAR LIBRO ---")

    libro = {
        "titulo": pedir_texto("Título: "),
        "autor": pedir_texto("Autor: "),
        "genero": pedir_texto("Género: "),
        "estado": pedir_estado("¿Leído o no leído?: "),
    }

    resultado = coleccion.insert_one(libro)
    print(f"Libro agregado correctamente (ID: {resultado.inserted_id}).")


def listar_libros(coleccion):
    print("\n--- LISTADO DE LIBROS ---")

    libros = list(coleccion.find().sort("titulo", ASCENDING))

    if not libros:
        print("No hay libros registrados.")
        return

    for libro in libros:
        mostrar_libro(libro)


def buscar_libros(coleccion):
    print("\n--- BUSCAR LIBROS ---")

    busqueda = pedir_texto("Escribe el título, autor o género: ")
    # re.escape evita que caracteres especiales se interpreten como regex.
    patron = {"$regex": re.escape(busqueda), "$options": "i"}

    resultados = list(
        coleccion.find(
            {"$or": [{"titulo": patron}, {"autor": patron}, {"genero": patron}]}
        ).sort("titulo", ASCENDING)
    )

    if not resultados:
        print("No se encontraron libros.")
        return

    for libro in resultados:
        mostrar_libro(libro)


def actualizar_libro(coleccion):
    print("\n--- ACTUALIZAR LIBRO ---")

    listar_libros(coleccion)

    id_libro = pedir_id("\nIngresa el ID del libro que deseas modificar: ")
    if id_libro is None:
        return

    if coleccion.find_one({"_id": id_libro}, {"_id": 1}) is None:
        print("No existe un libro con ese ID.")
        return

    print("\n¿Qué deseas modificar?")
    for numero, (_, nombre) in CAMPOS_EDITABLES.items():
        print(f"{numero}. {nombre}")

    opcion = input("Selecciona una opción: ").strip()

    if opcion not in CAMPOS_EDITABLES:
        print("Opción no válida.")
        return

    campo, _ = CAMPOS_EDITABLES[opcion]

    if campo == "estado":
        nuevo_valor = pedir_estado("Ingresa el nuevo estado (leído / no leído): ")
    else:
        nuevo_valor = pedir_texto("Ingresa el nuevo valor: ")

    resultado = coleccion.update_one({"_id": id_libro}, {"$set": {campo: nuevo_valor}})

    if resultado.matched_count == 0:
        print("El libro ya no existe.")
    else:
        print("Libro actualizado correctamente.")


def eliminar_libro(coleccion):
    print("\n--- ELIMINAR LIBRO ---")

    listar_libros(coleccion)

    id_libro = pedir_id("\nIngresa el ID del libro que deseas eliminar: ")
    if id_libro is None:
        return

    libro = coleccion.find_one({"_id": id_libro}, {"titulo": 1})
    if libro is None:
        print("No existe un libro con ese ID.")
        return

    confirmacion = input(f"¿Deseas eliminar '{libro['titulo']}'? (s/n): ").strip().lower()

    if confirmacion == "s":
        coleccion.delete_one({"_id": id_libro})
        print("Libro eliminado correctamente.")
    else:
        print("Eliminación cancelada.")


# ---------------------------------------------------------------------------
# Menú
# ---------------------------------------------------------------------------

def mostrar_menu():
    print("\n====== GESTOR DE BIBLIOTECA ======")
    print("1. Agregar libro")
    print("2. Actualizar libro")
    print("3. Eliminar libro")
    print("4. Ver todos los libros")
    print("5. Buscar libros")
    print("6. Salir")


def ejecutar_accion(coleccion, accion):
    """Ejecuta una acción y maneja los errores de MongoDB sin cerrar el programa."""
    try:
        accion(coleccion)
    except DuplicateKeyError:
        print("Error: ya existe un libro con el mismo título y autor.")
    except (ServerSelectionTimeoutError, ConnectionFailure) as error:
        print("Se perdió la conexión con MongoDB. Verifica que el servidor esté activo.")
        print(f"Detalle: {error}")
    except OperationFailure as error:
        print("MongoDB rechazó la operación (permisos o validación).")
        print(f"Detalle: {error}")
    except PyMongoError as error:
        print(f"Error inesperado en la base de datos: {error}")


def menu(coleccion):
    acciones = {
        "1": agregar_libro,
        "2": actualizar_libro,
        "3": eliminar_libro,
        "4": listar_libros,
        "5": buscar_libros,
    }

    while True:
        mostrar_menu()
        opcion = input("Selecciona una opción: ").strip()

        if opcion == "6":
            print("¡Gracias por utilizar el gestor de biblioteca!")
            break

        accion = acciones.get(opcion)
        if accion:
            ejecutar_accion(coleccion, accion)
        else:
            print("Opción no válida. Intenta nuevamente.")


def main():
    cliente = None
    try:
        cliente, coleccion = conectar()
    except (InvalidURI, ConfigurationError) as error:
        print("La cadena de conexión (MONGO_URI) no es válida.")
        print(f"  Detalle: {error}")
        sys.exit(1)
    except ServerSelectionTimeoutError as error:
        print("No se pudo conectar a MongoDB (tiempo de espera agotado).")
        print("  Revisa que el servicio esté activo, la URI sea correcta y, "
              "si usas Atlas, que tu IP esté permitida en 'Network Access'.")
        print(f"  Detalle: {error}")
        sys.exit(1)
    except OperationFailure as error:
        print("Autenticación fallida o permisos insuficientes. "
              "Revisa usuario, contraseña y authSource.")
        print(f"  Detalle: {error}")
        sys.exit(1)
    except PyMongoError as error:
        print(f"Error al conectar con MongoDB: {error}")
        sys.exit(1)

    try:
        menu(coleccion)
    except (KeyboardInterrupt, EOFError):
        print("\nPrograma interrumpido. ¡Hasta luego!")
    finally:
        cliente.close()


if __name__ == "__main__":
    main()