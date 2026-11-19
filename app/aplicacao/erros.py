class NaoEncontrado(LookupError):
    """O recurso pedido não existe (a API devolve HTTP 404)."""


class Conflito(Exception):
    """A operação conflita com o estado atual dos dados (a API devolve HTTP 409)."""
