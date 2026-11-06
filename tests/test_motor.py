from pathlib import Path

from engine.motor import carregar_regras, executar, validar_regras


def rodar(repo, *regras):
    erros = validar_regras(list(regras))
    assert not erros, erros
    return executar("develop", repo, list(regras))


def ids_linhas(res):
    return sorted((a["id"], a["arquivo"].split("/")[-1], a["linha"]) for a in res["achados"])


JAVA_COMENTARIOS = '''package x;

/**
 * Doc da classe.
 */
public class Foo {

    // campo
    private String a;

    /** Doc ok. */
    public String url() {
        String s = "http://x // nao e comentario";
        /* bloco */
        /** javadoc solto */
        return s;
    }
}
'''


def test_comentarios(novo_repo):
    repo = novo_repo({"src/Foo.java": JAVA_COMENTARIOS})
    res = rodar(repo, {"id": "C", "tipo": "comentarios", "severidade": "IMPORTANTE"})
    assert ids_linhas(res) == [("C", "Foo.java", 8), ("C", "Foo.java", 14), ("C", "Foo.java", 15)]


def test_comentarios_permitir_tipo(novo_repo):
    repo = novo_repo({"src/Foo.java": JAVA_COMENTARIOS})
    res = rodar(repo, {"id": "C", "tipo": "comentarios", "severidade": "IMPORTANTE", "permitir_tipos": ["linha", "bloco"]})
    assert ids_linhas(res) == [("C", "Foo.java", 15)]


def test_so_linhas_novas(novo_repo):
    novo_repo({"src/Foo.java": "package x;\n// antigo\npublic class Foo { }\n"})
    novo_repo.marcar_base()
    repo = novo_repo({"src/Foo.java": "package x;\n// antigo\npublic class Foo { }\n// novo\n"})
    res = rodar(repo, {"id": "C", "tipo": "comentarios", "severidade": "IMPORTANTE"})
    assert ids_linhas(res) == [("C", "Foo.java", 4)]


SQL = '''CREATE TABLE cliente (
    id_cliente BIGINT PRIMARY KEY,
    nm_razaosocial VARCHAR(100),
    nm_nome_fantasia VARCHAR(100),
    cnpj VARCHAR(14),
    CONSTRAINT uk_cliente UNIQUE (cnpj)
);
ALTER TABLE cliente ADD COLUMN dt_cadastro DATE;
ALTER TABLE cliente ADD CONSTRAINT fk_org FOREIGN KEY (id_org) REFERENCES org(id_org);
CREATE INDEX ix_cliente_cnpj ON cliente (cnpj);
'''
PADRAO_COL = {"tipo": "nomenclatura", "alvo": "coluna_sql", "severidade": "IMPORTANTE", "padrao": "(id|tp|nm|dt)_[a-z0-9]+"}


def test_coluna_sql(novo_repo):
    repo = novo_repo({"db/V1.sql": SQL})
    res = rodar(repo, {"id": "N", **PADRAO_COL})
    assert ids_linhas(res) == [("N", "V1.sql", 4), ("N", "V1.sql", 5)]


def test_tabela_indice_constraint_sql(novo_repo):
    repo = novo_repo({"db/V1.sql": SQL})
    res = rodar(
        repo,
        {"id": "T", "tipo": "nomenclatura", "alvo": "tabela_sql", "severidade": "MELHORIA", "padrao": "tb_[a-z0-9]+"},
        {"id": "I", "tipo": "nomenclatura", "alvo": "indice_sql", "severidade": "MELHORIA", "padrao": "ix_[a-z0-9_]+"},
        {"id": "K", "tipo": "nomenclatura", "alvo": "constraint_sql", "severidade": "MELHORIA", "padrao": "(pk|fk|uq)_[a-z0-9_]+"},
    )
    assert ids_linhas(res) == [("K", "V1.sql", 6), ("T", "V1.sql", 1)]


