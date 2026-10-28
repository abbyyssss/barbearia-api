# Navalha & Co. – API de agendamento

API REST do sistema de agendamento da barbearia fictícia **Navalha & Co.**, feita com Python, FastAPI e MySQL. Ela cuida das regras de horários, do cadastro dos agendamentos e do login do painel.

🔗 **Site que usa esta API:** [barbearia-agendamento](https://github.com/abbyyssss/barbearia-agendamento)
🔗 **API no ar (documentação interativa):** https://barbearia-api-s291.onrender.com/docs

> Projeto de portfólio. A barbearia e os dados são fictícios.

## ✨ O que a API faz

- Lista serviços e barbeiros
- Calcula os **horários livres** de um barbeiro em um dia, conforme a duração do serviço
- Cria agendamentos **sem permitir conflito de horário**, mesmo com pedidos simultâneos
- Recusa datas passadas, datas além de 30 dias, domingos e horários fora do expediente
- Protege o painel com **login (JWT)**: listar e cancelar agendamentos exige estar autenticado

## 🔌 Rotas

| Método | Rota | O que faz | Acesso |
|---|---|---|---|
| GET | `/servicos` | Lista os serviços | Público |
| GET | `/barbeiros` | Lista os barbeiros | Público |
| GET | `/horarios?barbeiro_id=&servico_id=&data=` | Horários livres do dia | Público |
| POST | `/agendamentos` | Cria um agendamento | Público |
| POST | `/login` | Autentica o administrador | Público |
| GET | `/agendamentos` | Lista os próximos agendamentos | Login |
| PATCH | `/agendamentos/{id}/cancelar` | Cancela e libera o horário | Login |

Com a API rodando, a documentação interativa fica em `/docs`.

## 🧠 Decisões técnicas

- **Regras no servidor:** o site valida para dar conforto, mas quem decide é a API.
- **Sem horários duplicados:** o agendamento roda em uma transação que trava a linha do barbeiro antes de consultar os horários. Dois pedidos para o mesmo horário não passam juntos: o segundo recebe erro 409.
- **Senhas com hash (bcrypt)** e login por token JWT com validade.
- **Segredos fora do código:** senha do banco e chave do token ficam em variáveis de ambiente (`.env`, que não vai para o GitHub).
- **CORS restrito:** só os endereços listados em `CORS_ORIGINS` podem chamar a API pelo navegador.
- **Código dividido por responsabilidade:** rotas, regras de negócio, modelos, esquemas de dados e segurança em arquivos separados.

## 🛠️ Tecnologias

Python · FastAPI · SQLAlchemy · MySQL · PyJWT · bcrypt · Pydantic

## 📁 Estrutura

```
barbearia-api/
├── app/
│   ├── main.py          # cria a API e liga as rotas
│   ├── config.py        # configurações (lidas do .env)
│   ├── database.py      # conexão com o MySQL
│   ├── models.py        # tabelas como classes Python
│   ├── schemas.py       # formato dos dados que entram e saem
│   ├── security.py      # hash de senha e login (JWT)
│   ├── regras.py        # expediente, prazos e conflito de horários
│   └── routers/
│       ├── publico.py   # rotas abertas
│       └── painel.py    # login e rotas protegidas
├── schema.sql           # banco de dados para uso local
├── schema_nuvem.sql     # o mesmo, para o banco na nuvem
├── criar_admin.py       # cria o usuário do painel
├── requirements.txt
└── .env.example
```

## ▶️ Como rodar localmente

Precisa de Python 3.10+ e MySQL.

1. Crie o banco executando o `schema.sql` no MySQL Workbench.
2. Copie `.env.example` para `.env` e preencha `DATABASE_URL` e `JWT_SECRET`.
3. No terminal, dentro da pasta do projeto:
   ```bash
   python -m venv .venv
   .venv\Scripts\activate        # no Windows
   pip install -r requirements.txt
   python criar_admin.py         # cria o usuário do painel
   uvicorn app.main:app --reload
   ```
4. Abra http://127.0.0.1:8000/docs

## ☁️ Publicação

```
Site (GitHub Pages) → API (Render) → Banco MySQL (Aiven)
```

- **API:** serviço web no Render (plano gratuito), com deploy automático a cada `git push` na `main`.
- **Banco:** MySQL gerenciado na Aiven, com conexão criptografada (SSL) usando o certificado em `certs/`.
- **Configuração:** variáveis de ambiente no Render (`DATABASE_URL`, `JWT_SECRET`, `DB_SSL_CA`, `CORS_ORIGINS`). Nada de segredo vai para o repositório.

Para usar um MySQL na nuvem em outro ambiente, rode o `schema_nuvem.sql`, aponte o `DATABASE_URL` para o servidor e informe o certificado em `DB_SSL_CA`.

> No plano gratuito, a API dorme depois de um tempo sem uso, e a primeira requisição pode demorar cerca de 1 minuto.

## 🗺️ Próximos passos

- [x] Rotas públicas e painel com login
- [x] Proteção contra horários duplicados
- [x] Publicar a API na nuvem
- [ ] Testes automatizados
- [ ] Limite de tentativas de login

## 👤 Autor

**Kauan Quaresma**
[LinkedIn](https://www.linkedin.com/in/kauan-quaresma-3a8ba5356/) · [GitHub](https://github.com/abbyyssss)
