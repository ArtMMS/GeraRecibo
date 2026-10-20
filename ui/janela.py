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

from core.validacao import validar_cnpj, validar_cpf

CIDADE_PADRAO = "São Gonçalo"
ESTADO_PADRAO = "RJ"

MASCARA_CPF = "000.000.000-00;_"
MASCARA_CNPJ = ">NN.NNN.NNN/NNNN-00;_"  # N = letra ou número (CNPJ alfanumérico)

ESTILO_ERRO = "border: 1px solid #d9534f; border-radius: 3px;"


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

        self._conectar_limpeza_de_erros()

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

    # ---------- Destaque de erros ----------

    def _campos_validados(self):
        return [
            self.input_nome,
            self.input_documento,
            self.input_produto,
            self.input_valor,
            self.input_rua,
            self.input_numero,
            self.input_bairro,
        ]

    def _marcar_erro(self, campo, erro):
        campo.setStyleSheet(ESTILO_ERRO if erro else "")

    def _conectar_limpeza_de_erros(self):
        """Tira o destaque vermelho assim que o usuário mexe no campo."""
        for campo in (
            self.input_nome,
            self.input_documento,
            self.input_produto,
            self.input_rua,
            self.input_numero,
            self.input_bairro,
        ):
            campo.textChanged.connect(lambda _texto, c=campo: self._marcar_erro(c, False))

        self.input_valor.valueChanged.connect(
            lambda _valor: self._marcar_erro(self.input_valor, False)
        )

    # ---------- Validação ----------

    def _validar(self):
        """Confere o formulário. Retorna a lista de erros (vazia = tudo certo)."""
        erros = []
        pessoa_fisica = self.combo_tipo.currentIndex() == 0

        # Campos de texto obrigatórios
        obrigatorios = [
            (self.input_nome, "Nome" if pessoa_fisica else "Razão social"),
            (self.input_produto, "Produto vendido"),
            (self.input_rua, "Rua"),
            (self.input_numero, "Número"),
            (self.input_bairro, "Bairro"),
        ]
        for campo, rotulo in obrigatorios:
            vazio = not campo.text().strip()
            self._marcar_erro(campo, vazio)
            if vazio:
                erros.append(f"Preencha o campo {rotulo}.")

        # CPF / CNPJ
        rotulo_doc = "CPF" if pessoa_fisica else "CNPJ"
        documento = self.input_documento.text()
        preenchido = any(ch.isalnum() for ch in documento)

        if not preenchido:
            erros.append(f"Preencha o {rotulo_doc}.")
            self._marcar_erro(self.input_documento, True)
        elif not self.input_documento.hasAcceptableInput():
            erros.append(f"{rotulo_doc} incompleto.")
            self._marcar_erro(self.input_documento, True)
        else:
            valido = validar_cpf(documento) if pessoa_fisica else validar_cnpj(documento)
            self._marcar_erro(self.input_documento, not valido)
            if not valido:
                erros.append(f"{rotulo_doc} inválido. Confira o que foi digitado.")

        # Valor
        valor_ok = self.input_valor.value() > 0
        self._marcar_erro(self.input_valor, not valor_ok)
        if not valor_ok:
            erros.append("O valor do pedido precisa ser maior que zero.")

        return erros

    # ---------- Comportamento ----------

    def _ao_mudar_tipo(self, indice):
        if indice == 0:
            self.label_nome.setText("Nome:")
            self.label_documento.setText("CPF:")
            self.input_documento.setInputMask(MASCARA_CPF)
        else:
            self.label_nome.setText("Razão social:")
            self.label_documento.setText("CNPJ:")
            self.input_documento.setInputMask(MASCARA_CNPJ)

        self.input_documento.clear()

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
        erros = self._validar()
        if erros:
            QMessageBox.warning(
                self,
                "Confira os dados",
                "Corrija os campos destacados:\n\n" + "\n".join(f"• {e}" for e in erros),
            )
            return

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

        for campo in self._campos_validados():
            self._marcar_erro(campo, False)

        self.input_nome.setFocus()