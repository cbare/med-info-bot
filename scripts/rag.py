"""
Implement RAG using Ollama and PostgreSQL.
"""
import io

import ollama
import psycopg2


def embed(text):
    response = ollama.embed(
        model='nomic-embed-text',
        input=text,
    )
    return response['embeddings'][0]


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


def get_metadata_for_similar_docs(vector, k=3):
    """
    Retrieve the `k` most similar documents to the given `vector`.
    """
    conn = psycopg2.connect(dbname='meds', user='med-info-bot')
    with conn:
        with conn.cursor() as curs:
            curs.execute("""
                select
                    key, title
                from docs
                order by embedding <-> %(vector)s::vector
                limit %(k)s
                """,
                {'vector': vector, 'k': k},
            )
            return curs.fetchall()


def list_similar_docs(text, k=3):
    """
    Retrieve the `k` most similar documents to the given `vector`.
    """
    docs = get_metadata_for_similar_docs(embed(text), k)
    for doc in docs:
        print(doc)


def find_rank(text, key, title, k=3):
    """
    Retrieve the `k` most similar documents to the given `vector`.
    """
    docs = get_metadata_for_similar_docs(embed(text), k)
    for i, doc in enumerate(docs):
        if doc == (key, title):
            print(i, doc)
            break
    else:
        print('Not found')


def retrieve(text, k=3):
    """
    Retrieve the `k` most similar documents to the given text.
    """
    return get_similar_docs(embed(text), k)


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
    Generate.
    """
    results = retrieve(text, k)
    prompt = (
        """You are a helpful assistant with expert knowledge about prescription
        and over the counter medications. You answer questions about medications
        concisely and truthfully to the best of your ability. Your answers will
        not be used to treat real patients. Your answers will be used to assess
        your knowledge, so do your best.\n\n"""
        + 'Please answer as briefly as possible.\n\n'
        + '\n\nQuestion: '
        + text
    )

    stream = ollama.chat(
        model='llama3.2',
        messages=[{'role': 'user', 'content': prompt}],
        stream=True,
    )

    response = io.StringIO()
    for chunk in stream:
        print(chunk['message']['content'], end='', flush=True)
        response.write(chunk['message']['content'])

    return response.getvalue()


def agentic_rag(text, k=3):
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
