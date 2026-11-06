"""Implementacao de cada tipo de regra. Cada handler recebe (regra, ctx) e devolve [(arquivo, linha, evidencia)]."""
import re

from . import sql as sqlmod

ALVOS_SQL = {"tabela_sql", "coluna_sql", "indice_sql", "constraint_sql"}
ALVOS_JAVA = {"classe", "interface", "enum", "metodo", "construtor", "campo", "constante", "parametro"}
ALVOS_ESPECIAIS = {"pacote", "arquivo", "caminho", "coluna_jpa", "tabela_jpa", "url_segmento"}
ALVOS = ALVOS_SQL | ALVOS_JAVA | ALVOS_ESPECIAIS

JPA_COLUNA = re.compile(r"@(?:Column|JoinColumn)\s*\([^)]*?\bname\s*=\s*\"([^\"]+)\"")
JPA_TABELA = re.compile(r"@Table\s*\([^)]*?\bname\s*=\s*\"([^\"]+)\"")
URL = re.compile(r"@(?:Request|Get|Post|Put|Delete|Patch)Mapping\s*\(\s*(?:(?:value|path)\s*=\s*)?\{?\s*\"([^\"]*)\"")


def _lista(v):
    return [] if v is None else (v if isinstance(v, list) else [v])


def _passa(d, q):
    """Filtros `quando` aplicados a uma declaracao Java."""
    q = q or {}
    if "anotada_com" in q and not set(_lista(q["anotada_com"])) & set(d.anotacoes):
        return False
    if "sem_anotacao" in q and set(_lista(q["sem_anotacao"])) & set(d.anotacoes):
        return False
    if "visibilidade" in q and d.visibilidade not in _lista(q["visibilidade"]):
        return False
    if "classe_anotada_com" in q and not set(_lista(q["classe_anotada_com"])) & set(d.classe_anotacoes):
        return False
    if "classe_nome" in q and not re.fullmatch(q["classe_nome"], d.classe_nome or ""):
        return False
    if "nome" in q and not re.fullmatch(q["nome"], d.nome):
        return False
    return True


def _motivo(regra, nome):
    p, q = regra.get("padrao"), regra.get("proibir_padrao")
    if p and not re.fullmatch(p, nome):
        return f"fora do padrao {p}"
    if q and re.search(q, nome):
        return f"contem padrao proibido {q}"
    return None


def h_nomenclatura(regra, ctx):
    alvo, achados = regra["alvo"], []

    def checar(arq, nome, linha):
        motivo = _motivo(regra, nome)
        if motivo and ctx.nova(arq, linha):
            achados.append((arq, linha, f"{alvo} '{nome}' {motivo}"))

    if alvo in ALVOS_SQL:
        for arq in ctx.arquivos(regra, (".sql",)):
            for nome, linha in sqlmod.extrair(ctx.texto(arq))[alvo]:
                checar(arq, nome, linha)
    elif alvo in ("coluna_jpa", "tabela_jpa", "url_segmento"):
        rx = {"coluna_jpa": JPA_COLUNA, "tabela_jpa": JPA_TABELA, "url_segmento": URL}[alvo]
        for arq in ctx.arquivos(regra, (".java",)):
            texto = ctx.texto(arq)
            for m in rx.finditer(texto):
                linha = texto.count("\n", 0, m.start(1)) + 1
                if alvo == "url_segmento":
                    for seg in [s for s in m.group(1).split("/") if s and not s.startswith("{")]:
                        checar(arq, seg, linha)
                else:
                    checar(arq, m.group(1), linha)
    elif alvo in ("arquivo", "caminho"):
        for arq in ctx.arquivos(regra, ()):
            checar(arq, arq.split("/")[-1] if alvo == "arquivo" else arq, 1)
    elif alvo == "pacote":
        for arq in ctx.arquivos(regra, (".java",)):
            pacote = ctx.java(arq).pacote
            if pacote:
                checar(arq, pacote, 1)
    else:
        for arq in ctx.arquivos(regra, (".java",)):
            for d in ctx.java(arq).decls:
                if d.kind == alvo and _passa(d, regra.get("quando")):
                    checar(arq, d.nome, d.linha)
    return achados


def h_declaracao_exige(regra, ctx):
    achados = []
    for arq in ctx.arquivos(regra, (".java",)):
        for d in ctx.java(arq).decls:
            if d.kind != regra["alvo"] or not _passa(d, regra.get("quando")) or not ctx.nova(arq, d.linha):
                continue
            for req in regra["exige"]:
                if req.get("javadoc") and not d.javadoc:
                    achados.append((arq, d.linha, f"{d.kind} '{d.nome}' sem JavaDoc"))
                if "anotacao" in req and req["anotacao"] not in d.anotacoes:
                    achados.append((arq, d.linha, f"{d.kind} '{d.nome}' sem @{req['anotacao']}"))
                if "sem_anotacao" in req and req["sem_anotacao"] in d.anotacoes:
                    achados.append((arq, d.linha, f"{d.kind} '{d.nome}' com @{req['sem_anotacao']} (proibido aqui)"))
    return achados


def h_comentarios(regra, ctx):
    permitidos = set(_lista(regra.get("permitir_tipos")))
    achados = []
    for arq in ctx.arquivos(regra, (".java",)):
        novas = ctx.added.get(arq, set())
        for c in ctx.java(arq).comentarios:
            if not (novas & set(range(c.ini, c.fim + 1))):
                continue
            if c.tipo == "javadoc" and c.solto:
                achados.append((arq, c.ini, "JavaDoc fora de declaracao (dentro de metodo ou solto)"))
            elif c.tipo != "javadoc" and c.tipo not in permitidos:
                rotulo = "comentario de linha (//)" if c.tipo == "linha" else "comentario de bloco (/* */)"
                achados.append((arq, c.ini, f"{rotulo}: {c.texto.strip().splitlines()[0][:80]}"))
    return achados


def h_proibido(regra, ctx):
    rx, achados = re.compile(regra["padrao"]), []
    for arq in ctx.arquivos(regra, ()):
        if arq.endswith(".java") and regra.get("onde", "codigo") == "codigo":
            linhas = ctx.java(arq).mascarado
        else:
            linhas = ctx.texto(arq).splitlines()
        for i, linha in enumerate(linhas, 1):
            if ctx.nova(arq, i) and rx.search(linha):
                achados.append((arq, i, linha.strip()[:80]))
    return achados


def h_dependencia_proibida(regra, ctx):
    achados = []
    for arq in ctx.arquivos(regra, (".java",)):
        for fqn, linha in ctx.java(arq).imports:
            if ctx.nova(arq, linha) and re.search(regra["importa"], fqn):
                achados.append((arq, linha, f"import proibido nesta camada: {fqn}"))
    return achados


def h_par_obrigatorio(regra, ctx):
    fonte = ctx.novos if regra.get("quando", "novos") == "novos" else ctx.alterados
    achados = []
    for arq in sorted(fonte):
        m = re.fullmatch(regra["origem"], arq)
        if not m:
            continue
        destino = m.expand(regra["destino"])
        if destino in ctx.alterados or (regra.get("aceitar_existente") and (ctx.repo / destino).exists()):
            continue
        achados.append((arq, 1, f"falta o arquivo correspondente: {destino}"))
    return achados


HANDLERS = {
    "nomenclatura": h_nomenclatura,
    "declaracao_exige": h_declaracao_exige,
    "comentarios": h_comentarios,
    "proibido": h_proibido,
    "dependencia_proibida": h_dependencia_proibida,
    "par_obrigatorio": h_par_obrigatorio,
}
