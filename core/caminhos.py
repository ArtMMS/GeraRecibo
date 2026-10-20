import sys
from pathlib import Path


def pasta_base():
    """Pasta do app: ao lado do .exe (empacotado) ou raiz do projeto."""
    if getattr(sys, "frozen", False):
        return Path(sys.executable).parent
    return Path(__file__).resolve().parent.parent


def pasta(nome):
    """Subpasta do app (criada se não existir). Ex.: pasta('dados')."""
    caminho = pasta_base() / nome
    caminho.mkdir(parents=True, exist_ok=True)
    return caminho