import json
import os
import re
import time
import requests
from openai import OpenAI

client = OpenAI()
MODEL_NAME = "gpt-4o-mini"


SUMMARY_PROMPT_TEMPLATE = """
We're creating a new entry in a drug database for the substance {name}.

We'd like to include a concise one sentence description that states the class of
drug and what condition it's most often used to treat. Include other information
only if it's very important. Be very brief. Here are some examples:

Albuterol, also known as Salbutamol, is a short-acting, selective beta2-adrenergic receptor agonist used to treat asthma and COPD.
Atazanavir is an antiretroviral protease inhibitor used to treat HIV.
Atogepant is a small molecule CGRP receptor antagonist (gepant) used for the preventive treatment of migraines.
Abacavir/Lamivudine/Zidovudine, marketed as Trizivir, is a combination antiretroviral medication used to treat HIV.
Ziprasidone is an atypical antipsychotic used to manage schizophrenia and bipolar mania.

Please write a description based on the following text:

{content}
"""


def sluggify(name):
    if name:
        return name.replace('; ', '/').replace(' ', '_')
    return None

def detect_redirect(content):
    if content:
        m = re.match(r"#REDIRECT\s*\[\[(.*?)(#(.*))?\]\]", content, re.IGNORECASE)
        if m:
            return m.group(1)
    return None


def get_wikipedia_entry_cached(slug):
    if slug:
        slug = slug.replace(' ', '_')
        filename = slug.lower().replace('/', '_')
        if os.path.exists(f"data/wikipedia/{filename}.txt"):
            with open(f"data/wikipedia/{filename}.txt") as f:
                content = f.read()
                return slug, content
    return slug, None


def get_wikipedia_entry(name):
    return get_wikipedia_entry_(sluggify(name))


def get_wikipedia_entry_(slug):

    filename = slug.lower().replace('/', '_').replace(' ', '_')
    if os.path.exists(f"data/wikipedia/{filename}.txt"):
        with open(f"data/wikipedia/{filename}.txt") as f:
            content = f.read()
        redirect_slug = detect_redirect(content)

        if redirect_slug and not redirect_slug == slug:
            return get_wikipedia_entry(redirect_slug)
        else:
            return slug, content

    url = f"http://en.wikipedia.org/w/api.php?action=query&format=json&prop=revisions&titles={slug}&formatversion=2&rvprop=content&rvslots=*"
    response = requests.get(url)

    page = response.json()

    # 'query': {'normalized': [
    #   {'fromencoded': False,
    #    'from': 'afamelanotide',
    #    'to': 'Afamelanotide'
    #   }
    # ]
    try:
        if 'query' in page and 'normalized' in page['query']:
            slug = page['query']['normalized'][0]['to'].replace(' ', '_')
            filename = slug.lower().replace('/', '_')
    except:
        pass

    try:
        page = page['query']['pages'][0]
        content = page['revisions'][0]['slots']['main']['content']
    except:
        content = None

    if content:

        redirect_slug = detect_redirect(content)
        if redirect_slug:
            return get_wikipedia_entry_(redirect_slug)

        with open(f'data/wikipedia/{filename}.txt', 'wt') as f:
            f.write(content)

        return slug, content
        
    return slug, None


def write_description(name, content):
    prompt = SUMMARY_PROMPT_TEMPLATE.format(name=name, content=content)
    completion = client.chat.completions.create(
        model=MODEL_NAME,
        messages=[
            {"role": "user", "content": prompt}
        ]
    )
    return completion.choices[0].message.content


def extract_drugbank_accession(content):
    db_pattern = r"DrugBank_Ref\s*=\s*\{\{drugbankcite\|correct\|drugbank\}\}\s*\|\s*DrugBank\s*=\s*(DB\d+)"
    m = re.search(db_pattern, content)
    if m:
        return m.group(1)
    db_pattern = r"DrugBank\s*=\s*(DB\d+)"
    m = re.search(db_pattern, content)
    if m:
        return m.group(1)
    return None


def extract_brand_name(content):
    pattern = r"tradename\s*=\s*([^|<]*)"
    m = re.search(pattern, content)
    if m:
        return m.group(1)
    return None


def extract_brand_names(content):
    pattern = r"tradename\s*=\s*([^|<\n]*?)(,\s*others?\s*(<ref name=genericnames/>)?)?\n"
    m = re.search(pattern, content)
    if m:
        return re.split(r',\s*', m.group(1))
    return None


def create_fda_entry(name, substance_name):

    med = {
        "name": name,
        "alt-names": [substance_name],
    }
    slug, content = get_wikipedia_entry(name)

    if not content:
        return med
    
    med['description'] = write_description(name, content) + f" [{MODEL_NAME}]"

    brand_name = extract_brand_name(content)
    if brand_name:
        med['brand-names'] = re.split(r',\s*', brand_name.replace(', others', ''))
        print(med['brand-names'])

    url = f"https://en.wikipedia.org/wiki/{slug}"
    links = [
        {
            "source": "Wikipedia",
            "url": url
        }
    ]

    accession = extract_drugbank_accession(content)
    if accession:
        links.append({
            "source": "DrugBank",
            "accession": accession
        })

    med["links"] = links

    return med


def get_link_key(med, source, key='slug'):
    for link in med.get('links', []):
        if link['source'] == source:
            return link[key]
    return None

