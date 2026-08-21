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

## Privacy

The repository is public, so the CSVs carry **no client names, phone numbers or emails** —
only ids, dates and metrics.

## Known gaps

- Sale visits show as 0: they either aren't booked in the Agenda or are logged under another type.
- 106 opportunities point at properties that are no longer in `imoveis.csv` (delisted or
  "Não Disponível"), so they have no project.
- Commission figures only appear once the `comision` field is filled in on a deal in Inmovilla.
