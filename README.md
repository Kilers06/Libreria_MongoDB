# Libreria_MongoDB

Requisitos
 -Python 3
 Visual Studio Code
 Servidor en MongoDB: local mediante Docker 
 Libreria de Python pymongo esta se intala mediante la terminal con el comando (python -m pip install pymongo)


1. Instalar y ejecutar MongoDB
- Instala y abre Docker Desktop, verifica que el motor de Docker esté funcionando
- En la terminar de VS Code ejecuta:
"docker run -d --name biblioteca_mongo -p 27017:27017 -v biblioteca_mongo_data:/data/db --restart unless-stopped mongo:7"

Ese comando permite descargar MongoDB, crea el contenedor y guarda los datos en un volumen persistente

3. Ejecuatar aplicación
- Ejecutamos el codigo donde tenemos el menu principal y aqui aparecera lo siguiente:
====== GESTOR DE BIBLIOTECA ======
1. Agregar libro
2. Actualizar libro
3. Eliminar libro
4. Ver todos los libros
5. Buscar libros
6. Salir
Selecciona una opción:

4. Proceso de entradas validas
Al seleccionar la opción 1 podremos agregar un libro un ejemplo puede ser:
Selecciona una opción: 1
Título: Cien años de soledad
Autor: Gabriel García Márquez
Género: Novela
¿Leído o no leído?: leído

Cosas que tenemos que tener en cuenta:
- El titulo, el autor y el género no pueden estar vacíos
- El estado válido es "leído" o "no leído"; el programa también acepta "leido" sin tilde.
- No se permite registrar dos libros con el mismo titulo y autor

Para consultar un libro podemos escoger la opción 4 aqui se visualizan todos los libros registrados.

Si queremos realizar una actualización de algun libro escogemos la opción 2, tambien si lo queremos eliminar podemos escoger la opción 3.

5. Estructura esperada de documento
Cada libro registrado se va a almacenar con la siguiente estructura:
{
  _id: ObjectId("6920a85a8c24f27e6b217b41"),
  titulo: "Cien años de soledad",
  autor: "Gabriel García Márquez",
  genero: "Novela",
  estado: "leído"
}

6. Verificación desde MongoDB en Docker
En una nueva terminal desde VS Code ingresamos:
docker exec -it biblioteca_mongo mongosh

aqui entraremos a mongosh aqui debemos escribir el siguiente comando:
use biblioteca
db.libros.find()

Ese comando nos permitira visualizar los datos almacenados desde la base de datos


