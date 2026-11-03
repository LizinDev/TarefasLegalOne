"""Autoteste da barreira de CNJ real (scripts/checar_cnj.py).

Uma checagem que parou de casar qualquer coisa passa por "arvore limpa". Por
isso cada lado tem caso fixo: o que a regra tem que pegar e o que ela tem que
deixar passar, os dois pela mesma funcao que o script usa na arvore.

Os numeros que tem que ser pegos sao montados aqui com o digito calculado, e
nunca escritos por extenso: escritos, o proprio arquivo reprovaria na checagem.
"""
import importlib.util
from pathlib import Path

import pytest

_CAMINHO = Path(__file__).resolve().parent.parent / "scripts" / "checar_cnj.py"
_spec = importlib.util.spec_from_file_location("checar_cnj", _CAMINHO)
checar_cnj = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(checar_cnj)


def valido(n: str, resto: str) -> str:
    """Numero CNJ formatado com o digito verificador certo.

    n: 7 digitos do sequencial; resto: AAAAJTROOOO (11 digitos).
    """
    dv = 98 - int(n + resto + "00") % 97
    return f"{n}-{dv:02d}.{resto[:4]}.{resto[4]}.{resto[5:7]}.{resto[7:]}"


VALIDO_TJBA = valido("0123456", "20258050001")
VALIDO_TJPR = valido("0007777", "20268160188")
VALIDO_TRT = valido("1000123", "20245020001")


def _so_digitos(numero: str) -> str:
    return "".join(c for c in numero if c.isdigit())


@pytest.mark.parametrize("linha", [
    VALIDO_TJBA,
    f"python main.py --processo {VALIDO_TJPR} --executar",
    f'CNJ = "{VALIDO_TRT}"',
    f"`{VALIDO_TJBA}`",
    _so_digitos(VALIDO_TJPR),                         # sem pontuacao
    VALIDO_TJBA.replace("-", ".", 1),                 # o erro de digitacao da planilha
    f"({VALIDO_TRT})",
])
def test_pega_numero_com_digito_valido(linha):
    assert len(checar_cnj.achar(linha)) == 1


def _digito_errado(numero: str) -> str:
    dv = int(numero[8:10])
    return f"{numero[:8]}{(dv + 1) % 100:02d}{numero[10:]}"


@pytest.mark.parametrize("linha", [
    _digito_errado(VALIDO_TJBA),
    "0012345-00.2019.8.05.0001",                      # os sinteticos da suite
    "0000000-00.0000.0.00.0000",
    "1" + _so_digitos(VALIDO_TJPR),                   # dentro de um numero maior
    _so_digitos(VALIDO_TJPR) + "9",
    "versao 1.8.0, 2026-11-03, telefone (71) 3333-4444",
    "0123456-7",
])
def test_deixa_passar_o_que_nao_e_cnj_real(linha):
    assert checar_cnj.achar(linha) == []


def test_permitido_nao_reprova(tmp_path):
    lista = tmp_path / "permitidos.txt"
    lista.write_text(f"# sintetico de proposito\n{VALIDO_TJBA}  # comentario\n")
    permitidos = checar_cnj.carregar_permitidos(lista)

    assert checar_cnj.achar(VALIDO_TJBA, permitidos) == []
    assert checar_cnj.achar(_so_digitos(VALIDO_TJBA), permitidos) == []
    assert len(checar_cnj.achar(VALIDO_TJPR, permitidos)) == 1


def test_relatorio_nao_repete_o_numero():
    mascarado = checar_cnj.mascarar(_so_digitos(VALIDO_TJBA))
    assert mascarado == "*******-**.2025.8.05.****"


def test_arquivo_com_numero_reprova(tmp_path, capsys):
    arquivo = tmp_path / "doc.md"
    arquivo.write_text(f"linha 1\nprocesso {VALIDO_TJPR}\n", encoding="utf-8")

    assert checar_cnj.main([str(arquivo)]) == 1
    saida = capsys.readouterr().out
    assert f"{arquivo}:2:" in saida
    assert VALIDO_TJPR not in saida


def test_nao_ler_nada_e_falha_e_nao_limpo(tmp_path):
    binario = tmp_path / "planilha.xlsx"
    binario.write_bytes(b"PK\x03\x04\x00\x00" + VALIDO_TJBA.encode())

    assert checar_cnj.main([str(binario)]) == 2


def test_arvore_versionada_sem_cnj_real():
    assert checar_cnj.main([]) == 0


# --- valores do local.toml ----------------------------------------------------

def test_valores_locais_pega_host_e_nomes_e_ignora_ficticio_e_curto(tmp_path):
    local = tmp_path / "local.toml"
    exemplo = tmp_path / "local.exemplo.toml"
    local.write_text(
        '[legalone]\nendereco = "https://firma-real.novajus.com.br/"\n'
        '[perfil]\nresponsavel = "Pessoa  Verdadeira"\n'
        '[outro]\nresponsavel = "Ana"\n'
        '[mais]\nresponsavel = "Fulana Regina de Araujo"\n', encoding="utf-8")
    exemplo.write_text('[x]\nresponsavel = "Fulana Regina de Araujo"\n',
                       encoding="utf-8")

    proibidos = checar_cnj.valores_locais(local, exemplo)

    assert proibidos == {"firma-real.novajus.com.br": "legalone.endereco",
                         "pessoa verdadeira": "perfil.responsavel"}


def test_valores_locais_sem_arquivo_nao_proibe_nada(tmp_path):
    assert checar_cnj.valores_locais(tmp_path / "nao.toml", tmp_path / "x") == {}


def test_achar_locais_ignora_caixa():
    proibidos = {"pessoa verdadeira": "perfil.responsavel"}
    texto = "linha 1\nresponsavel = 'PESSOA VERDADEIRA'\n"
    assert checar_cnj.achar_locais(texto, proibidos) == [(2, "perfil.responsavel")]


def test_arquivo_com_valor_local_reprova_sem_repetir_o_valor(tmp_path, monkeypatch,
                                                             capsys):
    monkeypatch.setattr(checar_cnj, "valores_locais",
                        lambda: {"firma-real.novajus.com.br": "legalone.endereco"})
    arquivo = tmp_path / "README.md"
    arquivo.write_text("abra https://firma-real.novajus.com.br/login\n",
                       encoding="utf-8")

    assert checar_cnj.main([str(arquivo)]) == 1
    saida = capsys.readouterr().out
    assert "valor do local.toml (legalone.endereco)" in saida
    assert "firma-real" not in saida
