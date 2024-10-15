import os
import json
import re
from PySide6.QtWidgets import (
    QApplication, QMainWindow, QWidget, QVBoxLayout, QHBoxLayout, QPushButton, QFileDialog,
    QLabel, QStackedWidget, QScrollArea, QGridLayout,
    QProgressBar, QTreeWidget, QTreeWidgetItem, QTextBrowser, QSizePolicy, QMessageBox, QSlider, QCheckBox)
from PySide6.QtCore import Qt, QSize, QUrl, QDir, Signal
from PySide6.QtGui import QIcon, QDesktopServices
from PySide6.QtWebEngineWidgets import QWebEngineView
from PySide6.QtWebEngineCore import QWebEnginePage
from PySide6.QtMultimedia import QMediaPlayer, QAudioOutput
from PySide6.QtMultimediaWidgets import QVideoWidget


class VideoItemWidget(QWidget):
    checkbox_changed = Signal(bool, object)

    def __init__(self, archivo, curso_name, curso_tracker, marcar_callback):
        super().__init__()

        layout = QHBoxLayout()
        layout.setContentsMargins(0, 0, 0, 0)

        vertical_layout = QVBoxLayout(self)
        vertical_layout.setContentsMargins(0, 10, 10, 10)

        self.checkbox = QCheckBox()
        self.checkbox.setChecked(archivo['visto'])
        self.checkbox.clicked.connect(self.on_checkbox_clicked)
        self.marcar_callback = marcar_callback
        self.archivo = archivo
        self.curso_name = curso_name
        self.curso_tracker = curso_tracker
        layout.addWidget(self.checkbox)

        self.nombre_label = QLabel(archivo['nombre'])
        self.nombre_label.setWordWrap(True)
        layout.addWidget(self.nombre_label)

        self.progress_bar = QProgressBar()
        self.progress_bar.setRange(0, 100)
        self.progress_bar.setTextVisible(False)

        vertical_layout.addLayout(layout)
        vertical_layout.addWidget(self.progress_bar)

        self.load_progress()

    def update_progress(self, progress):
        self.progress_bar.setValue(int(progress))

    def load_progress(self):
        ruta_curso = self.curso_tracker.cursos_data[self.curso_name]['ruta']
        seccion = self.archivo.get('seccion', 'Principal')
        ruta_archivo = os.path.join(
            ruta_curso, seccion, self.archivo['nombre'])
        ruta_archivo = os.path.normpath(ruta_archivo)  # Normalizar la ruta

        progress = self.curso_tracker.load_video_progress(
            self.curso_name, ruta_archivo)
        print(f"Cargando progreso para: {ruta_archivo}")
        print(f"Progreso encontrado: {progress}")

        if progress:
            position = progress.get("position", 0)
            duration = progress.get("duration", 1)  # Evitar división por cero
            progreso = (position / duration) * 100 if duration > 0 else 0
            self.progress_bar.setValue(int(progreso))
            print(f"Progreso establecido: {progreso:.2f}%")
        else:
            self.progress_bar.setValue(0)
            print("No se encontró progreso, estableciendo a 0%")

    def on_checkbox_clicked(self):
        is_checked = self.checkbox.isChecked()
        self.marcar_callback(self.archivo, is_checked)
        self.checkbox_changed.emit(is_checked, self.archivo)


class FileItemWidget(QWidget):
    checkbox_changed = Signal(bool, object)

    def __init__(self, archivo, visto, marcar_callback):
        super().__init__()
        layout = QHBoxLayout(self)
        layout.setContentsMargins(0, 10, 10, 10)

        self.checkbox = QCheckBox()
        self.checkbox.setChecked(visto)
        self.checkbox.clicked.connect(self.on_checkbox_clicked)
        self.marcar_callback = marcar_callback
        self.archivo = archivo
        layout.addWidget(self.checkbox)

        self.nombre_label = QLabel(archivo['nombre'])
        self.nombre_label.setWordWrap(True)
        layout.addWidget(self.nombre_label)

    def on_checkbox_clicked(self):
        is_checked = self.checkbox.isChecked()
        self.marcar_callback(self.archivo, is_checked)
        self.checkbox_changed.emit(is_checked, self.archivo)


