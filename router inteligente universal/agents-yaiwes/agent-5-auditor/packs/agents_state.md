## agent-1-chat-hf: estado=CLOSED marco=pocketflow pasos_cerrados=['vault_panel', 'router_panel', 'wire_panels']
- paso router_panel: CLOSED modelo=nvidia/nemotron-3-super-120b-a12b entregables=['router inteligente universal/agents-yaiwes/agent-1-chat-hf/steps/router_panel/results/router_panel.js'] gaps=-
- paso vault_panel: CLOSED modelo=nvidia/nemotron-3-super-120b-a12b entregables=['router inteligente universal/agents-yaiwes/agent-1-chat-hf/steps/vault_panel/results/vault_panel.js'] gaps=-
- paso wire_panels: CLOSED modelo=nvidia/nemotron-3-super-120b-a12b entregables=['router inteligente universal/agents-yaiwes/agent-1-chat-hf/steps/wire_panels/results/wire_panels.js'] gaps=-
## agent-10-model-install: estado=CLOSED marco=pocketflow pasos_cerrados=['install_launch_test']
- paso install_launch_test: CLOSED modelo=verbatim entregables=['router inteligente universal/agents-yaiwes/agent-10-model-install/steps/install_launch_test/results/install_launch_test.py'] gaps=-
- paso install_orders: CLOSED modelo=nvidia/nemotron-3-super-120b-a12b entregables=['router inteligente universal/agents-yaiwes/agent-10-model-install/steps/install_orders/results/orders.json'] gaps=-
- paso install_report: CLOSED modelo=nvidia/nemotron-3-super-120b-a12b entregables=['router inteligente universal/agents-yaiwes/agent-10-model-install/steps/install_report/results/install_report.py'] gaps=-
## agent-11-download-extraction: estado=CLOSED marco=smolagents pasos_cerrados=['jev_components_list', 'ms_agent_framework_donor']
- paso extend_download_list: BLOCKED modelo=- entregables=['router inteligente universal/agents-yaiwes/agent-11-download-extraction/steps/extend_download_list/results/extra_donors.py'] gaps=cerebras/gpt-oss-120b:AgentGenerationError:Error while generating output:
Error code: 402 - {'message': 'Payment require
- paso jev_components_list: CLOSED modelo=groq/openai/gpt-oss-120b entregables=['router inteligente universal/agents-yaiwes/agent-11-download-extraction/steps/jev_components_list/results/jev_components.py'] gaps=-
- paso ms_agent_framework_donor: CLOSED modelo=groq/openai/gpt-oss-120b entregables=['router inteligente universal/agents-yaiwes/agent-11-download-extraction/steps/ms_agent_framework_donor/results/ms_agent_framework_donor.py'] gaps=-
## agent-12-yaiwes-router: estado=CLOSED marco=smolagents pasos_cerrados=['yaiwes_donor_list']
- paso yaiwes_donor_list: CLOSED modelo=groq/openai/gpt-oss-120b entregables=['router inteligente universal/agents-yaiwes/agent-12-yaiwes-router/steps/yaiwes_donor_list/results/yaiwes_donors.py'] gaps=-
## agent-13-repo-inventory: estado=BLOCKED marco=pocketflow pasos_cerrados=[]
- paso inventory_module: BLOCKED modelo=nvidia/nemotron-3-super-120b-a12b entregables=['router inteligente universal/agents-yaiwes/agent-13-repo-inventory/steps/inventory_module/results/repo_inventory.py'] gaps=la prueba falló (exit=1): AssertionError
## agent-14-orchestrator-msaf: estado=CLOSED marco=pocketflow pasos_cerrados=['install_and_connect']
- paso install_and_connect: CLOSED modelo=nvidia/nemotron-3-super-120b-a12b entregables=['router inteligente universal/agents-yaiwes/agent-14-orchestrator-msaf/steps/install_and_connect/results/msaf_connect.py'] gaps=-
## agent-15-orchestrator-grok: estado=BLOCKED marco=smolagents pasos_cerrados=[]
- paso verify_and_connect: RUNNING modelo=- entregables=['router inteligente universal/agents-yaiwes/agent-15-orchestrator-grok/steps/verify_and_connect/results/grok_connect.py'] gaps=-
## agent-15-orchestrator-grokbuild: estado=BLOCKED marco=pocketflow pasos_cerrados=[]
- paso fetch_and_connect: BLOCKED modelo=nvidia/nemotron-3-super-120b-a12b entregables=['router inteligente universal/agents-yaiwes/agent-15-orchestrator-grokbuild/steps/fetch_and_connect/results/grokbuild_connect.py'] gaps=la prueba falló (exit=1): requests.exceptions.HTTPError: 404 Client Error: Not Found for url: https://api.github.com/rep
## agent-16-chat-space-oauth: estado=BLOCKED marco=pocketflow pasos_cerrados=[]
- paso publish_static_live: BLOCKED modelo=deepseek-ai/DeepSeek-V4-Flash entregables=['router inteligente universal/agents-yaiwes/agent-16-chat-space-oauth/steps/publish_static_live/results/publish_static_live.py'] gaps=Python inválido: unexpected character after line continuation character (línea 17); falta 'private=False'; la prueba fal
## agent-17-chat-backend-32gb: estado=BLOCKED marco=pocketflow pasos_cerrados=[]
- paso backend_live: BLOCKED modelo=deepseek-ai/DeepSeek-V4-Flash entregables=['router inteligente universal/agents-yaiwes/agent-17-chat-backend-32gb/steps/backend_live/results/chat_backend_32gb.py'] gaps=falta 'Volume'; la prueba falló (exit=1): ImportError: cannot import name 'run' from 'chat_backend_32gb' (/home/runner/w
## agent-18-chat-final-auditor: estado=BLOCKED marco=pocketflow pasos_cerrados=[]
- paso wait_live: BLOCKED modelo=nvidia/nemotron-3-super-120b-a12b entregables=['router inteligente universal/agents-yaiwes/agent-18-chat-final-auditor/steps/wait_live/results/gate_live.py'] gaps=Python inválido: invalid syntax (línea 1); la prueba falló (exit=1): SyntaxError: invalid syntax
## agent-19-chat-components-motors: estado=? marco=? pasos_cerrados=[]
## agent-2-chat-hf-smol: estado=CLOSED marco=smolagents pasos_cerrados=['jobs_panel', 'fixed_template', 'crazy_wall_chain']
- paso crazy_wall_chain: CLOSED modelo=hf/deepseek-ai/DeepSeek-V4-Flash entregables=['router inteligente universal/agents-yaiwes/agent-2-chat-hf-smol/steps/crazy_wall_chain/results/crazy_wall_chain.py'] gaps=-
- paso fixed_template: CLOSED modelo=hf/deepseek-ai/DeepSeek-V4-Flash entregables=['router inteligente universal/agents-yaiwes/agent-2-chat-hf-smol/steps/fixed_template/results/fixed_template.py'] gaps=-
- paso jobs_panel: CLOSED modelo=hf/deepseek-ai/DeepSeek-V4-Flash entregables=['router inteligente universal/agents-yaiwes/agent-2-chat-hf-smol/steps/jobs_panel/results/jobs_panel.js'] gaps=-
## agent-3-router: estado=CLOSED marco=pocketflow pasos_cerrados=['space_readme', 'space_index', 'deploy_script', 'publish_live']
- paso deploy_script: CLOSED modelo=nvidia/nemotron-3-super-120b-a12b entregables=['router inteligente universal/agents-yaiwes/agent-3-router/steps/deploy_script/results/deploy_static_space.py'] gaps=-
- paso publish_live: CLOSED modelo=nvidia/nemotron-3-super-120b-a12b entregables=['router inteligente universal/agents-yaiwes/agent-3-router/steps/publish_live/results/HANDOFF.md', 'router inteligente universal/agents-yaiwes/agent-3-router/steps/publish_live/results/PUBLISH_LIVE_REJECTED.md', 'router inteligente universal/agents-yaiwes/agent-3-router/steps/publish_live/results/publish_live.py'] gaps=-
- paso space_index: CLOSED modelo=nvidia/nemotron-3-super-120b-a12b entregables=[] gaps=-
- paso space_readme: CLOSED modelo=nvidia/nemotron-3-super-120b-a12b entregables=[] gaps=-
## agent-4-router-smol: estado=CLOSED marco=smolagents pasos_cerrados=['models_registry', 'job_spec', 'node_monitor']
- paso job_spec: CLOSED modelo=hf/deepseek-ai/DeepSeek-V4-Flash entregables=['router inteligente universal/agents-yaiwes/agent-4-router-smol/steps/job_spec/results/job_spec.py'] gaps=-
- paso models_registry: CLOSED modelo=hf/deepseek-ai/DeepSeek-V4-Flash entregables=['router inteligente universal/agents-yaiwes/agent-4-router-smol/steps/models_registry/results/hf_models_registry.py'] gaps=-
- paso node_monitor: CLOSED modelo=hf/deepseek-ai/DeepSeek-V4-Flash entregables=['router inteligente universal/agents-yaiwes/agent-4-router-smol/steps/node_monitor/results/node_monitor.py'] gaps=-
## agent-6-hf-nodes: estado=CLOSED marco=pocketflow pasos_cerrados=['ram_plan', 'node_hop']
- paso node_hop: CLOSED modelo=deepseek-ai/DeepSeek-V4-Flash entregables=['router inteligente universal/agents-yaiwes/agent-6-hf-nodes/steps/node_hop/results/hf_hop.py'] gaps=-
- paso ram_plan: CLOSED modelo=deepseek-ai/DeepSeek-V4-Flash entregables=['router inteligente universal/agents-yaiwes/agent-6-hf-nodes/steps/ram_plan/results/hf_nodes.py'] gaps=-
## agent-7-llama-hf: estado=CLOSED marco=smolagents pasos_cerrados=['llama_cmd', 'hf_job', 'bench_report', 'serve_health']
- paso bench_report: CLOSED modelo=hf/MiniMaxAI/MiniMax-M3 entregables=['router inteligente universal/agents-yaiwes/agent-7-llama-hf/steps/bench_report/results/bench_report.py'] gaps=-
- paso hf_job: CLOSED modelo=hf/deepseek-ai/DeepSeek-V4-Flash entregables=['router inteligente universal/agents-yaiwes/agent-7-llama-hf/steps/hf_job/results/hf_job.py'] gaps=-
- paso llama_cmd: CLOSED modelo=hf/deepseek-ai/DeepSeek-V4-Flash entregables=['router inteligente universal/agents-yaiwes/agent-7-llama-hf/steps/llama_cmd/results/llama_cmd.py'] gaps=-
- paso serve_health: CLOSED modelo=verbatim entregables=['router inteligente universal/agents-yaiwes/agent-7-llama-hf/steps/serve_health/results/serve_health.py'] gaps=-
## agent-8-router-local: estado=CLOSED marco=pocketflow pasos_cerrados=['local_pool', 'mirror_route']
- paso local_pool: CLOSED modelo=deepseek-ai/DeepSeek