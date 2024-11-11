import json

with open('data/meds.json') as f:
    meds = json.load(f)

def points(med):
    points = []
    points.append(1 if len(med.get('alt-names', [])) > 0 else 0)
    points.append(1 if len(med.get('brand-names', [])) > 0 else 0)
    points.append(1 if 'description' in med else 0)
    points.append(1 if 'clincalc' in med else 0)
    points.append( 1 if 'drugbank' in med and 'accession' in med['drugbank'] else 0)
    points.append(len(med.get('links', [])))
    points.append(1 if len(med.get('nzhm', [])) > 0 else 0)
    points.append(1 if len(med.get('categories', [])) > 0 else 0)
    return points

for name, med in meds.items():
    p = points(med)
    print(f"{name:-<64} {sum(p)} {'-'.join(str(x) for x in p)}")
