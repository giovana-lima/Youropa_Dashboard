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
def _num(v):
    try:
        return float(v or 0)
    except ValueError:
        return 0.0

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
# Sale or rental for a visit is not recorded on the Agenda entry, so it is read from the
# property that was visited, and failing that from the opportunity behind it. Visits that
# resolve to neither stay untyped: they are counted in the totals but belong to no funnel.
_op_by_ref = {r['ref']: prop_type(r) for r in imo if r.get('ref')}
_op_by_opp = {r['id_oportunidade']: ('rental' if r['operacao'] == 'arrendamento' else 'sale')
              for r in opp if r.get('id_oportunidade')}

def visit_type(v):
    return (_op_by_ref.get((v.get('imovel_ref') or '').strip())
            or _op_by_opp.get((v.get('id_oportunidade') or '').strip())
            or '')

visits = collections.Counter((v['mes'], visit_type(v)) for v in vis
                             if v.get('mes') in months and visit_type(v))

# A property can enter Ganho and later be put back on the market. Only count it as closed
# if it is still in a closed state today - otherwise reverted deals inflate the funnel.
CLOSED = {'Vendido', 'Arrendado', 'Vendido MLS', 'Arrendado MLS'}

def won_on(r):
    """Day the property entered Ganho, or '' if it is not a closed deal today."""
    d = (r.get('estado_ganho_data') or '')[:10]
    return d if len(d) == 10 and r.get('estado') in CLOSED else ''

def amount_of(r):
    v = r.get('preco_venda') if prop_type(r) == 'sale' else r.get('preco_arrendamento')
    try:
        return float(v or 0)
    except ValueError:
        return 0.0

# The single closed-deal list. Volume, the funnel, Brokers Performance, Quarterly
# Comparison and the broker pop-up all read this, so they cannot tell different stories.
deals = [{'ref': r.get('ref', ''), 'date': won_on(r), 'type': prop_type(r),
          'amount': amount_of(r), 'broker': (r.get('estado_ganho_utilizador') or '').strip(),
          'project': r.get('projeto', ''),
          'commission': _num(r.get('comissao')),
          'assignmentCommission': _num(r.get('comissao_cessao'))}
         for r in imo if won_on(r)]

offer, contract = collections.Counter(), collections.Counter()
for r in imo:
    t = prop_type(r)
    won, proposed = won_on(r), r.get('proposta_data', '')
    # A closed deal is dated by the day it closed at every stage, so the funnel reads the
    # same way top to bottom. Only proposals still open keep the day they were logged.
    # Without this, a proposal logged in July for a deal closed in August showed up as
    # Offer 9 / Contract Signed 11 in August.
    first = won or proposed
    if first and first[:7] in months:
        offer[(first[:7], t)] += 1
for x in deals:
    if x['date'][:7] in months:
        contract[(x['date'][:7], x['type'])] += 1

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
b_visits = collections.Counter(FULL.get((v.get('comercial') or '').strip(),
                                        (v.get('comercial') or '').strip())
                               for v in vis if v.get('comercial'))
b_closed = collections.Counter(x['broker'] for x in deals if x['broker'])

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

rec_vis = [[v['data'],
            FULL.get((v.get('comercial') or '').strip(), (v.get('comercial') or '').strip()),
            (v.get('projeto') or ''), visit_type(v)]
           for v in vis if v.get('data')]

rec_win = [[x['date'], x['type'], FULL.get(x['broker'], x['broker']),
            x['project'], x['ref'], x['amount']] for x in deals]

rec_offer, rec_listing = [], []
for r in imo:
    t = prop_type(r)
    # same rule as the funnel: closed deals sit in the period they closed in
    offer_date = won_on(r) or r.get('proposta_data')
    if offer_date:
        rec_offer.append([offer_date, t, r.get('projeto', '')])
    # Inmovilla has no creation date for 204 of the 310 records, so New Listings only
    # counts the ones that carry a real date. Months before the account started (the
    # first month with an opportunity or a closed deal) are stray imported records.
    created = (r.get('data_criacao') or '')[:10]
    if len(created) == 10 and created[:7] >= months[0]:
        rec_listing.append([created, t])

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

