import json
import re
import requests

with open('data/meds.json', 'rt') as f:
    data = json.load(f)

def sluggify(name):
    return name.lower().replace('; ', '/').replace(' ', '_')

db_pattern = r"DrugBank_Ref\s*=\s*\{\{drugbankcite\|correct\|drugbank\}\}\s*\|\s*DrugBank\s*=\s*(DB\d+)"

for name, med in data.items():
    try:
        if 'links' in med and len(med['links']) > 0:
            link = med['links'][0]['url']
            title = link[len('https://en.wikipedia.org/wiki/'):]
            if os.path.exists(f"data/wikipedia/{sluggify(title)}.txt"): continue

            print(name, title)

            url = f"http://en.wikipedia.org//w/api.php?action=query&format=json&prop=revisions&titles={title}&formatversion=2&rvprop=content&rvslots=*"
            response = requests.get(url)
            print(response.status_code)

            page = response.json()
            if 'query' in page and 'pages' in page['query']:
                page = page['query']['pages'][0]
                if 'revisions' in page and len(page['revisions']) > 0:
                    content = page['revisions'][0]['slots']['main']['content']
                    with open(f'data/wikipedia/{sluggify(title)}.txt', 'wt') as f:
                        f.write(content)

                    m = re.search(db_pattern, content)
                    if m:
                        drugbank_accession = m.group(1)
                        print(drugbank_accession)

                        if 'drugbank' in med:
                            if med['drugbank']['accession'] == drugbank_accession:
                                print("Already have this accession")
                            else:
                                print("Different accession")
                                print(med['drugbank']['accession'])
                                print(drugbank_accession)
                        else:
                            med['drugbank'] = {
                                "accession": drugbank_accession,
                            }
            else:
                print(":(")
    except Exception as e:
        print(e)
    print()


for name, med in data.items():
    if 'links' in med and len(med['links']) > 0:
        link = med['links'][0]['url']
        title = link[len('https://en.wikipedia.org/wiki/'):]
        with open(f'data/wikipedia/{sluggify(title)}.txt', 'rt') as f:
            content = f.read()
        m = re.match(r"#REDIRECT \[\[(.*)\]\]", content)
        if m:
            print(f"{title} ===> {m.group(1)}")
            link = med['links'][0]['url'] = f"https://en.wikipedia.org/wiki/{m.group(1).replace(' ', '_')}"


to_remove = []
for name, med in data.items():
    try:
        if 'links' in med and len(med['links']) > 0:
            link = med['links'][0]['url']
            title = link[len('https://en.wikipedia.org/wiki/'):]
            print(name, title)

            with open(f'data/wikipedia/{sluggify(title)}.txt', 'rt') as f:
                content = f.read()
            m = re.match(r"#REDIRECT \[\[(.*)\]\]", content)
            if m:
                print(f"{title} ===> {m.group(1)}")
                new_title = m.group(1).replace(' ', '_')
                link = med['links'][0]['url'] = f"https://en.wikipedia.org/wiki/{new_title}"
                to_remove.append(f'data/wikipedia/{sluggify(title)}.txt')
            else:
                continue

            url = f"http://en.wikipedia.org//w/api.php?action=query&format=json&prop=revisions&titles={new_title}&formatversion=2&rvprop=content&rvslots=*"
            response = requests.get(url)
            print(response.status_code)

            page = response.json()
            if 'query' in page and 'pages' in page['query']:
                page = page['query']['pages'][0]
                if 'revisions' in page and len(page['revisions']) > 0:
                    content = page['revisions'][0]['slots']['main']['content']
                    with open(f'data/wikipedia/{sluggify(new_title)}.txt', 'wt') as f:
                        f.write(content)

                    m = re.search(db_pattern, content)
                    if m:
                        drugbank_accession = m.group(1)
                        print(drugbank_accession)

                        if 'drugbank' in med:
                            if med['drugbank']['accession'] == drugbank_accession:
                                print("Already have this accession")
                            else:
                                print("Different accession")
                                print(med['drugbank']['accession'])
                                print(drugbank_accession)
                        else:
                            med['drugbank'] = {
                                "accession": drugbank_accession,
                            }
            else:
                print(":(")
    except Exception as e:
        print(e)
    print()
