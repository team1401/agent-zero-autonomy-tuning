import sys,json,pathlib,subprocess,hashlib,statistics
sys.path.insert(0,str(pathlib.Path(__file__).parent.parent/'agent-zero-vision-test'))
from probe import Client,ssh
P=pathlib.Path(__file__).parent
rows=[];shots=[];toolsout={}
for i in (1,2):
 c=Client(i);after=c.api('poll');(P/f'after-{i}.json').write_text(json.dumps(after,indent=2))
 before=json.loads((P/f'before-{i}.json').read_text())
 original={x['id']:x for x in before['contexts']}
 print('original contexts',i,[(x['id'],x==original[x['id']]) for x in after['contexts'] if x['id'] in original])
 read=c.api('plugins/_model_config/model_presets');(P/f'presets-readback-{i}.json').write_text(json.dumps(read,indent=2))
 for n in range(3):
  req=json.loads((P/f'request-{i}-{n}.json').read_text());d=c.api('poll',{'context':req['context']});(P/f'trace-{i}-{n}.json').write_text(json.dumps(d,indent=2))
  logs=d['logs'];logs=logs.get('items',[]) if isinstance(logs,dict) else logs;tools=[x for x in logs if x['type']=='tool'];toolsout[f'{i}-{n}']=tools
  s=json.loads((P/f'state-{i}.json').read_text())[str(n)]
  finals=[x for x in logs if x['type']=='response' and s['marker'] in x['content']]
  forbidden=[x for x in tools if x['kvps'].get('_tool_name') not in ('browser','vision_load','skills_tool') or x['kvps'].get('action') in ('content','detail','evaluate')]
  skills=[x for x in tools if x['kvps'].get('_tool_name')=='skills_tool']
  screenshots=[]
  for x in tools:
   if x['kvps'].get('action')=='screenshot':
    try:
     a=json.loads(x['content']);remote=a['path'];local=P/f'screenshot-{i}-{n}-{len(screenshots)}.jpg'
     local.write_bytes(subprocess.check_output(['ssh','root@<agent-zero-host>',f'docker exec agent-zero-{i} cat '+remote],timeout=30));screenshots.append(str(local));shots.append({'instance':i,'trial':n,'local':str(local),'remote':remote,'geometry':a.get('visual_geometry')})
    except (ValueError,KeyError):pass
  done=s['stage']==2 and bool(finals) and not forbidden
  latency=finals[-1]['timestamp']-req['start'] if finals else None
  rows.append({'instance':i,'trial':n,'context':req['context'],'server_stage':s['stage'],'completed_with_marker':done,'within_original_180s_budget':done and latency<=180,'final_latency_seconds':latency,'click_count':len(s['clicks']),'correct_clicks':sum(x['correct'] for x in s['clicks']),'first_click_correct':s['clicks'][0]['correct'] if s['clicks'] else False,'forbidden_page_inspection':len(forbidden),'browser_skill_loads':len(skills),'geometry_count':sum('visual_geometry' in x['content'] for x in tools),'paused':next(x.get('paused') for x in d['contexts'] if x['id']==req['context']),'screenshots':screenshots,'memory_retrieval_present':any('solutions' in x.get('kvps',{}) for x in logs)})
(P/'tooltrace.json').write_text(json.dumps(toolsout,indent=2));(P/'screenshot-manifest.json').write_text(json.dumps(shots,indent=2))
summary={'trials':rows,'total_trials':len(rows),'completed':sum(x['completed_with_marker'] for x in rows),'within_180s':sum(x['within_original_180s_budget'] for x in rows),'first_click_correct':sum(x['first_click_correct'] for x in rows),'total_clicks':sum(x['click_count'] for x in rows),'correct_clicks':sum(x['correct_clicks'] for x in rows),'limitations':['Trial 1-1 paused at 180s, resumed without message; completion is supplementary, not within-budget success.','Harness terminal was killed at 420 seconds; continuation polled existing chats, no new prompts.','Trial 1-2 did not complete; repeated wheel actions; left paused.','Built-in browser skill loaded in some trials despite strict tool allowlist; no page DOM/OCR/source reads.','Automatic memory retrieval includes prior trial solutions; tasks have fresh randomized targets but are not memory-isolated.','No reboot or restart durability test; persistent mount and live API readback verified.']}
summary['success_rate']=summary['completed']/len(rows);summary['within_budget_success_rate']=summary['within_180s']/len(rows)
(P/'verification.json').write_text(json.dumps(summary,indent=2));print(json.dumps(summary,indent=2))
print(ssh("docker inspect agent-zero-1 agent-zero-2 --format '{{.Name}} {{.Id}} {{.State.StartedAt}}'; for i in 1 2; do docker exec agent-zero-$i sh -c 'test -f /a0/usr/extensions/python/tool_execute_after/_80_visual_geometry.py && sha256sum /a0/usr/extensions/python/tool_execute_after/_80_visual_geometry.py; curl --max-time 2 -s -o /dev/null -w \"benchmark_port=%{http_code}\\n\" http://127.0.0.1:18765/0 || true'; done"))
