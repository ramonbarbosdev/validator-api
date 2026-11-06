CREATE TABLE banco (
    id_banco BIGSERIAL PRIMARY KEY,
    nm_razao_social VARCHAR(100) NOT NULL
);

ALTER TABLE banco ADD COLUMN descricao VARCHAR(200);
