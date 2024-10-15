import os
from PySide6.QtWidgets import QDialog, QVBoxLayout, QHBoxLayout, QPushButton, QScrollArea, QWidget, QGridLayout
from PySide6.QtCore import Qt, Signal
from PySide6.QtGui import QIcon


class IconManager:
    def __init__(self):
        self.icon_dir = "icons"
        self.icons = {}
        self.load_icons()

    def load_icons(self):
        for filename in os.listdir(self.icon_dir):
            if filename.endswith('.svg'):
                name = os.path.splitext(filename)[0]
                self.icons[name] = os.path.join(self.icon_dir, filename)

    def get_icon(self, name, size=50, color='black'):
        if name in self.icons:
            icon = QIcon(self.icons[name])
            return icon
        return QIcon()

    def get_icon_names(self):
        return list(self.icons.keys())


class IconSelectorDialog(QDialog):
    icon_selected = Signal(str)

    def __init__(self, icon_manager, parent=None):
        super().__init__(parent)
        self.icon_manager = icon_manager
        self.setWindowTitle("Seleccionar Icono")
        self.setModal(True)
        self.setup_ui()

    def setup_ui(self):
        layout = QVBoxLayout(self)
        scroll_area = QScrollArea()
        scroll_content = QWidget()
        grid_layout = QGridLayout(scroll_content)

        icons = self.icon_manager.get_icon_names()
        for i, icon_name in enumerate(icons):
            icon = self.icon_manager.get_icon(icon_name, size=50, color='blue')
            button = QPushButton()
            button.setIcon(icon)
            button.setFixedSize(60, 60)
            button.clicked.connect(
                lambda _, name=icon_name: self.on_icon_selected(name))
            grid_layout.addWidget(button, i // 5, i % 5)

        scroll_area.setWidget(scroll_content)
        layout.addWidget(scroll_area)

        button_layout = QHBoxLayout()
        cancel_button = QPushButton("Cancelar")
        cancel_button.clicked.connect(self.reject)
        button_layout.addWidget(cancel_button)
        layout.addLayout(button_layout)

    def on_icon_selected(self, icon_name):
        self.icon_selected.emit(icon_name)
        self.accept()
