import json
import re

import rag

with open('data/evals.json', 'rt', encoding='utf-8') as f:
    evals = json.load(f)

score = 0
out_of = 0
for eval in evals:
    prompt = eval['prompt']
    print(prompt)
    response = rag.ask(prompt)
    response_contains = eval['response_contains']
    print()
    for expected_strings in re.split(r',\s*', response_contains):
        for expected in re.split(r'\s*\|\s*', expected_strings):
            if expected.lower() in response.lower():
                print(f'✅ {expected}')
                score += 1
                break
        else:
            print(f'❌ {expected}')
        out_of += 1
    print('-' * 80)

print(f'Score: {score}/{out_of} = {score / out_of:.2%}')
