import ctypes
import sys
from pathlib import Path

from PySide6.QtCore import QLocale, Qt
from PySide6.QtGui import QIcon
from PySide6.QtWidgets import QApplication

from ui.janela import JanelaPrincipal

APP_ID = "geradorrecibos.app.1"


def caminho_recurso(relativo):
    """Caminho de um arquivo do projeto, funcionando no Python e no .exe (PyInstaller)."""
    base = Path(getattr(sys, "_MEIPASS", Path(__file__).resolve().parent))
    return str(base / relativo)


def main():
    # Faz o Windows usar o ícone do app na barra de tarefas (e não o do Python)
    if sys.platform == "win32":
        ctypes.windll.shell32.SetCurrentProcessExplicitAppUserModelID(APP_ID)

    # Português do Brasil em todo o app (vírgula decimal, calendário em pt-BR)
    QLocale.setDefault(QLocale(QLocale.Language.Portuguese, QLocale.Country.Brazil))

    app = QApplication(sys.argv)
    app.setWindowIcon(QIcon(caminho_recurso("assets/icon.ico")))

    janela = JanelaPrincipal()

    # Tamanho fixo: sem maximizar/tela cheia e sem redimensionar
    janela.setWindowFlag(Qt.WindowType.WindowMaximizeButtonHint, False)
    janela.adjustSize()
    janela.setFixedSize(janela.size())

    janela.show()
    sys.exit(app.exec())


if __name__ == "__main__":
    main()