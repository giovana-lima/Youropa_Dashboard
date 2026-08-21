# Atualização do dashboard — passo a passo da parte manual

Documento para revisão. A parte automática (GitHub Action) não está aqui: essa trata de
volumes, comissões, average ticket, new listings e quarterly comparison, e corre sozinha
de 3 em 3 dias sem computador ligado.

O que está descrito abaixo é o que **só existe no ecrã do CRM** e por isso obriga a abrir o
Inmovilla no Chrome.

---

## 0. Antes de começar

1. Chrome aberto, com sessão já iniciada em `https://crm.inmovilla.com/panel/`.
   As credenciais estão guardadas no browser — nunca as escrevo.
2. **Separador em primeiro plano.** O Chrome trava os temporizadores de separadores em
   segundo plano, o que faz a paginação andar a ~1 página por minuto em vez de ~1 por segundo.
   Verifico `document.visibilityState`; se estiver `hidden`, paro e peço-te para trazeres a
   janela à frente.

---

## 1. Total Leads (total de oportunidades)

**Onde:** módulo Oportunidades.

1. Entro em Oportunidades.
2. **Removo o filtro predefinido.** Ao entrar, o CRM aplica uma "Consulta Predefinida" que
   mostra só um punhado de registos (já apareceu 6). Clico no `x` do chip para o tirar.
3. Leio o número em "N Resultados".

**Valor que alimenta:** KPI *Total Leads*.

> ⚠️ Este número muda ao longo do dia — entram leads dos portais continuamente. Em leituras
> seguidas no mesmo dia já vi 571, 576 e 579.

---

## 2. Leads por mês e por tipo de operação

**Onde:** mesma lista de Oportunidades, sem filtros.

1. Percorro a lista página a página (10 por página, ~58 páginas).
2. Em cada linha leio:
   - **id** da oportunidade (para não contar o mesmo registo duas vezes)
   - **Data Criação** → define o mês
   - se o preço tem **"/ MES"** → arrendamento; caso contrário → venda
3. Somo por mês e por tipo.

**Valores que alimentam:** gráfico *Leads by Month*, *Leads by Quarter*, e o degrau
*Qualified* dos dois funis.

**Última leitura (12/08):** Jun 65 (52 arrend. / 13 venda), Jul 226 (204/22), Ago 285 (275/10)
— 576 de 579 registos lidos.

---

## 3. Leads por comercial

**Onde:** Oportunidades → filtro "Gerido Por".

1. Abro o filtro e seleciono **um comercial de cada vez**.
2. Aplico e leio o total de resultados.
3. Repito para: Eugénia Miranda, Sandra Dantas, Joana Côrte-Real, Teresa Archer.
   Giovana Lima e utilizadores administrativos ficam de fora.

> ⚠️ **Os filtros acumulam.** Ao reabrir o dropdown as caixas aparecem desmarcadas, mas o
> filtro anterior continua ativo por baixo. Confirmo sempre no chip do topo quantos comerciais
> estão selecionados — se disser "Come., Come." são dois, e calculo o valor de cada um por
> diferença.

**Valor que alimenta:** coluna *Leads* da tabela Brokers Performance.

**Última leitura (12/08):** Eugénia 186, Sandra 151, Joana 150, Teresa 32 (519 dos 571 ativos;
os restantes 52 estão sem comercial atribuído ou com utilizadores administrativos).

---

## 4. Visitas por mês e por comercial

**Onde:** módulo Agenda.

1. Visualização → **"Lista mensal"**.
2. Filtro **"Seguimento de Tarefa / Nota"**: existem **duas** entradas chamadas exatamente
   "Visita". Marco as duas por completo — marcar o pai seleciona todos os subtipos
   (Presencial, Online, 1ª Visita, arrendamento, venda, etc.).
3. Filtro **"Categoria"**: marco **Ativas** e **Concluídas** (só Ativas deixa de fora as
   visitas já realizadas).
4. Filtro **"Comerciais"**: marco os quatro.
5. Navego mês a mês com as setas `‹ ›` e conto as linhas por comercial.
6. Confiro o meu total com o contador "Tarefas: N" no topo.

**Valores que alimentam:** KPI *Visits*, coluna *Visits* dos brokers, degrau
*Visit Scheduled* do funil.

**Última leitura (12/08):** Jun 3, Jul 13, Ago 8 = 24 no total, nenhuma cancelada.
Por comercial: Sandra 11, Eugénia 8, Teresa 5, Joana 0.

> **Ponto para decidires:** estou a incluir as visitas já agendadas para datas futuras
> (foi o que pediste com o "inclui tudo"). Se preferires só as que já aconteceram, é aqui
> que mudo.

---

## 5. Publicar

1. Clono o repositório e edito **apenas** os campos desta parte manual:
   `totalLeads`, `visits`, `brokerPerformance`, e os degraus `opportunity` e
   `visit_scheduled` do funil.
   Não toco em `transactions`, `newPropertiesByMonth`, `quarterlyComparisonCounts` nem nos
   KPIs de volume/comissão — esses são do GitHub Action.
2. Valido o JSON.
3. Confirmo que a soma do degrau *Qualified* bate com o Total Leads lido.
4. Commit e push. O site republica em 1-2 minutos.

---

## Regras que sigo sempre

- Dashboard todo em **inglês**, sem texto em português visível.
- Se não consigo um valor, **deixo vazio** — não invento nem escrevo textos longos a explicar
  a falta.
- Edito sempre os mesmos ficheiros, nunca crio novos.

---

## O que continua por resolver

| Item | Situação |
|---|---|
| **Closed Deals por comercial** | Os fechos ficam registados no imóvel, não na oportunidade, por isso não consigo atribuí-los a um comercial. Falta encontrar onde isso aparece por comercial no CRM. |
| **Leads per Project** | O campo "Projeto" não vem na API. À espera de resposta do suporte do Inmovilla. |
| **Marketing — Origin** | A API tem os leads de portal com o canal, mas ainda não liguei essa parte ao dashboard. |
| **Offer / Contract Signed** | O CRM não regista estes estados de forma distinta, por isso os dois degraus do meio do funil estão a 0. |
