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

## Never estimate

Every figure on this dashboard is read from Inmovilla. If a value is missing there, it
stays **empty** — no averages, no percentages inferred from other deals, no filling in
of gaps. An empty card is information ("nobody filled this in"); an invented number is
not, and it is worse than nothing when someone is judging a broker or a campaign by it.

## Commission

Commission comes from the `comision` field in Inmovilla. When a closed deal has no value
there, `build_dashboard.py` looks in `data/imoveis.csv` — but only ever for a real value
that came from the CRM.

Currently missing: **Ref. 34775273** (280.000 €, sold 22 Aug by Eugénia Miranda) has no
commission recorded, so it contributes 0 to the commission KPIs until it is filled in.

## Known gaps

- Sale visits show as 0: they either aren't booked in the Agenda or are logged under another type.
- 106 opportunities point at properties that are no longer in `imoveis.csv` (delisted or
  "Não Disponível"), so they have no project.
- Commission figures only appear once the `comision` field is filled in on a deal in Inmovilla.

## One source per number

Everything on screen is recomputed in the browser from `records[]` and `transactions[]`
for the selected date range, so two cards can never be built by two different rules.

- **Closed deals** are a single list in `scripts/build_dashboard.py`. Total Volume, the
  funnel's Contract Signed / Commission Paid steps, Quarterly Comparison, Brokers
  Performance and the broker pop-up all read it.
- **The closing date** is the day the property entered *Ganho* in the CRM state history,
  never the API's `fechacambio` (that is the last record-change date and still carries the
  bulk-import dates of 12/06 and 23/06).
- **A deal only counts as closed** if the property is still in a closed state. Properties
  that went to Ganho and back on the market do not count.
- **A closed deal sits in the period it closed in** at every funnel stage, including Offer.
  Only proposals still open keep the day they were logged.
- **Visits** are typed sale or rental from the property visited, or failing that from the
  opportunity behind them. Visits with neither stay untyped: they count in the Visits card,
  which says how many, and belong to no funnel.
- **New Listings** counts only properties with a real creation date. Inmovilla has none for
  204 of 310 records, and those are left out rather than guessed.
- The GitHub Action refreshes `transactions[]` from the API and then runs
  `scripts/build_dashboard.py`, so both pipelines end in the same code.
