# Registro de uso de IA · AlertaEnchente API (SOA e Web Services)

> Global Solution 2026.2 · FIAP · Engenharia de Software (3º ano)
> Conforme os combinados da GS, registramos aqui como a IA generativa foi usada. Neste módulo, a IA teve um papel grande: o backend foi estruturado e escrito com o apoio dela, a partir do guia da disciplina. As decisões, a revisão e a validação couberam à equipe.

## Visão geral

| Item | Detalhe |
|---|---|
| Ferramenta | Claude (Anthropic) |
| Papel da IA | Ler o guia da disciplina e propor a arquitetura em camadas. Escrever o domínio, os repositórios, as migrações, as rotas e os testes. Executar a API e os testes e gerar as evidências |
| Papel da equipe | Definir o problema e a CitizenTech (o AlertaEnchente), exigir que a API seguisse o contrato do app de Mobile, revisar cada camada e conferir as evidências |
| Dados usados nas conversas | Só dados simulados (regiões, cotas e níveis de demonstração). Nenhum dado pessoal |
| IA dentro do produto | Não há: a API não chama nenhum modelo de IA |

---

## Prompts e resultados

| # | Objetivo | Prompt (resumo fiel) | Resultado e validação |
|---|---|---|---|
| 1 | Entender a entrega | Leitura do guia da disciplina (página HTML do professor) e do slide de SOA da GS, para montar um plano completo que buscasse a nota máxima. | Plano cobrindo os 22 itens de autoavaliação dos 5 critérios (domínio, banco, migrações, documentação e testes). |
| 2 | Integrar com a CitizenTech | Desenhar a API para o app de Mobile ler os dados dela sem mudar nada no app, e para o sensor ESP32 enviar as leituras. | `GET /regioes` no mesmo formato de `src/types.ts` do app, e `POST /regioes/{id}/leituras` para o sensor. A mesma regra do farol do app foi levada para o domínio. |
| 3 | Construir o backend | Pedido para construir do zero, em Python, com domínio em camadas, PostgreSQL, Alembic, Swagger e pytest. | Entidades Região, Leitura e Ocorrência com as regras no domínio, CRUD de Região, 2 chaves estrangeiras, consultas por período e com paginação, e 3 migrações (criação, carga simulada e evolução). |
| 4 | Comprovar | Executar tudo de verdade antes de entregar. | 38 testes passando. Banco criado do zero pelas migrações num PostgreSQL 17 real. App de Mobile lendo a API e mudando para PERIGO quando o "sensor" envia 125 cm. |
| 5 | Revisar a documentação | Conferir a página do Swagger contra a rubrica. | Encontrado um problema: os erros 404 e 422 mostravam o mesmo exemplo genérico. Corrigido para cada código ter o seu exemplo. |

---

## Compromissos da equipe

- Antes da entrega, cada integrante leu as quatro camadas (`dominio`, `aplicacao`, `infraestrutura` e `api`) e sabe explicar onde mora cada regra.
- Nenhum dado pessoal real: as ocorrências guardam só o local e a descrição do problema.
- A senha do banco fica só no `.env` local, fora do Git (há um `.env.example` de modelo).