JAVA_ENTIDADE = '''package x.model;

@Entity
public class cliente {
    @Column(name = "nm_razaosocial")
    private String razao;

    @Column(name = "razao_social")
    private String outro;

    @JoinColumn(name = "id_organizacao")
    private Long org;

    public static final int maximo = 1;

    private String Nome_Errado;
}
'''


def test_nomenclatura_java(novo_repo):
    repo = novo_repo({"src/cliente.java": JAVA_ENTIDADE})
    res = rodar(
        repo,
        {"id": "CL", "tipo": "nomenclatura", "alvo": "classe", "severidade": "IMPORTANTE", "padrao": "[A-Z][A-Za-z0-9]*"},
        {"id": "CO", "tipo": "nomenclatura", "alvo": "constante", "severidade": "MELHORIA", "padrao": "[A-Z][A-Z0-9_]*"},
        {"id": "CA", "tipo": "nomenclatura", "alvo": "campo", "severidade": "MELHORIA", "padrao": "[a-z][a-zA-Z0-9]*"},
        {"id": "JC", "tipo": "nomenclatura", "alvo": "coluna_jpa", "severidade": "IMPORTANTE", "padrao": "(id|tp|nm)_[a-z0-9]+"},
    )
    assert ids_linhas(res) == [("CA", "cliente.java", 16), ("CL", "cliente.java", 4),
                               ("CO", "cliente.java", 14), ("JC", "cliente.java", 8)]


JAVA_CONTROLLER = '''package x.controller;

import x.repository.ClienteRepository;
import x.service.ClienteService;

@RestController
@RequestMapping("/clientes-ativos/{id}/Detalhes")
public class ClienteController {

    /** Cria. */
    @PostMapping
    public void criar(@RequestBody @Valid ClienteDto dto) { }

    @PostMapping("/outro")
    @Transactional
    public void outro(@RequestBody ClienteDto dto) { }

    void interno() { }
}
'''


def test_declaracao_exige(novo_repo):
    repo = novo_repo({"src/controller/ClienteController.java": JAVA_CONTROLLER})
    res = rodar(
        repo,
        {"id": "DOC", "tipo": "declaracao_exige", "alvo": "metodo", "severidade": "IMPORTANTE",
         "quando": {"visibilidade": "public"}, "exige": [{"javadoc": True}]},
        {"id": "VAL", "tipo": "declaracao_exige", "alvo": "parametro", "severidade": "IMPORTANTE",
         "quando": {"anotada_com": ["RequestBody"]}, "exige": [{"anotacao": "Valid"}]},
        {"id": "TX", "tipo": "declaracao_exige", "alvo": "metodo", "severidade": "IMPORTANTE",
         "quando": {"classe_anotada_com": ["RestController"]}, "exige": [{"sem_anotacao": "Transactional"}]},
    )
    assert ids_linhas(res) == [("DOC", "ClienteController.java", 16), ("TX", "ClienteController.java", 16),
                               ("VAL", "ClienteController.java", 16)]


def test_dependencia_proibida(novo_repo):
    repo = novo_repo({"src/controller/ClienteController.java": JAVA_CONTROLLER})
    res = rodar(repo, {"id": "DEP", "tipo": "dependencia_proibida", "severidade": "IMPORTANTE",
                       "arquivos": ["**/controller/**"], "importa": r"\.repository\."})
    assert ids_linhas(res) == [("DEP", "ClienteController.java", 3)]


def test_url_kebab(novo_repo):
    repo = novo_repo({"src/controller/ClienteController.java": JAVA_CONTROLLER})
    res = rodar(repo, {"id": "URL", "tipo": "nomenclatura", "alvo": "url_segmento", "severidade": "MELHORIA",
                       "padrao": "[a-z0-9]+(-[a-z0-9]+)*"})
    assert [a["evidencia"] for a in res["achados"]] == ["url_segmento 'Detalhes' fora do padrao [a-z0-9]+(-[a-z0-9]+)*"]


