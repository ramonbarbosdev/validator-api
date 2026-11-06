"""EV-COM-001: proibido comentario no codigo Java; so JavaDoc (/** ... */)."""
from pathlib import Path
from _diff import achado, main_cli

REGRA = "EV-COM-001"


def comentarios(src):
    """Gera (tipo, linha_ini, linha_fim, texto) ignorando strings, chars e text blocks."""
    i, n, linha = 0, len(src), 1
    while i < n:
        c = src[i]
        if c == "\n":
            linha += 1
            i += 1
        elif src.startswith('"""', i):
            j = src.find('"""', i + 3)
            j = n if j == -1 else j + 3
            linha += src.count("\n", i, j)
            i = j
        elif c in "\"'":
            j = i + 1
            while j < n and src[j] != c and src[j] != "\n":
                j += 2 if src[j] == "\\" else 1
            i = j + 1
        elif src.startswith("//", i):
            j = src.find("\n", i)
            j = n if j == -1 else j
            yield ("linha", linha, linha, src[i:j])
            i = j
        elif src.startswith("/*", i):
            j = src.find("*/", i + 2)
            j = n if j == -1 else j + 2
            fim = linha + src.count("\n", i, j)
            javadoc = src.startswith("/**", i) and not src.startswith("/**/", i)
            yield ("javadoc" if javadoc else "bloco", linha, fim, src[i:j])
            linha, i = fim, j
        else:
            i += 1


def verificar(adicionadas, repo):
    achados = []
    for arq, linhas in adicionadas.items():
        if not arq.endswith(".java"):
            continue
        caminho = Path(repo) / arq
        if not caminho.exists():
            continue
        for tipo, ini, fim, texto in comentarios(caminho.read_text(encoding="utf-8")):
            if tipo == "javadoc" or not (linhas & set(range(ini, fim + 1))):
                continue
            rotulo = "comentario de linha (//)" if tipo == "linha" else "comentario de bloco (/* */)"
            achados.append(achado(
                REGRA, "IMPORTANTE", arq, ini,
                f"{rotulo}: {texto.strip().splitlines()[0][:80]}",
                "Remova o comentario. Se a informacao for necessaria, passe para JavaDoc na declaracao.",
            ))
    return achados


if __name__ == "__main__":
    main_cli(verificar)
