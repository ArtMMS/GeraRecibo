# 🧾 GeraRecibo

Em vez de editar o recibo na mão toda vez, você abre uma janela, preenche os
dados do pedido e o programa gera o PDF pronto para imprimir ou enviar pelo
WhatsApp.

---

## ✨ Funcionalidades

- Formulário gráfico (GUI) simples e direto
- Cliente como **pessoa física (CPF)** ou **empresa (CNPJ)**
- Valor em reais com **conversão automática por extenso**
  > Ex.: `R$ 300,00` → *trezentos reais*
- Quantidade de caçambas alugadas
- Endereço com **Cidade** e **Estado**
- Data do pedido (com seletor de calendário)
- Exportação do recibo em **PDF**

---

## 📝 Campos do formulário

| Campo                | Observação                         |
|----------------------|------------------------------------|
| Nome da pessoa       | + CPF                              |
| Nome da empresa      | + CNPJ                             |
| Valor do pedido      | Em R$                              |
| Qtd. de caçambas     | Número inteiro (mínimo 1)          |
| Rua                  |                                    |
| Número               |                                    |
| Bairro               |                                    |
| Cidade               |                                    |
| Estado               |                                    |
| Data do pedido       | Formato `dd/mm/aaaa`               |

---

## 🛠️ Stack

- **Python** 3.11+
- **PySide6** — interface gráfica
- **ReportLab** — geração do PDF
- **num2words** — valor por extenso em português

---

## 🚀 Como rodar

```bash
# 1. Clonar o projeto
git clone <url-do-repositorio>
cd gerador-recibos

# 2. Criar ambiente virtual
python -m venv .venv

# 3. Ativar (Windows)
.venv\Scripts\activate

# 4. Instalar dependências
pip install -r requirements.txt

# 5. Executar
python main.py
```