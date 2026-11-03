"""Barra numero CNJ real em arquivo versionado.

Em 23/10/2026 o repositorio estava publico com 4 numeros de processo reais no
README, no MANUAL e nos testes. Um numero CNJ inventado quase nunca tem o digito
verificador certo (1 chance em 97), entao "digito confere" e o sinal de que o
numero foi copiado de um processo de verdade. Este script procura esses numeros
e falha se achar algum que nao esteja em cnj_permitidos.txt.

    python scripts/checar_cnj.py              # arquivos versionados (git ls-files)
    python scripts/checar_cnj.py --staged     # o que vai no proximo commit
    python scripts/checar_cnj.py ARQ [ARQ...] # arquivos soltos

Saida: 0 limpo, 1 achou numero, 2 nao conseguiu conferir nada. Nao ter lido
arquivo nenhum e falha, e nao "limpo": uma checagem que nao olhou nada passaria
por aprovada.

O numero achado sai mascarado no relatorio (so ano, segmento e tribunal), porque
a saida da CI vira log e o log fica publico junto com o repositorio.
"""
import argparse
import re
import subprocess
import sys
from pathlib import Path

RAIZ = Path(__file__).resolve().parent.parent
PERMITIDOS = Path(__file__).resolve().parent / "cnj_permitidos.txt"

# NNNNNNN-DD.AAAA.J.TR.OOOO, com ou sem a pontuacao (a planilha e o Legal One
# trazem das duas formas). Os lookarounds impedem casar 20 digitos no meio de
# um numero maior.
PADRAO = re.compile(
    r"(?<!\d)(\d{7})[-.]?(\d{2})\.?(\d{4})\.?(\d)\.?(\d{2})\.?(\d{4})(?![\d])"
)


def digito_confere(digitos: str) -> bool:
    """Digito verificador da Res. CNJ 65/2008 (ISO 7064, modulo 97).

    digitos: os 20 digitos na ordem do numero (NNNNNNN DD AAAA J TR OOOO).
    Com o DD levado para o fim, o numero inteiro da resto 1 por 97.
    """
    n, dd, resto = digitos[:7], digitos[7:9], digitos[9:]
    return int(n + resto + dd) % 97 == 1


def mascarar(digitos: str) -> str:
    return f"*******-**.{digitos[9:13]}.{digitos[13]}.{digitos[14:16]}.****"


def carregar_permitidos(caminho: Path = PERMITIDOS) -> set[str]:
    """Numeros sinteticos aceitos de proposito, um por linha (# comenta)."""
    if not caminho.exists():
        return set()
    permitidos = set()
    for linha in caminho.read_text(encoding="utf-8").splitlines():
        linha = linha.split("#", 1)[0].strip()
        if linha:
            permitidos.add(re.sub(r"\D", "", linha))
    return permitidos


def achar(texto: str, permitidos: set[str] = frozenset()) -> list[tuple[int, str]]:
    """(numero da linha, 20 digitos) de cada CNJ com digito valido no texto."""
    achados = []
    for numero_linha, linha in enumerate(texto.splitlines(), start=1):
        for m in PADRAO.finditer(linha):
            digitos = "".join(m.groups())
            if digito_confere(digitos) and digitos not in permitidos:
                achados.append((numero_linha, digitos))
    return achados


def _git(*args: str) -> bytes:
    return subprocess.run(
        ["git", *args], cwd=RAIZ, check=True, capture_output=True
    ).stdout


def _fontes(staged: bool, arquivos: list[str]):
    """(nome, bytes) de cada arquivo a conferir."""
    if arquivos:
        for nome in arquivos:
            yield nome, Path(nome).read_bytes()
        return
    if staged:
        nomes = _git("diff", "--cached", "--name-only", "--diff-filter=ACMR", "-z")
        for nome in filter(None, nomes.decode().split("\0")):
            yield nome, _git("show", f":{nome}")
        return
    for nome in filter(None, _git("ls-files", "-z").decode().split("\0")):
        caminho = RAIZ / nome
        if caminho.is_file():
            yield nome, caminho.read_bytes()


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("--staged", action="store_true",
                        help="confere o conteudo preparado para o commit")
    parser.add_argument("arquivos", nargs="*")
    args = parser.parse_args(argv)

    permitidos = carregar_permitidos()
    lidos = 0
    total = 0
    try:
        for nome, conteudo in _fontes(args.staged, args.arquivos):
            if b"\0" in conteudo[:8192]:
                continue  # binario (xlsx, png): nao e texto que se le
            lidos += 1
            texto = conteudo.decode("utf-8", errors="replace")
            for numero_linha, digitos in achar(texto, permitidos):
                total += 1
                print(f"{nome}:{numero_linha}: numero CNJ com digito valido "
                      f"{mascarar(digitos)}")
    except (OSError, subprocess.CalledProcessError) as e:
        print(f"checar_cnj: nao consegui ler os arquivos: {e}", file=sys.stderr)
        return 2

    if args.staged and lidos == 0:
        return 0  # commit sem arquivo de texto: nada a conferir
    if lidos == 0:
        print("checar_cnj: nenhum arquivo conferido", file=sys.stderr)
        return 2
    if total:
        print(f"\n{total} numero(s) CNJ que parecem reais. Troque por um numero "
              "inventado (digito errado) ou, se for sintetico de proposito, "
              f"inclua em {PERMITIDOS.relative_to(RAIZ)}.")
        return 1
    print(f"checar_cnj: {lidos} arquivo(s) conferido(s), nenhum CNJ real")
    return 0


if __name__ == "__main__":
    sys.exit(main())
