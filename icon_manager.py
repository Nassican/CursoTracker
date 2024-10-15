import os
from PySide6.QtWidgets import QDialog, QVBoxLayout, QHBoxLayout, QPushButton, QScrollArea, QWidget, QGridLayout, QLineEdit
from PySide6.QtCore import Qt, Signal, QSize
from PySide6.QtGui import QIcon, QPixmap, QPainter
from PySide6.QtSvg import QSvgRenderer


class IconManager:
    def __init__(self):
        self.icon_dir = "icons"
        self.icons = {}
        self.load_icons()

    def load_icons(self):
        for root, dirs, files in os.walk(self.icon_dir):
            for file in files:
                if file.endswith(('.svg', '.png')):
                    full_path = os.path.join(root, file)
                    relative_path = os.path.relpath(full_path, self.icon_dir)
                    name = os.path.splitext(relative_path)[
                        0].replace(os.path.sep, '/')
                    self.icons[name] = full_path

    def get_icon(self, name, size=50):
        if name in self.icons:
            file_path = self.icons[name]
            if file_path.endswith('.svg'):
                try:
                    renderer = QSvgRenderer(file_path)
                    if not renderer.isValid():
                        print(f"Warning: Invalid SVG file: {file_path}")
                        return self.get_fallback_icon(size)
                    pixmap = QPixmap(size, size)
                    pixmap.fill(Qt.transparent)
                    painter = QPainter(pixmap)
                    renderer.render(painter)
                    painter.end()
                    return QIcon(pixmap)
                except Exception as e:
                    print(f"Error rendering SVG file {file_path}: {str(e)}")
                    return self.get_fallback_icon(size)
            else:
                return QIcon(file_path)
        return self.get_fallback_icon(size)

    def get_fallback_icon(self, size):
        pixmap = QPixmap(size, size)
        pixmap.fill(Qt.gray)
        return QIcon(pixmap)

    def get_icon_names(self):
        return list(self.icons.keys())

    def get_categories(self):
        categories = set()
        for name in self.icons.keys():
            parts = name.split('/')
            if len(parts) > 1:
                categories.add(parts[0])
        return list(categories)

    def report_problematic_icons(self):
        problematic_icons = []
        for name, file_path in self.icons.items():
            if file_path.endswith('.svg'):
                try:
                    renderer = QSvgRenderer(file_path)
                    if not renderer.isValid():
                        problematic_icons.append(name)
                except Exception:
                    problematic_icons.append(name)

        if problematic_icons:
            print("The following icons have rendering issues:")
            for icon in problematic_icons:
                print(f" - {icon}")
        else:
            print("No problematic icons found.")


class IconSelectorDialog(QDialog):
    icon_selected = Signal(str)

    def __init__(self, icon_manager, parent=None):
        super().__init__(parent)
        self.icon_manager = icon_manager
        self.setFixedSize(QSize(500, 500))
        self.setWindowTitle("Seleccionar Icono")
        self.setStyleSheet("QWidget { background-color: #f3f4f6; }")
        self.setModal(True)
        self.setup_ui()

    def setup_ui(self):
        layout = QVBoxLayout(self)

        self.search_bar = QLineEdit()
        self.search_bar.setStyleSheet(
            "QLineEdit { font-size: 12px; color: #000000; border: 1px solid #2596be; border-radius: 5px; padding-left: 10px;}")
        self.search_bar.setFixedHeight(30)
        self.search_bar.setPlaceholderText("Buscar icono...")
        self.search_bar.textChanged.connect(self.filter_icons)
        layout.addWidget(self.search_bar)

        self.scroll_area = QScrollArea()
        self.scroll_content = QWidget()
        self.grid_layout = QGridLayout(self.scroll_content)
        self.scroll_area.setWidget(self.scroll_content)
        self.scroll_area.setWidgetResizable(True)
        layout.addWidget(self.scroll_area)

        button_layout = QHBoxLayout()
        cancel_button = QPushButton("Cancelar")
        cancel_button.setStyleSheet("""
            QPushButton { font-size: 14px; color: #ffffff; border: 1px solid #2596be; border-radius: 5px; padding: 5px 10px; background-color: #2596be; font-weight: bold;}
            QPushButton:hover { background-color: #1f78a4; }
            QPushButton:pressed { background-color: #1a628a; }
        """)
        cancel_button.setCursor(Qt.PointingHandCursor)
        cancel_button.clicked.connect(self.reject)
        button_layout.addWidget(cancel_button)
        layout.addLayout(button_layout)

        self.load_all_icons()

    def load_all_icons(self):
        icons = self.icon_manager.get_icon_names()
        for i, icon_name in enumerate(icons):
            icon = self.icon_manager.get_icon(icon_name, size=50)
            button = QPushButton()
            button.setIcon(icon)
            button.setFixedSize(60, 60)
            button.setIconSize(QSize(50, 50))
            button.setToolTip(icon_name)
            button.clicked.connect(
                lambda _, name=icon_name: self.on_icon_selected(name))
            self.grid_layout.addWidget(button, i // 5, i % 5)

    def filter_icons(self):
        search_text = self.search_bar.text().lower()
        visible_widgets = []

        for i in range(self.grid_layout.count()):
            widget = self.grid_layout.itemAt(i).widget()
            if widget:
                icon_name = widget.toolTip().lower()
                is_visible = search_text in icon_name
                widget.setVisible(is_visible)
                if is_visible:
                    visible_widgets.append(widget)

        # Reorganizar los widgets visibles
        for i, widget in enumerate(visible_widgets):
            self.grid_layout.removeWidget(widget)
            self.grid_layout.addWidget(widget, i // 5, i % 5)

        self.scroll_content.adjustSize()
        self.scroll_area.setWidgetResizable(True)

    def on_icon_selected(self, icon_name):
        self.icon_selected.emit(icon_name)
        self.accept()
