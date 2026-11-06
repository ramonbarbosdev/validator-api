package com.esimples_api.model;

import jakarta.persistence.Column;
import jakarta.persistence.Entity;
import jakarta.persistence.JoinColumn;

/**
 * Banco.
 */
@Entity
public class Banco {

    @Column(name = "nm_razaosocial")
    private String razaoSocial;

    @JoinColumn(name = "id_empresa")
    private Empresa empresa;
}
