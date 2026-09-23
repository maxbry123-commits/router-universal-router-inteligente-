## agent-1-chat-hf: estado=CLOSED marco=pocketflow pasos_cerrados=['vault_panel', 'router_panel', 'wire_panels']
- paso router_panel: CLOSED modelo=nvidia/nemotron-3-super-120b-a12b entregables=['router inteligente universal/agents-yaiwes/agent-1-chat-hf/steps/router_panel/results/router_panel.js'] gaps=-
- paso vault_panel: CLOSED modelo=nvidia/nemotron-3-super-120b-a12b entregables=['router inteligente universal/agents-yaiwes/agent-1-chat-hf/steps/vault_panel/results/vault_panel.js'] gaps=-
- paso wire_panels: CLOSED modelo=nvidia/nemotron-3-super-120b-a12b entregables=['router inteligente universal/agents-yaiwes/agent-1-chat-hf/steps/wire_panels/results/wire_panels.js'] gaps=-
## agent-10-model-install: estado=BLOCKED marco=pocketflow pasos_cerrados=[]
- paso install_launch_test: BLOCKED modelo=nvidia/nemotron-3-super-120b-a12b entregables=['router inteligente universal/agents-yaiwes/agent-10-model-install/steps/install_launch_test/results/install_launch_test.py'] gaps=la prueba falló (exit=1): AttributeError: 'JobInfo' object has no attribute 'refresh'
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
## agent-14-orchestrator-msaf: estado=? marco=? pasos_cerrados=[]
## agent-15-orchestrator-grok: estado=? marco=? pasos_cerrados=[]
## agent-15-orchestrator-grokbuild: estado=? marco=? pasos_cerrados=[]
## agent-2-chat-hf-smol: estado=CLOSED marco=smolagents pasos_cerrados=['jobs_panel', 'fixed_template', 'crazy_wall_chain']
- paso crazy_wall_chain: CLOSED modelo=hf/deepseek-ai/DeepSeek-V4-Flash entregables=['router inteligente universal/agents-yaiwes/agent-2-chat-hf-smol/steps/crazy_wall_chain/results/crazy_wall_chain.py'] gaps=-
- paso fixed_template: CLOSED modelo=hf/deepseek-ai/DeepSeek-V4-Flash entregables=['router inteligente universal/agents-yaiwes/agent-2-chat-hf-smol/steps/fixed_template/results/fixed_template.py'] gaps=-
- paso jobs_panel: CLOSED modelo=hf/deepseek-ai/DeepSeek-V4-Flash entregables=['router inteligente universal/agents-yaiwes/agent-2-chat-hf-smol/steps/jobs_panel/results/jobs_panel.js'] gaps=-
## agent-3-router: estado=BLOCKED marco=pocketflow pasos_cerrados=['space_readme', 'space_index', 'deploy_script']
- paso deploy_script: CLOSED modelo=nvidia/nemotron-3-super-120b-a12b entregables=['router inteligente universal/agents-yaiwes/agent-3-router/steps/deploy_script/results/deploy_static_space.py'] gaps=-
- paso publish_live: BLOCKED modelo=nvidia/nemotron-3-super-120b-a12b entregables=['router inteligente universal/agents-yaiwes/agent-3-router/steps/publish_live/results/HANDOFF.md', 'router inteligente universal/agents-yaiwes/agent-3-router/steps/publish_live/results/PUBLISH_LIVE_REJECTED.md', 'router inteligente universal/agents-yaiwes/agent-3-router/steps/publish_live/results/publish_live.py'] gaps=Python inválido: unterminated string literal (detected at line 5) (línea 5); la prueba falló (exit=1): SyntaxError: unte
- paso space_index: CLOSED modelo=nvidia/nemotron-3-super-120b-a12b entregables=[] gaps=-
- paso space_readme: CLOSED modelo=nvidia/nemotron-3-super-120b-a12b entregables=[] gaps=-
## agent-4-router-smol: estado=CLOSED marco=smolagents pasos_cerrados=['models_registry', 'job_spec', 'node_monitor']
- paso job_spec: CLOSED modelo=hf/deepseek-ai/DeepSeek-V4-Flash entregables=['router inteligente universal/agents-yaiwes/agent-4-router-smol/steps/job_spec/results/job_spec.py'] gaps=-
- paso models_registry: CLOSED modelo=hf/deepseek-ai/DeepSeek-V4-Flash entregables=['router inteligente universal/agents-yaiwes/agent-4-router-smol/steps/models_registry/results/hf_models_registry.py'] gaps=-
- paso node_monitor: CLOSED modelo=hf/deepseek-ai/DeepSeek-V4-Flash entregables=['router inteligente universal/agents-yaiwes/agent-4-router-smol/steps/node_monitor/results/node_monitor.py'] gaps=-
## agent-6-hf-nodes: estado=CLOSED marco=pocketflow pasos_cerrados=['ram_plan', 'node_hop']
- paso node_hop: CLOSED modelo=deepseek-ai/DeepSeek-V4-Flash entregables=['router inteligente universal/agents-yaiwes/agent-6-hf-nodes/steps/node_hop/results/hf_hop.py'] gaps=-
- paso ram_plan: CLOSED modelo=deepseek-ai/DeepSeek-V4-Flash entregables=['router inteligente universal/agents-yaiwes/agent-6-hf-nodes/steps/ram_plan/results/hf_nodes.py'] gaps=-
## agent-7-llama-hf: estado=CLOSED marco=smolagents pasos_cerrados=['llama_cmd', 'hf_job', 'bench_report']
- paso bench_report: CLOSED modelo=hf/MiniMaxAI/MiniMax-M3 entregables=['router inteligente universal/agents-yaiwes/agent-7-llama-hf/steps/bench_report/results/bench_report.py'] gaps=-
- paso hf_job: CLOSED modelo=hf/deepseek-ai/DeepSeek-V4-Flash entregables=['router inteligente universal/agents-yaiwes/agent-7-llama-hf/steps/hf_job/results/hf_job.py'] gaps=-
- paso llama_cmd: CLOSED modelo=hf/deepseek-ai/DeepSeek-V4-Flash entregables=['router inteligente universal/agents-yaiwes/agent-7-llama-hf/steps/llama_cmd/results/llama_cmd.py'] gaps=-
## agent-8-router-local: estado=CLOSED marco=pocketflow pasos_cerrados=['local_pool', 'mirror_route']
- paso local_pool: CLOSED modelo=deepseek-ai/DeepSeek-V4-Flash entregables=['router inteligente universal/agents-yaiwes/agent-8-router-local/steps/local_pool/results/local_pool.py'] gaps=-
- paso mirror_route: CLOSED modelo=deepseek-ai/DeepSeek-V4-Flash entregables=['router inteligente universal/agents-yaiwes/agent-8-router-local/steps/mirror_route/results/mirror_route.py'] gaps=-
## agent-9-models-catalog: estado=CLOSED marco=smolagents pasos_cerrados=['models_catalog', 'install_plan']
- paso install_plan: CLOSED modelo=hf/deepseek-ai/DeepSeek-V4-Flash entregables=['router inteligente universal/agents-yaiwes/agent-9-models-catalog/steps/install_plan/results/install_plan.py'] gaps=-
- paso models_catalog: CLOSED modelo=hf/deepseek-ai/DeepSeek-V4-Flash entregables=['router inteligente universal/agents-yaiwes/agent-9-models-catalog/steps/models_catalog/results/models_catalog.py'] gaps=-