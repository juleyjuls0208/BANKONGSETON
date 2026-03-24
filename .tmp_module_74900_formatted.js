74900:(a,b,c)=>{"use strict";
c.d(b,{xD:()=>aa,Fs:()=>_,tL:()=>Z,yd:()=>$,tS:()=>W,pA:()=>v,tl:()=>P,Os:()=>X,jL:()=>R,eG:()=>L,O5:()=>Q,sM:()=>ac});
var d=c(31421),e=c(73024),f=c(46193),g=c(76760),h=c(73136),i=c(34431),j=c(36460),k=c(7849),l=c(45872);
let m="GSD_AUTO_DASHBOARD_MODULE";
function n(){return{active:!1,paused:!1,stepMode:!1,startTime:0,elapsed:0,currentUnit:null,completedUnits:[],basePath:"",totalCost:0,totalTokens:0}}
async function o(a,b={}){let c=b.env??process.env;
if("1"===c.GSD_WEB_TEST_USE_FALLBACK_AUTO_DASHBOARD)return n();
let f=b.existsSync??e.existsSync,j=(0,g.join)(a,"src","resources","extensions","gsd","tests","resolve-ts.mjs"),k=c.GSD_WEB_TEST_AUTO_DASHBOARD_MODULE||(0,g.join)(a,"src","resources","extensions","gsd","auto.ts");
if(!f(j)||!f(k))throw Error(`authoritative auto dashboard provider not found;
 checked=${j},${k}`);
let l=`const { pathToFileURL } = await import("node:url");
 const mod = await import(pathToFileURL(process.env.${m}).href);
 const result = await mod.getAutoDashboardData();
 process.stdout.write(JSON.stringify(result));
`;
return await new Promise((e,f)=>{(0,d.execFile)(b.execPath??process.execPath,["--import",(0,h.pathToFileURL)(j).href,(0,i.h)(a),"--input-type=module","--eval",l],{cwd:a,env:{...c,[m]:k},maxBuffer:1048576},(a,b,c)=>{if(a)return void f(Error(`authoritative auto dashboard subprocess failed: ${c||a.message}`));
try{e(JSON.parse(b))}catch(a){f(Error(`authoritative auto dashboard subprocess returned invalid JSON: ${a instanceof Error?a.message:String(a)}`))}})})}var p=c(52813);
let q=(0,g.resolve)((0,g.dirname)((0,h.fileURLToPath)("file:///home/runner/work/gsd-2/gsd-2/src/web/bridge-service.ts")),"../.."),r=new Set(["get_state","get_available_models","get_session_stats","get_messages","get_last_assistant_text","get_fork_messages","get_commands"]);
function s(a){return a.toLowerCase().replace(/\s+/g," ").trim()}
function t(a){return!!a.name?.trim()}
function u(a,b){let c=`${a.id} ${a.name??""} ${a.allMessagesText} ${a.cwd}`;
if("regex"===b.mode){if(!b.regex)return{matches:!1,score:0};
let a=c.search(b.regex);
return a<0?{matches:!1,score:0}:{matches:!0,score:.1*a}}if(0===b.tokens.length)return{matches:!0,score:0};
let d=0,e=null;
for(let a of b.tokens){if("phrase"===a.kind){null===e&&(e=s(c));
let b=s(a.value);
if(!b)continue;
let f=e.indexOf(b);
if(f<0)return{matches:!1,score:0};
d+=.1*f;
continue}let b=function(a,b){let c=a.toLowerCase(),d=b.toLowerCase(),e=a=>{if(0===a.length)return{matches:!0,score:0};
if(a.length>d.length)return{matches:!1,score:0};
let b=0,c=0,e=-1,f=0;
for(let g=0;
g<d.length&&b<a.length;
g++){if(d[g]!==a[b])continue;
let h=0===g||/[\s\-_./:]/.test(d[g-1]);
e===g-1?c-=5*++f:(f=0,e>=0&&(c+=(g-e-1)*2)),h&&(c-=10),c+=.1*g,e=g,b++}return b<a.length?{matches:!1,score:0}:{matches:!0,score:c}},f=e(c);
if(f.matches)return f;
let g=c.match(/^(?<letters>[a-z]+)(?<digits>[0-9]+)$/),h=c.match(/^(?<digits>[0-9]+)(?<letters>[a-z]+)$/),i=g?`${g.groups?.digits??""}${g.groups?.letters??""}`:h?`${h.groups?.letters??""}${h.groups?.digits??""}`:"";
if(!i)return f;
let j=e(i);
return j.matches?{matches:!0,score:j.score+5}:f}(a.value,c);
if(!b.matches)return{matches:!1,score:0};
d+=b.score}return{matches:!0,score:d}}
function v(a){let b,c=F().existsSync??e.existsSync,d=c((0,g.join)(a,".gsd")),f=c((0,g.join)(a,".planning")),h=c((0,g.join)(a,".git")),i=c((0,g.join)(a,"package.json")),j=c((0,g.join)(a,"Cargo.toml")),k=c((0,g.join)(a,"go.mod")),l=c((0,g.join)(a,"pyproject.toml")),m=0;
try{m=(0,e.readdirSync)(a).filter(a=>!a.startsWith(".")).length}catch{}let n={hasGsdFolder:d,hasPlanningFolder:f,hasGitRepo:h,hasPackageJson:i,hasCargo:j,hasGoMod:k,hasPyproject:l,fileCount:m};
if(d){let c=(0,g.join)(a,".gsd","milestones"),d=!1;
try{d=(0,e.readdirSync)(c,{withFileTypes:!0}).some(a=>a.isDirectory())}catch{}b=d?"active-gsd":"empty-gsd"}else b=f?"v1-legacy":i||j||k||l||m>2||h&&m>0?"brownfield":"blank";
return{kind:b,signals:n}}let w={spawn:(a,b,c)=>(0,d.spawn)(a,b,c),existsSync:e.existsSync,execPath:process.execPath,env:process.env,indexWorkspace:a=>K(a),getAutoDashboardData:async()=>{let a=F(),b=a.env??process.env,c=L(b);
return await o(c.packageRoot,{execPath:a.execPath??process.execPath,env:b,existsSync:a.existsSync??e.existsSync})},listSessions:async a=>J(a)},x=new Map,y=new Map;
async function z(a){let b=F(),c=(0,g.join)(a.packageRoot,"packages","pi-coding-agent","dist","core","session-manager.js");
if(!(b.existsSync??e.existsSync)(c))throw Error(`session manager module not found;
 checked=${c}`);
return await new Promise((e,f)=>{(0,d.execFile)(b.execPath??process.execPath,["--input-type=module","--eval",'const { pathToFileURL } = await import("node:url");
 const mod = await import(pathToFileURL(process.env.GSD_SESSION_MANAGER_MODULE).href);
 const sessions = await mod.SessionManager.list(process.env.GSD_SESSION_BROWSER_CWD, process.env.GSD_SESSION_BROWSER_DIR);
 process.stdout.write(JSON.stringify(sessions.map((session) => ({ ...session, created: session.created.toISOString(), modified: session.modified.toISOString() }))));
'],{cwd:a.packageRoot,env:{...b.env??process.env,GSD_SESSION_MANAGER_MODULE:c,GSD_SESSION_BROWSER_CWD:a.projectCwd,GSD_SESSION_BROWSER_DIR:a.projectSessionsDir},maxBuffer:1048576},(a,b,c)=>{if(a)return void f(Error(`session list subprocess failed: ${c||a.message}`));
try{let a=JSON.parse(b);
e(a.map(a=>({...a,created:new Date(a.created),modified:new Date(a.modified)})))}catch(a){f(Error(`session list subprocess returned invalid JSON: ${a instanceof Error?a.message:String(a)}`))}})})}
async function A(a,b,c){let f=F(),h=(0,g.join)(a.packageRoot,"packages","pi-coding-agent","dist","core","session-manager.js");
if(!(f.existsSync??e.existsSync)(h))throw Error(`session manager module not found;
 checked=${h}`);
await new Promise((e,g)=>{(0,d.execFile)(f.execPath??process.execPath,["--input-type=module","--eval",'const { pathToFileURL } = await import("node:url");
 const mod = await import(pathToFileURL(process.env.GSD_SESSION_MANAGER_MODULE).href);
 const manager = mod.SessionManager.open(process.env.GSD_TARGET_SESSION_PATH, process.env.GSD_SESSION_BROWSER_DIR);
 manager.appendSessionInfo(process.env.GSD_TARGET_SESSION_NAME);
'],{cwd:a.packageRoot,env:{...f.env??process.env,GSD_SESSION_MANAGER_MODULE:h,GSD_SESSION_BROWSER_DIR:a.projectSessionsDir,GSD_TARGET_SESSION_PATH:b,GSD_TARGET_SESSION_NAME:c},maxBuffer:1048576},(a,b,c)=>{a?g(Error(`session rename subprocess failed: ${c||a.message}`)):e()})})}
function B(){return new Date().toISOString()}
function C(a){return`${JSON.stringify(a)}
`}
function D(a){return a.replace(/sk-[A-Za-z0-9_-]{6,}/g,"[redacted]").replace(/xox[baprs]-[A-Za-z0-9-]+/g,"[redacted]").replace(/Bearer\s+[^\s]+/gi,"Bearer [redacted]").replace(/([A-Z0-9_]*(?:API[_-]?KEY|TOKEN|SECRET)["'=:\s]+)([^\s,;
"']+)/gi,"$1[redacted]")}
function E(a){return D(a instanceof Error?a.message:String(a)).replace(/\s+/g," ").trim()}
function F(){return{...w}}
function G(a){return structuredClone(a)}
async function H(a,b){let c=y.get(a),d=Date.now();
if(c?.value&&c.expiresAt>d)return G(c.value);
if(c?.promise)return G(await c.promise);
let e=b().then(b=>(y.set(a,{value:G(b),expiresAt:Date.now()+3e4,promise:null}),b)).catch(b=>{throw y.delete(a),b});
return y.set(a,{value:c?.value??null,expiresAt:0,promise:e}),G(await e)}
async function I(a,b){let c=F(),f=(0,g.join)(b,"src","resources","extensions","gsd","tests","resolve-ts.mjs"),j=(0,g.join)(b,"src","resources","extensions","gsd","workspace-index.ts"),k=c.existsSync??e.existsSync;
if(!k(f)||!k(j))throw Error(`workspace index loader not found;
 checked=${f},${j}`);
return await new Promise((e,g)=>{(0,d.execFile)(c.execPath??process.execPath,["--import",(0,h.pathToFileURL)(f).href,(0,i.h)(b),"--input-type=module","--eval",'const { pathToFileURL } = await import("node:url");
 const mod = await import(pathToFileURL(process.env.GSD_WORKSPACE_MODULE).href);
 const result = await mod.indexWorkspace(process.env.GSD_WORKSPACE_BASE);
 process.stdout.write(JSON.stringify(result));
'],{cwd:b,env:{...c.env??process.env,GSD_WORKSPACE_MODULE:j,GSD_WORKSPACE_BASE:a},maxBuffer:1048576},(a,b,c)=>{if(a)return void g(Error(`workspace index subprocess failed: ${c||a.message}`));
try{e(JSON.parse(b))}catch(a){g(Error(`workspace index subprocess returned invalid JSON: ${a instanceof Error?a.message:String(a)}`))}})})}
function J(a){if(!(0,e.existsSync)(a))return[];
let b=(0,e.readdirSync)(a).filter(a=>a.endsWith(".jsonl")).map(b=>(function(a){try{let b,c=(0,e.readFileSync)(a,"utf-8").split("\n").map(a=>a.trim()).filter(Boolean),d="",f="",g=(0,e.statSync)(a).birthtime,h=0;
for(let a of c){let c=JSON.parse(a);
"session"===c.type?(d="string"==typeof c.id?c.id:d,f="string"==typeof c.cwd?c.cwd:f,"string"==typeof c.timestamp&&(g=new Date(c.timestamp))):"session_info"===c.type&&"string"==typeof c.name?b=c.name:"message"===c.type&&(h+=1)}if(!d)return null;
return{path:a,id:d,cwd:f,name:b,created:g,modified:(0,e.statSync)(a).mtime,messageCount:h}}catch{return null}})((0,g.join)(a,b))).filter(a=>null!==a);
return b.sort((a,b)=>b.modified.getTime()-a.modified.getTime()),b}
async function K(a){let b=L().packageRoot;
return await I(a,b)}
function L(a=F().env??process.env,b){let c=b||a.GSD_WEB_PROJECT_CWD||process.cwd(),d=a.GSD_WEB_PROJECT_SESSIONS_DIR||function(a,b=k.vo){let c=`--${a.replace(/^[/\\]/,"").replace(/[/\\:]/g,"-")}--`;
return(0,g.join)(b,c)}(c);
return{projectCwd:c,projectSessionsDir:d,packageRoot:a.GSD_WEB_PACKAGE_ROOT||q}}
function M(a){return"extension_ui_response"===a.type}
function N(a){return a.success?a:{...a,error:D(a.error)}}
class O{constructor(a,b){this.subscribers=new Set,this.terminalSubscribers=new Set,this.pendingRequests=new Map,this.process=null,this.detachStdoutReader=null,this.startPromise=null,this.refreshPromise=null,this.authRefreshPromise=null,this.requestCounter=0,this.stderrBuffer="",this.config=a,this.deps=b,this.snapshot={phase:"idle",projectCwd:a.projectCwd,projectSessionsDir:a.projectSessionsDir,packageRoot:a.packageRoot,startedAt:null,updatedAt:B(),connectionCount:0,lastCommandType:null,activeSessionId:null,activeSessionFile:null,sessionState:null,lastError:null}}getSnapshot(){return structuredClone(this.snapshot)}publishLiveStateInvalidation(a){var b,c;
let d=(c=a,{type:"live_state_invalidation",at:B(),reason:c.reason,source:c.source,domains:[...new Set(c.domains)],workspaceIndexCacheInvalidated:!!c.workspaceIndexCacheInvalidated});
return d.workspaceIndexCacheInvalidated&&((b=this.config.projectCwd)?y.delete(b):y.clear()),this.emit(d),d}async ensureStarted(){if(!this.process||"ready"!==this.snapshot.phase){if(this.startPromise)return await this.startPromise;
this.startPromise=this.startInternal();
try{await this.startPromise}finally{this.startPromise=null}}}async sendInput(a){if(await this.ensureStarted(),!this.process?.stdin)throw Error(this.snapshot.lastError?.message||"RPC bridge is not connected");
if(M(a))return this.process.stdin.write(C(a)),null;
let b=N(await this.requestResponse(a));
if(this.snapshot.lastCommandType=a.type,this.snapshot.updatedAt=B(),!b.success)return this.recordError(b.error,this.snapshot.phase,{commandType:a.type}),this.broadcastStatus(),b;
if("get_state"===a.type&&b.success&&"get_state"===b.command)return this.applySessionState(b.data),this.broadcastStatus(),b;
let c=function(a,b){if(!b.success)return null;
switch(a.type){case"new_session":return"new_session"===b.command&&!1===b.data.cancelled?{reason:"new_session",source:"rpc_command",domains:["resumable_sessions","recovery"]}:null;
case"switch_session":return"switch_session"===b.command&&!1===b.data.cancelled?{reason:"switch_session",source:"rpc_command",domains:["resumable_sessions","recovery"]}:null;
case"fork":return"fork"===b.command&&!1===b.data.cancelled?{reason:"fork",source:"rpc_command",domains:["resumable_sessions","recovery"]}:null;
case"set_session_name":return"set_session_name"===b.command?{reason:"set_session_name",source:"rpc_command",domains:["resumable_sessions"]}:null;
default:return null}}(a,b);
return c&&this.publishLiveStateInvalidation(c),this.queueStateRefresh(),this.broadcastStatus(),b}async refreshAuth(){if(this.authRefreshPromise)return await this.authRefreshPromise;
this.authRefreshPromise=this.refreshAuthInternal().finally(()=>{this.authRefreshPromise=null}),await this.authRefreshPromise}async refreshAuthInternal(){this.startPromise&&await this.startPromise,this.process&&"ready"===this.snapshot.phase&&this.resetProcessForAuthRefresh(),await this.ensureStarted()}resetProcessForAuthRefresh(){let a=this.process;
for(let a of(this.process=null,this.detachStdoutReader?.(),this.detachStdoutReader=null,this.stderrBuffer="",this.pendingRequests.values()))clearTimeout(a.timeout),a.reject(Error("RPC bridge restarting to reload auth"));
if(this.pendingRequests.clear(),a){a.removeAllListeners("exit"),a.removeAllListeners("error"),a.kill("SIGTERM");
try{a?.stdin?.destroy()}catch{}try{a?.stdout?.destroy()}catch{}try{a?.stderr?.destroy()}catch{}}this.snapshot.phase="idle",this.snapshot.updatedAt=B(),this.snapshot.lastError=null,this.broadcastStatus()}subscribe(a){return this.subscribers.add(a),this.snapshot.connectionCount=this.subscribers.size,this.snapshot.updatedAt=B(),this.broadcastStatus(),()=>{this.subscribers.delete(a),this.snapshot.connectionCount=this.subscribers.size,this.snapshot.updatedAt=B(),this.subscribers.size>0&&this.broadcastStatus()}}subscribeTerminal(a){return this.terminalSubscribers.add(a),()=>{this.terminalSubscribers.delete(a)}}async sendTerminalInput(a){await this.sendTerminalCommand({type:"terminal_input",data:a})}async resizeTerminal(a,b){await this.sendTerminalCommand({type:"terminal_resize",cols:a,rows:b})}async redrawTerminal(){await this.sendTerminalCommand({type:"terminal_redraw"})}async sendTerminalCommand(a){await this.ensureStarted();
let b=N(await this.requestResponse(a));
if(!b.success)throw this.recordError(b.error,this.snapshot.phase,{commandType:a.type}),this.broadcastStatus(),Error(b.error)}async dispose(){for(let a of(this.detachStdoutReader?.(),this.detachStdoutReader=null,this.terminalSubscribers.clear(),this.pendingRequests.values()))clearTimeout(a.timeout),a.reject(Error("RPC bridge disposed"));
this.pendingRequests.clear(),this.process&&(this.process.removeAllListeners(),this.process.kill("SIGTERM"),this.process=null),this.snapshot.phase="idle",this.snapshot.connectionCount=0,this.snapshot.updatedAt=B()}async startInternal(){var a,b,c,g;
let h,i,j,k,l,m,n;
this.snapshot.phase="starting",this.snapshot.startedAt=B(),this.snapshot.updatedAt=this.snapshot.startedAt,this.snapshot.lastError=null,this.broadcastStatus();
try{a=this.config,b=this.deps,h=(0,p.N)({packageRoot:a.packageRoot,cwd:a.projectCwd,execPath:b.execPath??process.execPath,hostKind:(b.env??process.env).GSD_WEB_HOST_KIND,mode:"rpc",sessionDir:a.projectSessionsDir,existsSync:b.existsSync??e.existsSync})}catch(a){throw this.snapshot.phase="failed",this.recordError(a,"starting"),a}let o=this.deps.spawn??((a,b,c)=>(0,d.spawn)(a,b,c)),q={...this.deps.env??process.env};
delete q.GSD_CODING_AGENT_DIR,q.GSD_WEB_BRIDGE_TUI="1";
let r=o(h.command,h.args,{cwd:h.cwd,env:q,stdio:["pipe","pipe","pipe"]});
this.process=r,this.stderrBuffer="",r.stderr.on("data",a=>{var b,c;
let d;
this.stderrBuffer=(b=this.stderrBuffer,c=a.toString(),(d=`${b}${c}`).length<=8e3?d:d.slice(d.length-8e3))}),this.detachStdoutReader=(c=r.stdout,g=a=>this.handleStdoutLine(a),j=new f.StringDecoder("utf8"),k="",l=a=>{g(a.endsWith("\r")?a.slice(0,-1):a)},m=a=>{for(k+="string"==typeof a?a:j.write(a);
;
){let a=k.indexOf("\n");
if(-1===a)return;
l(k.slice(0,a)),k=k.slice(a+1)}},n=()=>{(k+=j.end()).length>0&&(l(k),k="")},c.on("data",m),c.on("end",n),()=>{c.off("data",m),c.off("end",n)}),r.once("exit",(a,b)=>this.handleProcessExit(a,b)),r.once("error",a=>this.handleProcessExit(null,null,a));
let s=new Promise((a,b)=>{i=setTimeout(()=>b(Error("RPC bridge startup timed out after 150000ms")),15e4)});
try{await Promise.race([this.refreshState(!0),s]),this.snapshot.phase="ready",this.snapshot.updatedAt=B(),this.snapshot.lastError=null,this.broadcastStatus()}catch(a){throw this.snapshot.phase="failed",this.recordError(a,"starting"),this.broadcastStatus(),a}finally{i&&clearTimeout(i)}}async queueStateRefresh(){if(this.refreshPromise)return await this.refreshPromise;
this.refreshPromise=this.refreshState(!1).catch(a=>{this.recordError(a,this.snapshot.phase,{commandType:"get_state"})}).finally(()=>{this.refreshPromise=null}),await this.refreshPromise}async refreshState(a){let b=N(await this.requestResponse({type:"get_state"},a?15e4:void 0));
if(!b.success)throw Error(b.error);
"get_state"===b.command&&this.applySessionState(b.data),this.snapshot.updatedAt=B(),a||this.broadcastStatus()}applySessionState(a){this.snapshot.sessionState=a,this.snapshot.activeSessionId=a.sessionId,this.snapshot.activeSessionFile=a.sessionFile??null}requestResponse(a,b){if(!this.process?.stdin)return Promise.reject(Error("RPC bridge is not connected"));
let c=a.id??`web_${++this.requestCounter}`,d={...a,id:c},e=b??3e4;
return new Promise((a,b)=>{let f=setTimeout(()=>{this.pendingRequests.delete(c),b(Error(`Timed out waiting for RPC response to ${d.type}`))},e);
this.pendingRequests.set(c,{resolve:b=>{clearTimeout(f),a(b)},reject:a=>{clearTimeout(f),b(a)},timeout:f}),this.process.stdin.write(C(d))})}handleStdoutLine(a){var b,c;
let d;
try{d=JSON.parse(a)}catch{return}if("object"==typeof(b=d)&&null!==b&&"type"in b&&"terminal_output"===b.type&&"string"==typeof b.data)return void this.emitTerminal(d.data);
if("object"==typeof d&&null!==d&&"type"in d&&"response"===d.type){let a=N(d);
if(a.id&&this.pendingRequests.has(a.id)){let b=this.pendingRequests.get(a.id);
this.pendingRequests.delete(a.id),b.resolve(a);
return}}let e="object"==typeof(c=d)&&null!==c&&"type"in c&&"extension_error"===c.type?{...c,error:D(c.error)}:c;
if(this.emit(e),"object"==typeof e&&null!==e&&"type"in e&&"session_state_changed"===e.type&&"string"==typeof e.reason){let a=function(a){switch(a){case"new_session":return{reason:"new_session",source:"bridge_event",domains:["resumable_sessions","recovery"]};
case"switch_session":return{reason:"switch_session",source:"bridge_event",domains:["resumable_sessions","recovery"]};
case"fork":return{reason:"fork",source:"bridge_event",domains:["resumable_sessions","recovery"]};
case"set_session_name":return{reason:"set_session_name",source:"bridge_event",domains:["resumable_sessions"]};
default:return null}}(e.reason);
a&&this.publishLiveStateInvalidation(a),this.queueStateRefresh();
return}let f=function(a){if("object"!=typeof a||null===a||!("type"in a))return null;
switch(a.type){case"agent_end":return{reason:"agent_end",source:"bridge_event",domains:["auto","workspace","recovery"],workspaceIndexCacheInvalidated:!0};
case"auto_retry_start":return{reason:"auto_retry_start",source:"bridge_event",domains:["auto","recovery"]};
case"auto_retry_end":return{reason:"auto_retry_end",source:"bridge_event",domains:["auto","recovery"]};
case"auto_compaction_start":return{reason:"auto_compaction_start",source:"bridge_event",domains:["auto","recovery"]};
case"auto_compaction_end":return{reason:"auto_compaction_end",source:"bridge_event",domains:["auto","recovery"]};
default:return null}}(e);
if(f&&this.publishLiveStateInvalidation(f),"object"==typeof e&&null!==e&&"type"in e){let a=e.type;
("agent_end"===a||"auto_retry_start"===a||"auto_retry_end"===a||"auto_compaction_start"===a||"auto_compaction_end"===a)&&this.queueStateRefresh()}}handleProcessExit(a,b,c){var d;
let e,f;
this.detachStdoutReader?.(),this.detachStdoutReader=null,this.process=null;
let g=Error((d=this.stderrBuffer,e=`RPC bridge exited${null!==a?` with code ${a}`:""}${b?` (${b})`:""}`,(f=D(d).trim())?`${e}. stderr=${f}`:e));
for(let a of this.pendingRequests.values())clearTimeout(a.timeout),a.reject(g);
this.pendingRequests.clear(),this.snapshot.phase="failed",this.snapshot.updatedAt=B(),this.recordError(c??g,this.snapshot.activeSessionId?"ready":"starting"),this.broadcastStatus()}recordError(a,b,c={}){this.snapshot.lastError={message:E(a),at:B(),phase:b,afterSessionAttachment:!!this.snapshot.activeSessionId,commandType:c.commandType},this.snapshot.updatedAt=this.snapshot.lastError.at}emit(a){for(let b of this.subscribers)try{b(a)}catch{}}emitTerminal(a){for(let b of this.terminalSubscribers)try{b(a)}catch{}}broadcastStatus(){0!==this.subscribers.size&&this.emit({type:"bridge_status",bridge:this.getSnapshot()})}}
function P(a){let b=(0,g.resolve)(a),c=x.get(b);
if(c)return c;
let d=new O(L(void 0,b),F());
return x.set(b,d),d}
function Q(a){try{let b=new URL(a.url).searchParams.get("project");
if(b)return decodeURIComponent(b)}catch{}return(F().env??process.env).GSD_WEB_PROJECT_CWD||null}
function R(a){let b=Q(a);
if(!b)throw new S;
return b}
class S extends Error{constructor(){super("No project selected"),this.name="NoProjectError"}}
function T(){return P(L().projectCwd)}
function U(a,b){return{id:a.id,path:a.path,cwd:a.cwd,name:a.name,createdAt:a.created.toISOString(),modifiedAt:a.modified.toISOString(),messageCount:a.messageCount,isActive:!!(b&&a.path===b)}}
function V(a,b,c={}){return{success:!1,action:"rename",scope:j.PO,code:a,error:b,...c}}
async function W(a={},b){let c=L(F().env??process.env,b),d=b?P(b):T();
try{await d.ensureStarted()}catch{}let e=d.getSnapshot(),f=await z(c),h=(0,j.on)(a),i=("threaded"===h.sortMode&&!h.query?function(a){let b=[],c=(a,d,e,f)=>{b.push({session:a.session,depth:d,isLastInThread:f,ancestorHasNextSibling:e});
for(let b=0;
b<a.children.length;
b++){let g=a.children[b];
if(!g)continue;
let h=b===a.children.length-1,i=d>0&&!f;
c(g,d+1,[...e,i],h)}};
for(let b=0;
b<a.length;
b++){let d=a[b];
d&&c(d,0,[],b===a.length-1)}return b}(function(a){let b=new Map;
for(let c of a)b.set(c.path,{session:c,children:[]});
let c=[];
for(let d of a){let a=b.get(d.path);
if(!a)continue;
let e=d.parentSessionPath;
if(e&&b.has(e)){b.get(e).children.push(a);
continue}c.push(a)}let d=a=>{for(let b of(a.sort((a,b)=>b.session.modified.getTime()-a.session.modified.getTime()),a))d(b.children)};
return d(c),c}("named"===h.nameFilter?f.filter(a=>t(a)):f)):(function(a,b,c,d){let e="all"===d?a:a.filter(a=>t(a));
if(!b.trim())return e;
let f=function(a){let b=a.trim();
if(!b)return{mode:"tokens",tokens:[],regex:null};
if(b.startsWith("re:")){let a=b.slice(3).trim();
if(!a)return{mode:"regex",tokens:[],regex:null,error:"Empty regex"};
try{return{mode:"regex",tokens:[],regex:RegExp(a,"i")}}catch(a){return{mode:"regex",tokens:[],regex:null,error:a instanceof Error?a.message:String(a)}}}let c=[],d="",e=!1,f=!1,g=a=>{let b=d.trim();
d="",b&&c.push({kind:a,value:b})};
for(let a=0;
a<b.length;
a++){let c=b[a];
if(c){if('"'===c){e?(g("phrase"),e=!1):(g("fuzzy"),e=!0);
continue}if(!e&&/\s/.test(c)){g("fuzzy");
continue}d+=c}}return(e&&(f=!0),f)?{mode:"tokens",tokens:b.split(/\s+/).map(a=>a.trim()).filter(a=>a.length>0).map(a=>({kind:"fuzzy",value:a})),regex:null}:(g(e?"phrase":"fuzzy"),{mode:"tokens",tokens:c,regex:null})}(b);
if(f.error)return[];
if("recent"===c){let a=[];
for(let b of e)u(b,f).matches&&a.push(b);
return a}let g=[];
for(let a of e){let b=u(a,f);
b.matches&&g.push({session:a,score:b.score})}return g.sort((a,b)=>a.score!==b.score?a.score-b.score:b.session.modified.getTime()-a.session.modified.getTime()),g.map(a=>a.session)})(f,h.query,h.sortMode,h.nameFilter).map(a=>({session:a,depth:0,isLastInThread:!0,ancestorHasNextSibling:[]}))).map(a=>(function(a,b){let{session:c}=a,d=!!(b&&(0,g.resolve)(c.path)===(0,g.resolve)(b));
return{id:c.id,path:c.path,cwd:c.cwd,name:c.name,createdAt:c.created.toISOString(),modifiedAt:c.modified.toISOString(),messageCount:c.messageCount,parentSessionPath:c.parentSessionPath,firstMessage:c.firstMessage,isActive:d,depth:a.depth,isLastInThread:a.isLastInThread,ancestorHasNextSibling:[...a.ancestorHasNextSibling]}})(a,e.activeSessionFile));
return{project:{scope:j.PO,cwd:c.projectCwd,sessionsDir:c.projectSessionsDir,activeSessionPath:e.activeSessionFile},query:h,totalSessions:f.length,returnedSessions:i.length,sessions:i}}
async function X(a,b){var c,d;
let e,f=L(F().env??process.env,b),h=a.name.trim();
if(!h)return V("invalid_request","Session name cannot be empty",{sessionPath:a.sessionPath,name:a.name});
let i=(c=await z(f),d=a.sessionPath,e=(0,g.resolve)(d),c.find(a=>(0,g.resolve)(a.path)===e));
if(!i)return V("not_found","Session is not available in the current project browser",{sessionPath:a.sessionPath,name:h});
let k=b?P(b):T();
try{await k.ensureStarted()}catch(a){return V("rename_failed",E(a),{sessionPath:i.path,name:h})}let l=k.getSnapshot().activeSessionFile;
if(l&&(0,g.resolve)(l)===(0,g.resolve)(i.path)){let a=await ac({type:"set_session_name",name:h},b);
return null===a?V("rename_failed","Active session rename did not return a response",{sessionPath:i.path,name:h,isActiveSession:!0,mutation:"rpc"}):a.success?{success:!0,action:"rename",scope:j.PO,sessionPath:i.path,name:h,isActiveSession:!0,mutation:"rpc"}:V("onboarding_locked"===a.code?"onboarding_locked":"rename_failed",a.error,{sessionPath:i.path,name:h,isActiveSession:!0,mutation:"rpc"})}try{return await A(f,i.path,h),k.publishLiveStateInvalidation({reason:"set_session_name",source:"session_manage",domains:["resumable_sessions"]}),{success:!0,action:"rename",scope:j.PO,sessionPath:i.path,name:h,isActiveSession:!1,mutation:"session_file"}}catch(a){return V("rename_failed",E(a),{sessionPath:i.path,name:h,isActiveSession:!1,mutation:"session_file"})}}
async function Y(a,b){if(a.getOnboardingState)return await a.getOnboardingState();
if(a.getOnboardingNeeded){var c;
return{status:(c=await a.getOnboardingNeeded(k.sI,b))?"blocked":"ready",locked:c,lockReason:c?"required_setup":null,required:{blocking:!0,skippable:!1,satisfied:!c,satisfiedBy:c?null:{providerId:"legacy",source:"runtime"},providers:[]},optional:{blocking:!1,skippable:!0,sections:[]},lastValidation:null,activeFlow:null,bridgeAuthRefresh:{phase:"idle",strategy:null,startedAt:null,completedAt:null,error:null}}}return await (0,l.r$)()}
async function Z(a){let b=F(),c=b.env??process.env;
return await Y(b,c)}
async function $(a=["auto","workspace","resumable_sessions"],b){let c=F(),d=L(c.env??process.env,b),e=b?P(b):T();
try{await e.ensureStarted()}catch{}let f=e.getSnapshot(),g=[...new Set(a)],h={bridge:f};
if(g.includes("workspace")&&(h.workspace=await H(d.projectCwd,async()=>await (c.indexWorkspace??K)(d.projectCwd))),g.includes("auto")){let a=c.getAutoDashboardData??(()=>n());
h.auto=await Promise.resolve(a())}return g.includes("resumable_sessions")&&(h.resumableSessions=(await (c.listSessions??(async a=>J(a)))(d.projectSessionsDir)).map(a=>U(a,f.activeSessionFile))),h}
async function _(a){let b=F(),c=b.env??process.env,d=L(c,a),e=b.getAutoDashboardData??(()=>n()),f=b.listSessions??(async a=>J(a)),g=v(d.projectCwd),h=await Y(b,c);
if(h.locked&&"packaged-standalone"===c.GSD_WEB_HOST_KIND)return{project:{cwd:d.projectCwd,sessionsDir:d.projectSessionsDir,packageRoot:d.packageRoot},workspace:{milestones:[],active:{phase:"pre-planning"},scopes:[{scope:"project",label:"project",kind:"project"}],validationIssues:[]},auto:n(),onboarding:h,onboardingNeeded:!0,resumableSessions:[],bridge:{phase:"idle",projectCwd:d.projectCwd,projectSessionsDir:d.projectSessionsDir,packageRoot:d.packageRoot,startedAt:null,updatedAt:new Date().toISOString(),connectionCount:0,lastCommandType:null,activeSessionId:null,activeSessionFile:null,sessionState:null,lastError:null},projectDetection:g};
let i=a?P(a):T(),j=H(d.projectCwd,async()=>await (b.indexWorkspace??K)(d.projectCwd)),k=Promise.resolve(e()),l=f(d.projectSessionsDir);
try{await i.ensureStarted()}catch{}let m=i.getSnapshot(),[o,p,q]=await Promise.all([j,k,l]);
return{project:{cwd:d.projectCwd,sessionsDir:d.projectSessionsDir,packageRoot:d.packageRoot},workspace:o,auto:p,onboarding:h,onboardingNeeded:h.locked,resumableSessions:q.map(a=>U(a,m.activeSessionFile)),bridge:m,projectDetection:g}}
function aa(a,b){return{type:"response",command:a,success:!1,error:E(b)}}
async function ab(a){let b=a?P(a):T();
await b.refreshAuth()}
async function ac(a,b){if(!(!M(a)&&r.has(a.type))){let b=await (0,l.r$)();
if(b.locked){let c;
return c=b.lockReason??"required_setup",{type:"response",command:a.type,success:!1,error:"bridge_refresh_failed"===c?"Workspace is locked because bridge auth refresh failed after setup":"bridge_refresh_pending"===c?"Workspace is still locked while bridge auth refresh completes":"Workspace is locked until required onboarding completes",code:"onboarding_locked",details:{reason:c,onboarding:{locked:b.locked,lockReason:b.lockReason,required:b.required,lastValidation:b.lastValidation,bridgeAuthRefresh:b.bridgeAuthRefresh}}}}}let c=b?P(b):T();
return await c.sendInput(a)}(0,l.Eu)(async()=>{await ab()})