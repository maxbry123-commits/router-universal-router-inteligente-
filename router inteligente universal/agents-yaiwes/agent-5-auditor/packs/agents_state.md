## agent-1-chat-hf: estado=CLOSED marco=pocketflow pasos_cerrados=['vault_panel', 'router_panel', 'wire_panels']
- paso router_panel: CLOSED modelo=nvidia/nemotron-3-super-120b-a12b entregables=['router inteligente universal/agents-yaiwes/agent-1-chat-hf/steps/router_panel/results/router_panel.js'] gaps=-
- paso vault_panel: CLOSED modelo=nvidia/nemotron-3-super-120b-a12b entregables=['router inteligente universal/agents-yaiwes/agent-1-chat-hf/steps/vault_panel/results/vault_panel.js'] gaps=-
- paso wire_panels: CLOSED modelo=nvidia/nemotron-3-super-120b-a12b entregables=['router inteligente universal/agents-yaiwes/agent-1-chat-hf/steps/wire_panels/results/wire_panels.js'] gaps=-
## agent-2-chat-hf-smol: estado=CLOSED marco=smolagents pasos_cerrados=['jobs_panel', 'fixed_template', 'crazy_wall_chain']
- paso crazy_wall_chain: CLOSED modelo=hf/deepseek-ai/DeepSeek-V4-Flash entregables=['router inteligente universal/agents-yaiwes/agent-2-chat-hf-smol/steps/crazy_wall_chain/results/crazy_wall_chain.py'] gaps=-
- paso fixed_template: CLOSED modelo=hf/deepseek-ai/DeepSeek-V4-Flash entregables=['router inteligente universal/agents-yaiwes/agent-2-chat-hf-smol/steps/fixed_template/results/fixed_template.py'] gaps=-
- paso jobs_panel: CLOSED modelo=hf/deepseek-ai/DeepSeek-V4-Flash entregables=['router inteligente universal/agents-yaiwes/agent-2-chat-hf-smol/steps/jobs_panel/results/jobs_panel.js'] gaps=-
## agent-3-router: estado=CLOSED marco=pocketflow pasos_cerrados=['space_readme', 'space_index', 'deploy_script']
- paso deploy_script: CLOSED modelo=nvidia/nemotron-3-super-120b-a12b entregables=['router inteligente universal/agents-yaiwes/agent-3-router/steps/deploy_script/results/deploy_static_space.py'] gaps=-
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