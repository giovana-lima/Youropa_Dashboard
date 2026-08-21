#!/usr/bin/env python3
"""Rebuild data.json from the CSV spreadsheets in data/.

The CSVs are the source of truth for everything that lives only on the CRM
screen (opportunities, visits, projects, who closed each deal). Money figures
(volumes, commissions, new listings) are refreshed separately by the GitHub
Action that talks to the Inmovilla REST API, so this script leaves them alone.

Usage:  python3 scripts/build_dashboard.py
"""
import csv, json, collections, datetime, os, sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
D = lambda *p: os.path.join(ROOT, *p)

def read(name):
    path = D('data', name)
    if not os.path.exists(path):
        return []
    with open(path, encoding='utf-8') as f:
        return list(csv.DictReader(f))

opp = read('oportunidades.csv')
vis = read('visitas.csv')
imo = read('imoveis.csv')

if not opp:
    sys.exit('data/oportunidades.csv is empty - nothing to build')

SALE_OPS = ('Vender', 'Venda')
def prop_type(r):
    return 'sale' if r.get('operacao') in SALE_OPS else 'rental'

def quarter(mk):
    y, m = mk.split('-')
    return 'Q%d %s' % ((int(m) - 1) // 3 + 1, y)

# ---- months actually covered by the data -------------------------------
months = sorted(
    {r['mes'] for r in opp if r.get('mes')}
    | {r['mes'] for r in vis if r.get('mes')}
    | {r['estado_ganho_data'][:7] for r in imo if r.get('estado_ganho_data')}
)
months = [m for m in months if m >= '2026-06']

# ---- funnel ------------------------------------------------------------
leads = collections.Counter(
    (r['mes'], 'rental' if r['operacao'] == 'arrendamento' else 'sale')
    for r in opp if r.get('mes') in months
)
visits = collections.Counter((v['mes'], 'rental') for v in vis if v.get('mes') in months)

offer, contract = collections.Counter(), collections.Counter()
for r in imo:
    t = prop_type(r)
    won, proposed = r.get('estado_ganho_data', ''), r.get('proposta_data', '')
    first = proposed or won          # a won deal always passed through "offer"
    if first and first[:7] in months:
        offer[(first[:7], t)] += 1
    if won and won[:7] in months:
        contract[(won[:7], t)] += 1

STAGES = [('opportunity', leads), ('visit_scheduled', visits),
          ('offer', offer), ('contract_signed', contract), ('win', contract)]
funnel = [
    {'month': m, 'quarter': quarter(m), 'type': t, 'stage': s, 'count': src.get((m, t), 0)}
    for m in months for t in ('rental', 'sale') for s, src in STAGES
]

# ---- marketing origin --------------------------------------------------
origin = collections.Counter()
for r in opp:
    o = (r.get('origem_contacto') or '').strip()
    if not o:
        continue
    low = o.lower()
    if 'idealista' in low: o = 'idealista'
    elif 'imovirtual' in low: o = 'imovirtual'
    origin[o] += 1

# ---- leads per project -------------------------------------------------
per_project = collections.Counter()
for r in opp:
    for p in filter(None, (r.get('projetos') or '').split(';')):
        per_project[p] += 1

# ---- brokers -----------------------------------------------------------
FULL = {'Sandra': 'Sandra Dantas', 'Eugénia': 'Eugénia Miranda',
        'Joana': 'Joana Côrte-Real', 'Teresa': 'Teresa Archer',
        'Andreia': 'Andreia Ferreirinha Marinho'}
b_leads = collections.Counter()
for r in opp:
    c = (r.get('comercial') or '').strip()
    if c and c != '.':
        b_leads[FULL.get(c, c)] += 1
b_visits = collections.Counter(v['comercial'] for v in vis if v.get('comercial'))
b_closed = collections.Counter(r['estado_ganho_utilizador'] for r in imo
                               if r.get('estado_ganho_utilizador'))

agents = [{'name': n, 'leads': b_leads.get(n, 0),
           'visits': b_visits.get(n, 0), 'closedDeals': b_closed.get(n, 0)}
          for n in sorted(set(b_leads) | set(b_visits), key=lambda x: -b_leads.get(x, 0))
          if n in FULL.values()]

# ---- record-level data (lets the dashboard filter by any date range) ----
# Compact arrays keep data.json small. No client names, phones or emails.
rec_opp = [[r['data_criacao'],
            'rental' if r['operacao'] == 'arrendamento' else 'sale',
            FULL.get((r.get('comercial') or '').strip(), (r.get('comercial') or '').strip()),
            (r.get('origem_contacto') or '').strip(),
            (r.get('projetos') or '')]
           for r in opp if r.get('data_criacao')]

rec_vis = [[v['data'], (v.get('comercial') or ''), (v.get('projeto') or '')]
           for v in vis if v.get('data')]

rec_offer, rec_win, rec_listing = [], [], []
for r in imo:
    t = prop_type(r)
    proj = r.get('projeto', '')
    # a won deal always passed through the offer stage, even if no proposal was logged
    offer_date = r.get('proposta_data') or r.get('estado_ganho_data')
    if offer_date:
        rec_offer.append([offer_date, t, proj])
    if r.get('estado_ganho_data'):
        rec_win.append([r['estado_ganho_data'], t,
                        r.get('estado_ganho_utilizador', ''), proj])
    if r.get('data_criacao'):
        rec_listing.append([r['data_criacao'], t])

# ---- write -------------------------------------------------------------
with open(D('data.json'), encoding='utf-8') as f:
    d = json.load(f)

today = datetime.date.today().isoformat()
d['funnel'] = funnel
d['meta']['months'] = months
d['meta']['generatedOn'] = today
d['meta']['leadsSnapshotOn'] = today
d['meta']['leadsSnapshotTotal'] = len(opp)
d['monthlyMargin'] = {m: d.get('monthlyMargin', {}).get(m, 0.85) for m in months}
d['marketingOrigin'] = {'asOf': today, 'byChannel': dict(origin.most_common()),
                        'note': 'Contact origin recorded on each Oportunidade record.'}
d['leadsPerProject'] = {'asOf': today, 'byProject': dict(per_project.most_common()),
                        'note': 'Opportunities linked to a project through the properties they consulted.'}
d['brokerPerformance'] = {'asOf': today, 'period': '%s to %s' % (months[0], months[-1]),
                          'note': '', 'agents': agents}
k = d['kpisApi']
k['totalLeads'] = sum(f['count'] for f in funnel if f['stage'] == 'opportunity')
k['visits'] = sum(f['count'] for f in funnel if f['stage'] == 'visit_scheduled')
k['visitsSale'] = sum(f['count'] for f in funnel if f['stage'] == 'visit_scheduled' and f['type'] == 'sale')
k['visitsRental'] = k['visits'] - k['visitsSale']
k['totalLeadsNote'] = k['visitsNote'] = ''

d['records'] = {
    'schema': {
        'opportunities': ['date', 'type', 'broker', 'origin', 'projects'],
        'visits': ['date', 'broker', 'project'],
        'offers': ['date', 'type', 'project'],
        'wins': ['date', 'type', 'broker', 'project'],
        'listings': ['date', 'type'],
    },
    'opportunities': rec_opp,
    'visits': rec_vis,
    'offers': rec_offer,
    'wins': rec_win,
    'listings': rec_listing,
}

with open(D('data.json'), 'w', encoding='utf-8') as f:
    json.dump(d, f, indent=2, ensure_ascii=False)

print('months        :', months)
print('opportunities :', len(opp))
print('visits        :', len(vis))
print('properties    :', len(imo))
print('total leads   :', k['totalLeads'])
for t in ('rental', 'sale'):
    print(t, {s: sum(f['count'] for f in funnel if f['stage'] == s and f['type'] == t)
              for s, _ in STAGES})
