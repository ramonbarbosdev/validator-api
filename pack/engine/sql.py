"""Extracao de nomes (tabela, coluna, indice, constraint) de migrations SQL."""
import re

RESERVADAS = {"constraint", "primary", "foreign", "unique", "key", "index", "check", "exclude", "like", "period"}
CREATE_TABELA = re.compile(r"create\s+(?:unlogged\s+|temporary\s+|temp\s+)?table\s+(?:if\s+not\s+exists\s+)?([\w\".`]+)\s*\(", re.I)
CREATE_INDICE = re.compile(r"create\s+(?:unique\s+)?index\s+(?:concurrently\s+)?(?:if\s+not\s+exists\s+)?[\"`]?(\w+)", re.I)
ALTER = re.compile(r"alter\s+table\s+(?:only\s+)?(?:if\s+exists\s+)?[\w\".`]+\s+[^;]*", re.I)
ADD = re.compile(r"\badd\s+(?:column\s+)?(?:if\s+not\s+exists\s+)?[\"`]?(\w+)[\"`]?", re.I)
RENAME_COLUNA = re.compile(r"\brename\s+column\s+[\"`]?\w+[\"`]?\s+to\s+[\"`]?(\w+)", re.I)
RENAME_TABELA = re.compile(r"\brename\s+to\s+[\"`]?(\w+)", re.I)
CONSTRAINT = re.compile(r"\bconstraint\s+[\"`]?(\w+)", re.I)


def _limpar(sql):
    sql = re.sub(r"--[^\n]*", lambda m: " " * len(m.group()), sql)
    return re.sub(r"/\*.*?\*/", lambda m: re.sub(r"[^\n]", " ", m.group()), sql, flags=re.S)


def _simples(nome):
    return nome.split(".")[-1].strip("\"`")


def extrair(sql):
    """Devolve {alvo: [(nome, linha)]} para tabela_sql, coluna_sql, indice_sql e constraint_sql."""
    s = _limpar(sql)
    res = {"tabela_sql": [], "coluna_sql": [], "indice_sql": [], "constraint_sql": []}

    def add(alvo, nome, pos):
        res[alvo].append((nome, sql.count("\n", 0, pos) + 1))

    for m in CREATE_TABELA.finditer(s):
        add("tabela_sql", _simples(m.group(1)), m.start(1))
        prof, i, partida, itens = 1, m.end(), m.end(), []
        while i < len(s) and prof:
            c = s[i]
            prof += (c == "(") - (c == ")")
            if (c == "," and prof == 1) or prof == 0:
                itens.append((s[partida:i], partida))
                partida = i + 1
            i += 1
        for texto, pos in itens:
            tok = re.match(r"\s*[\"`]?(\w+)", texto)
            if not tok:
                continue
            palavra = tok.group(1).lower()
            if palavra == "constraint":
                c = CONSTRAINT.match(texto.lstrip())
                if c:
                    add("constraint_sql", c.group(1), pos + texto.index(c.group(1)))
            elif palavra not in RESERVADAS:
                add("coluna_sql", tok.group(1), pos + tok.start(1))
    for m in CREATE_INDICE.finditer(s):
        if m.group(1).lower() != "on":
            add("indice_sql", m.group(1), m.start(1))
    for m in ALTER.finditer(s):
        stmt, base = m.group(0), m.start()
        for a in ADD.finditer(stmt):
            nome = a.group(1)
            if nome.lower() == "constraint":
                c = CONSTRAINT.search(stmt, a.start())
                if c:
                    add("constraint_sql", c.group(1), base + c.start(1))
            elif nome.lower() not in RESERVADAS:
                add("coluna_sql", nome, base + a.start(1))
        for r in RENAME_COLUNA.finditer(stmt):
            add("coluna_sql", r.group(1), base + r.start(1))
        for r in RENAME_TABELA.finditer(stmt):
            add("tabela_sql", r.group(1), base + r.start(1))
    return res
