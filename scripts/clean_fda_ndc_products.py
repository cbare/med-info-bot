import json
import pandas as pd

products = pd.read_csv('data/fda/ndc/product.txt', sep='\t', encoding="ISO-8859-1")

products.columns
products.MARKETINGCATEGORYNAME.value_counts()
products.PRODUCTTYPENAME.value_counts()

products = products[
    ~products.MARKETINGCATEGORYNAME.isin(['UNAPPROVED HOMEOPATHIC', 'UNAPPROVED MEDICAL GAS'])
    &
    products.PRODUCTTYPENAME.isin(['HUMAN PRESCRIPTION DRUG', 'HUMAN OTC DRUG'])
    &
    products.SUBSTANCENAME.ne('AIR')
    &
    ~products.SUBSTANCENAME.str.contains('POLLEN', na=False)
    &
    ~products.PHARM_CLASSES.str.startswith('Allergens [CS]', na=False)
]

products[ products.MARKETINGCATEGORYNAME.isin(['ANDA', 'NDA', 'BLA']) ].SUBSTANCENAME.unique().shape

with open('data/meds.json') as f:
    meds = json.load(f)

med_idx = {
    name.lower(): med
    for med in meds.values()
        for name in [med['name']] + med.get('alt-names', [])
}

counter_ions = [
    "acetate",
    "anhydrous",
    "aspartate",
    "benzoate",
    "besylate",
    "borate",
    "butyrate",
    "calcium",
    "carbonate",
    "citrate",
    "fumarate",
    "gluconate",
    "hemihydrate",
    "lactate",
    "maleate",
    "mesylate",
    "oxalate",
    "palmitate",
    "phosphate",
    "potassium",
    "disodium",
    "sodium",
    "succinate",
    "tannate",
    "taurate",
    "tosylate",
    "vedotin",
    "monohydrate",
    "dihydrate",
    "hydrate",
    "bisulfate",
    "sulfate",
    "bitartrate",
    "tartrate",
    "hydrobromide",
    "bromide",
    "dipropionate",
    "propionate",
    "dihydrochloride",
    "hydrochloride",
    "chloride",
]

def strip_suffix(name, counter_ions=counter_ions):
    while True:
        for ion in counter_ions:
            if name.endswith(ion):
                name = name[:-len(ion)].strip()
        else:
            break
    return name

def strip_suffixes(name, counter_ions=counter_ions):
    parts = [part.strip() for part in name.split(";")]
    return "; ".join(strip_suffix(part, counter_ions).title() for part in parts)


new_names = sorted([
    name for name in products[ products.MARKETINGCATEGORYNAME.isin(['ANDA', 'NDA', 'BLA']) ].SUBSTANCENAME.unique()
    if not pd.isna(name) and strip_suffix(name.lower()) not in med_idx and name.lower() not in med_idx
])

new_names_df = pd.DataFrame({'name': new_names})
new_names_df.to_csv('new_names.csv', index=False)


from collections import Counter
counter = Counter()
for substance in products[ products.MARKETINGCATEGORYNAME.isin(['ANDA', 'NDA', 'BLA']) ].SUBSTANCENAME.unique():
    if pd.isna(substance): continue
    counter['found' if substance.lower() in med_idx else 'not found'] += 1


import difflib


targets = {
    target.lower(): name
    for name, med in meds.items()
        for target in [med['name']] + med.get('alt-names', [])
}

def find_best_match(item, targets, min_score=0.5):
    item = item.lower()
    if item in targets:
        return targets.get(item), 1.0

    item = strip_suffixes(item)
    if item in targets:
        return targets.get(item), 1.0

    best_score  = min_score
    best_target = None
    for key, value in targets.items():
        x = difflib.SequenceMatcher(None, item, key).ratio()
        if x > best_score:
            best_score, best_target = x, value
    return best_target, best_score

for name in new_names:
    bm, score = find_best_match(name, targets, min_score=0.7)
    if bm and score < 1.0:
        print(f"{name[0:60]:-<64} {bm} {score}")
