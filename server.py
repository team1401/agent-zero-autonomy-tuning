from http.server import HTTPServer,BaseHTTPRequestHandler
from PIL import Image,ImageDraw,ImageFont
import random,json,pathlib,io,time
P=pathlib.Path('/a0/usr/workdir/autonomy-benchmark');P.mkdir(exist_ok=True)
r=random.SystemRandom();trials={};font=ImageFont.truetype('/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf',25)
for n,(w,h) in enumerate([(1024,768),(800,600),(900,700)]):
 stages=[]
 for step in range(2):
  labels=['ALPHA','BETA','GAMMA','DELTA'];r.shuffle(labels);target=r.choice(labels)
  coords=[(r.randint(115,210),r.randint(170,220)),(r.randint(w-280,w-120),r.randint(170,240)),(r.randint(120,240),r.randint(380,480)),(r.randint(w-280,w-120),r.randint(380,480))]
  if n==2 and step==1: coords=[(x,y+550) for x,y in coords]
  stages.append({'labels':labels,'target':target,'coords':coords,'center':coords[labels.index(target)]})
 trials[str(n)]={'width':w,'height':h,'stages':stages,'stage':0,'clicks':[],'marker':'PASS-'+str(r.randrange(100000,999999))}
def persist(): (P/'groundtruth-state.json').write_text(json.dumps(trials,indent=2))
def image(t):
 tall=t['height']+550 if t['stage']==1 and t is trials['2'] else t['height'];im=Image.new('RGB',(t['width'],tall),'#eeeeee');d=ImageDraw.Draw(im)
 if t['stage']==2:d.text((70,160),t['marker'],font=font,fill='black')
 else:
  s=t['stages'][t['stage']];d.text((20,25),'Click '+s['target']+(' (scroll down)' if tall>t['height'] else ''),font=font,fill='black')
  for label,(x,y) in zip(s['labels'],s['coords']):
   if t is trials['0']:d.ellipse((x-75,y-45,x+75,y+45),fill='#b7d9ef',outline='black',width=3)
   else:d.rounded_rectangle((x-75,y-40,x+75,y+40),radius=7,fill='#c4e0bb',outline='black',width=3)
   d.text((x,y),label,font=font,anchor='mm',fill='black')
 b=io.BytesIO();im.save(b,format='PNG');return b.getvalue()
class H(BaseHTTPRequestHandler):
 def log_message(self,*a):pass
 def do_GET(self):
  n=self.path.split('?')[0].strip('/').split('/')[0];t=trials.get(n)
  if t is None:self.send_error(404);return
  if '/image' in self.path:data=image(t);mime='image/png'
  else:data=('''<!doctype html><title>Visual benchmark</title><style>body{margin:0}</style><img draggable="false" src="/'''+n+'''/image"><script>document.querySelector('img').onclick=async e=>{await fetch('/'''+n+'''/click',{method:'POST',body:JSON.stringify({x:e.offsetX,y:e.offsetY})});e.target.src='/'''+n+'''/image?t='+Date.now()}</script>''').encode();mime='text/html'
  self.send_response(200);self.send_header('Content-Type',mime);self.send_header('Cache-Control','no-store');self.end_headers();self.wfile.write(data)
 def do_POST(self):
  n=self.path.strip('/').split('/')[0];t=trials[n];v=json.loads(self.rfile.read(int(self.headers['Content-Length'])));s=t['stages'][min(t['stage'],1)];x,y=s['center'];ok=abs(v['x']-x)<=75 and abs(v['y']-y)<=40
  t['clicks'].append({'time':time.time(),'stage':t['stage'],**v,'correct':ok})
  if ok and t['stage']<2:t['stage']+=1
  persist();self.send_response(204);self.end_headers()
persist();HTTPServer(('127.0.0.1',18765),H).serve_forever()
