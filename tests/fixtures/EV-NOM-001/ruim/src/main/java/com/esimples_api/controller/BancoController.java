package com.esimples_api.controller;

import org.springframework.web.bind.annotation.GetMapping;
import org.springframework.web.bind.annotation.RequestMapping;
import org.springframework.web.bind.annotation.RestController;

/**
 * Banco.
 */
@RestController
@RequestMapping("/contaBancaria")
public class BancoController {

    /**
     * Detalhe.
     */
    @GetMapping("/{id}/dados_extras")
    public void detalhe() {
    }
}
