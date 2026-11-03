"""Um programa por vez no Chrome de debug.

A rodada, o scripts/auditar.py e qualquer outra automacao que se pendure na
mesma porta de debug trabalham no mesmo navegador. Dois ao mesmo tempo trocam
de aba e de pagina um embaixo do outro: a rodada le a grade que a auditoria
abriu, ou clica num formulario que nao e o dela. A trava nao deixa o segundo
comecar e diz quem esta usando.

A trava e do sistema operacional (flock no Linux, msvcrt.locking no Windows),
presa a um arquivo aberto. Ela se solta sozinha quando o processo termina, ate
morto pelo gerenciador de tarefas, entao nao existe trava velha para apagar
a mao. O arquivo fica no diretorio temporario do usuario, com a porta no nome:
outra automacao que use a mesma porta so precisa travar o mesmo arquivo.
"""
import os
import sys
import tempfile
import time
from pathlib import Path


class ChromeOcupado(RuntimeError):
    """Outro programa ja esta usando o Chrome de debug nesta porta."""


def caminho(porta: int, pasta: str | Path | None = None) -> Path:
    return Path(pasta or tempfile.gettempdir()) / f"chrome-debug-{porta}.lock"


def _travar(arquivo) -> bool:
    try:
        if sys.platform == "win32":
            import msvcrt
            arquivo.seek(0)
            msvcrt.locking(arquivo.fileno(), msvcrt.LK_NBLCK, 1)
        else:
            import fcntl
            fcntl.flock(arquivo.fileno(), fcntl.LOCK_EX | fcntl.LOCK_NB)
    except OSError:
        return False
    return True


def _dono(lock: Path) -> str:
    try:
        return lock.with_suffix(".dono").read_text(encoding="utf-8").strip()
    except OSError:
        return ""


class Trava:
    """Trava exclusiva do Chrome de debug. Segure o objeto enquanto usar o Chrome.

    O byte travado (o primeiro do .lock) e separado do arquivo .dono, que diz
    quem segura: no Windows o trecho travado nao pode ser lido por outro
    processo, entao o recado nao pode morar nele.
    """

    def __init__(self, porta: int, programa: str, pasta: str | Path | None = None):
        self.lock = caminho(porta, pasta)
        self.porta = porta
        self.programa = programa
        self._arquivo = None

    def adquirir(self) -> "Trava":
        self.lock.parent.mkdir(parents=True, exist_ok=True)
        arquivo = open(self.lock, "a+b")  # noqa: SIM115 — fica aberto de proposito
        if not _travar(arquivo):
            arquivo.close()
            dono = _dono(self.lock)
            raise ChromeOcupado(
                f"o Chrome de debug na porta {self.porta} ja esta em uso"
                + (f" ({dono})" if dono else "")
                + ". Espere terminar ou encerre o outro programa."
            )
        self._arquivo = arquivo
        self.lock.with_suffix(".dono").write_text(
            f"{self.programa}, PID {os.getpid()}, desde "
            f"{time.strftime('%d/%m %H:%M')}", encoding="utf-8")
        return self

    def soltar(self) -> None:
        if self._arquivo is not None:
            if sys.platform == "win32":
                # O Windows solta a trava de um arquivo fechado sem dizer
                # quando; soltar antes deixa o proximo entrar na hora.
                import msvcrt
                self._arquivo.seek(0)
                msvcrt.locking(self._arquivo.fileno(), msvcrt.LK_UNLCK, 1)
            self._arquivo.close()
            self._arquivo = None

    def __enter__(self) -> "Trava":
        return self.adquirir()

    def __exit__(self, *_) -> None:
        self.soltar()
