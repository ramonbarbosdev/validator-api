package com.esimples_api.controller;

import com.esimples_api.repository.BancoRepository;
import org.springframework.web.bind.annotation.RestController;

/**
 * Banco.
 */
@RestController
public class BancoController {

    private final BancoRepository repository;

    BancoController(BancoRepository repository) {
        this.repository = repository;
    }
}
