import json

import pandas as pd
import spacy

nlp = spacy.load('en_core_web_lg')

with open('data/meds.json', 'rt') as f:
    data = json.load(f)

hm = pd.read_csv('data/hospital-medicines.csv',
                 skiprows=2,
                 dtype={'Pharmacode': str, 'NZMT_CTPP_ID': str},)
hm_names_set_lower = set(name.lower() for name in  hm.Chemical)
hm_names_set = set(hm.Chemical)

def iter_names(med):
    yield med['name']
    for alt_name in med.get('alt-names', []):
        yield alt_name
    for brand_name in med.get('brands-names', []):
        yield brand_name

proposed_changes = {}
for canonical_name, med in data.items():
    for name in iter_names(med):
        if name.lower() in hm_names_set_lower:
            print(canonical_name, name)
            continue
        vec_name = nlp(name.lower())
        score, best_match = max((
            (vec_name.similarity(nlp(hm_name.lower())), hm_name)
            for hm_name in hm_names_set
        ))
        print(canonical_name, '~=', best_match, '-', score)

        if score > 0.85:
            proposed_changes[canonical_name] = best_match


for k,v in proposed_changes.items():
    print(k, "~=", v)
    x = input("y/n")
    if x == 'y':
        med = data[k]
        if 'alt-names' not in med:
            med['alt-names'] = []
        med['alt-names'].append(v)

with open('data/meds.json', 'wt') as f:
    json.dump(data, f, indent=2)


counter_ions = {
    "acetate",
    "bromide",
    "carbonate",
    "chloride",
    "citrate",
    "dihydrochloride",
    "dipropionate",
    "fumarate",
    "gluconate",
    "hydrobromide",
    "hydrochloride",
    "lactate",
    "maleate",
    "propionate",
    "sodium",
    "sulfate",
    "tartrate",
}

def find_med(data, name, counter_ions=counter_ions):
    if name in data:
        return data[name]
    for med in data.values():
        for n in iter_names(med):
            if n.lower() == name.lower():
                return med
    for ion in counter_ions:
        if name.endswith(ion):
            name = name[:-len(ion)].strip()
            break
    if name in data:
        return data[name]
    for med in data.values():
        for n in iter_names(med):
            if n.lower() == name.lower():
                return med
    return None

from collections import Counter

counts = Counter()
for name in hm_names:
    med = find_med(data, name)
    counts[med is not None] += 1


for name in hm_names:
    med = find_med(data, name)
    if not med:
        print(name)
        x = input("y/n")
        if x=='y':
            data[name] = {"name": name, "alt-names": [name]}

hm_lookup = {
    hm_name: name
    for name, hm_name in hm_lookup_df.itertuples(index=False)
}

to_add = {}
for hm_name, name in hm_lookup.items():
    med = find_med(data, name)
    if not med:
        print(f"{name} - {hm_name}")
        to_add[name] = {
          "name": name,
          "alt-names": [hm_name],
          "links": [{"source": "Wikipedia", "url": f"https://en.wikipedia.org/wiki/{name}"}],
          "source": "NZHM",
        }

z = dict(sorted((data | to_add).items()))
with open('data/meds.json', 'wt') as f:
    json.dump(z, f, indent=2)


updated_meds = set()
for (Chemical,Presentation,Brand,Pharmacode,NZMT_CTPP_ID,Price,Per,DV_Limit,HSS_PSS,Rules_Apply,TG1,TG2,TG3) in hm.itertuples(index=False):
    name = hm_lookup.get(Chemical, Chemical)
    med = find_med(data, name)
    if not med:
        print(f"❌ {Chemical}")
    else:
        print(f"✅ {Chemical} -> {med['name']}")
        updated_meds.add(med['name'])

        nzhm_entries = med.get('nzhm', [])
        nzhm_e = {
            "name": Chemical,
            "presentation": Presentation,
            "brand": Brand,
            "pharmacode": Pharmacode,
        }
        if not pd.isnull(NZMT_CTPP_ID):
            nzhm_e["nzmt-ctpp-id"] = NZMT_CTPP_ID
        if not pd.isnull(Price):
            nzhm_e["price"] = Price
        if not pd.isnull(Per):
            nzhm_e["per"] = Per
        nzhm_entries.append(nzhm_e)
        med['nzhm'] = nzhm_entries

        categories = med.get('categories', [])
        new_category = {
            "source": "nzhm",
            "tg1": TG1,
            "tg2": TG2,
            "tg3": TG3,
        }
        if new_category not in categories:
            categories.append(new_category)
        med['categories'] = categories


with open('data/meds.json', 'wt') as f:
    json.dump(data, f, indent=2)


mo_drugs = [
"Abciximab",
"Adalimumab",
"Alteplase",
"Ambrisentan",
"Baricitinib",
"Basiliximab",
"Betaxolol",
"Bortezomib",
"Candesartan cilexetil",
"Candesartan cilexetil with hydrochlorothiazide",
"Casirivimab and imdevimab",
"Cetuximab",
]

with open('data/meds.json', 'rt') as f:
    data = json.load(f)



updated_meds = set()
for (Chemical,Presentation,Brand,Pharmacode,NZMT_CTPP_ID,Price,Per,DV_Limit,HSS_PSS,Rules_Apply,TG1,TG2,TG3) in hm.itertuples(index=False):
    if Chemical not in mo_drugs: continue

    name = Chemical
    med = find_med(data, Chemical)
    if not med:
        med = {
          "name": name,
          "brand-names": [Brand],
          "links": [{"source": "Wikipedia", "url": f"https://en.wikipedia.org/wiki/{name}"}],
          "source": "NZHM",
        }
        data[name] = med

    print(f"✅ {Chemical} -> {med['name']}")
    updated_meds.add(med['name'])

    nzhm_entries = med.get('nzhm', [])
    nzhm_e = {
        "name": Chemical,
        "presentation": Presentation,
        "brand": Brand,
        "pharmacode": Pharmacode,
    }
    if not pd.isnull(NZMT_CTPP_ID):
        nzhm_e["nzmt-ctpp-id"] = NZMT_CTPP_ID
    if not pd.isnull(Price):
        nzhm_e["price"] = Price
    if not pd.isnull(Per):
        nzhm_e["per"] = Per
    nzhm_entries.append(nzhm_e)
    med['nzhm'] = nzhm_entries

    categories = med.get('categories', [])
    new_category = {
        "source": "nzhm",
        "tg1": TG1,
        "tg2": TG2,
        "tg3": TG3,
    }
    if new_category not in categories:
        categories.append(new_category)
    med['categories'] = categories

data = dict(sorted(data.items()))
with open('data/meds.json', 'wt') as f:
    json.dump(data, f, indent=2)
