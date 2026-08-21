# Youropa Dashboard — índice do projeto

Dashboard publicado em **https://dashboard.youropapt.com**
Repositório: `github.com/giovana-lima/Youropa_Dashboard`

## O que está em cada ficheiro

| Ficheiro | Para que serve |
|---|---|
| `index.html` | O dashboard. HTML + Chart.js, ficheiro único. |
| `data.json` | Os dados que o dashboard lê. **Não editar à mão.** |
| `CNAME` | Domínio próprio do GitHub Pages. |
| `README.md` | Como os dados fluem entre as duas automações. |

## `data/` — as planilhas (fonte de verdade)

| Ficheiro | Conteúdo |
|---|---|
| `imoveis.csv` | Um imóvel por linha: projeto, estado, data da proposta, data do ganho e comercial que fechou. |
| `oportunidades.csv` | Uma oportunidade por linha: data, comercial, operação, tipologia, origem do contacto, imóveis consultados e projeto. |
| `visitas.csv` | Uma visita por linha: data, comercial, imóvel, oportunidade e projeto. |

Sem nomes, telefones ou emails de clientes — o repositório é público.

## `scripts/`

`build_dashboard.py` reconstrói o `data.json` a partir das planilhas.
Corre-o sempre que acrescentares linhas aos CSVs:

```bash
python3 scripts/build_dashboard.py
```

## `workflows/` — automação no GitHub

`inmovilla-full-sync.yml` corre de 3 em 3 dias nos servidores do GitHub e vai
buscar à API do Inmovilla os volumes, comissões, average ticket, new listings e
quarterly comparison. Não precisa do computador ligado.
O token do Inmovilla está guardado como secret `INMOVILLA_TOKEN`.

## `docs/`

- `PASSO_A_PASSO_manual.md` — o que é lido no ecrã do CRM e como.
- `email_suporte_inmovilla.md` — pedido ao suporte para expor o campo "Projeto" na API.

## A outra automação

A tarefa **youropa-dashboard-crm-refresh** corre no Cowork de 3 em 3 dias às 9h e
atualiza as planilhas com o que é novo no CRM. Precisa do computador ligado, do
Chrome aberto e do separador em primeiro plano.