def test_proibido_ignora_strings_e_comentarios(novo_repo):
    java = 'package x;\npublic class A {\n void m() {\n  System.out.println("ok");\n  String s = "System.out.println";\n }\n}\n'
    repo = novo_repo({"src/A.java": java})
    res = rodar(repo, {"id": "P", "tipo": "proibido", "severidade": "IMPORTANTE", "arquivos": ["**/*.java"],
                       "padrao": r"System\.out\.println"})
    assert ids_linhas(res) == [("P", "A.java", 4)]


def test_nome_de_arquivo(novo_repo):
    repo = novo_repo({"db/migration/V1__ok.sql": "select 1;\n", "db/migration/v2_ruim.sql": "select 1;\n"})
    res = rodar(repo, {"id": "F", "tipo": "nomenclatura", "alvo": "arquivo", "severidade": "IMPORTANTE",
                       "arquivos": ["**/db/migration/*.sql"], "padrao": r"V\d+__[a-z0-9_]+\.sql"})
    assert ids_linhas(res) == [("F", "v2_ruim.sql", 1)]


def test_par_obrigatorio(novo_repo):
    repo = novo_repo({"src/main/java/x/FooService.java": "package x;\npublic class FooService { }\n",
                      "src/main/java/x/BarService.java": "package x;\npublic class BarService { }\n",
                      "src/test/java/x/BarServiceTest.java": "package x;\npublic class BarServiceTest { }\n"})
    res = rodar(repo, {"id": "PAR", "tipo": "par_obrigatorio", "severidade": "MELHORIA",
                       "origem": r"src/main/java/(.*)/(\w+)Service\.java", "destino": r"src/test/java/\1/\2ServiceTest.java"})
    assert ids_linhas(res) == [("PAR", "FooService.java", 1)]


def test_llm_lista_regras_aplicaveis_e_inativas(novo_repo):
    repo = novo_repo({"src/A.java": "package x;\npublic class A { }\n"})
    res = rodar(repo,
                {"id": "L1", "tipo": "llm", "severidade": "IMPORTANTE", "arquivos": ["**/*.java"], "descricao": "d"},
                {"id": "L2", "tipo": "llm", "severidade": "IMPORTANTE", "arquivos": ["**/*.sql"], "descricao": "d"},
                {"id": "OFF", "tipo": "comentarios", "severidade": "IMPORTANTE", "ativa": False})
    assert [r["id"] for r in res["regras_llm_aplicaveis"]] == ["L1"]
    assert res["regras_inativas"] == ["OFF"]


def test_falha_de_uma_regra_nao_derruba_as_outras(novo_repo):
    repo = novo_repo({"src/A.java": "package x;\n// c\npublic class A { }\n"})
    res = executar("develop", repo, [
        {"id": "QUEBRA", "tipo": "proibido", "severidade": "IMPORTANTE", "arquivos": ["**/*.java"], "padrao": "(["},
        {"id": "C", "tipo": "comentarios", "severidade": "IMPORTANTE"}])
    assert [f["id"] for f in res["falhas_de_regra"]] == ["QUEBRA"]
    assert [a["id"] for a in res["achados"]] == ["C"]


def test_validar_catalogo():
    erros = validar_regras([
        {"id": "A", "tipo": "nomenclatura", "alvo": "inexistente", "severidade": "IMPORTANTE", "padrao": "x"},
        {"id": "A", "tipo": "xyz", "severidade": "IMPORTANTE"},
        {"id": "B", "tipo": "proibido", "severidade": "ALTA", "arquivos": ["*"], "padrao": "(["},
    ])
    assert len(erros) >= 5


def test_catalogo_padroes_yaml_e_valido():
    regras = carregar_regras(Path(__file__).parent.parent / "pack" / "rules" / "padroes.yaml")
    assert validar_regras(regras) == []
