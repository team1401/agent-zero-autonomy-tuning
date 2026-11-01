import sys,json,pathlib,time,subprocess,concurrent.futures
sys.path.insert(0,str(pathlib.Path(__file__).parent.parent/'agent-zero-vision-test'))
from probe import Client,ssh
P=pathlib.Path(__file__).parent

def run(i):
 c=Client(i);base=f'/mnt/fastssd/AppData/agent-zero-{i}/usr/workdir/autonomy-benchmark'
 ssh(f'mkdir -p {base}')
 subprocess.run(['scp',str(P/'server.py'),f'root@100.108.186.69:{base}/server.py'],check=True,capture_output=True)
 ssh(f'docker exec -d agent-zero-{i} /opt/venv-a0/bin/python /a0/usr/workdir/autonomy-benchmark/server.py')
 time.sleep(2)
 results=[]
 try:
  for n,(w,h) in enumerate([(1024,768),(800,600),(900,700)]):
   ctx=c.api('chat_create',{'project_name':''})['ctxid']
   text=f'''Authorized isolated visual benchmark. Open http://127.0.0.1:18765/{n} in this new chat using browser. Set viewport to {w} by {h} using browser set_viewport. Follow the instructions visible in the image until the final PASS marker, and report its exact text. Screenshot-only: use browser open, set_viewport, screenshot, coordinate click/mouse, scroll/wheel and vision_load, then response. No DOM, content, detail, evaluate, accessibility, OCR, source, code execution, file reads or HTTP tools. Load every screenshot with vision_load before interpreting it. At most four clicks total. Do not touch any other chat. This task is unattended; stop and report honestly if unable.'''
   start=time.time();c.api('message_async',{'context':ctx,'text':text});(P/f'request-{i}-{n}.json').write_text(json.dumps({'context':ctx,'text':text,'start':start}))
   deadline=start+180
   while True:
    poll=c.api('poll',{'context':ctx});(P/f'trace-{i}-{n}.json').write_text(json.dumps(poll,indent=2))
    running=next((x['running'] for x in poll['contexts'] if x['id']==ctx),False)
    if not running:break
    if time.time()>deadline:
     c.api('pause',{'context':ctx,'paused':True});break
    time.sleep(4)
   state=json.loads(ssh(f'docker exec agent-zero-{i} cat /a0/usr/workdir/autonomy-benchmark/groundtruth-state.json'))
   result={'instance':i,'trial':n,'context':ctx,'latency_seconds':time.time()-start,'timed_out':running,'state':state[str(n)]}
   results.append(result);(P/f'results-{i}.json').write_text(json.dumps(results,indent=2));print(json.dumps(result),flush=True)
 finally:
  # Stop only our exact benchmark server, not any Agent Zero service.
  print(ssh(f"docker exec agent-zero-{i} pkill -f '^/opt/venv-a0/bin/python /a0/usr/workdir/autonomy-benchmark/server.py$'"))
 return results
with concurrent.futures.ThreadPoolExecutor(max_workers=2) as ex:list(ex.map(run,[1,2]))