class CustomWebEnginePage(QWebEnginePage):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.linkHovered.connect(self.onLinkHovered)

    def acceptNavigationRequest(self, url, _type, isMainFrame):
        print(f"acceptNavigationRequest: url={url}, type={
              _type}, isMainFrame={isMainFrame}")
        if url.scheme() == "file":
            return True
        if _type == QWebEnginePage.NavigationTypeLinkClicked:
            QDesktopServices.openUrl(url)
            return False
        return True

    def onLinkHovered(self, url):
        pass
        # print(f"Link hovered: {url}")

    def javaScriptConsoleMessage(self, level, message, lineNumber, sourceID):
        # print(f"JavaScript Console: {message}")
        if message.startswith("Link clicked:"):
            url = QUrl(message.split(": ")[1])
            QDesktopServices.openUrl(url)


class CustomWebEngineView(QWebEngineView):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setPage(CustomWebEnginePage(self))
        self.page().loadFinished.connect(self.onLoadFinished)

    def onLoadFinished(self, ok):
        if ok:
            self.page().runJavaScript("""
                document.addEventListener('click', function(e) {
                    var target = e.target;
                    while(target) {
                        if(target.tagName === 'A') {
                            console.log('Link clicked: ' + target.href);
                            break;
                        }
                        target = target.parentElement;
                    }
                });
            """)


class CursoCard(QWidget):
    def __init__(self, curso):
        super().__init__()
        self.curso = curso
        layout = QVBoxLayout(self)

        icon_label = QLabel()
        icon_label.setPixmap(QIcon("path_to_icon.png").pixmap(QSize(50, 50)))
        layout.addWidget(icon_label, alignment=Qt.AlignCenter)

        name_label = QLabel(curso['name'])
        name_label.setWordWrap(True)
        name_label.setAlignment(Qt.AlignCenter)
        layout.addWidget(name_label)

        self.progress_bar = QProgressBar()
        self.progress_bar.setRange(0, self.curso['totalArchivos'])
        self.progress_bar.setValue(self.curso['archivosVistos'])
        layout.addWidget(self.progress_bar)

        self.progress_label = QLabel(
            f"{self.curso['archivosVistos']} / {self.curso['totalArchivos']} archivos vistos")
        self.progress_label.setAlignment(Qt.AlignCenter)
        layout.addWidget(self.progress_label)

        change_icon_btn = QPushButton("Cambiar icono")
        layout.addWidget(change_icon_btn)

        self.setFixedSize(200, 250)
        self.setStyleSheet("border-radius: 10px;")

    def actualizar_progreso(self):
        self.progress_bar.setValue(self.curso['archivosVistos'])
        self.progress_label.setText(
            f"{self.curso['archivosVistos']} / {self.curso['totalArchivos']} archivos vistos")


