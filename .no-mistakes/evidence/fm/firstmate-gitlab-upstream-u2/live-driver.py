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
results=[]; log=[]
def case(name,patch={},policy=None,outcome='merged',args=[],ready=False,expected=True,omit=None,policy_error=False):
 global current,requests
 home=W/name; shutil.rmtree(home,ignore_errors=True); run([R/'bin/fm-lab-home.sh','create',home]); env['FM_HOME']=str(home)
 (home/'config/backlog-backend').write_text('manual\n')
 meta=home/'state/task-x1.meta'; meta.write_text(f'kind=ship\nmode=no-mistakes\nworktree={W}/repo\nproject={W}/repo\nwindow=fm-task-x1\n')
 current={'mr':dict(base,**patch),'outcome':outcome,'policy_error':policy_error}
 if policy is not None: current['policy']=policy
 if omit: current['mr'].pop(omit,None)
 requests=[]
 cmd=[R/('bin/fm-pr-check.sh' if ready else 'bin/fm-pr-merge.sh'),'task-x1',url]+args
 p=run(cmd); passed=(p.returncode==0)==expected
 writes=[q for q in requests if q['method']=='PUT']
 if not ready and expected: passed=passed and len(writes)==1 and head in writes[0]['body']
 if not expected and not ready and outcome=='merged': passed=passed and not writes
 if ready and not expected: passed=passed and 'pr=' not in meta.read_text() and not (home/'state/task-x1.pr-poll').exists()
 if not ready and outcome!='merged': passed=passed and (home/'state/task-x1.pr-poll').exists() and not (home/'state/task-x1.pr-poll-merge-notified').exists()
 if not ready and not name.startswith('arg-'): passed=passed and bool(requests)
 result={'name':name,'pass':bool(passed),'exit':p.returncode,'requests':list(requests),'output':p.stdout,'meta':meta.read_text(),'state_files':sorted(p.name for p in (home/'state').iterdir())}
 results.append(result); print(name,passed,p.returncode,flush=True)
 log.append(json.dumps(result,indent=2)); (E/'live-cli-transcript.json').write_text(json.dumps(results,indent=2))
case('successful-pipeline')
case('optional-absent-pipeline',{'head_pipeline':None})
case('required-absent-pipeline',{'head_pipeline':None},policy={'only_allow_merge_if_pipeline_succeeds':True},expected=False)
for label,policy in [('missing',{}),('string',{'only_allow_merge_if_pipeline_succeeds':'false'}),('array',[{'only_allow_merge_if_pipeline_succeeds':False}])]: case('policy-'+label,{'head_pipeline':None},policy=policy,expected=False)
case('policy-unreadable',{'head_pipeline':None},policy_error=True,expected=False)
case('green-policy-unreadable',policy_error=True)
for status in ['failed','running']: case('pipeline-'+status,{'head_pipeline':{'sha':head,'status':status}},expected=False)
case('pipeline-stale',{'head_pipeline':{'sha':'b'*40,'status':'success'}},expected=False)
case('pipeline-omitted',omit='head_pipeline',expected=False)
for label,value in [('true',True),('null',None),('string','false')]: case('draft-'+label,{'draft':value},expected=False)
case('draft-missing',omit='draft',expected=False)
for flag in ['--auto-merge','--when-pipeline-succeeds','--sha=bbbb','--repo=other/project']: case('arg-'+flag.split('=')[0][2:],args=['--',flag],expected=False)
for outcome in ['opened','closed','unreadable']: case('outcome-'+outcome,outcome=outcome,expected=False)
case('ready-draft',{'draft':True},ready=True,expected=False)
case('ready-normal',ready=True)
server.shutdown()
(E/'live-driver.py').write_text(pathlib.Path(__file__).read_text())
print('TOTAL',len(results),'FAIL',sum(not r['pass'] for r in results))
