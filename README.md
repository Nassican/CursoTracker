# CursoTracker

CursoTracker es una aplicación de escritorio desarrollada en Python utilizando PySide6 para el seguimiento y gestión de cursos de video.

## Descripción

Esta aplicación permite a los usuarios:

- Visualizar una lista de cursos disponibles
- Ver el progreso de cada curso
- Reproducir videos de los cursos
- Marcar videos como vistos
- Cambiar los iconos de los cursos
- Agregar nuevas carpetas de cursos

## Estructura del Proyecto

El proyecto está estructurado de la siguiente manera:

- `main.py`: Contiene la lógica principal de la aplicación.
- `icon_manager.py`: Maneja la carga y selección de iconos para los cursos.
- `cursos_data.json`: Almacena la información de los cursos.
- `progress_data.json`: Guarda el progreso de visualización de los videos.

## Instalación

1. Asegúrate de tener Python 3.7 o superior instalado.

2. Instala las dependencias necesarias:

```bash
pip install -r requirements.txt
```

3. Clona el repositorio:

```bash
git clone https://github.com/Nassican/CursoTracker.git
```

4. Ejecuta la aplicación:

```bash
python main.py
```

## Uso

- Al iniciar la aplicación, verás una lista de cursos disponibles en la carpeta `cursos_videos`.
- Si no encuentras tu curso en la lista, puedes agregarlo creando una nueva carpeta en `cursos_videos` con el nombre del curso.
- Haz clic en un curso para ver su contenido.
- Reproduce los videos haciendo clic en ellos.
- Marca los videos como vistos utilizando las casillas de verificación.
- Cambia el icono de un curso haciendo clic en el botón "Cambiar icono".
- Agrega nuevas carpetas de cursos utilizando el botón "Agregar Carpeta".

## Agradecimientos

Un agradecimiento especial a [Devicon](https://devicon.dev/) por proporcionar los iconos utilizados en esta aplicación.

## Licencia

Este proyecto está bajo la Licencia MIT.
