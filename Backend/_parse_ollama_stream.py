import requests, json, sys
url="http://localhost:11434/api/generate"
payload={"model":"qwen2.5:7b","prompt":"Explain the significance of transformer models in NLP in one concise paragraph.","max_tokens":256,"temperature":0.2}
try:
    r=requests.post(url,json=payload,stream=True,timeout=60)
except Exception as e:
    print('ERROR',e); sys.exit(2)
text=''
final=None
for line in r.iter_lines(decode_unicode=True):
    if not line: continue
    try:
        j=json.loads(line)
    except Exception:
        continue
    resp=j.get('response')
    if isinstance(resp,str):
        text+=resp
    if j.get('done'):
        final=j
        break
print('--- FULL RESPONSE TEXT ---')
print(text)
print('')
if final:
    td=final.get('total_duration')
    ld=final.get('load_duration')
    ped=final.get('prompt_eval_duration')
    ed=final.get('eval_duration')
    def ns_to_s(x):
        return f"{(x/1e9):.3f}s" if isinstance(x,(int,float)) else 'N/A'
    context=final.get('context')
    print('--- METADATA ---')
    print('model:', final.get('model'))
    print('done_reason:', final.get('done_reason'))
    print('total_duration:', ns_to_s(td), f'({td})')
    print('load_duration:', ns_to_s(ld), f'({ld})')
    print('prompt_eval_duration:', ns_to_s(ped), f'({ped})')
    print('eval_duration:', ns_to_s(ed), f'({ed})')
    print('prompt_eval_count:', final.get('prompt_eval_count'))
    print('eval_count:', final.get('eval_count'))
    if isinstance(context,list):
        print('context token count:', len(context))
    else:
        print('context token count: N/A')
else:
    print('No final JSON with metadata received')
