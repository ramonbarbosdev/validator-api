package com.esimples_api.controller;

import com.esimples_api.service.BancoService;
import org.springframework.web.bind.annotation.RestController;

/**
 * Banco.
 */
@RestController
public class BancoController {

    private final BancoService service;

    BancoController(BancoService service) {
        this.service = service;
    }
}
