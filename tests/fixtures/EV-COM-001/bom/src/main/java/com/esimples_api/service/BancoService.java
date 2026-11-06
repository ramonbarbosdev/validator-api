package com.esimples_api.service;

/**
 * Regras de banco.
 */
public class BancoService {

    private static final String URL = "https://exemplo.com/api";

    private static final String SQL = """
            SELECT 1 -- // nao e comentario
            /* tambem nao */
            """;

    /**
     * Salva o banco.
     *
     * @return url usada
     */
    public String salvar() {
        String padrao = "a // b /* c */";
        return URL + SQL + padrao;
    }
}