class CustomVideoWidget(QWidget):
    progress_updated = Signal(str, str, float)

    def __init__(self, parent=None, curso_tracker=None):
        super().__init__(parent)
        self.curso_tracker = curso_tracker
        self.current_video_path = None
        self.curso_name = None
        self.last_position = 0  # Añadimos esta variable para almacenar la última posición
        self.end_of_media_processed = False
        self.video_completed = False
        self.media_player = QMediaPlayer()
        self.media_player.mediaStatusChanged.connect(
            self.on_media_status_changed)
        self.setup_ui()

    def setup_ui(self):
        layout = QVBoxLayout(self)

        self.video_widget = QVideoWidget()
        layout.addWidget(self.video_widget)

        self.audio_output = QAudioOutput()
        self.media_player.setAudioOutput(self.audio_output)
        self.media_player.setVideoOutput(self.video_widget)
        self.media_player.positionChanged.connect(self.save_progress)
        self.media_player.playbackStateChanged.connect(
            self.on_playback_state_changed)
        self.media_player.mediaStatusChanged.connect(
            self.on_media_status_changed)

        controls_layout = QHBoxLayout()

        self.play_pause_button = QPushButton("Play")
        self.play_pause_button.clicked.connect(self.play_pause)
        controls_layout.addWidget(self.play_pause_button)

        self.rewind_button = QPushButton("<<")
        self.rewind_button.clicked.connect(self.rewind)
        controls_layout.addWidget(self.rewind_button)

        self.forward_button = QPushButton(">>")
        self.forward_button.clicked.connect(self.forward)
        controls_layout.addWidget(self.forward_button)

        self.position_slider = QSlider(Qt.Horizontal)
        self.position_slider.sliderMoved.connect(self.set_position)
        controls_layout.addWidget(self.position_slider, 1)

        self.duration_label = QLabel("00:00 / 00:00")
        controls_layout.addWidget(self.duration_label)

        volume_layout = QHBoxLayout()
        self.volume_slider = QSlider(Qt.Horizontal)
        self.volume_slider.setRange(0, 100)
        self.volume_slider.setValue(50)
        # Ajusta este valor según tus preferencias
        self.volume_slider.setFixedWidth(60)
        self.volume_slider.valueChanged.connect(self.set_volume)
        volume_layout.addWidget(QLabel("Vol"))
        volume_layout.addWidget(self.volume_slider)
        controls_layout.addLayout(volume_layout)

        layout.addLayout(controls_layout)

        self.media_player.positionChanged.connect(self.position_changed)
        self.media_player.durationChanged.connect(self.duration_changed)

    def play_pause(self):
        if self.media_player.playbackState() == QMediaPlayer.PlayingState:
            self.media_player.pause()
            self.play_pause_button.setText("Play")
            # Emitir señal con el progreso actual al pausar
            if self.media_player.duration() > 0:
                progress = (self.last_position /
                            self.media_player.duration()) * 100
                self.progress_updated.emit(
                    self.curso_name, self.current_video_path, progress)
        else:
            self.media_player.setPosition(self.last_position)
            self.media_player.play()
            self.play_pause_button.setText("Pause")

    def rewind(self):
        self.media_player.setPosition(
            max(0, self.media_player.position() - 5000))

    def forward(self):
        self.media_player.setPosition(
            min(self.media_player.duration(), self.media_player.position() + 5000))

    def position_changed(self, position):
        self.position_slider.setValue(position)
        self.last_position = position
        self.update_duration_label()

        # Emitir señal con el progreso actual
        if self.media_player.duration() > 0:
            progress = (position / self.media_player.duration()) * 100
            self.progress_updated.emit(
                self.curso_name, self.current_video_path, progress)

    def set_position(self, position):
        self.media_player.setPosition(position)
        self.last_position = position  # Actualizamos la última posición

    def duration_changed(self, duration):
        self.position_slider.setRange(0, duration)
        self.update_duration_label()

    def update_duration_label(self):
        position = self.media_player.position()
        duration = self.media_player.duration()
        self.duration_label.setText(
            f"{self.format_time(position)} / {self.format_time(duration)}")

    def format_time(self, ms):
        s = ms // 1000
        m, s = divmod(s, 60)
        return f"{m:02d}:{s:02d}"

    def set_volume(self, volume):
        self.audio_output.setVolume(volume / 100.0)

    def set_source(self, url, curso_name):
        # Guardar el progreso del video actual antes de cambiar
        self.save_current_progress()

        # Reiniciar las variables para el nuevo video
        self.current_video_path = url.toLocalFile()
        self.curso_name = curso_name
        self.last_position = 0
        self.position_slider.setValue(0)
        self.video_completed = False
        self.end_of_media_processed = False

        # Establecer la nueva fuente
        self.media_player.setSource(url)

        # Cargar el progreso del nuevo video
        self.load_progress()

    def save_current_progress(self):
        if self.current_video_path and self.curso_name:
            progress = {
                "position": self.last_position,
                "duration": self.media_player.duration()
            }
            self.curso_tracker.save_video_progress(
                self.curso_name, self.current_video_path, progress)
            print(f"Progreso guardado para {self.current_video_path}: {
                  self.format_time(self.last_position)}")

    def save_progress(self, position):
        self.last_position = position

    def load_progress(self):
        if self.current_video_path and self.curso_name:
            progress = self.curso_tracker.load_video_progress(
                self.curso_name, self.current_video_path)
            if progress:
                self.last_position = progress.get("position", 0)
                self.position_slider.setValue(self.last_position)
                self.update_duration_label()
                print(f"Video cargado en la posición: {
                      self.format_time(self.last_position)}")
            else:
                self.last_position = 0
                self.position_slider.setValue(0)
                print("No se encontró progreso guardado para este video")

    def on_playback_state_changed(self, state):
        if state == QMediaPlayer.PausedState:
            self.save_current_progress()

    def on_media_status_changed(self, status):
        if status == QMediaPlayer.EndOfMedia and not self.end_of_media_processed:
            self.end_of_media_processed = True  # Marcar como procesado
            self.media_player.mediaStatusChanged.disconnect(
                self.on_media_status_changed)
            self.last_position = self.media_player.duration()
            self.save_current_progress()
            self.video_completed = True
            print(f"Video completado: {self.current_video_path}")
            print(f"Curso actual: {self.curso_name}")
            if self.curso_name and self.current_video_path:
                self.curso_tracker.marcar_video_como_visto(
                    self.curso_name, self.current_video_path)
            else:
                print("Error: curso_name o current_video_path no están definidos")
            print("Video terminado, marcado como visto y progreso guardado al final")

    def on_state_changed(self, state):
        if state == QMediaPlayer.StoppedState:
            self.save_progress(self.media_player.duration())


