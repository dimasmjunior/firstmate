import os, pathlib, subprocess, json, threading, http.server, shutil
R=pathlib.Path.cwd(); W=R/'.live-validation'; E=pathlib.Path('/home/dimas/.no-mistakes/evidence/01M4DS4Q9EA0N68CM3Q1SX7CMA')
env={k:v for k,v in os.environ.items() if not k.startswith(('FM_','GITLAB_','GLAB_','GIT_'))}
env.update(HOME=str(W/'user'), XDG_CONFIG_HOME=str(W/'user/config'), GLAB_CONFIG_DIR=str(W/'glab'), GIT_CONFIG_NOSYSTEM='1',GIT_CONFIG_GLOBAL='/dev/null',GIT_AUTHOR_NAME='Validation',GIT_AUTHOR_EMAIL='validation@example.invalid',GIT_COMMITTER_NAME='Validation',GIT_COMMITTER_EMAIL='validation@example.invalid',GLAB_CHECK_UPDATE='false',NO_COLOR='1')
for d in ['user','glab']: (W/d).mkdir(exist_ok=True)
def run(args, **kw): return subprocess.run([str(x) for x in args],env=env,text=True,stdout=subprocess.PIPE,stderr=subprocess.STDOUT,timeout=45,**kw)
run(['git','init',W/'repo']); run(['git','-C',W/'repo','commit','--allow-empty','-m','fixture'])
head=run(['git','-C',W/'repo','rev-parse','HEAD']).stdout.strip(); run(['git','-C',W/'repo','update-ref','refs/remotes/origin/main',head])
current={}; requests=[]
class Handler(http.server.BaseHTTPRequestHandler):
 def log_message(self,*a): pass
 def respond(self):
  body=self.rfile.read(int(self.headers.get('Content-Length',0))).decode(); requests.append({'method':self.command,'path':self.path,'body':body})
  code=200; path=self.path.split('?')[0]
  if path.endswith('/merge'):
   current['submitted']=True; data=dict(current['mr'],state='merged')
  elif '/merge_requests/7' in path:
   if path.endswith(('/notes','/discussions','/approvals')): data=[]
   elif current.get('submitted') and current.get('outcome')=='unreadable': code=503; data={'message':'unavailable'}
   else:
    data=dict(current['mr']); data['state']=current.get('outcome','merged') if current.get('submitted') else 'opened'
  elif path.endswith('/user'): data={'id':1,'username':'validation','name':'Validation'}
  elif '/projects/' in path:
   if current.get('policy_error'): code=503; data={'message':'unavailable'}
   else: data=current.get('policy',{'only_allow_merge_if_pipeline_succeeds':False})
  else: code=404; data={'message':'unknown path'}
  self.send_response(code);self.send_header('Content-Type','application/json');self.end_headers(); self.wfile.write(json.dumps(data).encode())
 do_GET=respond; do_PUT=respond; do_POST=respond
server=http.server.ThreadingHTTPServer(('127.0.0.1',0),Handler); threading.Thread(target=server.serve_forever,daemon=True).start()
port=server.server_address[1]
(W/'glab/config.yml').write_text(f"hosts:\n  gitlab.example.test:\n    token: disposable-local-token\n    api_host: 127.0.0.1:{port}\n    api_protocol: http\n    git_protocol: https\n")
(W/'glab/config.yml').chmod(0o600)
url='https://gitlab.example.test/group/project/-/merge_requests/7'
base={'id':7,'iid':7,'project_id':1,'title':'Disposable validation MR','state':'opened','user':{'can_merge':True},'draft':False,'detailed_merge_status':'mergeable','has_conflicts':False,'blocking_discussions_resolved':True,'sha':head,'source_branch':'feature','target_branch':'main','web_url':url,'head_pipeline':{'id':1,'sha':head,'status':'success'}}

home=W/'bootstrap-live'; run([R/'bin/fm-lab-home.sh','create',home]); env['FM_HOME']=str(home)
(home/'data/projects.md').write_text('- one [direct-PR forge=gitlab] - disposable\n- two [direct-PR forge=gitlab] - disposable\n')
for name in ['one','two']:
 repo=home/'projects'/name; run(['git','init',repo]); run(['git','-C',repo,'remote','add','origin','https://gitlab.example.test/group/'+name+'.git'])
current={'mr':base}; requests=[]
env['FM_BOOTSTRAP_DETECT_ONLY']='1'
p=run([R/'bin/fm-bootstrap.sh'])
results=[{'name':'bound-host-authenticated','exit':p.returncode,'output':p.stdout,'requests':list(requests)}]
assert p.returncode==0 and 'NEEDS_GLAB_AUTH' not in p.stdout and any('/user' in q['path'] for q in requests)
# Forward SSH to the real CLI with a disposable configuration, preserving the product host resolver.
ssh=shutil.which('ssh'); bindir=W/'ssh-forward'; bindir.mkdir(exist_ok=True)
config=W/'ssh-config'; config.write_text('Host lab-alias\n  HostName gitlab.example.test\n')
(bindir/'ssh').write_text('#!/bin/sh\nexec '+ssh+' -F '+str(config)+' "$@"\n'); (bindir/'ssh').chmod(0o755)
env['PATH']=str(bindir)+':'+env['PATH']
for name in ['one','two']: run(['git','-C',home/'projects'/name,'remote','set-url','origin','git@lab-alias:group/'+name+'.git'])
requests=[]; p=run([R/'bin/fm-bootstrap.sh']); results.append({'name':'resolved-ssh-alias-authenticated','exit':p.returncode,'output':p.stdout,'requests':list(requests)})
assert p.returncode==0 and 'NEEDS_GLAB_AUTH' not in p.stdout and sum('/user' in q['path'] for q in requests)==1
with (W/'glab/config.yml').open('a') as f: f.write('  lab-alias:\n    token: disposable-local-token\n    api_host: 127.0.0.1:'+str(port)+'\n    api_protocol: http\n')
p=run(['bash','-c','. bin/fm-forge-host-lib.sh; fm_forge_origin_host git@lab-alias:group/one.git gitlab']); results.append({'name':'explicit-login-key-preserved','exit':p.returncode,'output':p.stdout}); assert p.stdout.strip()=='lab-alias'
(E/'bootstrap-live-transcript.json').write_text(json.dumps(results,indent=2)); server.shutdown(); print('Three live bootstrap/host checks passed')
