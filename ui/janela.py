from PySide6.QtCore import QDate
from PySide6.QtWidgets import (
    QComboBox,
    QDateEdit,
    QDoubleSpinBox,
    QFormLayout,
    QGroupBox,
    QHBoxLayout,
    QLabel,
    QLineEdit,
    QMainWindow,
    QMessageBox,
    QPushButton,
    QSpinBox,
    QVBoxLayout,
    QWidget,
)

CIDADE_PADRAO = "São Gonçalo"
ESTADO_PADRAO = "RJ"


class JanelaPrincipal(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Gerador de Recibos")
        self.setMinimumWidth(480)

        central = QWidget()
        self.layout_principal = QVBoxLayout(central)
        self.setCentralWidget(central)

        self.layout_principal.addWidget(self._criar_grupo_cliente())
        self.layout_principal.addWidget(self._criar_grupo_pedido())
        self.layout_principal.addWidget(self._criar_grupo_endereco())
        self.layout_principal.addStretch()
        self.layout_principal.addLayout(self._criar_botoes())

    # ---------- Grupos do formulário ----------

    def _criar_grupo_cliente(self):
        grupo = QGroupBox("Cliente")
        form = QFormLayout(grupo)

        self.combo_tipo = QComboBox()
        self.combo_tipo.addItems(["Pessoa física (CPF)", "Empresa (CNPJ)"])
        self.combo_tipo.currentIndexChanged.connect(self._ao_mudar_tipo)

        self.label_nome = QLabel()
        self.input_nome = QLineEdit()

        self.label_documento = QLabel()
        self.input_documento = QLineEdit()

        form.addRow("Tipo de cliente:", self.combo_tipo)
        form.addRow(self.label_nome, self.input_nome)
        form.addRow(self.label_documento, self.input_documento)

        self._ao_mudar_tipo(0)
        return grupo

    def _criar_grupo_pedido(self):
        grupo = QGroupBox("Pedido")
        form = QFormLayout(grupo)

        self.input_produto = QLineEdit()

        self.input_qtd = QSpinBox()
        self.input_qtd.setRange(1, 9999)

        self.input_valor = QDoubleSpinBox()
        self.input_valor.setPrefix("R$ ")
        self.input_valor.setDecimals(2)
        self.input_valor.setRange(0, 1_000_000)
        self.input_valor.setSingleStep(50)

        self.input_data = QDateEdit(QDate.currentDate())
        self.input_data.setCalendarPopup(True)
        self.input_data.setDisplayFormat("dd/MM/yyyy")

        form.addRow("Produto vendido:", self.input_produto)
        form.addRow("Qtd. de produto:", self.input_qtd)
        form.addRow("Valor do pedido:", self.input_valor)
        form.addRow("Data do pedido:", self.input_data)
        return grupo

    def _criar_grupo_endereco(self):
        grupo = QGroupBox("Endereço")
        form = QFormLayout(grupo)

        self.input_rua = QLineEdit()

        self.input_numero = QLineEdit()
        self.input_numero.setMaximumWidth(100)

        self.input_bairro = QLineEdit()

        self.input_cidade = QLineEdit(CIDADE_PADRAO)
        self.input_cidade.setReadOnly(True)

        self.input_estado = QLineEdit(ESTADO_PADRAO)
        self.input_estado.setReadOnly(True)
        self.input_estado.setMaximumWidth(60)

        form.addRow("Rua:", self.input_rua)
        form.addRow("Número:", self.input_numero)
        form.addRow("Bairro:", self.input_bairro)
        form.addRow("Cidade:", self.input_cidade)
        form.addRow("Estado:", self.input_estado)
        return grupo

    def _criar_botoes(self):
        layout = QHBoxLayout()

        self.botao_limpar = QPushButton("Limpar")
        self.botao_limpar.clicked.connect(self._limpar)

        self.botao_gerar = QPushButton("Gerar PDF")
        self.botao_gerar.setDefault(True)
        self.botao_gerar.clicked.connect(self._gerar_pdf)

        layout.addStretch()
        layout.addWidget(self.botao_limpar)
        layout.addWidget(self.botao_gerar)
        return layout

    # ---------- Comportamento ----------

    def _ao_mudar_tipo(self, indice):
        if indice == 0:
            self.label_nome.setText("Nome:")
            self.label_documento.setText("CPF:")
            self.input_documento.setPlaceholderText("000.000.000-00")
        else:
            self.label_nome.setText("Razão social:")
            self.label_documento.setText("CNPJ:")
            self.input_documento.setPlaceholderText("00.000.000/0000-00")

    def _coletar_dados(self):
        """Junta tudo o que foi preenchido em um dicionário."""
        return {
            "tipo": "CPF" if self.combo_tipo.currentIndex() == 0 else "CNPJ",
            "nome": self.input_nome.text().strip(),
            "documento": self.input_documento.text().strip(),
            "produto": self.input_produto.text().strip(),
            "quantidade": self.input_qtd.value(),
            "valor": self.input_valor.value(),
            "data": self.input_data.date().toString("dd/MM/yyyy"),
            "rua": self.input_rua.text().strip(),
            "numero": self.input_numero.text().strip(),
            "bairro": self.input_bairro.text().strip(),
            "cidade": self.input_cidade.text(),
            "estado": self.input_estado.text(),
        }

    def _gerar_pdf(self):
        dados = self._coletar_dados()
        print(dados)  # Provisório: a geração real do PDF entra na Fase 3

        QMessageBox.information(
            self,
            "Gerar PDF",
            "Dados coletados! (veja no terminal)\n\n"
            "A geração do PDF será feita na Fase 3.",
        )

    def _limpar(self):
        self.combo_tipo.setCurrentIndex(0)
        self.input_nome.clear()
        self.input_documento.clear()
        self.input_produto.clear()
        self.input_qtd.setValue(1)
        self.input_valor.setValue(0)
        self.input_data.setDate(QDate.currentDate())
        self.input_rua.clear()
        self.input_numero.clear()
        self.input_bairro.clear()
        self.input_nome.setFocus()