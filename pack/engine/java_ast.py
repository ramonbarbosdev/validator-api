"""Analise de arquivos Java via tree-sitter: declaracoes, comentarios, imports e codigo mascarado."""
from dataclasses import dataclass, field

import tree_sitter_java as tsj
from tree_sitter import Language, Parser

_PARSER = Parser(Language(tsj.language()))

TIPOS = {
    "class_declaration": "classe",
    "record_declaration": "classe",
    "interface_declaration": "interface",
    "enum_declaration": "enum",
}
DECLARACOES_COM_DOC = {
    "class_declaration", "record_declaration", "interface_declaration", "enum_declaration",
    "annotation_type_declaration", "method_declaration", "constructor_declaration",
    "compact_constructor_declaration", "field_declaration", "enum_constant",
    "annotation_type_element_declaration", "package_declaration", "module_declaration",
}
COMENTARIOS = {"line_comment", "block_comment"}


@dataclass
class Decl:
    kind: str
    nome: str
    linha: int
    anotacoes: list = field(default_factory=list)
    modificadores: set = field(default_factory=set)
    visibilidade: str = "package"
    javadoc: bool = False
    classe_nome: str = ""
    classe_anotacoes: list = field(default_factory=list)


@dataclass
class Comentario:
    tipo: str
    ini: int
    fim: int
    texto: str
    solto: bool = False


@dataclass
class ArquivoJava:
    decls: list
    comentarios: list
    mascarado: list
    pacote: str
    imports: list


def _texto(no):
    return no.text.decode("utf-8", "replace")


def _modificadores(no):
    anotacoes, palavras = [], set()
    for filho in no.children:
        if filho.type != "modifiers":
            continue
        for m in filho.children:
            if m.type in ("annotation", "marker_annotation"):
                nome = m.child_by_field_name("name")
                anotacoes.append(_texto(nome).split(".")[-1] if nome else "")
            else:
                palavras.add(m.type)
    return anotacoes, palavras


def _visibilidade(no, palavras):
    for v in ("public", "protected", "private"):
        if v in palavras:
            return v
    return "public" if no.parent is not None and no.parent.type == "interface_body" else "package"


def _tem_javadoc(no):
    ant = no.prev_sibling
    return ant is not None and ant.type == "block_comment" and _texto(ant).startswith("/**")


def _doc_solto(no):
    seguinte = no.next_sibling
    while seguinte is not None and seguinte.type in COMENTARIOS:
        seguinte = seguinte.next_sibling
    return seguinte is None or seguinte.type not in DECLARACOES_COM_DOC


def _decl(kind, no, nome_no, classe):
    anotacoes, palavras = _modificadores(no)
    cn, ca = classe if classe else ("", [])
    d = Decl(kind, _texto(nome_no), nome_no.start_point[0] + 1, anotacoes, palavras,
             _visibilidade(no, palavras), _tem_javadoc(no), cn, ca)
    return d


def analisar(texto):
    """Analisa o fonte Java e devolve ArquivoJava."""
    dados = texto.encode("utf-8")
    raiz = _PARSER.parse(dados).root_node
    decls, comentarios, intervalos, imports, pacote = [], [], [], [], ""
    pilha = [(raiz, None)]
    while pilha:
        no, classe = pilha.pop()
        t = no.type
        if t in COMENTARIOS:
            txt = _texto(no)
            if t == "line_comment":
                tipo = "linha"
            else:
                tipo = "javadoc" if txt.startswith("/**") and not txt.startswith("/**/") else "bloco"
            solto = tipo == "javadoc" and _doc_solto(no)
            comentarios.append(Comentario(tipo, no.start_point[0] + 1, no.end_point[0] + 1, txt, solto))
            intervalos.append((no.start_byte, no.end_byte))
            continue
        if t in ("string_literal", "character_literal"):
            intervalos.append((no.start_byte, no.end_byte))
            continue
        nova = classe
        if t in TIPOS and no.child_by_field_name("name"):
            d = _decl(TIPOS[t], no, no.child_by_field_name("name"), None)
            d.classe_nome, d.classe_anotacoes = d.nome, d.anotacoes
            decls.append(d)
            nova = (d.nome, d.anotacoes)
        elif t in ("method_declaration", "constructor_declaration") and no.child_by_field_name("name"):
            kind = "metodo" if t == "method_declaration" else "construtor"
            decls.append(_decl(kind, no, no.child_by_field_name("name"), classe))
        elif t == "field_declaration":
            anotacoes, palavras = _modificadores(no)
            kind = "constante" if {"static", "final"} <= palavras else "campo"
            for filho in no.children:
                if filho.type == "variable_declarator" and filho.child_by_field_name("name"):
                    decls.append(_decl(kind, no, filho.child_by_field_name("name"), classe))
        elif t in ("formal_parameter", "spread_parameter"):
            nome_no = no.child_by_field_name("name")
            if nome_no is not None:
                decls.append(_decl("parametro", no, nome_no, classe))
        elif t == "package_declaration":
            pacote = _texto(no).replace("package", "", 1).strip().rstrip(";").strip()
        elif t == "import_declaration":
            fqn = _texto(no).replace("import", "", 1).replace("static", "", 1).strip().rstrip(";").strip()
            imports.append((fqn, no.start_point[0] + 1))
        for filho in reversed(no.children):
            pilha.append((filho, nova))
    mascara = bytearray(dados)
    for ini, fim in intervalos:
        for i in range(ini, fim):
            if mascara[i] != 10:
                mascara[i] = 32
    mascarado = mascara.decode("utf-8", "replace").splitlines()
    return ArquivoJava(decls, sorted(comentarios, key=lambda c: c.ini), mascarado, pacote, imports)
