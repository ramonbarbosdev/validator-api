"""Leitura do diff: linhas adicionadas e arquivos novos/alterados em origin/<base>...HEAD."""
import re
import subprocess

HUNK = re.compile(r"^@@ -\d+(?:,\d+)? \+(\d+)(?:,(\d+))? @@")


def _git(repo, *args):
    return subprocess.run(
        ["git", "-C", str(repo), "-c", "core.quotepath=false", *args],
        capture_output=True, text=True, encoding="utf-8", check=True,
    ).stdout


def linhas_adicionadas(base, repo="."):
    """Retorna {arquivo: {numeros das linhas adicionadas}}."""
    saida = _git(repo, "diff", "-U0", "--no-color", f"origin/{base}...HEAD")
    res, arq, n = {}, None, 0
    for linha in saida.splitlines():
        if linha.startswith("+++ "):
            alvo = linha[4:].rstrip("\t")
            arq = None if alvo == "/dev/null" else alvo[2:]
            if arq:
                res.setdefault(arq, set())
        elif linha.startswith("@@"):
            m = HUNK.match(linha)
            if m:
                n = int(m.group(1))
        elif arq and linha.startswith("+") and not linha.startswith("+++"):
            res[arq].add(n)
            n += 1
    return res


def arquivos_por_status(base, repo="."):
    """Retorna {"novos": set, "alterados": set}; alterados inclui os novos e os renomeados."""
    saida = _git(repo, "diff", "--name-status", "--no-color", "-M", f"origin/{base}...HEAD")
    novos, alterados = set(), set()
    for linha in saida.splitlines():
        partes = linha.split("\t")
        status, caminho = partes[0][:1], partes[-1]
        if status == "D":
            continue
        alterados.add(caminho)
        if status == "A":
            novos.add(caminho)
    return {"novos": novos, "alterados": alterados}