class CursoTracker(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Seguimiento de Cursos")
        self.setGeometry(100, 100, 1200, 800)
        self.curso_actual = None

        self.central_widget = QWidget()
        self.setCentralWidget(self.central_widget)
        self.layout = QVBoxLayout(self.central_widget)

        self.stacked_widget = QStackedWidget()
        self.layout.addWidget(self.stacked_widget)

        self.video_widget = CustomVideoWidget(curso_tracker=self)
        self.video_widget.progress_updated.connect(self.update_video_progress)

        self.setup_ui()
        self.cargar_cursos()
        self.load_progress_data()
        self.btn_volver_inicio.hide()

    def setup_ui(self):
        # Página principal de cursos
        self.cursos_page = QWidget()
        cursos_layout = QVBoxLayout(self.cursos_page)

        titulo = QLabel("Cursos disponibles")
        titulo.setStyleSheet("font-size: 24px; font-weight: bold;")
        cursos_layout.addWidget(titulo)

        scroll_area = QScrollArea()
        scroll_area.setWidgetResizable(True)
        cursos_layout.addWidget(scroll_area)

        self.cursos_grid = QWidget()
        self.grid_layout = QGridLayout(self.cursos_grid)
        scroll_area.setWidget(self.cursos_grid)

        self.btn_agregar_carpeta = QPushButton("Agregar Carpeta")
        self.btn_agregar_carpeta.clicked.connect(self.agregar_carpeta)
        cursos_layout.addWidget(self.btn_agregar_carpeta)

        self.stacked_widget.addWidget(self.cursos_page)

        # Página de detalle del curso
        self.curso_detail_page = QWidget()
        curso_detail_layout = QHBoxLayout(self.curso_detail_page)

        # Página de detalle del curso
        self.curso_detail_page = QWidget()
        curso_detail_layout = QHBoxLayout(self.curso_detail_page)

        # Crear un widget para contener el árbol y el botón
        tree_container = QWidget()
        tree_layout = QVBoxLayout(tree_container)

        self.tree_widget = QTreeWidget()
        self.tree_widget.setHeaderHidden(True)
        self.tree_widget.itemClicked.connect(self.mostrar_archivo)
        tree_layout.addWidget(self.tree_widget)

        # Crear el botón "Volver al Inicio"
        self.btn_volver_inicio = QPushButton("Volver al Inicio")
        self.btn_volver_inicio.clicked.connect(self.volver_al_inicio)
        tree_layout.addWidget(self.btn_volver_inicio)

        curso_detail_layout.addWidget(tree_container, 1)

        self.content_area = QStackedWidget()

        # Área de video
        self.content_area.addWidget(self.video_widget)

        # Área de HTML
        self.web_view = CustomWebEngineView()
        self.content_area.addWidget(self.web_view)

        # Área de texto (para mostrar mensajes)
        self.text_browser = QTextBrowser()
        self.content_area.addWidget(self.text_browser)

        curso_detail_layout.addWidget(self.content_area, 2)

        self.stacked_widget.addWidget(self.curso_detail_page)

    def update_video_progress(self, curso_name, video_path, progress):
        # Buscar el VideoItemWidget correspondiente y actualizar su barra de progreso
        for i in range(self.tree_widget.topLevelItemCount()):
            seccion_item = self.tree_widget.topLevelItem(i)
            for j in range(seccion_item.childCount()):
                archivo_item = seccion_item.child(j)
                widget = self.tree_widget.itemWidget(archivo_item, 0)
                if isinstance(widget, VideoItemWidget):
                    ruta_completa = os.path.join(self.cursos_data[curso_name]['ruta'],
                                                 widget.archivo['seccion'],
                                                 widget.archivo['nombre'])
                    if os.path.normpath(ruta_completa) == os.path.normpath(video_path):
                        widget.update_progress(progress)
                        return

    def volver_al_inicio(self):
        self.stacked_widget.setCurrentWidget(self.cursos_page)
        self.curso_actual = None
        self.tree_widget.clear()
        self.content_area.setCurrentWidget(self.text_browser)
        self.text_browser.setText("Selecciona un curso para ver su contenido.")

    def cargar_cursos(self):
        try:
            with open("cursos_data.json", "r", encoding="utf-8") as f:
                self.cursos_data = json.load(f)

            self.actualizar_grid_cursos()
        except FileNotFoundError:
            self.generar_json_cursos()

    def marcar_video_como_visto(self, curso_name, video_path):
        print(f"Intentando marcar como visto: {video_path}")
        print(f"Curso: {curso_name}")
        if curso_name in self.cursos_data:
            for seccion, archivos in self.cursos_data[curso_name]['archivos'].items():
                for archivo in archivos:
                    ruta_completa = os.path.join(
                        self.cursos_data[curso_name]['ruta'], seccion, archivo['nombre'])
                    print(f"Comparando: {ruta_completa} con {video_path}")
                    if os.path.normpath(ruta_completa) == os.path.normpath(video_path):
                        if not archivo['visto']:
                            archivo['visto'] = True
                            self.cursos_data[curso_name]['archivosVistos'] += 1
                            self.actualizar_progreso_curso(curso_name)
                            self.guardar_cursos_data()
                            print(f"Video marcado como visto: {video_path}")
                        else:
                            print("El video ya estaba marcado como visto")
                        return
        else:
            print(f"El curso {curso_name} no se encuentra en los datos")
        print("No se encontró el video en los datos del curso")

    def actualizar_progreso_curso(self, curso_name):
        curso = self.cursos_data[curso_name]
        total_archivos = curso['totalArchivos']
        archivos_vistos = curso['archivosVistos']
        progreso = (archivos_vistos / total_archivos) * \
            100 if total_archivos > 0 else 0
        print(f"Progreso del curso {curso_name}: {progreso:.2f}%")
        self.actualizar_grid_cursos()

    def guardar_cursos_data(self):
        with open("cursos_data.json", "w", encoding="utf-8") as f:
            json.dump(self.cursos_data, f, ensure_ascii=False, indent=2)
        print("Datos de cursos guardados en cursos_data.json")

    def actualizar_grid_cursos(self):
        for i in reversed(range(self.grid_layout.count())):
            self.grid_layout.itemAt(i).widget().setParent(None)

        for i, (curso_name, curso_data) in enumerate(self.cursos_data.items()):
            curso_card = CursoCard(curso_data)
            curso_card.mousePressEvent = lambda event, c=curso_name: self.mostrar_detalle_curso(
                c)
            self.grid_layout.addWidget(curso_card, i // 3, i % 3)

    def generar_json_cursos(self):
        ruta_cursos = "cursos_videos"
        self.cursos_data = {}

        for curso in os.listdir(ruta_cursos):
            ruta_curso = os.path.join(ruta_cursos, curso)
            if os.path.isdir(ruta_curso):
                total_archivos = self.contar_archivos(ruta_curso)
                self.cursos_data[curso] = {
                    "id": curso,
                    "name": curso,
                    "description": f"Descripción del curso {curso}",
                    "totalArchivos": total_archivos,
                    "archivosVistos": 0,
                    "icon": "SiNextdotjs",
                    "archivos": self.obtener_archivos(ruta_curso),
                    "progress": {},
                    "ruta": ruta_curso
                }

        with open("cursos_data.json", "w", encoding="utf-8") as f:
            json.dump(self.cursos_data, f, ensure_ascii=False, indent=2)

        self.actualizar_grid_cursos()

    def contar_archivos(self, ruta):
        total = 0
        for raiz, dirs, archivos in os.walk(ruta):
            for archivo in archivos:
                if archivo.lower().endswith(('.mp4', '.avi', '.mov', '.html')):
                    total += 1
        return total

    def obtener_archivos(self, ruta):
        archivos = {}
        for raiz, dirs, archivos_lista in os.walk(ruta):
            seccion = os.path.relpath(raiz, ruta)
            if seccion == '.':
                seccion = 'Principal'
            archivos[seccion] = []
            for archivo in archivos_lista:
                if archivo.lower().endswith(('.mp4', '.avi', '.mov', '.html')):
                    archivos[seccion].append({
                        "nombre": archivo,
                        "tipo": "video" if archivo.lower().endswith(('.mp4', '.avi', '.mov')) else "html",
                        "visto": False
                    })
            archivos[seccion] = sorted(
                archivos[seccion], key=lambda x: self.ordenar_clave(x['nombre']))
        return archivos

    def ordenar_clave(self, nombre):
        match = re.search(r'^(\d+)', nombre)
        if match:
            numero = int(match.group(1))
            resto = nombre[match.end():]
            return (numero, resto.lower())
        else:
            return (float('inf'), nombre.lower())

    def mostrar_detalle_curso(self, curso_name):
        self.curso_actual = curso_name
        self.tree_widget.clear()

        for seccion, archivos in self.cursos_data[curso_name]['archivos'].items():
            seccion_item = QTreeWidgetItem(self.tree_widget, [seccion])
            for archivo in archivos:
                archivo_item = QTreeWidgetItem(seccion_item)
                archivo['seccion'] = seccion  # Añadir la sección al archivo
                if archivo['tipo'] == 'video':
                    widget = VideoItemWidget(
                        archivo,
                        curso_name,
                        self,
                        self.marcar_archivo
                    )
                else:
                    widget = FileItemWidget(
                        archivo,
                        archivo['visto'],
                        self.marcar_archivo
                    )
                self.tree_widget.setItemWidget(archivo_item, 0, widget)

        self.stacked_widget.setCurrentWidget(self.curso_detail_page)
        self.btn_volver_inicio.show()

    def marcar_archivo(self, archivo, checked):
        if archivo['visto'] != checked:
            archivo['visto'] = checked
            if checked:
                self.cursos_data[self.curso_actual]['archivosVistos'] += 1
            else:
                self.cursos_data[self.curso_actual]['archivosVistos'] -= 1
            self.actualizar_progreso_curso(self.curso_actual)
            self.guardar_cursos_data()
        print(f"Archivo: {archivo['nombre']}, Visto: {checked}")

    def load_progress_data(self):
        try:
            with open("progress_data.json", "r", encoding="utf-8") as f:
                self.progress_data = json.load(f)
        except FileNotFoundError:
            print("Archivo progress_data.json no encontrado. Creando uno nuevo.")
            self.progress_data = {}
            self.save_progress_data()

    def load_video_progress(self, curso_name, video_path):
        video_path = os.path.normpath(video_path)
        if curso_name in self.progress_data:
            for path, progress in self.progress_data[curso_name].items():
                if os.path.normpath(path) == video_path:
                    print(f"Progreso encontrado para {video_path}: {progress}")
                    return progress
        print(f"No se encontró progreso para {video_path}")
        return None

    def save_video_progress(self, curso_name, video_path, progress):
        if curso_name not in self.progress_data:
            self.progress_data[curso_name] = {}
        self.progress_data[curso_name][video_path] = progress
        self.save_progress_data()

    def save_progress_data(self):
        with open("progress_data.json", "w", encoding="utf-8") as f:
            json.dump(self.progress_data, f, ensure_ascii=False, indent=2)

    def mostrar_archivo(self, item, column):
        if self.curso_actual is None:
            print("Error: No hay curso seleccionado")
            return

        # Obtener el widget del item
        widget = self.tree_widget.itemWidget(item, 0)
        if widget is None:
            return

        # Obtener el nombre del archivo
        if isinstance(widget, VideoItemWidget) or isinstance(widget, FileItemWidget):
            nombre_archivo = widget.nombre_label.text()
        else:
            return

        # Construir la ruta completa del archivo
        ruta_curso = self.cursos_data[self.curso_actual]['ruta']
        seccion = item.parent().text(0) if item.parent() else 'Principal'
        ruta_archivo = os.path.join(ruta_curso, seccion, nombre_archivo)

        if os.path.exists(ruta_archivo):
            if ruta_archivo.lower().endswith(('.mp4', '.avi', '.mov')):
                self.video_widget.set_source(
                    QUrl.fromLocalFile(ruta_archivo), self.curso_actual)
                self.content_area.setCurrentWidget(self.video_widget)
            elif ruta_archivo.lower().endswith('.html'):
                url = QUrl(
                    f"file:///{QDir.fromNativeSeparators(ruta_archivo)}")
                print(f"Cargando archivo: {url}")
                self.web_view.setUrl(url)
                self.content_area.setCurrentWidget(self.web_view)
                self.web_view.setSizePolicy(
                    QSizePolicy.Expanding, QSizePolicy.Expanding)
                self.web_view.setZoomFactor(1.0)
            else:
                self.text_browser.setText(
                    f"Archivo no soportado: {ruta_archivo}")
                self.content_area.setCurrentWidget(self.text_browser)
        else:
            print(f"El archivo no existe: {ruta_archivo}")

    def agregar_carpeta(self):
        carpeta = QFileDialog.getExistingDirectory(self, "Seleccionar Carpeta")
        if carpeta:
            nombre_curso = os.path.basename(carpeta)
            total_archivos = self.contar_archivos(carpeta)
            self.cursos_data[nombre_curso] = {
                "id": nombre_curso,
                "name": nombre_curso,
                "description": f"Descripción del curso {nombre_curso}",
                "totalArchivos": total_archivos,
                "archivosVistos": 0,
                "icon": "SiNextdotjs",
                "archivos": self.obtener_archivos(carpeta),
                "progress": {},
                "ruta": carpeta
            }

            with open("cursos_data.json", "w", encoding="utf-8") as f:
                json.dump(self.cursos_data, f, ensure_ascii=False, indent=2)

            self.actualizar_grid_cursos()

    def closeEvent(self, event):
        self.video_widget.save_current_progress()
        super().closeEvent(event)


if __name__ == "__main__":
    import sys
    app = QApplication(sys.argv)
    ventana = CursoTracker()
    ventana.show()
    sys.exit(app.exec())
