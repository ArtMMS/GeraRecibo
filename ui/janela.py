from PySide6.QtWidgets import QMainWindow, QVBoxLayout, QWidget


class JanelaPrincipal(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Gerador de Recibos")
        self.setMinimumWidth(480)

        central = QWidget()
        self.layout_principal = QVBoxLayout(central)
        self.setCentralWidget(central)