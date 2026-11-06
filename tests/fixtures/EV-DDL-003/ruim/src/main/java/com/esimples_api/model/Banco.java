package com.esimples_api.model;

import jakarta.persistence.Column;
import jakarta.persistence.Entity;

/**
 * Banco.
 */
@Entity
public class Banco {

    @Column(name = "razao_social")
    private String razaoSocial;
}
