from PySide6.QtPdf import QPdfDocument
from PySide6.QtPdfWidgets import QPdfView
from PySide6.QtWidgets import QDialog, QDialogButtonBox, QVBoxLayout


class DialogoPreview(QDialog):
    """Mostra o PDF gerado e pergunta se é para salvar."""

    def __init__(self, caminho_pdf, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Pré-visualizar recibo")
        self.resize(820, 600)

        self.documento = QPdfDocument(self)
        self.documento.load(str(caminho_pdf))

        self.visualizador = QPdfView(self)
        self.visualizador.setDocument(self.documento)
        self.visualizador.setZoomMode(QPdfView.ZoomMode.FitToWidth)

        botoes = QDialogButtonBox()
        botao_salvar = botoes.addButton("Salvar", QDialogButtonBox.ButtonRole.AcceptRole)
        botoes.addButton("Voltar e editar", QDialogButtonBox.ButtonRole.RejectRole)
        botao_salvar.setDefault(True)

        botoes.accepted.connect(self.accept)
        botoes.rejected.connect(self.reject)

        layout = QVBoxLayout(self)
        layout.addWidget(self.visualizador)
        layout.addWidget(botoes)

    def done(self, resultado):
        # Libera o arquivo antes de fechar (o temporário precisa ser apagado depois)
        self.documento.close()
        super().done(resultado)


if __name__ == "__main__":
    # Teste isolado: python -m ui.preview caminho\do\recibo.pdf
    import sys

    from PySide6.QtWidgets import QApplication

    app = QApplication(sys.argv)
    dialogo = DialogoPreview(sys.argv[1])
    print("Salvar" if dialogo.exec() == QDialog.DialogCode.Accepted else "Voltar")