# transactions[] is the same closed-deal list the funnel and Brokers Performance use, so
# Total Volume, Closed Deals and Quarterly Comparison can never tell different stories.
# Dates are the day the property entered Ganho in the CRM state history, never the API's
# fechacambio (that is the last record-change date and still carries import dates).
# Commissions are the real comision/cesioncom values - never estimated. A deal with no
# commission recorded stays at zero until someone fills it in the CRM.
api_tx = {(t.get('project') or '').replace('Ref. ', ''): t for t in d.get('transactions', [])}
tx = []
for i, x in enumerate(sorted(deals, key=lambda x: x['date']), 1):
    tx.append({'id': 'R%05d' % i, 'date': x['date'], 'amount': x['amount'],
               'type': x['type'], 'commission': x['commission'],
               'assignmentCommission': x['assignmentCommission'],
               'channel': '', 'category': '', 'project': 'Ref. %s' % x['ref'],
               'region': '', 'clientId': '', 'quarter': quarter(x['date'][:7]),
               'month': x['date'][:7]})

# A deal the API already reports as sold or rented but that the CRM pass has not picked up
# yet is kept, so the every-3-days API sync is never rolled back by an older spreadsheet.
known = {x['ref'] for x in deals}
for ref, t in api_tx.items():
    if ref not in known and t.get('date'):
        t['id'] = 'R%05d' % (len(tx) + 1)
        tx.append(t)
d['transactions'] = tx

qc = collections.OrderedDict()
for t in tx:
    qc.setdefault(t['quarter'], {'quarter': t['quarter'], 'sales': 0, 'rentals': 0})
    qc[t['quarter']]['sales' if t['type'] == 'sale' else 'rentals'] += 1
d['quarterlyComparisonCounts'] = [qc[q] for q in
                                  sorted(qc, key=lambda q: (q.split()[1], q.split()[0]))]

# Keys nothing reads any more. They were recomputed by a different rule than the charts,
# so leaving them in data.json meant two versions of the same number sitting side by side.
for dead in ('leadsByTypology', 'leadsByOperation', 'proposalsThisMonth', 'monthlyMargin',
             'newPropertiesByMonth'):
    d.pop(dead, None)

d['records'] = {
    'schema': {
        'opportunities': ['date', 'type', 'broker', 'origin', 'projects'],
        'visits': ['date', 'broker', 'project', 'type'],
        'offers': ['date', 'type', 'project'],
        'wins': ['date', 'type', 'broker', 'project', 'ref', 'amount'],
        'listings': ['date', 'type'],
    },
    'opportunities': rec_opp,
    'visits': rec_vis,
    'offers': rec_offer,
    'wins': rec_win,
    'listings': rec_listing,
}

# Whole-history summary. Nothing on screen reads it - the cards recompute from records[]
# for the selected date range - but it is kept in step so it can never contradict them.
sales = [t for t in tx if t['type'] == 'sale']
rentals = [t for t in tx if t['type'] == 'rental']
com_sale = sum(t['commission'] for t in sales)
com_rent = sum(t['commission'] for t in rentals)
com_assign = sum(t['assignmentCommission'] for t in tx)
d['kpisApi'] = {
    'asOf': today,
    'salesVolume': sum(t['amount'] for t in sales),
    'rentalVolume': sum(t['amount'] for t in rentals),
    'totalVolume': sum(t['amount'] for t in tx),
    'salesCount': len(sales), 'rentalCount': len(rentals),
    'avgTicketSales': (sum(t['amount'] for t in sales) / len(sales)) if sales else None,
    'commissionSale': com_sale, 'commissionRental': com_rent,
    'commissionAssignment': com_assign,
    'totalCommission': com_sale + com_rent + com_assign,
    'totalLeads': len(rec_opp), 'visits': len(rec_vis),
    'visitsSale': sum(1 for v in rec_vis if v[3] == 'sale'),
    'visitsRental': sum(1 for v in rec_vis if v[3] == 'rental'),
    'visitsUnlinked': sum(1 for v in rec_vis if not v[3]),
    'note': ('Closed deals are dated by the day the property entered Ganho in the CRM '
             'state history. Rental Volume is the sum of monthly rent, not a one-time '
             'amount. Commissions are the values recorded in Inmovilla and are never '
             'estimated; a deal with none recorded counts as zero.'),
}

with open(D('data.json'), 'w', encoding='utf-8') as f:
    json.dump(d, f, indent=2, ensure_ascii=False)

print('months        :', months)
print('opportunities :', len(opp))
print('visits        :', len(vis))
print('properties    :', len(imo))
print('total leads   :', d['kpisApi']['totalLeads'])
for t in ('rental', 'sale'):
    print(t, {s: sum(f['count'] for f in funnel if f['stage'] == s and f['type'] == t)
              for s, _ in STAGES})
