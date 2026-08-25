# Youropa Dashboard

Live at **https://dashboard.youropapt.com**

## How the data flows

```
Inmovilla REST API  ──(GitHub Action, every 3 days)──►  data.json   ┐
                                                                    ├─►  index.html
data/*.csv  ──(scripts/build_dashboard.py)────────────►  data.json  ┘
     ▲
     └── Cowork scheduled task, every 3 days (reads the CRM screen)
```

Two independent sources, because Inmovilla only exposes part of the data:

| Source | What it feeds | Needs a computer on? |
|---|---|---|
| **REST API** (`.github/workflows/inmovilla-full-sync.yml`) | Volumes, commissions, average ticket, new listings, quarterly comparison, transactions | No — runs on GitHub |
| **CRM screen** (Cowork scheduled task) | Opportunities, visits, projects, contact origin, who closed each deal | Yes — Chrome open and in the foreground |

## The spreadsheets are the source of truth

Everything that only exists on the CRM screen lives in `data/`:

- **`imoveis.csv`** — one row per property: project, state, proposal date, won date and the broker who won it.
  Properties in state "Não Disponível" are skipped.
- **`oportunidades.csv`** — one row per opportunity: creation date, broker, operation, typology,
  contact origin, the properties it consulted and the project(s) those belong to.
- **`visitas.csv`** — one row per visit: date, broker, property, opportunity and project.

Never hand-edit numbers in `data.json`. Add rows to the CSVs and run:

```bash
python3 scripts/build_dashboard.py
```

That rebuilds the funnel, marketing origin, leads per project, broker performance and the
lead/visit KPIs. It deliberately leaves the API-sourced money figures untouched.

## Date filter

The dashboard has no fixed periods. Two date pickers define any range you want.

**Follows the date range:** KPIs, Brokers Performance, Marketing Origin, Leads per Project,
Proposals and both conversion funnels.

**Deliberately ignores it:** New Listings by Month, Quarterly Comparison, Leads by Month,
Leads by Quarter and the Monthly Summary. These exist to compare periods against each
other, so they always show the full history — narrowing the range would leave nothing to
compare. They still follow the Sales/Rental filter.

Each time the page opens it defaults to **the 1st of the current month → today**, so the
link always shows the month in progress without anyone touching the filter. The
"This month" button returns to that default.

This works because `data.json` carries the individual records (dates only, no personal
data) under `records`, not pre-aggregated monthly totals.

## Privacy

The repository is public, so the CSVs carry **no client names, phone numbers or emails** —
only ids, dates and metrics.

## Commission

Commission comes from the `comision` field in Inmovilla. When a closed deal has no value
there, `build_dashboard.py` falls back to the value in `data/imoveis.csv`. Rows flagged
`comissao_estimada = sim` are estimates, and the KPI card says "includes an estimate".
As soon as the real figure is entered in Inmovilla, the API value wins automatically and
the flag should be cleared in the CSV.

Currently estimated: **Ref. 34775273** (280.000 €, sold 22 Aug by Eugénia Miranda) —
14.000 € assumed at 5%, matching the only other own-sale on record.

## Known gaps

- Sale visits show as 0: they either aren't booked in the Agenda or are logged under another type.
- 106 opportunities point at properties that are no longer in `imoveis.csv` (delisted or
  "Não Disponível"), so they have no project.
- Commission figures only appear once the `comision` field is filled in on a deal in Inmovilla.
