package com.esimples_api.controller;

import org.springframework.web.bind.annotation.GetMapping;
import org.springframework.web.bind.annotation.RequestMapping;
import org.springframework.web.bind.annotation.RestController;

/**
 * Banco.
 */
@RestController
@RequestMapping("/conta-bancaria")
public class BancoController {

    /**
     * Detalhe.
     */
    @GetMapping("/{idContaBancaria}/dados-extras")
    public void detalhe() {
    }
}
