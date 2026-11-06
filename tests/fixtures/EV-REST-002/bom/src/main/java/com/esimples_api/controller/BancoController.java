package com.esimples_api.controller;

import jakarta.validation.Valid;
import org.springframework.web.bind.annotation.PostMapping;
import org.springframework.web.bind.annotation.RequestBody;
import org.springframework.web.bind.annotation.RestController;

/**
 * Banco.
 */
@RestController
public class BancoController {

    /**
     * Cria.
     */
    @PostMapping("/banco")
    public void criar(
            @Valid
            @RequestBody BancoRequest request) {
    }
}
