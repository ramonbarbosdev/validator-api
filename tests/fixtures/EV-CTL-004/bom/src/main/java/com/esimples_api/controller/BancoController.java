package com.esimples_api.controller;

import org.springframework.web.bind.annotation.RestController;

/**
 * Banco. Transactional fica no service.
 */
@RestController
public class BancoController {

    private static final String NOTA = "@Transactional";

    /**
     * Remove.
     */
    public String remover() {
        return NOTA;
    }
}
