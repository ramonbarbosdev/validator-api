CREATE TABLE banco (
    id_banco BIGSERIAL PRIMARY KEY,
    nm_razaosocial VARCHAR(100) NOT NULL,
    id_empresa BIGINT NOT NULL,
    CONSTRAINT fk_banco_empresa FOREIGN KEY (id_empresa) REFERENCES empresa (id_empresa)
);

ALTER TABLE banco ADD COLUMN ds_observacao VARCHAR(200);
ALTER TABLE banco ADD CONSTRAINT uk_banco_razaosocial UNIQUE (nm_razaosocial);
CREATE INDEX idx_banco_empresa ON banco (id_empresa);
