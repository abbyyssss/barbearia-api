-- Banco de dados da Navalha & Co.
-- Execute este arquivo inteiro no MySQL Workbench (ícone do raio).

CREATE DATABASE IF NOT EXISTS navalha CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;
USE navalha;

CREATE TABLE IF NOT EXISTS servicos (
  id           INT AUTO_INCREMENT PRIMARY KEY,
  nome         VARCHAR(80)  NOT NULL,
  duracao_min  INT          NOT NULL,
  preco        DECIMAL(8,2) NOT NULL,
  ativo        BOOLEAN      NOT NULL DEFAULT TRUE
);

CREATE TABLE IF NOT EXISTS barbeiros (
  id             INT AUTO_INCREMENT PRIMARY KEY,
  nome           VARCHAR(60) NOT NULL,
  especialidade  VARCHAR(80),
  ativo          BOOLEAN     NOT NULL DEFAULT TRUE
);

CREATE TABLE IF NOT EXISTS clientes (
  id        INT AUTO_INCREMENT PRIMARY KEY,
  nome      VARCHAR(100) NOT NULL,
  telefone  VARCHAR(20)  NOT NULL UNIQUE
);

CREATE TABLE IF NOT EXISTS agendamentos (
  id           INT AUTO_INCREMENT PRIMARY KEY,
  cliente_id   INT          NOT NULL,
  servico_id   INT          NOT NULL,
  barbeiro_id  INT          NOT NULL,
  data         DATE         NOT NULL,
  hora_inicio  TIME         NOT NULL,
  hora_fim     TIME         NOT NULL,
  preco        DECIMAL(8,2) NOT NULL,
  status       ENUM('agendado','cancelado') NOT NULL DEFAULT 'agendado',
  criado_em    TIMESTAMP    NOT NULL DEFAULT CURRENT_TIMESTAMP,
  FOREIGN KEY (cliente_id)  REFERENCES clientes(id),
  FOREIGN KEY (servico_id)  REFERENCES servicos(id),
  FOREIGN KEY (barbeiro_id) REFERENCES barbeiros(id),
  INDEX idx_barbeiro_dia (barbeiro_id, data)
);

CREATE TABLE IF NOT EXISTS usuarios (
  id          INT AUTO_INCREMENT PRIMARY KEY,
  email       VARCHAR(120) NOT NULL UNIQUE,
  senha_hash  VARCHAR(255) NOT NULL
);

-- Dados iniciais (só insere se as tabelas estiverem vazias)
INSERT INTO servicos (nome, duracao_min, preco)
SELECT * FROM (
  SELECT 'Corte clássico' AS nome, 45 AS duracao_min, 55.00 AS preco UNION ALL
  SELECT 'Barba com toalha quente', 30, 40.00 UNION ALL
  SELECT 'Corte e barba', 75, 85.00 UNION ALL
  SELECT 'Acabamento e sobrancelha', 30, 25.00
) AS novos WHERE NOT EXISTS (SELECT 1 FROM servicos);

INSERT INTO barbeiros (nome, especialidade)
SELECT * FROM (
  SELECT 'Rafael' AS nome, 'Cortes clássicos' AS especialidade UNION ALL
  SELECT 'Diego', 'Barba e navalha' UNION ALL
  SELECT 'Marcos', 'Degradê e estilo'
) AS novos WHERE NOT EXISTS (SELECT 1 FROM barbeiros);