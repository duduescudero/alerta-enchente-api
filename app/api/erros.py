"""Transforma as exceções do domínio e da aplicação em respostas HTTP previsíveis."""
from fastapi import FastAPI, Request
from fastapi.encoders import jsonable_encoder
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse

from app.api.esquemas import Erro
from app.aplicacao.erros import Conflito, NaoEncontrado
from app.dominio.erros import RegraViolada


def _resposta(status: int, mensagem: str, detalhes=None) -> JSONResponse:
    corpo = {"erro": mensagem}
    if detalhes is not None:
        corpo["detalhes"] = jsonable_encoder(detalhes)
    return JSONResponse(status_code=status, content=corpo)


def registrar_tratadores(app: FastAPI) -> None:
    @app.exception_handler(NaoEncontrado)
    async def _404(_: Request, exc: NaoEncontrado):
        return _resposta(404, str(exc))

    @app.exception_handler(Conflito)
    async def _409(_: Request, exc: Conflito):
        return _resposta(409, str(exc))

    @app.exception_handler(RegraViolada)
    async def _422_regra(_: Request, exc: RegraViolada):
        return _resposta(422, str(exc))

    @app.exception_handler(RequestValidationError)
    async def _422_formato(_: Request, exc: RequestValidationError):
        detalhes = [{"campo": ".".join(str(p) for p in e["loc"][1:]), "problema": e["msg"]} for e in exc.errors()]
        return _resposta(422, "dados inválidos", detalhes)


_DOCUMENTACAO_DOS_ERROS = {
    404: ("Não encontrado", {"erro": "região 'vila-nova' não encontrada"}),
    409: ("Conflito com o estado atual dos dados", {"erro": "já existe uma região com o id 'jardim-helena'"}),
    422: ("Dados inválidos (formato) ou regra do domínio violada", {
        "examples": {
            "regra do domínio": {"value": {"erro": "nível fora do alcance do sensor (0 a 2000 cm): -999"}},
            "formato inválido": {"value": {"erro": "dados inválidos",
                                           "detalhes": [{"campo": "nivelCm", "problema": "Field required"}]}},
        }}),
}


def erros(*codigos: int) -> dict:
    """Documenta no Swagger as respostas de erro de cada endpoint, com um exemplo para cada código."""
    respostas = {}
    for c in codigos:
        descricao, exemplo = _DOCUMENTACAO_DOS_ERROS[c]
        conteudo = exemplo if "examples" in exemplo else {"example": exemplo}
        respostas[c] = {"model": Erro, "description": descricao, "content": {"application/json": conteudo}}
    return respostas
