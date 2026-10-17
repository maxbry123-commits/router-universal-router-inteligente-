
const MODE={v:"file"};
const COL=["verde","amarillo","naranja","rojo"];
const ST=["cerrado","pendiente","incompleto","no_plugins","faltante","no_existe"];
const SL={cerrado:"Cerrado",pendiente:"Pendiente",incompleto:"Incompleto",no_plugins:"No plugins",faltante:"Faltante",no_existe:"No existe"};
const CST={cerrado:"verde",pendiente:"amarillo",incompleto:"amarillo",no_plugins:"naranja",faltante:"rojo",no_existe:"rojo"};
const PCT0={cerrado:100,pendiente:50,incompleto:35,no_plugins:25,faltante:10,no_existe:0};
const RED=new Set(["04","05","06","07","08","09","10","17","18","19","20","G","K","C","P"]);
function N(id,name,st,pct,flow,desc,xray,dest,seg,kids){
  return {id,name,st,pct,flow,desc,xray,dest,seg,kids:kids||[]};
}
const SIX=[
  N("R1","1 Desplegar/","pendiente",40,"lote → destino canónico → si pisa vivo: Refactoria","Inbox del lote N. Sin lote = WAIT.","FACT: raíz autorizada. Destino lo marca ROOT MAP, no el LLM.","Desplegar/","25",[
    N("R1.inbox","inbox lote","faltante",10,"recibir lote → validar → encolar","Carpeta de entrada del lote.","GAP: sin lote activo.","Desplegar/inbox","25"),
    N("R1.dest","destino canónico","pendiente",40,"mapear path → no embeber","Selector de destino.","FACT: deploy v2 dry-run plan.json.","despliegue/","25")
  ]),
  N("R2","2 PIPELINE/","pendiente",45,"plan → S1..Sk → checkpoint → ficha","Planes vivos. PLAN_YAIWES no se reescribe.","FACT: docs CURSOR en PIPELINE/.","PIPELINE/","15",[
    N("R2.plan","PLAN_YAIWES / 52_V1","pendiente",50,"leer plan → no reescribir","Plan 49 tareas método + xray.","FACT: archivo en repo.","PIPELINE/52_V1_PLAN_49_TAREAS_METODO_Y_XRAY.md","15"),
    N("R2.arq","ARQUITECTURA_01/03","pendiente",55,"mapa repo → wordflow","Mapas con flechas.","FACT: ARQ-01 y ARQ-03 existen.","PIPELINE/ARQUITECTURA_*.md","11")
  ]),
  N("R3","3 Método de trabajo/","pendiente",50,"leer ley → aplicar → no inventar path","Leyes. Parche, no rewrite.","FACT: método inmutable. COPY>LINK>PATCH>ADAPT>GENERATE.","Método/","04"),
  N("R4","4 Refactoria/","pendiente",30,"vivo → source → new → ×3 → canónico","source=foto. new=reescritura ×3.","FACT: paridad ×3 antes de tocar hot path.","Refactoria/","00"),
  N("R5","5 Yaiwes wordflow/","naranja",30,"plano Fables → folio → kernel dueño","Etiqueta. Cuerpo=agente-yaiwes/. Sin python -m agente.","FACT: control plane incompleto. Folio ~10%. No hay main.","agente-yaiwes/","08"),
  N("R6","6 Wordflow Code/","naranja",40,"reception → misión → runner → evidence","Etiqueta. Vivo=extensions/wordflow/. Hot path runner.","FACT: motor corre a medias. No reescribir runner.","extensions/wordflow/","20")
];
const YAI=[
  N("CPE","code-programming-engine/","naranja",40,"source OS → fusionar → enchufe → A22","Motor de programación. Pieza única fuera del kernel.","FACT: espejo MIX. NUNCA code desde 0. Dos cuerpos si se copia Wordflow.","code-programming-engine/","19",[
    N("CPE.em","engine-modules/","pendiente",50,"pipeline → dual_compiler → quality_bar","Módulos REAL del pipeline.","FACT: programming_pipeline.py existe.","engine-modules/","19"),
    N("CPE.cp","code-path-execution/","naranja",55,"p01→p12 → runner → smoke","Hot path Fables + stubs p01-p12.","FACT: runner copiado ~15% destino vs 100% origen. Paridad ×3.","code-path-execution/","20",[
      N("CPE.runner","code_path_runner.py","naranja",70,"misión code → runner → smoke → evidence","HOT PATH. No reescribir.","FACT: ~20KB origen 100%. Destino Fables incompleto.","extensions/wordflow/engine/code_path_runner.py","20"),
      N("CPE.p01","p01_context.py … p12_closure.py","rojo",15,"p01→p12 E2E","Stubs 108B.","FACT: gaps S10 p01–p12 E2E abiertos.","code-path-execution/p0*.py","20")
    ]),
    N("CPE.std","standards-forensic/","pendiente",45,"CORE14 + FC-01..13","Standards forensic.","FACT: PLACEHOLDER + pack.","standards-forensic/","06"),
    N("CPE.io","schema-contracts-io/","pendiente",40,"C19 in → runner out","Schemas C-19.","FACT: gap C-19 abierto.","schema-contracts-io/","04"),
    N("CPE.ext","external-motor-bridge/","pendiente",35,"call/download/send/kernel_ext","Puente motores externos.","INFERENCE: motors thin.","external-motor-bridge/","23"),
    N("CPE.mab","multi-account-bridge/","faltante",10,"cuenta A → B via credential_ref","Bridge multi-cuenta.","FACT: PLACEHOLDER.","multi-account-bridge/","25"),
    N("CPE.inb","inbox-normalization/","faltante",10,"inbox → normalizar","Inbox motor.","FACT: PLACEHOLDER.","inbox-normalization/","02"),
    N("CPE.test","module-tests/","pendiente",30,"smoke C-19","Tests módulo.","FACT: code_path_smoke.py existe.","module-tests/","24")
  ]),
  N("KP","kernel-principal/","naranja",35,"AUDIT → PLAN → EXECUTE → VERIFY → REFUTE","Kernel dueño. audit→plan sí; chat→cierre no.","FACT: usable ~30–40%. 0% LLM en núcleo. No hay un solo proceso.","kernel-principal/","08",[
    N("KP.cl","control-layer/","pendiente",40,"kernel dueño → plugin → evidencia","Capa control. SOURCE.md.","FACT: piezas del hilo, no el hilo.","control-layer/","10"),
    N("KP.ek","extension-kernel/","naranja",30,"ficha → validator_v2 → bus.enchufar","ABI mount + passport + registry.","FACT: enchufe v2 en docs. No ley en cada file nuevo.","extension-kernel/","09",[
      N("KP.abi","abi-mount/","pendiente",40,"engine_attach → ficha_loader","Montaje ABI.","MIX.","abi-mount/","09"),
      N("KP.reg","capability-registry/","pendiente",40,"registry → brain → intent","Registry + ficha.v2.json.","MIX.","capability-registry/","09"),
      N("KP.pass","capability-passport/","rojo",15,"passport emitir","Passport ESQ.","FACT: nodo §4.1 obligatorio, body corto.","capability-passport/","09"),
      N("KP.nl","native-learning/","rojo",5,"learn native","ESQ.","PENDIENTE_CODE.","native-learning/","09"),
      N("KP.mg","mount-guard/","rojo",5,"guard mount","ESQ.","PENDIENTE_CODE.","mount-guard/","09")
    ]),
    N("KP.rk","reasoning-kernel/","rojo",20,"panel → consenso → goal dual","Razonamiento.","FACT: cognitive loop no cerrado. Ledger opcional.","reasoning-kernel/","08",[
      N("KP.dod","decision-on-demand/","rojo",5,"decidir on-demand","ESQ.","PENDIENTE_CODE.","decision-on-demand/","08"),
      N("KP.epr","expert-panel-router/","pendiente",35,"expert → router → decision","Panel MIX.","Body parcial.","expert-panel-router/","08"),
      N("KP.ct","consensus-trigger/","rojo",5,"trigger consenso","ESQ.","PENDIENTE_CODE.","consensus-trigger/","08"),
      N("KP.gdd","goal-dual-driver/","rojo",5,"goal dual","ESQ obligatorio §4.1.","PENDIENTE_CODE.","goal-dual-driver/","08"),
      N("KP.wc","workflow-capacity/","rojo",5,"capacity","ESQ.","PENDIENTE_CODE.","workflow-capacity/","08")
    ]),
    N("KP.rg","resource-governance/","naranja",35,"gate → lease → watchdog → breaker → retry","Gobierno recursos.","MIX.","resource-governance/","23",[
      N("KP.rbg","resource-broker-gate/","pendiente",40,"broker → validate resource","MIX.","Body loaders.","resource-broker-gate/","23"),
      N("KP.lease","lease-management/","pendiente",35,"lease acquire/release","MIX.","lease_manager.py.","lease-management/","21"),
      N("KP.wd","watchdog/","pendiente",35,"watch → kill","MIX.","watchdog.py.","watchdog/","24"),
      N("KP.cb","circuit-breaker/","pendiente",35,"open/half/close","MIX.","circuit_breaker.py.","circuit-breaker/","24"),
      N("KP.rp","retry-policy/","pendiente",35,"retry backoff","MIX.","retry_policy.py.","retry-policy/","21")
    ]),
    N("KP.bus","internal-bus/","pendiente",40,"publish → subscribe runtime_bus","Bus interno.","runtime_bus.py MIX.","internal-bus/","10"),
    N("KP.em","execution-manifest/","rojo",10,"manifest run","ESQ.","PENDIENTE_CODE.","execution-manifest/","14"),
    N("KP.wf","workflow.py + runtime.py","naranja",35,"stages → kernel_hook","Entry kernel.","FACT: no es python -m agente.","kernel-principal/workflow.py","08")
  ]),
  N("IN","input-layer/","rojo",20,"usuario → input crudo → recepción → BLOCK","Cara del agente. Se queda en preguntas.","FACT: ~20%. cli-entry ESQ. No hay main.","input-layer/","02",[
    N("IN.cli","cli-entry/","rojo",5,"python -m agente","Puerta usuario.","FACT: PLACEHOLDER. Hueco del producto.","cli-entry/","01"),
    N("IN.rt","route-entry/","rojo",5,"route in","ESQ.","PENDIENTE_CODE.","route-entry/","01"),
    N("IN.xt","cross-tool-session-import/","rojo",5,"import sesión tool","ESQ §4.1.","PENDIENTE_CODE.","cross-tool-session-import/","02"),
    N("IN.rx","reception/","pendiente",45,"convert → enchufe_gate → INPUT_BLOCK","Reception REAL.","FACT: link a Wordflow reception. Cierra mal.","reception/convert.py","02")
  ]),
  N("DR","definition-registry/","pendiente",40,"id estable → ROOT_ID → FILE → TASK","Contratos y defs.","COPY_MANIFEST: organizar no inventar.","definition-registry/","11",[
    N("DR.wd","workflow-definition/","faltante",15,"yaml-dag → step-template","Defs workflow.","main_12.yaml existe; hojas ESQ.","workflow-definition/","12"),
    N("DR.ad","agent/task/tool/skill-definition/","rojo",8,"defs agente","ESQ.","PLACEHOLDER.","*-definition/","11"),
    N("DR.sc","schema-contracts/","pendiente",55,"schema JSON","REAL muchos schemas.","FACT: body presente.","schema-contracts/","04"),
    N("DR.dsc","domain-specific-contracts/","pendiente",40,"C_WF_INPUT/LOOP","REAL yaml.","C_WF_*.yaml.","domain-specific-contracts/","04"),
    N("DR.cat","declared-dependency-catalog/","pendiente",50,"component + connect catalog","REAL.","list_connections.py.","declared-dependency-catalog/","11"),
    N("DR.az","authorization-model/","rojo",5,"authz model","ESQ.","PENDIENTE_CODE.","authorization-model/","07")
  ]),
  N("CG","control-governance/","naranja",45,"veto → fail-closed → evidence → verdict","🔴 GOVERNANCE G1..G5. 0% LLM núcleo.","FACT: copias SHA vs import. Debe montar plugin, no duplicar.","control-governance/","05",[
    N("CG.cb","contracts-base + C00-C85/","faltante",15,"contratos C*","Hojas.","PLACEHOLDER.","contracts-*/","04"),
    N("CG.sh","sheriff-bridge + sheriff.py","pendiente",50,"checklist → sheriff","Enforcement.","FACT: copia Wordflow.","sheriff-bridge/","05"),
    N("CG.se","sentinel/","pendiente",45,"sentinel.yaml → veto","Sentinel.","Copia.","sentinel/","05"),
    N("CG.co","council/","pendiente",45,"roles → 12","Council.","Copia.","council/","05"),
    N("CG.fc","forensic-core/","pendiente",50,"CORE14 + FC → report","Forensic.","LLM nunca declara PASS.","forensic-core/","06"),
    N("CG.va","verdict-authority/","pendiente",40,"verdict determinista","Authority.","PASS solo Evidence+VerdictAuthority.","verdict-authority/","06"),
    N("CG.sy","symbol-index-wiring-graph/","pendiente",35,"symbol → wiring","Index.","symbol_index.py.","symbol-index-wiring-graph/","11"),
    N("CG.wv","workflow-validation/","pendiente",35,"preflight","Validación WF.","preflight.py.","workflow-validation/","12"),
    N("CG.pe","policy-engine/","pendiente",40,"policy eval","Policy.","policy_engine.py.","policy-engine/","05"),
    N("CG.gv","guardrails + structured-output/","faltante",15,"guard + SOV","Hojas.","PLACEHOLDER.","guardrails-validation/","24"),
    N("CG.llm","llm-control-deny/","pendiente",40,"fail_closed → whitelist","🔴 LLM control.","FACT: 90/10 no cableada como gate.","llm-control-deny/","07"),
    N("CG.pp","pre-post-gates/","pendiente",40,"pre → exec → post","Gates.","executor_gates.py.","pre-post-gates/","05"),
    N("CG.cl","closure-engine/","pendiente",30,"close run","Closure.","Thin.","closure-engine/","06"),
    N("CG.qd","quality-dag/","pendiente",35,"quality handlers","QDAG.","quality_dag.py.","quality-dag/","06"),
    N("CG.gap","gap_tasks + gap_registry/","pendiente",40,"gap → task","Gaps.","Registry existe.","gap_*/","06")
  ]),
  N("MWE","multi-workflow-engine/","pendiente",30,"DAG nodos → paralelo_max → join","Instancias aisladas.","FACT: workflow-2/3 forma vacía.","multi-workflow-engine/","13",[
    N("MWE.sh","shared-services/","pendiente",35,"registry → runner-host → budget","Servicios.","main_loop.py existe.","shared-services/","13"),
    N("MWE.w1","instances/workflow-1/","faltante",15,"bind def/state/queue/pool/prog","Bindings.","Casi PLACEHOLDER.","workflow-1/","13"),
    N("MWE.wn","workflow-2/3/N","rojo",0,"misma forma","No materializado.","Faltante.","instances/","13")
  ]),
  N("EO","execution-orchestration/","naranja",35,"nodo → idempotencia → ejecutar → tribunal","Orquestador fino. No chat→misión.","FACT: sin engines = VK-01 skeleton.","execution-orchestration/","14",[
    N("EO.sm","state-machine-executor/","rojo",8,"SM exec","ESQ.","PLACEHOLDER.","state-machine-executor/","14"),
    N("EO.dag","dag-executor/","pendiente",25,"dag.py","Thin.","851B.","dag-executor/","13"),
    N("EO.lp","sequential-parallel-loop-route/","rojo",8,"seq/par/loop","ESQ.","PLACEHOLDER.","sequential-parallel-loop-route/","13"),
    N("EO.iso","container-pod-isolation/","pendiente",30,"docker/ssh/sandbox","Aislamiento.","Body parcial.","container-pod-isolation/","21"),
    N("EO.tg","task-generation/","rojo",5,"gen tasks","ESQ.","PLACEHOLDER.","task-generation/","15"),
    N("EO.de","deterministic-execution/","rojo",8,"det exec","ESQ.","PLACEHOLDER.","deterministic-execution/","14"),
    N("EO.mp","mission-planning/","pendiente",45,"goals → lock → plan","Mission.","goals_extractor/compiler existen.","mission-planning/","03"),
    N("EO.gl","goal-lock/","pendiente",30,"GOAL_LOCK","REF única.","PLACEHOLDER+ref.","goal-lock/","03"),
    N("EO.tc","task-classifier-scheduler/","pendiente",40,"classify → schedule → queue","También raíz hermana.","task_classifier.py.","task-classifier-scheduler/","15"),
    N("EO.di","dependency-injection-context/","pendiente",35,"builder → context_pack","DI.","Body.","dependency-injection-context/","14"),
    N("EO.pp","programming-pipeline/","naranja",40,"REF → CPE","No duplicar motor.","SOURCE.md.","programming-pipeline/","19")
  ]),
  N("AF","agent-fleet-parallelism/","pendiente",30,"Chat A → N Chat B → integrate","Fleet.","spawn/handoff/supervisor body. Sin hilo dueño no prende.","agent-fleet-parallelism/","16"),
  N("EEP","execution-engine-pool/","naranja",30,"pool → adapter C1 → engine id → ABI","🔴 CODE ENGINE. OpenClaw CI verde.","FACT: FakeRepoTruth default. Adapters reales pendientes. Body OpenClaw/Hermes stub.","execution-engine-pool/","17",[
    N("EEP.ad","adapter-layer/","naranja",35,"ports memory/planning + http","Cables existen.","FACT: adapters reales hueco.","adapter-layer/","17"),
    N("EEP.cm","capability-matching/","pendiente",25,"kimi_policy","Match.","Thin.","capability-matching/","18"),
    N("EEP.pd","parallel-dispatch/","rojo",8,"dispatch","ESQ.","PLACEHOLDER.","parallel-dispatch/","17"),
    N("EEP.wt","worktree-isolation/","rojo",8,"worktree","ESQ.","PLACEHOLDER.","worktree-isolation/","17"),
    N("EEP.rn","result-normalization/","rojo",8,"normalize","ESQ.","PLACEHOLDER.","result-normalization/","17"),
    N("EEP.au","auxiliary-role-agents/","naranja",25,"openclaw/hermes stub","Stubs.","FACT: body incompleto. CI plugin verde.","auxiliary-role-agents/","18")
  ]),
  N("MESH","mesh-routing-collaboration/","rojo",5,"mesh route","Colab mesh.","PLACEHOLDER.","mesh-routing-collaboration/","16"),
  N("PRT","pipeline-runtime/","rojo",5,"runtime pipeline","ESQ.","PLACEHOLDER.","pipeline-runtime/","14"),
  N("CBI","codebase-intelligence/","pendiente",30,"repo_truth graph","Inteligencia repo.","FACT: FakeRepoTruth si no pasas repo.","codebase-intelligence/","11"),
  N("SR","session-resilience/","rojo",5,"resume session","ESQ.","PLACEHOLDER.","session-resilience/","21"),
  N("ID","identity-config/","rojo",5,"identity","ESQ.","PLACEHOLDER.","identity-config/","01"),
  N("HITL","human-in-the-loop/","rojo",8,"ask director","HITL §4.1.","PLACEHOLDER.","human-in-the-loop/","01"),
  N("COM","communication-notifications/","rojo",5,"notify","§4.1.","PLACEHOLDER.","communication-notifications/","01"),
  N("UI","control-plane-ui/","rojo",5,"UI control","§4.1.","PLACEHOLDER. No es el producto agente.","control-plane-ui/","01"),
  N("SED","state-events-durability/","pendiente",35,"checkpoint → resume RT-04","Durable.","blackboard/ledger/bitacora body. mission_id producto hueco.","state-events-durability/","21",[
    N("SED.dl","dead-letter-handling/","rojo",8,"DLQ","§4.1.","PLACEHOLDER.","dead-letter-handling/","21")
  ]),
  N("TMK","tools-models-memory-knowledge/","pendiente",25,"memory.lee → escribe claves","Memory/tools.","adapter memory body. RAG thin.","tools-models-memory-knowledge/","22",[
    N("TMK.mcp","mcp-transport/","rojo",8,"MCP","§4.1.","PLACEHOLDER.","mcp-transport/","23")
  ]),
  N("RE","research-evidence/","rojo",5,"research pack","ESQ.","PLACEHOLDER.","research-evidence/","06"),
  N("SEC","security-auth/","pendiente",25,"credential_store","Secrets.","credential_ref only.","security-auth/","24"),
  N("OBS","observability/","pendiente",35,"claim → tests → CI → evidence.json","Evidence packet = PASS. HTTP 200 ≠ PASS.","evidence_packet.py body. Witness post-push falta.","observability/","24",[
    N("OBS.tr","trace-history/","pendiente",25,"trace.py","Trace opcional.","G1_G3 verify md.","trace-history/","24")
  ]),
  N("MPO","multi-project-orchestration/","rojo",5,"multi project","ESQ.","PLACEHOLDER.","multi-project-orchestration/","16"),
  N("AOS","artifact-output-storage/","rojo",8,"store artifacts","§4.1.","PLACEHOLDER.","artifact-output-storage/","25"),
  N("DP","deploy-publish/","pendiente",35,"dry-run → OK Director → copiar → hash → evidence","Destino = ROOT MAP.","github_api/publisher body. No embeber path.","deploy-publish/","25",[
    N("DP.mar","multi-account-registry/","pendiente",30,"registry A/B","Cuentas.","credential_ref.","multi-account-registry/","25"),
    N("DP.push","push-injection/","pendiente",35,"github_external","Push.","external_accounts.yaml.","push-injection/","25"),
    N("DP.ps","publish-schema-layer/","rojo",8,"publish schema","ESQ.","PLACEHOLDER.","publish-schema-layer/","25"),
    N("DP.crud","remote-crud-ops/","rojo",8,"CRUD remote","NOT_CLAIMED.","PLACEHOLDER.","remote-crud-ops/","25"),
    N("DP.dts","deployment-target-selector/","rojo",10,"selector destino","§4.1.","PLACEHOLDER. Destino lo marca la raíz.","deployment-target-selector/","25")
  ]),
  N("EX","extensions/","naranja",30,"REF wordflow + kernel + evolution","REFs. No segunda copia.","FACT: debió importar, copió módulos.","extensions/","09",[
    N("EX.wem","wordflow-engine-module/","naranja",40,"REF → ../../extensions/wordflow","Puntero LEGACY.","SOURCE.md. No apagar hot path.","extensions/wordflow","20"),
    N("EX.wkm","wordflow-kernel-module/","naranja",30,"REF → ../../extensions/wordflow_kernel","Puntero kernel.","SOURCE.md.","extensions/wordflow_kernel","08"),
    N("EX.sev","source-evolution-module/","pendiente",30,"acquire→analyze→reuse 12","Evolución source.","Body 12.","source-evolution-module/","19")
  ]),
  N("PL","PIPELINE/ [REF]","pendiente",50,"REF → ../../PIPELINE","Docs plan.","No reescribir PLAN.","PIPELINE/","15"),
  N("AG","agents/ [REF]","pendiente",20,"REF → ../../agents","Agents root.","SOURCE.md.","agents/","16")
];
const WF=[
  N("WF","extensions/wordflow/","naranja",40,"reception → planner → engine → evidence","Motor vivo R6. LEGACY hasta cutover.","FACT: no reescribir. Importar, no copiar.","extensions/wordflow/","20",[
    N("WF.acc","accounts/","pendiente",30,"credential_ref","Cuentas.","No PAT en git.","accounts/","25"),
    N("WF.rx","reception/","pendiente",45,"convert / input_compiler / quality_bar","Entrada.","Cierra mal ~20%.","reception/","02"),
    N("WF.pl","planner/","pendiente",40,"goals_extractor → compiler → goal_lock","Plan.","audit_to_plan ≠ chat misión.","planner/","03"),
    N("WF.en","engine/","naranja",55,"programming_pipeline → code_path_runner","Hot path.","code_path_runner.py NO TOCAR.","engine/","20",[
      N("WF.runner","engine/code_path_runner.py","naranja",70,"misión code → runner → smoke → evidence","Archivo canónico hot path.","https://github.com/maxbry123-commits/agentes/blob/main/extensions/wordflow/engine/code_path_runner.py","engine/code_path_runner.py","20")
    ]),
    N("WF.st","standards/","pendiente",45,"sheriff forensic","Standards.","Copia destino Fables.","standards/","06"),
    N("WF.sch","schemas/","pendiente",40,"C-19 schemas","IO.","Gap C-19.","schemas/","04"),
    N("WF.mo","motors/ connectors/ state/ store/","pendiente",30,"motor → connector → state","Soporte.","Pool pensado.","motors/","18")
  ])
];
let STATE={v:2,mode:"file",ov:{},notes:{},extra:[],sel:"WF.runner"};
function toast(m){const t=document.getElementById("toast");t.textContent=m;t.style.display="block";setTimeout(()=>t.style.display="none",1600);}
function esc(s){return String(s||"").replace(/[&<>"]/g,c=>({"&":"&amp;","<":"&lt;",">":"&gt;","\"":"&quot;"}[c]));}
function ov(n){const o=STATE.ov[n.id]||{};return{
  st:o.st||n.st, col:o.col||CST[o.st||n.st]||n.st,
  pct:o.pct!=null?o.pct:(n.pct!=null?n.pct:PCT0[o.st||n.st]||0)
};}
function worst(nodes){
  const rank={rojo:0,naranja:1,amarillo:2,verde:3};
  let w="verde",i=9;
  (function walk(a){a.forEach(n=>{const c=ov(n).col;const r=rank[c];if(r<i){i=r;w=c;}if(n.kids)walk(n.kids);});})(nodes);
  return w;
}
function rowHTML(n,depth){
  const o=ov(n);
  const red=RED.has(n.seg)?"redband":"";
  return `<button class="row ${red}" data-id="${n.id}" onclick="tap('${n.id}')">
    <span class="dot ${o.col}"></span>
    <span class="nm">${"│ ".repeat(Math.max(0,depth-1))}${depth? "├─ ":""}<span class="path">${esc(n.name)}</span></span>
    <span class="meta">${o.pct}%</span>
  </button>`+(n.kids&&n.kids.length?`<div class="kids">${n.kids.map(k=>rowHTML(k,depth+1)).join("")}</div>`:"");
}
function find(id,arr){
  for(const n of arr){if(n.id===id)return n;const x=n.kids&&find(id,n.kids);if(x)return x;}
  return null;
}
function allTrees(){return SIX.concat(YAI,WF).concat(STATE.extra.map(e=>e.node));}
function findAny(id){return find(id,allTrees());}
function render(){
  document.getElementById("six").innerHTML=SIX.map(n=>rowHTML(n,0)).join("");
  document.getElementById("yaiwes").innerHTML=YAI.map(n=>rowHTML(n,0)).join("");
  document.getElementById("wf").innerHTML=WF.map(n=>rowHTML(n,0)).join("");
  document.getElementById("extra").innerHTML=STATE.extra.map(e=>rowHTML(e.node,0)).join("")||'<div class="k" style="color:var(--dim);padding:6px">ninguna</div>';
  document.getElementById("ver").textContent="v"+STATE.v;
  document.getElementById("mfile").className=STATE.mode==="file"?"on":"";
  document.getElementById("mblock").className=STATE.mode==="block"?"on":"";
}
function setMode(m){STATE.mode=m;render();}
function tap(id){
  const n=findAny(id);if(!n)return;
  STATE.sel=id;
  if(STATE.mode==="block" || (n.kids&&n.kids.length) && STATE.mode==="block"){
    openBlock(n);
  }else if(STATE.mode==="file"){
    openFile(n);
  }else{
    openBlock(n);
  }
}
function sheetBox(html){document.getElementById("sheetbox").innerHTML=html;document.getElementById("sheet").classList.add("on");}
function closeSheet(){document.getElementById("sheet").classList.remove("on");}
function pal(n){
  const o=ov(n);
  return `<div class="k" style="font-size:10px;color:var(--dim)">COLOR</div>
    <div class="sts">${COL.map(c=>`<button class="${o.col===c?"on":""}" onclick="setCol('${n.id}','${c}')">${c}</button>`).join("")}</div>
    <div class="k" style="font-size:10px;color:var(--dim)">STATUS</div>
    <div class="sts">${ST.map(s=>`<button class="${o.st===s?"on":""}" onclick="setSt('${n.id}','${s}')">${SL[s]}</button>`).join("")}</div>
    <div class="k" style="font-size:10px;color:var(--dim)">% CODE</div>
    <div class="sts">${[0,10,25,40,55,70,85,100].map(p=>`<button class="${o.pct===p?"on":""}" onclick="setPct('${n.id}',${p})">${p}%</button>`).join("")}</div>`;
}
function openFile(n){
  const o=ov(n);
  sheetBox(`
    <div class="k" style="font-size:10px;color:var(--blue)">ARCHIVO · ${esc(n.seg||"—")}</div>
    <h3>${esc(n.name)}</h3>
    <div class="micro">${esc(n.flow||"—")}</div>
    <div class="xray"><b>Qué hace.</b> ${esc(n.desc)}</div>
    <div class="xray"><b>X-ray.</b> ${esc(n.xray)}</div>
    <div class="xray"><b>Destino ROOT MAP.</b> ${esc(n.dest)}</div>
    <div class="xray"><b>Ahora.</b> ${SL[o.st]} · ${o.col} · ${o.pct}%</div>
    ${pal(n)}
    <textarea class="note" rows="4" placeholder="nota de este archivo" oninput="STATE.notes['${n.id}']=this.value">${esc(STATE.notes[n.id]||"")}</textarea>
    <button class="p" onclick="shareNode('${n.id}')">Compartir archivo</button>
    <button class="p" style="background:var(--card);color:var(--fg);border:1px solid var(--bd)" onclick="closeSheet()">Cerrar</button>`);
}
function openBlock(n){
  const o=ov(n);
  const files=(n.kids||[]).map(k=>{const x=ov(k);return `├─ [${x.col} ${x.pct}%] ${k.name}`;}).join("\n")||"(hoja)";
  sheetBox(`
    <div class="k" style="font-size:10px;color:${RED.has(n.seg)?"var(--rojo)":"var(--blue)"}">BLOQUE · seg ${esc(n.seg||"—")}${RED.has(n.seg)?" · ROJO":""}</div>
    <h3>${esc(n.name)}</h3>
    <div class="micro">${esc(n.flow||"—")}</div>
    <div class="xray"><b>Qué hace el bloque.</b> ${esc(n.desc)}</div>
    <div class="xray"><b>Problema X-ray.</b> ${esc(n.xray)}</div>
    <div class="xray"><b>Destino.</b> ${esc(n.dest)}</div>
    <div class="micro" style="white-space:pre">${esc(files)}</div>
    <div class="xray"><b>Rollup.</b> ${SL[o.st]} · ${o.col} · ${o.pct}%</div>
    ${pal(n)}
    <textarea class="note" rows="4" placeholder="nota del bloque" oninput="STATE.notes['${n.id}']=this.value">${esc(STATE.notes[n.id]||"")}</textarea>
    <button class="p" onclick="shareNode('${n.id}')">Compartir bloque</button>
    <button class="p" style="background:var(--card);color:var(--fg);border:1px solid var(--bd)" onclick="closeSheet()">Cerrar</button>`);
}
function setSt(id,s){
  STATE.ov[id]=Object.assign({},STATE.ov[id],{st:s,col:CST[s],pct:STATE.ov[id]&&STATE.ov[id].pct!=null?STATE.ov[id].pct:PCT0[s]});
  persist();render();const n=findAny(id);if(n) (STATE.mode==="file"&&!(n.kids&&n.kids.length)?openFile:openBlock)(n);
}
function setCol(id,c){STATE.ov[id]=Object.assign({},STATE.ov[id],{col:c});persist();render();const n=findAny(id);if(n)(STATE.mode==="file"&&!(n.kids&&n.kids.length)?openFile:openBlock)(n);}
function setPct(id,p){STATE.ov[id]=Object.assign({},STATE.ov[id],{pct:p});persist();render();const n=findAny(id);if(n)(STATE.mode==="file"&&!(n.kids&&n.kids.length)?openFile:openBlock)(n);}
function addRoot(){
  const title=document.getElementById("ntitle").value||document.getElementById("clone").selectedOptions[0].text;
  const md=document.getElementById("nmd").value||"";
  const id="XR"+Date.now();
  const node=N(id,title,"pendiente",0,"nueva raíz → bloque único → compartir",md||"Raíz añadida. Solo bloque, no árbol de archivos.","Usuario pegó markdown. Sin hojas de archivo.","extra/"+title,"00");
  STATE.extra.push({node,md});
  document.getElementById("ntitle").value="";document.getElementById("nmd").value="";
  persist();render();toast("raíz-bloque añadida");
}
function blockText(n){
  const o=ov(n);
  const six=SIX.map(r=>{const x=ov(r);return `  ${r.name} [${x.col} ${x.pct}%]`;}).join("\n");
  return `# YAIWES ${n.id}\n## RAÍZ\n\`\`\`\nagentes/\n${six}\n\`\`\`\n## NODO\n${n.name}\nFlujo: ${n.flow}\nDestino: ${n.dest}\nEstado: ${SL[o.st]} · ${o.col} · ${o.pct}%\n## DESC\n${n.desc}\n## XRAY\n${n.xray}\n## NOTA\n${STATE.notes[n.id]||""}\n## LEY\nEnchufe IN+OUT cada file nuevo. Destino=ROOT MAP. Formato A22. No from-scratch.`;
}
async function shareNode(id){
  const n=findAny(id);if(!n)return;
  const text=blockText(n);
  try{
    if(navigator.share) await navigator.share({title:"YAIWES "+n.name,text});
    else await navigator.clipboard.writeText(text);
    toast("share/copiado");
  }catch(e){try{await navigator.clipboard.writeText(text);toast("copiado");}catch(e2){toast("cancel");}}
}
function shareSel(){shareNode(STATE.sel||"WF.runner");}
function persist(){try{localStorage.setItem("yaiwes-wall",JSON.stringify(STATE));}catch(e){}}
function saveVersion(){
  STATE.v=(STATE.v||2)+1;persist();
  const tag=document.getElementById("state");
  if(tag) tag.textContent=JSON.stringify(STATE);
  const html="<!DOCTYPE html>\n"+document.documentElement.outerHTML;
  const a=document.createElement("a");
  a.href=URL.createObjectURL(new Blob([html],{type:"text/html"}));
  a.download="YAIWES-CRAZY-WALL-v"+STATE.v+".html";a.click();
  document.getElementById("ver").textContent="v"+STATE.v;
  toast("v"+STATE.v+" → Descargas");
}
(function(){
  const el=document.getElementById("state");
  try{if(el) Object.assign(STATE,JSON.parse(el.textContent));}catch(e){}
  try{const ls=localStorage.getItem("yaiwes-wall");if(ls){const p=JSON.parse(ls);if((p.v||0)>=(STATE.v||0)) Object.assign(STATE,p);}}catch(e){}
  render();
})();
</script>
<script type="application/json" id="state">{"v":2,"mode":"file","ov":{},"notes":{},"extra":[],"sel":"WF.runner"}
(function lockWall(){
  var L=window.FROMTED_LOCK||{};
  var s=L.view||'arbol';
  function hide(sel, on){ document.querySelectorAll(sel).forEach(function(n){ n.style.display=on?'':'none'; }); }
  function apply(){
    var map={
      'bloques': {show:'.plane,#yaiwes', hide:'.add,.bar,#six,#wf,#extra,.modes,.hilo'},
      'arbol': {show:'.plane,#yaiwes,#wf,#six', hide:'.add'},
      'archivos': {show:'.plane,#wf', hide:'#six,#yaiwes,#extra,.add'},
      'preguntar': {show:'.hdr', hide:'.plane,.add,.bar'},
      'tap-archivo': {show:'.plane,.modes', hide:'.add'},
      'tap-bloque': {show:'.plane,.modes', hide:'.add'},
      'raices': {show:'#six,.plane', hide:'#yaiwes,#wf,#extra,.add,.bar'},
      'grid': {show:'.plane', hide:'.add,.bar'},
      'lista': {show:'#wf,.plane', hide:'#six,#yaiwes,.add'},
      'sheet-bloque': {show:'#sheet', hide:'.add'},
      'sheet-archivo': {show:'#sheet', hide:'.add'},
      'sheet-raiz': {show:'#sheet', hide:'.add'},
      'sheet-extra': {show:'#sheet,#extra', hide:'.add'},
      'add-raiz': {show:'.add', hide:'.bar'},
      'barra': {show:'.bar', hide:'.add'},
      'state': {show:'.plane', hide:'.add,.bar,.modes'}
    };
    var m=map[s]||map.arbol;
    if(typeof setMode==='function'){
      if(s==='tap-archivo') setMode('file');
      if(s==='tap-bloque') setMode('block');
    }
    if(s.indexOf('sheet')===0 && typeof sheetBox==='function'){
      sheetBox('<h3>'+s+'</h3><p class="xray">Sheet extraído. Cierra con tap fuera.</p><button class="p" onclick="closeSheet()">Cerrar</button>');
    }
    if(s==='preguntar'){
      var plane=document.querySelector('.plane');
      if(plane){ plane.style.display='block'; plane.innerHTML='<div class="card"><label>Preguntar al plano</label><textarea id="q" rows="4" placeholder="Escribe la pregunta"></textarea><button class="little" id="ask">Preguntar</button><pre class="log" id="qout"></pre></div>';
        document.getElementById('ask').onclick=function(){ var q=document.getElementById('q').value; ABS.dispatch('wall.preguntar',{q:q}); document.getElementById('qout').textContent=q?('ABS wall.preguntar · '+q):'SIN_INPUT'; }; }
    }
    if(s==='state'){
      var plane=document.querySelector('.plane');
      var st='{}';
      try{ st=localStorage.getItem('yaiwes-crazy-wall-v4')||localStorage.getItem('yaiwes-crazy-wall')||'{}'; }catch(e){}
      if(plane) plane.innerHTML='<h2>state.json</h2><textarea id="st" rows="16" style="width:100%">'+st.replace(/</g,'<')+'</textarea><button class="cargar" id="ld">Cargar</button> <button class="descargar" id="sv">Descargar</button>';
    }
    if(s==='grid'){
      var plane=document.querySelector('.plane');
      if(plane){ var h='<h2>Grid 00–25</h2><div class="docs" style="display:grid;grid-template-columns:repeat(4,1fr);gap:6px">';
        for(var i=0;i<26;i++){ var k=('0'+i).slice(-2); h+='<button class="card" data-k="'+k+'">'+k+'</button>'; }
        h+='</div>'; plane.innerHTML=h;
        plane.onclick=function(e){ var b=e.target.closest('[data-k]'); if(!b)return; ABS.dispatch('wall.grid',{k:b.getAttribute('data-k')}); b.classList.toggle('on'); };
      }
    }
  }
  var n=0, t=setInterval(function(){ apply(); if(++n>8) clearInterval(t); }, 80);
})();
