from num2words import num2words

# Palavras que mudam no feminino (ex.: "duas unidades", "duzentas unidades")
FEMININO = {
    "um": "uma",
    "dois": "duas",
    "duzentos": "duzentas",
    "trezentos": "trezentas",
    "quatrocentos": "quatrocentas",
    "quinhentos": "quinhentas",
    "seiscentos": "seiscentas",
    "setecentos": "setecentas",
    "oitocentos": "oitocentas",
    "novecentos": "novecentas",
}


def numero_por_extenso(numero, feminino=False):
    """Ex.: 2 → 'dois' (ou 'duas' no feminino)."""
    texto = num2words(numero, lang="pt_BR")
    if feminino:
        texto = " ".join(FEMININO.get(palavra, palavra) for palavra in texto.split())
    return texto


def valor_por_extenso(valor):
    """Ex.: 300.0 → 'trezentos reais' · 1.5 → 'um real e cinquenta centavos'."""
    total_centavos = round(valor * 100)
    reais, centavos = divmod(total_centavos, 100)

    partes = []

    if reais:
        if reais == 1:
            moeda = "real"
        elif reais % 1_000_000 == 0:
            moeda = "de reais"  # "um milhão de reais"
        else:
            moeda = "reais"
        partes.append(f"{numero_por_extenso(reais)} {moeda}")

    if centavos:
        moeda = "centavo" if centavos == 1 else "centavos"
        partes.append(f"{numero_por_extenso(centavos)} {moeda}")

    return " e ".join(partes) if partes else "zero real"


def quantidade_por_extenso(quantidade):
    """Ex.: 1 → '1 (uma) unidade' · 3 → '3 (três) unidades'."""
    extenso = numero_por_extenso(quantidade, feminino=True)
    unidade = "unidade" if quantidade == 1 else "unidades"
    return f"{quantidade} ({extenso}) {unidade}"


def formatar_moeda(valor):
    """Ex.: 1234.5 → 'R$ 1.234,50'."""
    texto = f"{valor:,.2f}"
    return "R$ " + texto.replace(",", "X").replace(".", ",").replace("X", ".")