"""Motor de validacao: le as regras (YAML), executa os tipos estaticos e lista as regras para o LLM.

Uso: python -m engine.motor <base> [--repo .] [--regras rules/padroes.yaml] [--saida findings-estaticos.json] [--validar]
"""
import argparse
import json
import re
import sys
from pathlib import Path

import yaml

from . import java_ast
from .diff import arquivos_por_status, linhas_adicionadas
from .tipos import ALVOS, HANDLERS

SEVERIDADES = ["CRITICO", "IMPORTANTE", "MELHORIA"]
EXIGIDOS = {
    "nomenclatura": ["alvo"],
    "declaracao_exige": ["alvo", "exige"],
    "comentarios": [],
    "proibido": ["arquivos", "padrao"],
    "dependencia_proibida": ["arquivos", "importa"],
    "par_obrigatorio": ["origem", "destino"],
    "llm": ["descricao"],
}
CAMPOS_REGEX = ["padrao", "proibir_padrao", "importa", "origem"]


def glob_regex(g):
    i, out = 0, ""
    while i < len(g):
        if g.startswith("**/", i):
            out, i = out + "(?:.*/)?", i + 3
        elif g.startswith("**", i):
            out, i = out + ".*", i + 2
        elif g[i] == "*":
            out, i = out + "[^/]*", i + 1
        elif g[i] == "?":
            out, i = out + "[^/]", i + 1
        else:
            out, i = out + re.escape(g[i]), i + 1
    return re.compile(out + r"\Z")


def casa(arq, globs):
    globs = [globs] if isinstance(globs, str) else (globs or [])
    return not globs or any(glob_regex(g).match(arq) for g in globs)


def carregar_regras(caminho):
    dados = yaml.safe_load(Path(caminho).read_text(encoding="utf-8")) or {}
    return dados.get("regras", [])


def validar_regras(regras):
    """Devolve a lista de problemas encontrados no catalogo (vazia = ok)."""
    erros, ids = [], set()
    for r in regras:
        rid = r.get("id", "<sem id>")
        if not r.get("id"):
            erros.append("regra sem id")
        elif rid in ids:
            erros.append(f"{rid}: id duplicado")
        ids.add(rid)
        tipo = r.get("tipo")
        if tipo not in EXIGIDOS:
            erros.append(f"{rid}: tipo desconhecido '{tipo}' (validos: {sorted(EXIGIDOS)})")
            continue
        if r.get("severidade") not in SEVERIDADES:
            erros.append(f"{rid}: severidade deve ser uma de {SEVERIDADES}")
        for campo in EXIGIDOS[tipo]:
            if not r.get(campo):
                erros.append(f"{rid}: falta o campo '{campo}'")
        if tipo == "nomenclatura":
            if r.get("alvo") not in ALVOS:
                erros.append(f"{rid}: alvo invalido '{r.get('alvo')}' (validos: {sorted(ALVOS)})")
            if not (r.get("padrao") or r.get("proibir_padrao")):
                erros.append(f"{rid}: informe 'padrao' e/ou 'proibir_padrao'")
        for campo in CAMPOS_REGEX:
            if r.get(campo):
                try:
                    re.compile(r[campo])
                except re.error as e:
                    erros.append(f"{rid}: regex invalida em '{campo}': {e}")
    return erros


class Contexto:
    def __init__(self, base, repo):
        self.repo = Path(repo)
        self.added = linhas_adicionadas(base, repo)
        status = arquivos_por_status(base, repo)
        self.novos, self.alterados = status["novos"], status["alterados"]
        self._texto, self._java = {}, {}

    def texto(self, arq):
        if arq not in self._texto:
            self._texto[arq] = (self.repo / arq).read_text(encoding="utf-8", errors="replace")
        return self._texto[arq]

    def java(self, arq):
        if arq not in self._java:
            self._java[arq] = java_ast.analisar(self.texto(arq))
        return self._java[arq]

    def nova(self, arq, linha):
        return linha in self.added.get(arq, ())

    def arquivos(self, regra, extensoes):
        return [a for a in sorted(self.alterados)
                if (not extensoes or a.endswith(extensoes)) and casa(a, regra.get("arquivos")) and (self.repo / a).is_file()]


def executar(base, repo, regras):
    ctx = Contexto(base, repo)
    achados, falhas, executadas, inativas, llm = [], [], [], [], []
    for r in regras:
        rid = r.get("id")
        if not r.get("ativa", True):
            inativas.append(rid)
            continue
        try:
            if r["tipo"] == "llm":
                alvos = [a for a in sorted(ctx.alterados) if casa(a, r.get("arquivos"))]
                if alvos:
                    llm.append({"id": rid, "severidade": r.get("severidade"), "descricao": r["descricao"],
                                "arquivos": alvos})
                continue
            for arq, linha, evidencia in HANDLERS[r["tipo"]](r, ctx):
                achados.append({"id": rid, "severidade": r["severidade"], "arquivo": arq, "linha": linha,
                                "evidencia": evidencia, "como_corrigir": r.get("como_corrigir", ""),
                                "origem": "estatico"})
            executadas.append(rid)
        except Exception as e:
            falhas.append({"id": rid, "erro": f"{type(e).__name__}: {e}"})
    vistos, unicos = set(), []
    for a in achados:
        chave = (a["id"], a["arquivo"], a["linha"], a["evidencia"])
        if chave not in vistos:
            vistos.add(chave)
            unicos.append(a)
    unicos.sort(key=lambda a: (SEVERIDADES.index(a["severidade"]), a["arquivo"], a["linha"], a["id"]))
    return {"achados": unicos, "falhas_de_regra": falhas, "regras_executadas": executadas,
            "regras_inativas": inativas, "regras_llm_aplicaveis": llm}


def main(argv=None):
    ap = argparse.ArgumentParser(prog="motor")
    ap.add_argument("base", nargs="?", default="develop")
    ap.add_argument("--repo", default=".")
    ap.add_argument("--regras", default=str(Path(__file__).parent.parent / "rules" / "padroes.yaml"))
    ap.add_argument("--saida")
    ap.add_argument("--validar", action="store_true", help="so valida o catalogo de regras")
    args = ap.parse_args(argv)
    regras = carregar_regras(args.regras)
    erros = validar_regras(regras)
    if args.validar:
        print("\n".join(erros) if erros else f"catalogo ok ({len(regras)} regras)")
        return 2 if erros else 0
    if erros:
        print("Catalogo invalido:\n" + "\n".join(erros), file=sys.stderr)
        return 2
    resultado = executar(args.base, args.repo, regras)
    texto = json.dumps(resultado, ensure_ascii=False, indent=2)
    if args.saida:
        Path(args.saida).write_text(texto, encoding="utf-8")
    else:
        print(texto)
    return 1 if resultado["achados"] else 0


if __name__ == "__main__":
    sys.exit(main())
