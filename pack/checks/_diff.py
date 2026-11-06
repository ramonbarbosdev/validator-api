"""Utilitarios compartilhados pelos checks: linhas adicionadas no diff e formato de achado."""
import json
import re
import subprocess
import sys

HUNK = re.compile(r"^@@ -\d+(?:,\d+)? \+(\d+)(?:,(\d+))? @@")


def linhas_adicionadas(base, repo="."):
    """Retorna {arquivo: {numeros das linhas adicionadas}} do diff origin/<base>...HEAD."""
    saida = subprocess.run(
        ["git", "-C", repo, "diff", "-U0", "--no-color", f"origin/{base}...HEAD"],
        capture_output=True, text=True, check=True,
    ).stdout
    res, arq, n = {}, None, 0
    for linha in saida.splitlines():
        if linha.startswith("+++ "):
            arq = None if linha.endswith("/dev/null") else linha[6:]
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


def achado(regra, severidade, arquivo, linha, evidencia, correcao):
    return {"id": regra, "severidade": severidade, "arquivo": arquivo,
            "linha": linha, "evidencia": evidencia, "como_corrigir": correcao}


def main_cli(verificar):
    """Uso: python check_x.py <base> [repo]  ->  imprime JSON com os achados."""
    base = sys.argv[1] if len(sys.argv) > 1 else "develop"
    repo = sys.argv[2] if len(sys.argv) > 2 else "."
    achados = verificar(linhas_adicionadas(base, repo), repo)
    print(json.dumps(achados, ensure_ascii=False, indent=2))
    sys.exit(1 if achados else 0)
