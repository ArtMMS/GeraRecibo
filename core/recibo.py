from dataclasses import dataclass
from datetime import date

from core.extenso import formatar_moeda, quantidade_por_extenso, valor_por_extenso


@dataclass
class Recibo:
    # Emitente (quem recebe o pagamento e assina)
    emitente_tipo_documento: str  # "CPF" ou "CNPJ"
    emitente_nome: str
    emitente_documento: str

    # Cliente (quem paga)
    tipo_documento: str  # "CPF" ou "CNPJ"
    nome: str
    documento: str

    # Pedido
    produto: str
    quantidade: int
    valor: float
    data: date

    # Endereço
    rua: str
    numero: str
    bairro: str
    cidade: str
    estado: str

    # Opcional
    emitente_telefones: str = ""

    @property
    def valor_formatado(self):
        return formatar_moeda(self.valor)

    @property
    def data_formatada(self):
        return self.data.strftime("%d/%m/%Y")

    @property
    def endereco(self):
        return f"{self.rua}, nº {self.numero}, {self.bairro}, {self.cidade}, {self.estado}"

    def linhas_do_texto(self):
        """Texto principal do recibo, já dividido em linhas."""
        return [
            f"Recebi de {self.nome}, portador do {self.tipo_documento} {self.documento},",
            f"a quantia de {valor_por_extenso(self.valor)}, "
            f"correspondente a {quantidade_por_extenso(self.quantidade)} de {self.produto}",
            f"no endereço {self.endereco},",
            "e para clareza firmo o presente.",
        ]

    def texto(self):
        return "\n".join(self.linhas_do_texto())

    def local_e_data(self):
        return f"{self.cidade}, {self.data_formatada}."