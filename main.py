import sys

from PySide6.QtCore import QLocale
from PySide6.QtWidgets import QApplication

from ui.janela import JanelaPrincipal


def main():
    # Português do Brasil em todo o app (vírgula decimal, calendário em pt-BR)
    QLocale.setDefault(QLocale(QLocale.Language.Portuguese, QLocale.Country.Brazil))

    app = QApplication(sys.argv)
    janela = JanelaPrincipal()
    janela.show()
    sys.exit(app.exec())


if __name__ == "__main__":
    main()