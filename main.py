"""AlertaEnchente API: o backend da CitizenTech (SOA & Web Services)."""
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.api.erros import registrar_tratadores
from app.api.rotas import leituras, ocorrencias, regioes, sistema

DESCRICAO = """
Backend do **AlertaEnchente**, CitizenTech para moradores de áreas alagáveis do Jardim Helena (Zona Leste de São Paulo).

* **Regiões:** bairros monitorados, com o córrego e as cotas de alerta e de emergência (CRUD completo).
* **Leituras do sensor:** o ESP32 do córrego envia o nível; o backend classifica o farol verde, amarelo ou vermelho.
* **Ocorrências:** avisos dos moradores (rua alagada, bueiro entupido...), com ciclo de atendimento.

O app de Mobile consome `GET /regioes` no mesmo formato de `src/types.ts`.
Erros sempre voltam como `{"erro": "mensagem"}`: **404** não encontrado, **409** conflito, **422** dados inválidos ou regra violada.
"""

app = FastAPI(
    title="AlertaEnchente API",
    version="1.0.0",
    description=DESCRICAO,
    openapi_tags=[
        {"name": "Regiões", "description": "Bairros monitorados e o farol de risco de cada um"},
        {"name": "Leituras do sensor", "description": "Medições do nível do córrego enviadas pelo ESP32"},
        {"name": "Ocorrências", "description": "Avisos registrados pelos moradores no app"},
        {"name": "Sistema", "description": "Saúde da aplicação"},
    ],
)
app.add_middleware(CORSMiddleware, allow_origins=["*"], allow_methods=["*"], allow_headers=["*"])
registrar_tratadores(app)
for roteador in (regioes, leituras, ocorrencias, sistema):
    app.include_router(roteador)
