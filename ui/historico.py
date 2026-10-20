from pathlib import Path

from PySide6.QtCore import QDate, Qt, QUrl, Signal
from PySide6.QtGui import QDesktopServices
from PySide6.QtWidgets import (
    QAbstractItemView,
    QCheckBox,
    QDateEdit,
    QDialog,
    QHBoxLayout,
    QHeaderView,
    QLabel,
    QLineEdit,
    QMessageBox,
    QPushButton,
    QTableWidget,
    QTableWidgetItem,
    QVBoxLayout,
)

from core import banco

COLUNAS = ["Nº", "Data", "Cliente", "CPF/CNPJ", "Produto", "Qtd.", "Valor"]
COLUNAS_A_DIREITA = {0, 5, 6}
COLUNAS_ESTICADAS = {2, 4}


class DialogoHistorico(QDialog):
    """Lista os recibos salvos, com busca, abrir PDF e reemitir."""

    reemitir = Signal(int)  # número do recibo

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Histórico de recibos")
        self.resize(900, 520)

        self._caminhos = {}

        # ---------- Filtros ----------

        self.input_busca = QLineEdit()
        self.input_busca.textChanged.connect(self.atualizar)

        hoje = QDate.currentDate()
        self.check_periodo = QCheckBox("Período:")
        self.data_de = self._criar_data(hoje.addMonths(-1))
        self.data_ate = self._criar_data(hoje)
        self.data_de.setEnabled(False)
        self.data_ate.setEnabled(False)
        self.check_periodo.toggled.connect(self._ao_marcar_periodo)

        filtros = QHBoxLayout()
        filtros.addWidget(QLabel("Cliente ou CPF/CNPJ:"))
        filtros.addWidget(self.input_busca, 1)
        filtros.addSpacing(16)
        filtros.addWidget(self.check_periodo)
        filtros.addWidget(self.data_de)
        filtros.addWidget(QLabel("até"))
        filtros.addWidget(self.data_ate)

        # ---------- Tabela ----------

        self.tabela = QTableWidget(0, len(COLUNAS))
        self.tabela.setHorizontalHeaderLabels(COLUNAS)
        self.tabela.setEditTriggers(QAbstractItemView.EditTrigger.NoEditTriggers)
        self.tabela.setSelectionBehavior(QAbstractItemView.SelectionBehavior.SelectRows)
        self.tabela.setSelectionMode(QAbstractItemView.SelectionMode.SingleSelection)
        self.tabela.setAlternatingRowColors(True)
        self.tabela.verticalHeader().setVisible(False)

        cabecalho = self.tabela.horizontalHeader()
        cabecalho.setSectionResizeMode(QHeaderView.ResizeMode.ResizeToContents)
        for coluna in COLUNAS_ESTICADAS:
            cabecalho.setSectionResizeMode(coluna, QHeaderView.ResizeMode.Stretch)

        self.tabela.cellDoubleClicked.connect(lambda *_: self._abrir_pdf())
        self.tabela.itemSelectionChanged.connect(self._atualizar_botoes)

        # ---------- Rodapé ----------

        self.label_total = QLabel()

        self.botao_abrir = QPushButton("Abrir PDF")
        self.botao_abrir.clicked.connect(self._abrir_pdf)

        self.botao_reemitir = QPushButton("Reemitir")
        self.botao_reemitir.clicked.connect(self._reemitir)

        botao_fechar = QPushButton("Fechar")
        botao_fechar.clicked.connect(self.reject)

        rodape = QHBoxLayout()
        rodape.addWidget(self.label_total)
        rodape.addStretch()
        rodape.addWidget(self.botao_abrir)
        rodape.addWidget(self.botao_reemitir)
        rodape.addWidget(botao_fechar)

        layout = QVBoxLayout(self)
        layout.addLayout(filtros)
        layout.addWidget(self.tabela)
        layout.addLayout(rodape)

        self.atualizar()

    # ---------- Montagem ----------

    def _criar_data(self, data):
        campo = QDateEdit(data)
        campo.setCalendarPopup(True)
        campo.setDisplayFormat("dd/MM/yyyy")
        campo.dateChanged.connect(self.atualizar)
        return campo

    def _ao_marcar_periodo(self, ativo):
        self.data_de.setEnabled(ativo)
        self.data_ate.setEnabled(ativo)
        self.atualizar()

    # ---------- Dados ----------

    def atualizar(self):
        """Refaz a busca com os filtros atuais."""
        texto = self.input_busca.text().strip()

        inicio = fim = None
        if self.check_periodo.isChecked():
            inicio = self.data_de.date().toPython()
            fim = self.data_ate.date().toPython()

        resultados = banco.buscar(texto, inicio, fim)

        self.tabela.setRowCount(0)
        self._caminhos.clear()

        for linha, (recibo, caminho) in enumerate(resultados):
            self.tabela.insertRow(linha)

            valores = [
                recibo.numero_formatado,
                recibo.data_formatada,
                recibo.nome,
                recibo.documento,
                recibo.produto,
                str(recibo.quantidade),
                recibo.valor_formatado,
            ]

            for coluna, valor in enumerate(valores):
                item = QTableWidgetItem(valor)
                item.setData(Qt.ItemDataRole.UserRole, recibo.numero_recibo)
                if coluna in COLUNAS_A_DIREITA:
                    item.setTextAlignment(
                        Qt.AlignmentFlag.AlignRight | Qt.AlignmentFlag.AlignVCenter
                    )
                self.tabela.setItem(linha, coluna, item)

            self._caminhos[recibo.numero_recibo] = caminho

        total = len(resultados)
        self.label_total.setText(f"{total} recibo{'s' if total != 1 else ''}")
        self._atualizar_botoes()

    def _numero_selecionado(self):
        itens = self.tabela.selectedItems()
        return itens[0].data(Qt.ItemDataRole.UserRole) if itens else None

    def _atualizar_botoes(self):
        tem_selecao = self._numero_selecionado() is not None
        self.botao_abrir.setEnabled(tem_selecao)
        self.botao_reemitir.setEnabled(tem_selecao)

    # ---------- Ações ----------

    def _abrir_pdf(self):
        numero = self._numero_selecionado()
        if numero is None:
            return

        caminho = self._caminhos.get(numero, "")
        if not caminho or not Path(caminho).is_file():
            QMessageBox.warning(
                self,
                "PDF não encontrado",
                "O arquivo deste recibo não foi encontrado.\n\n"
                "Ele pode ter sido movido ou apagado. "
                "Use 'Reemitir' para gerar o PDF de novo.",
            )
            return

        QDesktopServices.openUrl(QUrl.fromLocalFile(caminho))

    def _reemitir(self):
        numero = self._numero_selecionado()
        if numero is not None:
            self.reemitir.emit(numero)


if __name__ == "__main__":
    # Teste isolado: python -m ui.historico
    import sys

    from PySide6.QtWidgets import QApplication

    app = QApplication(sys.argv)
    dialogo = DialogoHistorico()
    dialogo.reemitir.connect(lambda numero: print("Reemitir recibo", numero))
    dialogo.exec()