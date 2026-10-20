from dataclasses import dataclass
from datetime import date

from core.extenso import formatar_moeda, quantidade_por_extenso, valor_por_extenso


@dataclass
class Recibo:
    tipo_documento: str  # "CPF" ou "CNPJ"
    nome: str
    documento: str
    produto: str
    quantidade: int
    valor: float
    data: date
    rua: str
    numero: str
    bairro: str
    cidade: str
    estado: str

    @property
    def valor_formatado(self):
        return formatar_moeda(self.valor)

    @property
    def data_formatada(self):
        return self.data.strftime("%d/%m/%Y")

    @property
    def endereco(self):
        return f"{self.rua}, nº {self.numero}, {self.bairro}, {self.cidade}, {self.estado}"

    def texto(self):
        """Parágrafo principal do recibo."""
        return (
            f"Recebi de {self.nome}, portador do {self.tipo_documento} {self.documento}, "
            f"a quantia de {valor_por_extenso(self.valor)}, "
            f"correspondente a {quantidade_por_extenso(self.quantidade)} de {self.produto}, "
            f"no endereço {self.endereco}, "
            f"e para clareza firmo o presente."
        )

    def local_e_data(self):
        return f"{self.cidade}, {self.data_formatada}."