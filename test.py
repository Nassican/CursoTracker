import sys
from PySide6.QtWidgets import QApplication, QLabel, QVBoxLayout, QWidget


class MainWindow(QWidget):
    def __init__(self):
        super().__init__()
        layout = QVBoxLayout(self)

        # Crear un QLabel simple
        label = QLabel("Hola, PySide6!")
        layout.addWidget(label)

        self.setLayout(layout)


if __name__ == "__main__":
    try:
        app = QApplication(sys.argv)
        ventana = MainWindow()
        ventana.show()
        sys.exit(app.exec())
    except Exception as e:
        print(f"Error al iniciar la aplicación: {e}")
