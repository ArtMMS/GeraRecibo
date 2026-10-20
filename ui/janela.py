import shutil
import tempfile
from pathlib import Path

from PySide6.QtCore import QDate, QUrl
from PySide6.QtGui import QDesktopServices
from PySide6.QtWidgets import (
    QCheckBox,
    QComboBox,
    QDateEdit,
    QDialog,
    QDoubleSpinBox,
    QFileDialog,
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

from core.pdf import caminho_disponivel, gerar_pdf, pasta_recibos
from core.recibo import Recibo
from core.validacao import validar_cnpj, validar_cpf
from ui.area_logo import AreaLogo
from ui.preview import DialogoPreview

MASCARA_CPF = "000.000.000-00;_"
MASCARA_CNPJ = ">NN.NNN.NNN/NNNN-00;_"  # N = letra ou número (CNPJ alfanumérico)

TIPOS_DOCUMENTO = ["Pessoa física (CPF)", "Empresa (CNPJ)"]

ESTILO_ERRO = "border: 1px solid #d9534f; border-radius: 3px;"


class JanelaPrincipal(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Gerador de Recibos")
        self.setMinimumWidth(480)

        self.pasta_destino = pasta_recibos()

        central = QWidget()
        self.layout_principal = QVBoxLayout(central)
        self.setCentralWidget(central)

        self.layout_principal.addWidget(self._criar_grupo_emitente())
        self.layout_principal.addWidget(self._criar_grupo_cliente())
        self.layout_principal.addWidget(self._criar_grupo_pedido())
        self.layout_principal.addWidget(self._criar_grupo_endereco())
        self.layout_principal.addWidget(self._criar_grupo_arquivo())
        self.layout_principal.addStretch()
        self.layout_principal.addLayout(self._criar_botoes())

        self._conectar_limpeza_de_erros()

    # ---------- Grupos do formulário ----------

    def _criar_grupo_emitente(self):
        grupo = QGroupBox("Emitente (quem recebe)")
        form = QFormLayout(grupo)

        self.combo_tipo_emitente = QComboBox()
        self.combo_tipo_emitente.addItems(TIPOS_DOCUMENTO)

        self.label_nome_emitente = QLabel()
        self.input_nome_emitente = QLineEdit()

        self.label_documento_emitente = QLabel()
        self.input_documento_emitente = QLineEdit()

        self.input_telefones = QLineEdit()

        self.area_logo = AreaLogo()

        self.combo_tipo_emitente.currentIndexChanged.connect(
            lambda indice: self._aplicar_tipo(
                indice,
                self.label_nome_emitente,
                self.label_documento_emitente,
                self.input_documento_emitente,
            )
        )

        form.addRow("Tipo:", self.combo_tipo_emitente)
        form.addRow(self.label_nome_emitente, self.input_nome_emitente)
        form.addRow(self.label_documento_emitente, self.input_documento_emitente)
        form.addRow("Telefones (opcional):", self.input_telefones)
        form.addRow("Logo (opcional):", self.area_logo)

        self._aplicar_tipo(
            0, self.label_nome_emitente, self.label_documento_emitente, self.input_documento_emitente
        )
        return grupo

    def _criar_grupo_cliente(self):
        grupo = QGroupBox("Cliente (quem paga)")
        form = QFormLayout(grupo)

        self.combo_tipo = QComboBox()
        self.combo_tipo.addItems(TIPOS_DOCUMENTO)

        self.label_nome = QLabel()
        self.input_nome = QLineEdit()

        self.label_documento = QLabel()
        self.input_documento = QLineEdit()

        self.combo_tipo.currentIndexChanged.connect(
            lambda indice: self._aplicar_tipo(
                indice, self.label_nome, self.label_documento, self.input_documento
            )
        )

        form.addRow("Tipo:", self.combo_tipo)
        form.addRow(self.label_nome, self.input_nome)
        form.addRow(self.label_documento, self.input_documento)

        self._aplicar_tipo(0, self.label_nome, self.label_documento, self.input_documento)
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
        self.input_cidade = QLineEdit()

        self.input_estado = QLineEdit()
        self.input_estado.setMaximumWidth(100)

        form.addRow("Rua:", self.input_rua)
        form.addRow("Número:", self.input_numero)
        form.addRow("Bairro:", self.input_bairro)
        form.addRow("Cidade:", self.input_cidade)
        form.addRow("Estado:", self.input_estado)
        return grupo

    def _criar_grupo_arquivo(self):
        grupo = QGroupBox("Arquivo")
        form = QFormLayout(grupo)

        self.input_pasta = QLineEdit()
        self.input_pasta.setReadOnly(True)

        self.botao_pasta = QPushButton("Alterar...")
        self.botao_pasta.clicked.connect(self._escolher_pasta)

        linha_pasta = QHBoxLayout()
        linha_pasta.addWidget(self.input_pasta)
        linha_pasta.addWidget(self.botao_pasta)

        self.check_abrir = QCheckBox("Abrir o PDF depois de salvar")
        self.check_abrir.setChecked(True)

        form.addRow("Salvar em:", linha_pasta)
        form.addRow("", self.check_abrir)

        self._mostrar_pasta()
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

    # ---------- Listas de campos ----------

    def _campos_emitente(self):
        return [
            self.input_nome_emitente,
            self.input_documento_emitente,
            self.input_telefones,
        ]

    def _campos_do_recibo(self):
        """Campos que mudam a cada recibo (são apagados pelo botão Limpar)."""
        return [
            self.input_nome,
            self.input_documento,
            self.input_produto,
            self.input_rua,
            self.input_numero,
            self.input_bairro,
            self.input_cidade,
            self.input_estado,
        ]

    def _campos_de_texto(self):
        return self._campos_emitente() + self._campos_do_recibo()

    def _campos_validados(self):
        return self._campos_de_texto() + [self.input_valor]

    # ---------- Destaque de erros ----------

    def _marcar_erro(self, campo, erro):
        campo.setStyleSheet(ESTILO_ERRO if erro else "")

    def _conectar_limpeza_de_erros(self):
        """Tira o destaque vermelho assim que o usuário mexe no campo."""
        for campo in self._campos_de_texto():
            campo.textChanged.connect(lambda _texto, c=campo: self._marcar_erro(c, False))

        self.input_valor.valueChanged.connect(
            lambda _valor: self._marcar_erro(self.input_valor, False)
        )

    # ---------- Validação ----------

    def _validar_documento(self, campo, pessoa_fisica, contexto, erros):
        """Confere CPF/CNPJ de um campo e adiciona os erros na lista."""
        rotulo = "CPF" if pessoa_fisica else "CNPJ"
        documento = campo.text()
        preenchido = any(ch.isalnum() for ch in documento)

        if not preenchido:
            erros.append(f"Preencha o {rotulo} {contexto}.")
            self._marcar_erro(campo, True)
        elif not campo.hasAcceptableInput():
            erros.append(f"{rotulo} {contexto} incompleto.")
            self._marcar_erro(campo, True)
        else:
            valido = validar_cpf(documento) if pessoa_fisica else validar_cnpj(documento)
            self._marcar_erro(campo, not valido)
            if not valido:
                erros.append(f"{rotulo} {contexto} inválido. Confira o que foi digitado.")

    def _validar(self):
        """Confere o formulário. Retorna a lista de erros (vazia = tudo certo)."""
        erros = []
        emitente_pf = self.combo_tipo_emitente.currentIndex() == 0
        cliente_pf = self.combo_tipo.currentIndex() == 0

        # Campos de texto obrigatórios
        obrigatorios = [
            (self.input_nome_emitente, "Nome do emitente" if emitente_pf else "Razão social do emitente"),
            (self.input_nome, "Nome do cliente" if cliente_pf else "Razão social do cliente"),
            (self.input_produto, "Produto vendido"),
            (self.input_rua, "Rua"),
            (self.input_numero, "Número"),
            (self.input_bairro, "Bairro"),
            (self.input_cidade, "Cidade"),
            (self.input_estado, "Estado"),
        ]
        for campo, rotulo in obrigatorios:
            vazio = not campo.text().strip()
            self._marcar_erro(campo, vazio)
            if vazio:
                erros.append(f"Preencha o campo {rotulo}.")

        # CPF / CNPJ
        self._validar_documento(self.input_documento_emitente, emitente_pf, "do emitente", erros)
        self._validar_documento(self.input_documento, cliente_pf, "do cliente", erros)

        # Valor
        valor_ok = self.input_valor.value() > 0
        self._marcar_erro(self.input_valor, not valor_ok)
        if not valor_ok:
            erros.append("O valor do pedido precisa ser maior que zero.")

        return erros

    # ---------- Comportamento ----------

    def _aplicar_tipo(self, indice, label_nome, label_documento, input_documento):
        """Troca rótulos e máscara entre pessoa física (CPF) e empresa (CNPJ)."""
        if indice == 0:
            label_nome.setText("Nome:")
            label_documento.setText("CPF:")
            input_documento.setInputMask(MASCARA_CPF)
        else:
            label_nome.setText("Razão social:")
            label_documento.setText("CNPJ:")
            input_documento.setInputMask(MASCARA_CNPJ)

        input_documento.clear()

    def _mostrar_pasta(self):
        self.input_pasta.setText(str(self.pasta_destino))
        self.input_pasta.setToolTip(str(self.pasta_destino))
        self.input_pasta.setCursorPosition(0)

    def _escolher_pasta(self):
        pasta = QFileDialog.getExistingDirectory(
            self, "Escolher pasta dos recibos", str(self.pasta_destino)
        )
        if pasta:
            self.pasta_destino = Path(pasta)
            self._mostrar_pasta()

    def _coletar_dados(self):
        """Monta o Recibo com o que foi preenchido no formulário."""
        return Recibo(
            emitente_tipo_documento="CPF" if self.combo_tipo_emitente.currentIndex() == 0 else "CNPJ",
            emitente_nome=self.input_nome_emitente.text().strip(),
            emitente_documento=self.input_documento_emitente.text().strip(),
            emitente_telefones=self.input_telefones.text().strip(),
            emitente_logo=self.area_logo.caminho,
            tipo_documento="CPF" if self.combo_tipo.currentIndex() == 0 else "CNPJ",
            nome=self.input_nome.text().strip(),
            documento=self.input_documento.text().strip(),
            produto=self.input_produto.text().strip(),
            quantidade=self.input_qtd.value(),
            valor=self.input_valor.value(),
            data=self.input_data.date().toPython(),
            rua=self.input_rua.text().strip(),
            numero=self.input_numero.text().strip(),
            bairro=self.input_bairro.text().strip(),
            cidade=self.input_cidade.text().strip(),
            estado=self.input_estado.text().strip(),
        )

    def _gerar_pdf(self):
        erros = self._validar()
        if erros:
            QMessageBox.warning(
                self,
                "Confira os dados",
                "Corrija os campos destacados:\n\n" + "\n".join(f"• {e}" for e in erros),
            )
            return

        recibo = self._coletar_dados()

        with tempfile.TemporaryDirectory(ignore_cleanup_errors=True) as pasta_temp:
            previa = Path(pasta_temp) / "previa.pdf"

            # 1. Gera uma prévia temporária
            try:
                gerar_pdf(recibo, previa)
            except Exception as erro:
                QMessageBox.critical(self, "Erro", f"Não foi possível gerar o PDF.\n\n{erro}")
                return

            # 2. Mostra a prévia
            dialogo = DialogoPreview(previa, self)
            if dialogo.exec() != QDialog.DialogCode.Accepted:
                return

            # 3. Salva na pasta escolhida
            try:
                destino = caminho_disponivel(recibo, self.pasta_destino)
                shutil.copyfile(previa, destino)
            except PermissionError:
                QMessageBox.critical(
                    self,
                    "Erro ao salvar",
                    "Não foi possível salvar o PDF.\n\n"
                    "Verifique se você tem permissão para gravar na pasta escolhida.",
                )
                return
            except OSError as erro:
                QMessageBox.critical(self, "Erro ao salvar", f"Não foi possível salvar o PDF.\n\n{erro}")
                return

        # 4. Abre o PDF ou avisa onde ficou
        if self.check_abrir.isChecked():
            QDesktopServices.openUrl(QUrl.fromLocalFile(str(destino)))
        else:
            QMessageBox.information(
                self,
                "Recibo salvo",
                f"Recibo salvo com sucesso!\n\n{destino}",
            )

    def _limpar(self):
        """Limpa cliente, pedido e endereço. Os dados do emitente (e a logo) são mantidos."""
        self.combo_tipo.setCurrentIndex(0)
        self.input_qtd.setValue(1)
        self.input_valor.setValue(0)
        self.input_data.setDate(QDate.currentDate())

        for campo in self._campos_do_recibo():
            campo.clear()

        for campo in self._campos_validados():
            self._marcar_erro(campo, False)

        self.input_nome.setFocus()