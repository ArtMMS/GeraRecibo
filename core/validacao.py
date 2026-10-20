import re


def apenas_digitos(texto):
    """Remove tudo que não for número."""
    return re.sub(r"\D", "", texto)


def normalizar_cnpj(texto):
    """Mantém só letras e números, em maiúsculas (aceita CNPJ alfanumérico)."""
    return re.sub(r"[^0-9A-Z]", "", texto.upper())


def validar_cpf(cpf):
    """Valida os dígitos verificadores do CPF."""
    d = apenas_digitos(cpf)

    if len(d) != 11 or d == d[0] * 11:
        return False

    for posicao in (9, 10):
        soma = sum(int(d[i]) * (posicao + 1 - i) for i in range(posicao))
        digito = (soma * 10) % 11 % 10
        if digito != int(d[posicao]):
            return False

    return True


def validar_cnpj(cnpj):
    """Valida os dígitos verificadores do CNPJ (numérico ou alfanumérico)."""
    c = normalizar_cnpj(cnpj)

    if len(c) != 14 or not c[12:].isdigit() or c == c[0] * 14:
        return False

    # Cada caractere vale (código ASCII - 48): '0'-'9' → 0-9, 'A' → 17, 'B' → 18...
    valores = [ord(ch) - 48 for ch in c]

    pesos_1 = [5, 4, 3, 2, 9, 8, 7, 6, 5, 4, 3, 2]
    pesos_2 = [6] + pesos_1

    for pesos in (pesos_1, pesos_2):
        posicao = len(pesos)
        soma = sum(valores[i] * pesos[i] for i in range(posicao))
        resto = soma % 11
        digito = 0 if resto < 2 else 11 - resto
        if digito != valores[posicao]:
            return False

    return True