def get_link(med, source, key='slug', template="https://en.wikipedia.org/wiki/{slug}"):
    link_key = get_link_key(med, source, key='slug')
    return template.format_map({key: link_key}) if link_key else None




## Rewrite links section
for name, med in track(unmatched_meds.items(), total=len(unmatched_meds)):
    links = med.get('links', [])
    new_source = 'Wikipedia' if link['source']=='Wikipedia' else 'DrugBank'
    new_links = {
        new_source: {
            'source': new_source,
            'key': link['slug' if link['source']=='Wikipedia' else 'accession'],
            #'key-type': 'slug' if link['source']=='Wikipedia' else 'accession',
        }
        for link in links
    }
    med['links'] = new_links



def count_parts(med):
    parts = 0
    if 'description' in med:
        parts += 1
    if 'brand-names' in med:
        parts += 1
    if 'links' in med:
        if 'Wikipedia' in med['links']:
            parts += 1
        if 'DrugBank' in med['links']:
            parts += 1
    return parts


for name, med in unmatched_meds.items():
    links = med.get('links', {})
    slug = links.get('Wikipedia', {}).get('key') if 'Wikipedia' in links else sluggify(name)
    slug, content = get_wikipedia_entry_cached(slug)
    redirect_to = detect_redirect(content)
    if redirect_to or content is None:
        print(f"{name[0:48]:-<50} {count_parts(med)} {slug} " + 
              (f"==> {redirect_to}" if redirect_to else "") +
              (f"    content is None" if content is None else ""))



with open('data/unmatched_meds.json', 'rt') as f:
    unmatched_meds = json.load(f)

for name, med in unmatched_meds.items():
    links = med.get('links', {})
    slug = links.get('Wikipedia', {}).get('key') if 'Wikipedia' in links else sluggify(name)
    slug, content = get_wikipedia_entry_cached(slug)
    redirect_to = detect_redirect(content)
    if redirect_to or content is None:
        print(f"{name[0:48]:-<50} {count_parts(med)} {slug} " + 
              (f"==> {redirect_to}" if redirect_to else "") +
              (f"    content is None" if content is None else ""))
        slug, content = get_wikipedia_entry(slug)
        if content:
            redirect_to = detect_redirect(content)
            if redirect_to:
                print(f"  ====> {redirect_to}")
            else:
                print("✅")
        else:
            print("❌")
    time.sleep(1)



i = 0
for name, med in unmatched_meds.items():
    links = med.get('links', {})
    slug = links.get('Wikipedia', {}).get('key') if 'Wikipedia' in links else sluggify(name)
    slug, content = get_wikipedia_entry_cached(slug)
    redirect_to = detect_redirect(content)
    if redirect_to or content is None:
        print(f"{name[0:48]:-<50} {count_parts(med)} {slug} " + 
              (f"==> {redirect_to}" if redirect_to else "") +
              (f"    content is None" if content is None else ""))
        slug, content = get_wikipedia_entry(slug)
        if content:
            redirect_to = detect_redirect(content)
            if redirect_to:
                print(f"  ====> {redirect_to}")
            else:
                print("✅")
                i += 1

                brand_names = extract_brand_names(content)
                if brand_names:
                    print(brand_names)
                    med['brand-names'] = brand_names

                new_links = {
                    "Wikipedia": {
                        "source": "Wikipedia",
                        "key": slug
                    }
                }

                accession = extract_drugbank_accession(content)
                if accession:
                    new_links["DrugBank"] = {
                        "source": "DrugBank",
                        "key": accession
                    }

                print(new_links)
                med['links'] = new_links

                descr = med.get('description')
                if not descr or descr.endswith(f" [{MODEL_NAME}]"):
                    med['description'] = write_description(name, content) + f" [{MODEL_NAME}]"
        else:
            print("❌")
    #time.sleep(1)
print(f"Updated {i} entries")

with open('data/unmatched_meds.json', 'wt') as f:
    json.dump(unmatched_meds, f, indent=2)


for name, med in unmatched_meds.items():
    if ';' not in name and 'DrugBank' not in med.get('links', {}):
        slug = med.get('links', {}).get('Wikipedia', {}).get('key')
        print(f"{name[0:48]:-<50} {count_parts(med)} {slug or '-'}")



for name, med in unmatched_meds.items():
    if ';' not in name and 'DrugBank' not in med.get('links', {}):
        slug = med.get('links', {}).get('Wikipedia', {}).get('key')
        print(f"{name[0:48]:-<50} {count_parts(med)} {slug or '-'}")
        if slug:
            slug, content = get_wikipedia_entry(slug)
            accession = extract_drugbank_accession(content)
            if accession:
                print(f"✅ {accession}")
            else:
                print("❌")


for name, med in unmatched_meds.items():
    if ';' not in name and 'DrugBank' not in med.get('links', {}):
        slug = med.get('links', {}).get('Wikipedia', {}).get('key')
        print(f"{name[0:48]:-<50} {count_parts(med)} {slug or '-'}")
        if slug:
            slug, content = get_wikipedia_entry(slug)
            accession = extract_drugbank_accession(content)
            if accession:
                print(f"✅ {accession}")
            else:
                print("❌")
                filename = slug.lower().replace('/', '_')
                cont = input(f"rm {filename}? ")
                if cont == 'n' : continue
                if cont == 'q' : break
                os.remove(f"data/wikipedia/{filename}.txt")
