import os
import json
import re
from PySide6.QtWidgets import (
    QApplication, QMainWindow, QWidget, QVBoxLayout, QHBoxLayout, QPushButton, QFileDialog,
    QLabel, QStackedWidget, QScrollArea, QGridLayout,
    QProgressBar, QTreeWidget, QTreeWidgetItem, QTextBrowser, QSizePolicy, QMessageBox, QSlider, QCheckBox, QSplitter)
from PySide6.QtCore import Qt, QSize, QUrl, QDir, Signal, QTimer
from PySide6.QtGui import QIcon, QDesktopServices, QFontMetrics
from PySide6.QtWebEngineWidgets import QWebEngineView
from PySide6.QtWebEngineCore import QWebEnginePage
from PySide6.QtMultimedia import QMediaPlayer, QAudioOutput
from PySide6.QtMultimediaWidgets import QVideoWidget
from icon_manager import IconManager, IconSelectorDialog


class EmptyCourseWidget(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setup_ui()

    def setup_ui(self):
        layout = QVBoxLayout(self)

        empty_widget = QWidget()
        empty_widget.setContentsMargins(20, 20, 20, 20)

        empty_layout = QVBoxLayout(empty_widget)

        message_label = QLabel("No hay cursos disponibles.")
        message_label.setStyleSheet(
            "font-size: 18px; color: #666; padding:20px")

        add_button = QPushButton("Agrega tu curso favorito")
        add_button.setFixedWidth(200)
        add_button.setFixedHeight(30)
        add_button.setCursor(Qt.PointingHandCursor)
        add_button.setStyleSheet("""
            QPushButton { font-size: 14px; color: #ffffff; border: 1px solid #2596be; border-radius: 5px; padding: 5px 10px; background-color: #2596be; font-weight: bold;}
            QPushButton:hover { background-color: #1f78a4; }
            QPushButton:pressed { background-color: #1a628a; }
        """)

        add_button.clicked.connect(self.parent().agregar_carpeta)

        empty_layout.addWidget(message_label, alignment=Qt.AlignCenter)
        empty_layout.addWidget(add_button, alignment=Qt.AlignCenter)

        layout.addWidget(empty_widget, alignment=Qt.AlignCenter)

        self.setStyleSheet("""
            background-color: #f0f0f0;
            border-radius: 10px;
        """)


class VideoItemWidget(QWidget):
    checkbox_changed = Signal(bool, object)

    def __init__(self, archivo, curso_name, curso_tracker, marcar_callback):
        super().__init__()

        # Configuración del layout principal
        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(0, 0, 0, 0)
        main_layout.setSpacing(5)

        self.setMinimumHeight(50)

        # Layout horizontal para checkbox y nombre
        top_layout = QHBoxLayout()
        top_layout.setSpacing(0)

        self.checkbox = QCheckBox()
        self.checkbox.setChecked(archivo['visto'])
        self.checkbox.setFixedSize(18, 18)
        self.checkbox.setStyleSheet(
            "border: 1px solid #2596be; border-radius: 5px;")
        self.checkbox.clicked.connect(self.on_checkbox_clicked)
        top_layout.addWidget(self.checkbox)

        self.nombre_label = QLabel(archivo['nombre'])
        self.nombre_label.setWordWrap(True)
        self.nombre_label.setSizePolicy(
            QSizePolicy.Expanding, QSizePolicy.Preferred)
        self.nombre_label.setStyleSheet(
            "font-size: 12px; padding-left: 10px;")
        # Añade factor de estiramiento
        top_layout.addWidget(self.nombre_label, 1)

        main_layout.addLayout(top_layout)

        # Configuración de la barra de progreso
        self.progress_bar = QProgressBar()
        self.progress_bar.setRange(0, 100)
        self.progress_bar.setTextVisible(False)
        # Aumenta el grosor de la barra de progreso
        self.progress_bar.setFixedHeight(10)
        self.progress_bar.setStyleSheet(
            "QProgressBar { border: 1px solid #2596be; border-radius: 5px; height: 10px; background-color: #f3f4f6; }"
            "QProgressBar::chunk { background-color: #2596be; }"
        )
        main_layout.addWidget(self.progress_bar)

        self.marcar_callback = marcar_callback
        self.archivo = archivo
        self.curso_name = curso_name
        self.curso_tracker = curso_tracker

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
        # print(f"Cargando progreso para: {ruta_archivo}")
        # print(f"Progreso encontrado: {progress}")

        if progress:
            position = progress.get("position", 0)
            duration = progress.get("duration", 1)  # Evitar división por cero
            progreso = (position / duration) * 100 if duration > 0 else 0
            self.progress_bar.setValue(int(progreso))
            print(f"Progreso establecido: {progreso:.2f}%")
        else:
            self.progress_bar.setValue(0)
            # print("No se encontró progreso, estableciendo a 0%")

    def on_checkbox_clicked(self):
        is_checked = self.checkbox.isChecked()
        self.marcar_callback(self.archivo, is_checked)
        self.checkbox_changed.emit(is_checked, self.archivo)

    def setSelected(self, selected):
        if selected:
            self.setStyleSheet("""
                QLabel {
                    font-weight: bold;
                    padding-left: 10px;
                }
            """)
        else:
            self.setStyleSheet("")


class FileItemWidget(QWidget):
    checkbox_changed = Signal(bool, object)

    def __init__(self, archivo, visto, marcar_callback):
        super().__init__()
        # Configuración del layout principal
        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(0, 5, 5, 5)
        main_layout.setSpacing(5)

        self.setMinimumHeight(50)

        # Layout horizontal para checkbox y nombre
        top_layout = QHBoxLayout()
        top_layout.setSpacing(0)

        self.checkbox = QCheckBox()
        self.checkbox.setChecked(visto)
        self.checkbox.setFixedSize(18, 18)
        self.checkbox.setStyleSheet(
            "border: 1px solid #2596be; border-radius: 5px;")
        self.checkbox.clicked.connect(self.on_checkbox_clicked)
        top_layout.addWidget(self.checkbox)

        self.nombre_label = QLabel(archivo['nombre'])
        self.nombre_label.setWordWrap(True)
        self.nombre_label.setSizePolicy(
            QSizePolicy.Expanding, QSizePolicy.Preferred)
        self.nombre_label.setStyleSheet("font-size: 12px; padding-left: 10px;")
        top_layout.addWidget(self.nombre_label, 1)

        main_layout.addLayout(top_layout)

        self.marcar_callback = marcar_callback
        self.archivo = archivo

    def on_checkbox_clicked(self):
        is_checked = self.checkbox.isChecked()
        self.marcar_callback(self.archivo, is_checked)
        self.checkbox_changed.emit(is_checked, self.archivo)

    def setSelected(self, selected):
        if selected:
            self.setStyleSheet("""
                QLabel {
                    font-weight: bold;
                    padding-left: 10px;
                }
            """)
        else:
            self.setStyleSheet("")


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
    icon_changed = Signal(str, str)

    def __init__(self, curso, icon_manager):
        super().__init__()
        self.curso = curso
        self.icon_manager = icon_manager
        self.setCursor(Qt.PointingHandCursor)
        self.setup_ui()

    def setup_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(5)

        # Contenedor principal con borde
        container = QWidget(self)
        container.setObjectName("cursoCardContainer")
        container.setStyleSheet("""
            #cursoCardContainer {
                border: 1px solid #ddd;
                border-radius: 8px;
            }
        """)
        container_layout = QVBoxLayout(container)
        container_layout.setContentsMargins(10, 10, 10, 10)
        container_layout.setSpacing(5)

        # Icono
        self.icon_label = QLabel()
        self.update_icon(self.curso['icon'])
        container_layout.addWidget(self.icon_label, alignment=Qt.AlignCenter)

        # Nombre del curso
        name_label = QLabel(self.curso['name'])
        name_label.setAlignment(Qt.AlignCenter)
        name_label.setWordWrap(True)
        name_label.setStyleSheet(" font-size: 14px;")
        container_layout.addWidget(name_label)

        self.progress_bar = QProgressBar()
        self.progress_bar.setRange(0, self.curso['totalArchivos'])
        self.progress_bar.setValue(self.curso['archivosVistos'])
        self.progress_bar.setTextVisible(False)
        layout.addWidget(self.progress_bar)

        container_layout.addWidget(self.progress_bar)

        # Etiqueta de progreso
        progress_label = QLabel(
            f"{self.curso['archivosVistos']} / {self.curso['totalArchivos']} videos vistos")
        progress_label.setAlignment(Qt.AlignCenter)
        container_layout.addWidget(progress_label)

        # Botón para cambiar icono
        change_icon_button = QPushButton("Cambiar icono")
        change_icon_button.clicked.connect(self.change_icon)
        container_layout.addWidget(change_icon_button)

        layout.addWidget(container)
        self.setFixedSize(200, 250)
        self.setStyleSheet("""
            QWidget {
                border-radius: 10px;
                background-color: #f3f4f6;
            }
            QLabel {
                font-size: 14px;
                color: #000000;
            }
            QPushButton { font-size: 14px; color: #ffffff; border: 1px solid #2596be; border-radius: 5px; padding: 5px 10px; background-color: #2596be; font-weight: bold;}
            QPushButton:hover { background-color: #1f78a4; }
            QPushButton:pressed { background-color: #1a628a; }
            QProgressBar {
                border: 1px solid #384052;
                border-radius: 5px;
                background-color: #384052;
                height: 10px;
                text-align: center;
            }
            QProgressBar::chunk {
                border-radius: 5px;
                background-color: #2596be;
            }
        """)

    def actualizar_progreso(self):
        self.progress_bar.setValue(self.curso['archivosVistos'])
        self.progress_label.setText(
            f"{self.curso['archivosVistos']} / {self.curso['totalArchivos']} videos vistos")

    def update_icon(self, icon_name):
        icon = self.icon_manager.get_icon(icon_name, size=50)
        self.icon_label.setPixmap(icon.pixmap(50, 50))

    def change_icon(self):
        dialog = IconSelectorDialog(self.icon_manager, self)
        dialog.icon_selected.connect(self.on_icon_selected)
        dialog.exec()

    def on_icon_selected(self, icon_name):
        self.update_icon(icon_name)
        self.icon_changed.emit(self.curso['id'], icon_name)


class CustomVideoWidget(QWidget):
    progress_updated = Signal(str, str, float)

    def __init__(self, parent=None, curso_tracker=None):
        super().__init__(parent)
        self.curso_tracker = curso_tracker
        self.current_video_path = None
        self.curso_name = None
        self.last_position = 0  # Añadimos esta variable para almacenar la última posición
        self.end_of_media_processed = False
        self.media_player = QMediaPlayer()
        self.media_player.mediaStatusChanged.connect(
            self.on_media_status_changed)
        self.setContentsMargins(0, 0, 0, 0)
        self.setup_ui()

    def setup_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)

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

        self.fullscreen_button = QPushButton()
        self.fullscreen_button.setIcon(QIcon("path/to/fullscreen_icon.png"))
        self.fullscreen_button.setObjectName("fullscreenButton")
        controls_layout.addWidget(self.fullscreen_button)

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

        self.setStyleSheet("""
            QPushButton { font-size: 14px; color: #ffffff; border: 1px solid #2596be; border-radius: 5px; padding: 5px 10px; background-color: #2596be; font-weight: bold;}
            QPushButton:hover { background-color: #1f78a4; }
            QPushButton:pressed { background-color: #1a628a; }
            QSlider::groove:horizontal {
                border: 1px solid #5c5c5c;
                border-radius: 5px;
                height: 8px;
                background: #cccccc;
                margin: 2px 0;
            }
            QSlider::handle:horizontal {
                background: #1f78a4;
                border: 1px solid #5c5c5c;
                width: 18px;
                height: 18px;
                margin: -6px 0;
                border-radius: 10px;
            }
        """)

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

    def full_screen(self):
        # Funcion para poner en pantalla completa y salir de la misma
        print("Full screen")
        pass

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
        new_video_path = url.toLocalFile()

        # Si es el mismo video, no hacemos nada
        if self.current_video_path == new_video_path:
            return

        # Guardar el progreso del video actual antes de cambiar
        self.save_current_progress()

        # Establecer la nueva fuente
        self.current_video_path = new_video_path
        self.curso_name = curso_name
        self.media_player.setSource(url)

        # Cargar el progreso del nuevo video
        self.load_progress()

        # Actualizar la interfaz
        self.update_ui()

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

    def update_ui(self):
        # Actualizar la interfaz sin reiniciar el reproductor
        current_position = self.media_player.position()
        self.position_slider.setValue(current_position)
        self.update_duration_label()

        # Emitir señal con el progreso actual
        duration = self.media_player.duration()
        if duration > 0:
            progress = (current_position / duration) * 100
            self.progress_updated.emit(
                self.curso_name, self.current_video_path, progress)

    def update_ui_with_progress(self, progress):
        if progress:
            position = progress.get("position", 0)
            duration = progress.get("duration", 1)
            self.media_player.setPosition(position)
            self.last_position = position
            self.position_slider.setRange(0, duration)
            self.position_slider.setValue(position)
            self.update_duration_label()

            # Emitir señal con el progreso actual
            if duration > 0:
                progress_percentage = (position / duration) * 100
                self.progress_updated.emit(
                    self.curso_name, self.current_video_path, progress_percentage)
        else:
            self.position_slider.setValue(0)
            self.update_duration_label()
            self.progress_updated.emit(
                self.curso_name, self.current_video_path, 0)

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
                # Emitir señal para marcar el checkbox como visto
                self.curso_tracker.marcar_archivo_como_visto(
                    self.current_video_path)
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
        self.splitter = None
        self.empty_course_widget = EmptyCourseWidget(self)
        self.empty_course_widget.hide()
        self.icon_manager = IconManager()
        self.icon_manager.report_problematic_icons()

        self.setStyleSheet("""
            QMainWindow, QWidget {
                background-color: white;
                color: black;
            }
            QPushButton { font-size: 14px; color: #ffffff; border: 1px solid #2596be; border-radius: 5px; padding: 5px 10px; background-color: #2596be; font-weight: bold;}
            QPushButton:hover { background-color: #1f78a4; }
            QPushButton:pressed { background-color: #1a628a; }
            QScrollArea { border: 1px solid #2596be; border-radius: 5px; padding: 10px; }
            QScrollBar:vertical { width: 5px; }
            QScrollBar::handle:vertical { background-color: #2596be; border-radius: 5px; }
            QScrollBar::handle:vertical:hover { background-color: #1f78a4; }
            QScrollBar::handle:vertical:pressed { background-color: #1a628a; }
            QTreeWidget {
                font-size: 12px;
                padding-top: 10px;
                padding-bottom: 10px;
                border: 1px solid #1f78a4;
                border-radius: 10px;
            }
            QTreeWidget::item {
                height: 30px;
                padding-right: 10px;
            }
        """)

        self.central_widget = QWidget()
        self.setCentralWidget(self.central_widget)
        self.layout = QVBoxLayout(self.central_widget)
        self.layout.setContentsMargins(0, 0, 0, 0)

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

        layout_title = QHBoxLayout()
        layout_title.setContentsMargins(0, 0, 0, 0)

        titulo = QLabel("Cursos disponibles")
        titulo.setStyleSheet("font-size: 24px; font-weight: bold;")

        self.btn_agregar_carpeta = QPushButton("Agregar Carpeta")
        self.btn_agregar_carpeta.clicked.connect(self.agregar_carpeta)
        self.btn_agregar_carpeta.setFixedWidth(200)
        self.btn_agregar_carpeta.setCursor(Qt.PointingHandCursor)

        layout_title.addWidget(titulo)
        layout_title.addWidget(self.btn_agregar_carpeta)

        cursos_layout.addLayout(layout_title)

        scroll_area = QScrollArea()
        scroll_area.setWidgetResizable(True)
        cursos_layout.addWidget(scroll_area)

        self.cursos_grid = QWidget()
        self.grid_layout = QGridLayout(self.cursos_grid)
        scroll_area.setWidget(self.cursos_grid)

        self.stacked_widget.addWidget(self.cursos_page)

        # Página de detalle del curso
        self.curso_detail_page = QWidget()
        curso_detail_layout = QHBoxLayout(self.curso_detail_page)
        curso_detail_layout.setContentsMargins(0, 0, 0, 0)

        # Crear un widget para contener el árbol y el botón
        tree_container = QWidget()
        tree_layout = QVBoxLayout(tree_container)
        tree_layout.setContentsMargins(10, 10, 0, 10)

        # Añadir widget para mostrar el icono y nombre del curso
        self.curso_info_widget = QWidget()
        curso_info_layout = QHBoxLayout(self.curso_info_widget)
        curso_info_layout.setContentsMargins(0, 0, 0, 0)
        self.curso_icon_label = QLabel()
        self.curso_name_label = QLabel()
        self.curso_name_label.setWordWrap(True)
        curso_info_layout.addWidget(self.curso_icon_label)
        curso_info_layout.addWidget(self.curso_name_label, 1)
        tree_layout.addWidget(self.curso_info_widget)

        self.tree_widget = QTreeWidget()
        self.tree_widget.setHeaderHidden(True)
        self.tree_widget.setWordWrap(True)
        self.tree_widget.itemClicked.connect(self.mostrar_archivo)
        self.tree_widget.setStyleSheet("QTreeWidget::item { height: 30px; }")
        tree_layout.addWidget(self.tree_widget)
        # Crear el botón "Volver al Inicio"
        self.btn_volver_inicio = QPushButton("Volver al Inicio")
        self.btn_volver_inicio.setCursor(Qt.PointingHandCursor)
        self.btn_volver_inicio.clicked.connect(self.volver_al_inicio)

        tree_layout.addWidget(self.tree_widget)

        # Crear un QSplitter para permitir ajustar el ancho del tree_container

        self.content_area = QStackedWidget()

        # Área de video
        self.content_area.addWidget(self.video_widget)

        # Área de HTML
        self.web_view = CustomWebEngineView()
        self.content_area.addWidget(self.web_view)

        # Área de texto (para mostrar mensajes)
        self.text_browser = QTextBrowser()
        self.content_area.addWidget(self.text_browser)

        self.curso_info_widget = self.crear_curso_info_widget()
        self.content_area.addWidget(self.curso_info_widget)

        tree_layout.addWidget(self.tree_widget)
        tree_layout.addWidget(self.btn_volver_inicio)

        right_container = QWidget()
        right_layout = QVBoxLayout(right_container)
        right_layout.setContentsMargins(0, 10, 10, 10)

        # Crear el breadcrumb
        self.breadcrumb_label = QLabel()
        self.breadcrumb_label.setStyleSheet("""
            font-size: 14px;
            color: #666;
            padding: 10px;
            margin-left: 10px;
            margin-right: 10px;
            background-color: #f0f0f0;
            border-radius: 3px;
        """)
        self.breadcrumb_label.setContentsMargins(10, 0, 10, 0)
        right_layout.addWidget(self.breadcrumb_label)

        # Añadir el content_area al right_container
        right_layout.addWidget(self.content_area)

        # Crear un QSplitter para permitir ajustar el ancho del tree_container
        self.splitter = QSplitter(Qt.Horizontal)
        self.splitter.addWidget(tree_container)
        self.splitter.addWidget(right_container)
        # Hace que el content_area se expanda más que el tree_container
        self.splitter.setStretchFactor(1, 1)
        self.splitter.splitterMoved.connect(
            self.ajustar_titulo_curso)  # Conecta la señal splitterMoved

        curso_detail_layout.addWidget(self.splitter)

        self.stacked_widget.addWidget(self.curso_detail_page)

    def crear_curso_info_widget(self):
        widget = QWidget()
        layout = QVBoxLayout(widget)
        layout.setAlignment(Qt.AlignCenter)
        layout.setSpacing(10)  # Reduce el espacio entre los elementos

        # Contenedor para el icono y el nombre
        icon_name_container = QWidget()
        icon_name_layout = QHBoxLayout(icon_name_container)
        icon_name_layout.setAlignment(Qt.AlignCenter)
        icon_name_layout.setSpacing(20)  # Espacio entre el icono y el nombre

        self.curso_info_icon = QLabel()
        self.curso_info_icon.setAlignment(Qt.AlignHCenter | Qt.AlignVCenter)
        layout.addWidget(self.curso_info_icon)

        self.curso_info_name = QLabel()
        self.curso_info_name.setAlignment(Qt.AlignLeft | Qt.AlignVCenter)
        self.curso_info_name.setStyleSheet(
            "font-size: 24px; font-weight: bold;")
        icon_name_layout.addWidget(self.curso_info_name)

        layout.addWidget(icon_name_container)

        return widget

    def marcar_archivo_como_visto(self, video_path):
        # Buscar el VideoItemWidget correspondiente y marcar el checkbox
        for i in range(self.tree_widget.topLevelItemCount()):
            seccion_item = self.tree_widget.topLevelItem(i)
            for j in range(seccion_item.childCount()):
                archivo_item = seccion_item.child(j)
                widget = self.tree_widget.itemWidget(archivo_item, 0)
                if isinstance(widget, VideoItemWidget):
                    ruta_completa = os.path.join(self.cursos_data[self.curso_actual]['ruta'],
                                                 widget.archivo['seccion'],
                                                 widget.archivo['nombre'])
                    if os.path.normpath(ruta_completa) == os.path.normpath(video_path):
                        widget.checkbox.setChecked(True)
                        return

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
            print(
                "No se encontró el archivo cursos_data.json. Iniciando con una lista de cursos vacía.")
            self.cursos_data = {}

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
        # Limpiar el grid layout
        for i in reversed(range(self.grid_layout.count())):
            self.grid_layout.itemAt(i).widget().setParent(None)

        if not self.cursos_data:
            self.empty_course_widget.show()
            self.grid_layout.addWidget(self.empty_course_widget)
            return

        self.empty_course_widget.hide()

        # Calcular el número de columnas basado en el ancho de la ventana
        ancho_ventana = self.width()
        ancho_tarjeta = 300  # Ancho de cada tarjeta de curso
        # 20 es el espacio entre tarjetas
        columnas = max(1, ancho_ventana // (ancho_tarjeta + 20))

        # Agregar las tarjetas de curso al grid
        row = 0
        col = 0
        for curso_name, curso_data in self.cursos_data.items():
            curso_card = CursoCard(curso_data, self.icon_manager)
            curso_card.mousePressEvent = lambda event, c=curso_name: self.mostrar_detalle_curso(
                c)
            curso_card.icon_changed.connect(self.update_curso_icon)
            self.grid_layout.addWidget(curso_card, row, col)

            col += 1
            if col >= columnas:
                col = 0
                row += 1

    def resizeEvent(self, event):
        super().resizeEvent(event)
        self.actualizar_grid_cursos()

    def update_curso_icon(self, curso_id, new_icon):
        if curso_id in self.cursos_data:
            self.cursos_data[curso_id]['icon'] = new_icon
            self.guardar_cursos_data()
            self.actualizar_grid_cursos()

    def generar_json_cursos(self):
        """
        ruta_cursos = "cursos_videos"
        self.cursos_data = {}

        for curso in os.listdir(ruta_cursos):
            ruta_curso = os.path.join(ruta_cursos, curso)
            if os.path.isdir(ruta_curso):
                archivos = self.obtener_archivos(ruta_curso)
                total_archivos = sum(len(files) for files in archivos.values())
                self.cursos_data[curso] = {
                    "id": curso,
                    "name": curso,
                    "description": f"Descripción del curso {curso}",
                    "totalArchivos": total_archivos,
                    "archivosVistos": 0,
                    "icon": "folder/folder-color",
                    "archivos": archivos,
                    "progress": {},
                    "ruta": ruta_curso
                }

        with open("cursos_data.json", "w", encoding="utf-8") as f:
            json.dump(self.cursos_data, f, ensure_ascii=False, indent=2)

        self.actualizar_grid_cursos()
        """
        pass

    def contar_archivos(self, ruta):
        total = 0
        for raiz, dirs, archivos in os.walk(ruta):
            for archivo in archivos:
                if archivo.lower().endswith(('.mp4', '.avi', '.mov', '.html')):
                    total += 1
        return total

    def obtener_archivos(self, ruta):
        def ordenar_clave(nombre):
            match = re.match(r'^(\d+)', nombre)
            if match:
                numero = int(match.group(1))
                resto = nombre[match.end():].lower()
                return (numero, resto)
            else:
                return (float('inf'), nombre.lower())
        archivos = {}
        for raiz, dirs, archivos_lista in os.walk(ruta):
            seccion = os.path.relpath(raiz, ruta)
            archivos_seccion = []
            for archivo in archivos_lista:
                if archivo.lower().endswith(('.mp4', '.avi', '.mov', '.html')):
                    archivos_seccion.append({
                        "nombre": archivo,
                        "tipo": "video" if archivo.lower().endswith(('.mp4', '.avi', '.mov')) else "html",
                        "visto": False,
                        "seccion": seccion
                    })

            if archivos_seccion:
                if seccion == '.':
                    seccion = 'Principal'
                archivos[seccion] = sorted(
                    archivos_seccion, key=lambda x: ordenar_clave(x['nombre']))

        # Ordenar las secciones
        archivos_ordenados = dict(
            sorted(archivos.items(), key=lambda x: ordenar_clave(x[0])))
        return archivos_ordenados

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

        # Actualizar el icono y nombre del curso
        curso_data = self.cursos_data[curso_name]
        icon = self.icon_manager.get_icon(curso_data['icon'], size=32)
        self.curso_icon_label.setPixmap(icon.pixmap(32, 32))
        self.curso_name_label.setText(curso_data['name'])
        self.curso_name_label.setStyleSheet("""
            font-size: 18px;
            font-weight: bold;
            qproperty-alignment: AlignLeft | AlignVCenter;
        """)

        # Forzar el layout a actualizarse
        self.curso_info_widget.adjustSize()
        self.curso_info_widget.updateGeometry()

        # Programar el ajuste del título para después de que se haya actualizado el layout
        QTimer.singleShot(0, self.ajustar_titulo_curso)

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

        self.tree_widget.itemSelectionChanged.connect(
            self.on_item_selection_changed)

        # Añade estas líneas al final del método
        curso_data = self.cursos_data[curso_name]
        icon = self.icon_manager.get_icon(curso_data['icon'], size=256)
        self.curso_info_icon.setPixmap(icon.pixmap(256, 256))
        self.curso_info_name.setText(curso_data['name'])
        self.content_area.setCurrentWidget(self.curso_info_widget)
        self.stacked_widget.setCurrentWidget(self.curso_detail_page)
        self.btn_volver_inicio.show()

    def on_item_selection_changed(self):
        for item in self.tree_widget.selectedItems():
            widget = self.tree_widget.itemWidget(item, 0)
            if isinstance(widget, (VideoItemWidget, FileItemWidget)):
                widget.setSelected(True)

        for item in self.tree_widget.findItems("", Qt.MatchContains | Qt.MatchRecursive):
            widget = self.tree_widget.itemWidget(item, 0)
            if isinstance(widget, (VideoItemWidget, FileItemWidget)) and item not in self.tree_widget.selectedItems():
                widget.setSelected(False)

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
        # print(f"No se encontró progreso para {video_path}")
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

        widget = self.tree_widget.itemWidget(item, 0)
        if not isinstance(widget, (VideoItemWidget, FileItemWidget)):
            return

        nombre_archivo = widget.nombre_label.text()
        ruta_curso = self.cursos_data[self.curso_actual]['ruta']
        seccion = item.parent().text(0) if item.parent() else 'Principal'
        ruta_archivo = os.path.join(ruta_curso, seccion, nombre_archivo)

        breadcrumb = self.crear_breadcrumb(
            self.curso_actual, seccion, nombre_archivo)

        # Pausar el video actual si se está reproduciendo
        if self.video_widget.media_player.playbackState() == QMediaPlayer.PlayingState:
            self.video_widget.media_player.pause()

        if os.path.exists(ruta_archivo):
            if ruta_archivo.lower().endswith(('.mp4', '.avi', '.mov')):
                # Cargar el progreso guardado
                progress = self.load_video_progress(
                    self.curso_actual, ruta_archivo)

                if self.video_widget.current_video_path != ruta_archivo:
                    # Si es un video diferente, establecer una nueva fuente
                    self.video_widget.set_source(
                        QUrl.fromLocalFile(ruta_archivo), self.curso_actual)
                    self.content_area.setCurrentWidget(self.video_widget)

                self.actualizar_breadcrumb(breadcrumb)

                # Actualizar la interfaz del reproductor de video
                self.video_widget.update_ui_with_progress(progress)

                # Actualizar el progreso en la barra del VideoItemWidget
                if progress:
                    widget.update_progress(progress.get(
                        "position", 0) / progress.get("duration", 1) * 100)
                else:
                    widget.update_progress(0)

            elif ruta_archivo.lower().endswith('.html'):
                url = QUrl(
                    f"file:///{QDir.fromNativeSeparators(ruta_archivo)}")
                print(f"Cargando archivo: {url}")
                self.web_view.setUrl(url)
                self.content_area.setCurrentWidget(self.web_view)
                self.web_view.setSizePolicy(
                    QSizePolicy.Expanding, QSizePolicy.Expanding)
                self.web_view.setZoomFactor(1.0)

                self.actualizar_breadcrumb(breadcrumb)
            else:
                self.text_browser.setText(
                    f"Archivo no soportado: {ruta_archivo}")
                self.content_area.setCurrentWidget(self.text_browser)

                self.actualizar_breadcrumb(breadcrumb)
        else:
            print(f"El archivo no existe: {ruta_archivo}")
            self.content_area.setCurrentWidget(self.curso_info_widget)

        self.actualizar_breadcrumb(breadcrumb)

    def crear_breadcrumb(self, curso_name, seccion, nombre_archivo):
        if seccion == 'Principal':
            return f"{curso_name} > {nombre_archivo}"
        else:
            return f"{curso_name} > ... > {nombre_archivo}"

    def actualizar_breadcrumb(self, breadcrumb):
        self.breadcrumb_label.setText(breadcrumb)

    def agregar_carpeta(self):
        carpeta = QFileDialog.getExistingDirectory(
            self, "Seleccionar Carpeta de Curso")
        if carpeta:
            nombre_curso = os.path.basename(carpeta)
            if nombre_curso in self.cursos_data:
                QMessageBox.warning(self, "Curso Existente", f"El curso '{
                                    nombre_curso}' ya existe.")
                return

            total_archivos = self.contar_archivos(carpeta)
            self.cursos_data[nombre_curso] = {
                "id": nombre_curso,
                "name": nombre_curso,
                "description": f"Descripción del curso {nombre_curso}",
                "totalArchivos": total_archivos,
                "archivosVistos": 0,
                "icon": "folder/folder-color",
                "archivos": self.obtener_archivos(carpeta),
                "progress": {},
                "ruta": carpeta
            }

            self.guardar_cursos_data()
            self.actualizar_grid_cursos()
            QMessageBox.information(self, "Curso Agregado", f"El curso '{
                                    nombre_curso}' ha sido agregado exitosamente.")

    def resizeEvent(self, event):
        super().resizeEvent(event)
        self.actualizar_grid_cursos()
        self.ajustar_titulo_curso()

    def ajustar_titulo_curso(self):
        if hasattr(self, 'curso_name_label') and self.curso_actual:
            curso_data = self.cursos_data[self.curso_actual]
            nombre_original = curso_data['name']
            available_width = self.curso_info_widget.width() - self.curso_icon_label.width()
            font = self.curso_name_label.font()
            font_metrics = QFontMetrics(font)

            # Comprobar si el texto original cabe en el espacio disponible
            if font_metrics.horizontalAdvance(nombre_original) <= available_width:
                self.curso_name_label.setText(nombre_original)
            else:
                elided_text = font_metrics.elidedText(
                    nombre_original, Qt.ElideRight, available_width)
                self.curso_name_label.setText(elided_text)

    def closeEvent(self, event):
        self.video_widget.save_current_progress()
        super().closeEvent(event)


if __name__ == "__main__":
    import sys
    app = QApplication(sys.argv)
    ventana = CursoTracker()
    ventana.show()
    sys.exit(app.exec())
