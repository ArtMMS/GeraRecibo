from pathlib import Path

from PySide6.QtCore import Qt, Signal
from PySide6.QtGui import QPixmap
from PySide6.QtWidgets import (
    QFileDialog,
    QHBoxLayout,
    QLabel,
    QPushButton,
    QVBoxLayout,
    QWidget,
)

EXTENSOES = {".png", ".jpg", ".jpeg"}

ESTILO_AREA = """
QLabel {
    border: 2px dashed #9a9a9a;
    border-radius: 6px;
    color: #7a7a7a;
}
"""


class AreaLogo(QWidget):
    """Área para escolher a logo: arrastar e soltar ou escolher o arquivo."""

    alterado = Signal(str)  # caminho novo ("" quando removida)

    def __init__(self, parent=None):
        super().__init__(parent)
        self.caminho = ""
        self.setAcceptDrops(True)

        self.area = QLabel()
        self.area.setFixedSize(180, 80)
        self.area.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.area.setStyleSheet(ESTILO_AREA)
        self.area.setCursor(Qt.CursorShape.PointingHandCursor)
        self.area.mousePressEvent = lambda _evento: self._escolher()

        self.botao_escolher = QPushButton("Escolher...")
        self.botao_escolher.clicked.connect(self._escolher)

        self.botao_remover = QPushButton("Remover")
        self.botao_remover.clicked.connect(self.remover)

        botoes = QVBoxLayout()
        botoes.addWidget(self.botao_escolher)
        botoes.addWidget(self.botao_remover)
        botoes.addStretch()

        layout = QHBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.addWidget(self.area)
        layout.addLayout(botoes)
        layout.addStretch()

        self._atualizar()

    # ---------- API ----------

    def definir(self, caminho):
        """Usa a imagem do caminho como logo. Retorna False se não for uma imagem válida."""
        if Path(caminho).suffix.lower() not in EXTENSOES:
            return False
        if QPixmap(caminho).isNull():
            return False

        self.caminho = caminho
        self._atualizar()
        self.alterado.emit(self.caminho)
        return True

    def remover(self):
        self.caminho = ""
        self._atualizar()
        self.alterado.emit(self.caminho)

    # ---------- Interno ----------

    def _escolher(self):
        caminho, _filtro = QFileDialog.getOpenFileName(
            self, "Escolher logo", "", "Imagens (*.png *.jpg *.jpeg)"
        )
        if caminho:
            self.definir(caminho)

    def _atualizar(self):
        if self.caminho:
            pixmap = QPixmap(self.caminho).scaled(
                self.area.width() - 12,
                self.area.height() - 12,
                Qt.AspectRatioMode.KeepAspectRatio,
                Qt.TransformationMode.SmoothTransformation,
            )
            self.area.setPixmap(pixmap)
            self.area.setToolTip(self.caminho)
        else:
            self.area.clear()
            self.area.setText("Arraste uma imagem\nou clique aqui")
            self.area.setToolTip("")

        self.botao_remover.setEnabled(bool(self.caminho))

    @staticmethod
    def _imagem_do_arraste(mime):
        """Primeiro arquivo de imagem válido entre os arrastados (ou None)."""
        if not mime.hasUrls():
            return None
        for url in mime.urls():
            if url.isLocalFile():
                caminho = url.toLocalFile()
                if Path(caminho).suffix.lower() in EXTENSOES:
                    return caminho
        return None

    # ---------- Arrastar e soltar ----------

    def dragEnterEvent(self, evento):
        if self._imagem_do_arraste(evento.mimeData()):
            evento.acceptProposedAction()

    def dropEvent(self, evento):
        caminho = self._imagem_do_arraste(evento.mimeData())
        if caminho and self.definir(caminho):
            evento.acceptProposedAction()


if __name__ == "__main__":
    # Teste isolado: python -m ui.area_logo
    import sys

    from PySide6.QtWidgets import QApplication

    app = QApplication(sys.argv)
    area = AreaLogo()
    area.alterado.connect(lambda caminho: print("Logo:", caminho or "(removida)"))
    area.show()
    sys.exit(app.exec())