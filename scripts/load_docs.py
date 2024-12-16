"""
Load vectorized text chunks into the `docs` table in the `meds` database for
retreival augmented generation (RAG) with the `ollama` library.
"""
from io import StringIO
import json
import re

import ollama
import psycopg2
import wikitextparser as wtp


sections_to_ignore = {
    'References',
    'External links',
    'Further reading',
    'See also',
    'Bibliography',
    'Notes',
    'Veterinary medicine',
    'Veterinary use',
}


def rm_nested_brackets(txt):
    """
    Wikipedia text contains nested bracketed structures. We'll remove them to
    get cleaner text.
    """
    result = StringIO()
    stack = [0]
    for m in re.finditer(r'(\{\{|\}\})', txt):
        if m[1] == '{{':
            stack.append(m.start())
        elif m[1] == '}}':
            b = stack.pop()
            if len(stack) == 1:
                a = stack.pop()
                result.write(txt[a:b])
                stack.append(m.end())
    if len(stack) == 1:
        a = stack.pop()
        result.write(txt[a:])
    return result.getvalue()


def clean_wikipedia_text(txt):
    """
    Clean up Wikipedia markup.
    """
    txt = re.sub(r'\{\{nbsp\}\}', ' ', txt)
    txt = rm_nested_brackets(txt)
    txt = re.sub(r'<!--(.*?)-->', '', txt, flags=re.DOTALL)
    txt = re.sub(r'\{\|(.*?)\|\}', '', txt, flags=re.DOTALL)
    txt = re.sub(r'\{\{(.*?)\|(.*?)\}\}', r'\1', txt)
    txt = re.sub(r'\[\[(.*?)\]\]', r'\1', txt).strip()
    return txt


def load_documents():
    """
    Chunk and index Wikipedia text for retrieval augmented generation.
    """
    with open(f'data/meds.json', 'rt', encoding='utf-8') as f:
        meds = json.load(f)

    sections_indexed = 0
    for name, med in meds.items():
        # for now, let's limit ourselves to the clincalc 300
        # most prescribed medications
        if 'clincalc' in med and ';' not in name:
            links = {l['source']:l['key'] for l in med.get('links', {})}
            if 'Wikipedia' in links:
                slug = links['Wikipedia']
                _, txt = get_wikipedia_entry_cached(slug)
                if txt:
                    m = re.search(r'\{\{Short description\|(.*)\}\}', txt)
                    desc = m[1] if m else None
                    print(f"\n{name}: {desc}")

                    txt = clean_wikipedia_text(txt)
                    parsed = wtp.parse(txt)
                    for section in parsed.sections:
                        title = section.title.strip() if section.title else ''
                        if (title not in sections_to_ignore):
                            index('Wikipedia', slug, title, section.plain_text())
                            sections_indexed += 1
                            print(title)


def index(source, key, title, text):
    """
    Insert a row into table `docs` in the `meds` database.

    Schema:
        CREATE TABLE docs (
            id bigserial PRIMARY KEY,
            embedding vector(768),
            source text,
            key text,
            title text,
            text text
        );
    """
    response = ollama.embed(
        model='nomic-embed-text',
        input=f"{key} {title}\n\n{text}",
    )
    vector = response['embeddings'][0]
    conn = psycopg2.connect(dbname='meds', user='med-info-bot')
    with conn:
        with conn.cursor() as curs:
            curs.execute(
                "INSERT INTO docs (embedding, source, key, title, text) VALUES (%s, %s, %s, %s, %s)",
                (vector, source, key, title, text),
            )


def get_similar_docs(vector, k=3):
    """
    Retrieve the `k` most similar documents to the given `vector`.
    """
    conn = psycopg2.connect(dbname='meds', user='med-info-bot')
    with conn:
        with conn.cursor() as curs:
            curs.execute("""
                select
                    source, key, title, text
                from docs
                order by embedding <-> %(vector)s::vector
                limit %(k)s
                """,
                {'vector': vector, 'k': k},
            )
            return curs.fetchall()


def retrieve(text, k=3):
    """
    Vector search in the `docs` table.
    """
    response = ollama.embed(
        model='nomic-embed-text',
        input=text,
    )
    vector = response['embeddings'][0]
    return get_similar_docs(vector, k)


def rag(text, k=3):
    """
    Retrieve and generate.
    """
    results = retrieve(text, k)
    prompt = (
        'You are a helpful expert in pharmacology. You answer questions about medications'
        'truthfully to the best of your ability.\n\n'
        + "First decide if these documents are helpful. Ignore unhelpful documents. Then answer the question below.\n\n"
        + '\n----\n'.join([
                f"{key} {title}:\n{text}"
                for _, key, title, text in results
            ])
        + '\n\nQuestion: '
        + text
    )

    print('-' * 80)
    print('Prompt:', prompt)
    print('-' * 80)

    stream = ollama.chat(
        model='llama3.2',
        messages=[{'role': 'user', 'content': prompt}],
        stream=True,
    )

    for chunk in stream:
        print(chunk['message']['content'], end='', flush=True)

    print('\nsources:')
    for source, key, title, text in results:
        print(f"{source}: {key} {title}")


def ask(text, k=3):
    """
    Ask LM a question, without retrieval.
    """
    results = retrieve(text, k)
    prompt = (
        'You are a helpful expert medical advisor. You answer questions about medications'
        'truthfully to the best of your ability.\n\n'
        + '\n\nQuestion: '
        + text
    )

    stream = ollama.chat(
        model='llama3.2',
        messages=[{'role': 'user', 'content': prompt}],
        stream=True,
    )

    for chunk in stream:
        print(chunk['message']['content'], end='', flush=True)


def agrag(text, k=3):
    """
    Retrieve and generate.
    """
    results = retrieve(text, k)
    prompt = (
        'You are a helpful expert in pharmacology. You answer questions about medications'
        'truthfully to the best of your ability.\n\n'
        "First, let's have a look at the question. Is the question about a specific medication?"
        + '\n\nQuestion: '
        + text
    )

    print('-' * 80)
    print('Prompt:', prompt)
    print('-' * 80)

    stream = ollama.chat(
        model='llama3.2',
        messages=[{'role': 'user', 'content': prompt}],
        stream=True,
    )

    for chunk in stream:
        print(chunk['message']['content'], end='', flush=True)

    print('\nsources:')
    for source, key, title, text in results:
        print(f"{source}: {key} {title}")
