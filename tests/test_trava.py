"""Trava do Chrome de debug (src/trava.py).

Duas aberturas do mesmo arquivo conflitam mesmo dentro de um processo, no
flock do Linux e no msvcrt do Windows, entao da para testar sem subprocesso.
O Windows esta na matriz da CI: e la que o programa roda.
"""
import subprocess
import sys
from pathlib import Path

import pytest

import trava


def test_segunda_trava_na_mesma_porta_e_recusada_e_diz_o_dono(tmp_path):
    with trava.Trava(9222, "main.py", tmp_path), \
            pytest.raises(trava.ChromeOcupado) as erro:
        trava.Trava(9222, "auditar.py", tmp_path).adquirir()
    assert "main.py, PID" in str(erro.value)
    assert "9222" in str(erro.value)


def test_porta_diferente_nao_conflita(tmp_path):
    with trava.Trava(9222, "main.py", tmp_path), \
            trava.Trava(9223, "outro.py", tmp_path):
        pass


def test_soltar_libera_para_o_proximo(tmp_path):
    primeira = trava.Trava(9222, "main.py", tmp_path).adquirir()
    primeira.soltar()
    trava.Trava(9222, "auditar.py", tmp_path).adquirir().soltar()


def _dono_em_outro_processo(tmp_path, depois: str) -> subprocess.Popen:
    """Outro processo pega a trava, avisa e faz `depois`. Guarda o objeto da
    trava numa variavel: solto, o coletor de lixo fecharia o arquivo e a trava
    sumiria antes da hora."""
    src = str(Path(trava.__file__).parent)
    codigo = (
        "import os, sys; sys.path.insert(0, sys.argv[1]); import trava; "
        "t = trava.Trava(9222, 'outro.py', sys.argv[2]).adquirir(); "
        f"print('ok', flush=True); {depois}"
    )
    filho = subprocess.Popen(
        [sys.executable, "-c", codigo, src, str(tmp_path)],
        stdin=subprocess.PIPE, stdout=subprocess.PIPE, text=True,
    )
    assert filho.stdout.readline().strip() == "ok"
    return filho


def test_outro_processo_vivo_segura_a_trava(tmp_path):
    filho = _dono_em_outro_processo(tmp_path, "sys.stdin.read()")
    try:
        with pytest.raises(trava.ChromeOcupado, match=r"outro\.py, PID"):
            trava.Trava(9222, "main.py", tmp_path).adquirir()
    finally:
        filho.communicate("")
    trava.Trava(9222, "main.py", tmp_path).adquirir().soltar()


def test_processo_que_morre_solta_a_trava(tmp_path):
    # Sem trava velha: o sistema solta quando o dono acaba, mesmo sem soltar()
    # e sem fechar o arquivo (os._exit pula tudo isso).
    filho = _dono_em_outro_processo(tmp_path, "os._exit(0)")
    filho.wait()

    trava.Trava(9222, "main.py", tmp_path).adquirir().soltar()
