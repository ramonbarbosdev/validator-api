"""EV-DDL-002: colunas de banco devem seguir <prefixo>_<tudojunto> (ex.: id_organizacao, nm_razaosocial)."""
import json
import re
from pathlib import Path
from _diff import achado, main_cli

REGRA = "EV-DDL-002"
CFG = json.loads((Path(__file__).parent.parent / "rules" / "nomenclatura-db.json").read_text(encoding="utf-8"))
PADRAO = re.compile(r"^(?:%s)_[a-z0-9]+$" % "|".join(map(re.escape, CFG["prefixos"])))
RESERVADAS = {"constraint", "primary", "foreign", "unique", "key", "index", "check", "exclude", "like", "period"}

CREATE = re.compile(r"create\s+(?:unlogged\s+|temporary\s+|temp\s+)?table\s+(?:if\s+not\s+exists\s+)?[\w\".`]+\s*\(", re.I)
ADD = re.compile(r"\badd\s+(?:column\s+)?(?:if\s+not\s+exists\s+)?[\"`]?(\w+)[\"`]?", re.I)
RENAME = re.compile(r"\brename\s+column\s+[\"`]?\w+[\"`]?\s+to\s+[\"`]?(\w+)", re.I)
JPA = re.compile(r"@(?:Column|JoinColumn)\s*\([^)]*?\bname\s*=\s*\"([^\"]+)\"")


def limpar_sql(sql):
    """Troca comentarios SQL por espacos, preservando posicoes e quebras de linha."""
    sql = re.sub(r"--[^\n]*", lambda m: " " * len(m.group()), sql)
    return re.sub(r"/\*.*?\*/", lambda m: re.sub(r"[^\n]", " ", m.group()), sql, flags=re.S)


def colunas_sql(sql):
    """Gera (nome, posicao) das colunas criadas/adicionadas/renomeadas."""
    sql = limpar_sql(sql)
    for m in CREATE.finditer(sql):
        prof, i = 1, m.end()
        itens, partida = [], m.end()
        while i < len(sql) and prof:
            c = sql[i]
            prof += (c == "(") - (c == ")")
            if (c == "," and prof == 1) or prof == 0:
                itens.append((sql[partida:i], partida))
                partida = i + 1
            i += 1
        for texto, pos in itens:
            tok = re.match(r"\s*[\"`]?(\w+)", texto)
            if tok and tok.group(1).lower() not in RESERVADAS:
                yield tok.group(1), pos + tok.start(1)
    for m in ADD.finditer(sql):
        if m.group(1).lower() not in RESERVADAS:
            yield m.group(1), m.start(1)
    for m in RENAME.finditer(sql):
        yield m.group(1), m.start(1)


def verificar(adicionadas, repo):
    achados = []
    for arq, linhas in adicionadas.items():
        caminho = Path(repo) / arq
        if not caminho.exists():
            continue
        texto = caminho.read_text(encoding="utf-8")
        if arq.endswith(".sql"):
            candidatas = [(nome, texto.count("\n", 0, pos) + 1) for nome, pos in colunas_sql(texto)]
        elif arq.endswith(".java"):
            candidatas = [(m.group(1), texto.count("\n", 0, m.start(1)) + 1) for m in JPA.finditer(texto)]
        else:
            continue
        for nome, linha in candidatas:
            if linha in linhas and not PADRAO.match(nome):
                achados.append(achado(
                    REGRA, "IMPORTANTE", arq, linha, f"coluna '{nome}' fora do padrao",
                    f"Use <prefixo>_<tudojunto> com prefixo em {CFG['prefixos']} (ex.: nm_razaosocial).",
                ))
    return achados


if __name__ == "__main__":
    main_cli(verificar)
