"""Testes da API: conferem o contrato do lado de fora (status HTTP e corpo da resposta)."""


def test_lista_regioes_no_formato_do_app_mobile(cliente):
    r = cliente.get("/regioes")
    assert r.status_code == 200
    helena = next(x for x in r.json() if x["id"] == "jardim-helena")
    # mesmos campos de src/types.ts do app, em camelCase
    for campo in ("id", "nome", "corrego", "nivelCm", "cotaAlertaCm", "cotaEmergenciaCm", "atualizadoEm", "orientacao"):
        assert campo in helena
    assert helena["nivelCm"] == 92          # a leitura mais recente
    assert helena["risco"] == "amarelo"
    assert helena["orientacao"].startswith("Fique atento")


def test_crud_completo_de_regiao(cliente):
    criada = cliente.post("/regioes", json={"nome": "Jardim Romano", "corrego": "Córrego Três Pontes",
                                            "cotaAlertaCm": 70, "cotaEmergenciaCm": 110})
    assert criada.status_code == 201
    assert criada.json()["id"] == "jardim-romano"
    assert criada.headers["location"] == "/regioes/jardim-romano"

    assert cliente.get("/regioes/jardim-romano").json()["risco"] == "verde"

    atualizada = cliente.put("/regioes/jardim-romano", json={"nome": "Jardim Romano", "corrego": "Córrego Três Pontes",
                                                             "cotaAlertaCm": 60, "cotaEmergenciaCm": 100})
    assert atualizada.status_code == 200 and atualizada.json()["cotaAlertaCm"] == 60

    assert cliente.delete("/regioes/jardim-romano").status_code == 204
    assert cliente.get("/regioes/jardim-romano").status_code == 404


def test_regiao_com_cotas_invertidas_viola_regra_do_dominio(cliente):
    r = cliente.post("/regioes", json={"nome": "Vila Curuçá", "corrego": "Córrego X",
                                       "cotaAlertaCm": 120, "cotaEmergenciaCm": 100})
    assert r.status_code == 422
    assert "emergência" in r.json()["erro"]


def test_regiao_repetida_da_409(cliente):
    r = cliente.post("/regioes", json={"id": "jardim-helena", "nome": "Jardim Helena", "corrego": "Córrego Itaim",
                                       "cotaAlertaCm": 80, "cotaEmergenciaCm": 120})
    assert r.status_code == 409


def test_formato_invalido_da_422_com_detalhes(cliente):
    r = cliente.post("/regioes", json={"nome": "Ab"})
    assert r.status_code == 422
    assert r.json()["erro"] == "dados inválidos"
    assert any(d["campo"] == "corrego" for d in r.json()["detalhes"])


def test_sensor_registra_leitura_e_o_backend_classifica_o_risco(cliente):
    r = cliente.post("/regioes/itaim-paulista/leituras", json={"nivelCm": 134})
    assert r.status_code == 201
    assert r.json()["risco"] == "vermelho"
    regiao = cliente.get("/regioes/itaim-paulista").json()
    assert regiao["nivelCm"] == 134 and regiao["orientacao"].startswith("Perigo")


def test_codigo_de_falha_do_sensor_e_recusado(cliente):
    r = cliente.post("/regioes/itaim-paulista/leituras", json={"nivelCm": -999})
    assert r.status_code == 422
    assert "sensor" in r.json()["erro"]


def test_leitura_em_regiao_inexistente_da_404(cliente):
    r = cliente.post("/regioes/nao-existe/leituras", json={"nivelCm": 50})
    assert r.status_code == 404
    assert r.json() == {"erro": "região 'nao-existe' não encontrada"}


def test_historico_de_leituras_por_periodo_da_mais_recente_para_a_mais_antiga(cliente):
    todas = cliente.get("/regioes/jardim-helena/leituras").json()
    assert [l["nivelCm"] for l in todas] == [92, 84, 70]
    periodo = cliente.get("/regioes/jardim-helena/leituras",
                          params={"de": "2026-11-15T16:00:00Z", "ate": "2026-11-15T17:00:00Z"}).json()
    assert [l["nivelCm"] for l in periodo] == [84]
    invertido = cliente.get("/regioes/jardim-helena/leituras",
                            params={"de": "2026-11-16T00:00:00Z", "ate": "2026-11-15T00:00:00Z"})
    assert invertido.status_code == 422


def test_ciclo_completo_de_uma_ocorrencia(cliente):
    criada = cliente.post("/ocorrencias", json={"regiaoId": "jardim-helena", "tipo": "bueiro_entupido",
                                                "local": "Rua Três Pontes, perto da escola"})
    assert criada.status_code == 201
    oc = criada.json()
    assert oc["status"] == "aberta" and oc["descricao"] == ""

    assert cliente.patch(f"/ocorrencias/{oc['id']}/status", json={"status": "em_atendimento"}).status_code == 200
    resolvida = cliente.patch(f"/ocorrencias/{oc['id']}/status", json={"status": "resolvida"})
    assert resolvida.json()["status"] == "resolvida"

    reabrir = cliente.patch(f"/ocorrencias/{oc['id']}/status", json={"status": "aberta"})
    assert reabrir.status_code == 422


def test_busca_de_ocorrencias_com_filtro_e_paginacao(cliente):
    for local in ("Rua A, 10", "Rua B, 20", "Rua C, 30"):
        cliente.post("/ocorrencias", json={"regiaoId": "jardim-helena", "tipo": "rua_alagada", "local": local})
    cliente.post("/ocorrencias", json={"regiaoId": "itaim-paulista", "tipo": "entulho", "local": "Praça Central"})

    pagina = cliente.get("/ocorrencias", params={"regiaoId": "jardim-helena", "status": "aberta",
                                                 "pagina": 1, "tamanho": 2}).json()
    assert pagina["total"] == 3 and len(pagina["itens"]) == 2
    assert pagina["itens"][0]["local"] == "Rua C, 30"        # mais recente primeiro
    segunda = cliente.get("/ocorrencias", params={"regiaoId": "jardim-helena", "pagina": 2, "tamanho": 2}).json()
    assert len(segunda["itens"]) == 1


def test_ocorrencia_sem_local_ou_com_tipo_invalido_da_422(cliente):
    assert cliente.post("/ocorrencias", json={"regiaoId": "jardim-helena", "tipo": "rua_alagada",
                                              "local": " "}).status_code == 422
    assert cliente.post("/ocorrencias", json={"regiaoId": "jardim-helena", "tipo": "terremoto",
                                              "local": "Rua A"}).status_code == 422


def test_regiao_com_ocorrencia_nao_pode_ser_apagada(cliente):
    cliente.post("/ocorrencias", json={"regiaoId": "itaim-paulista", "tipo": "entulho", "local": "Praça Central"})
    r = cliente.delete("/regioes/itaim-paulista")
    assert r.status_code == 409


def test_documentacao_openapi_tem_tags_e_erros(cliente):
    spec = cliente.get("/openapi.json").json()
    post_leitura = spec["paths"]["/regioes/{regiao_id}/leituras"]["post"]
    assert post_leitura["tags"] == ["Leituras do sensor"]
    assert {"201", "404", "422"} <= set(post_leitura["responses"])
    assert all(op.get("summary") for caminho in spec["paths"].values() for op in caminho.values())
