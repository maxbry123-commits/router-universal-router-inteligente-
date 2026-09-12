# Subscription authorization repair — 2026-09-12

Target: two ChatGPT/Codex subscription accounts and one Claude Code subscription; Hugging Face secret storage; later use by GitHub agents.

## Completed and verified
- Added scripts/persist_codex_auth_hf.py in 4d809732b73190b93a1cebbf07b48dbd773e2773.
- Updated Codex account 1 workflow in bdcc2ed1d768fc8b21b3e48d5dc2f7aaff87b962.
- Updated Codex account 2 workflow in d778eb6526d1dd73cf3fd5cf55021b1163f98664.
- Read both workflows back from main and compared exact contents: PASS.
- Local checks: valid subscription JSON accepted; API-key mode, empty object, missing tokens and mixed API-key credentials rejected; missing HF configuration returns exit 2 before login. These checks do not establish remote login or inference success.
- Codex jobs now run manually, avoid duplicate same-account logins, check HF destination accessibility before login, and send complete auth JSON through HfApi.add_space_secret. No credentials in artifacts or Git.

## Required configuration
- Actions secret: RIU_HF_TOKEN or HF_TOKEN or HUGGINGFACE_TOKEN, authorized to write Secrets on the intended Space.
- Actions variable: HF_SPACE_ID, exact existing owner/Space ID. No destination guessed.
- Stored keys: CODEX_AUTH_JSON_ACCOUNT_1 and CODEX_AUTH_JSON_ACCOUNT_2.
- Preflight checks accessibility, not write permission. Actual save must succeed before claiming persistence.

## Unresolved
1. Current connected HF OAuth identity is COMAND-CENTER-1; scopes jobs/openid/profile/read-mcp/read-repos, without repository-write permission. No writable HF runtime is exposed in this session.
2. Space COMAND-CENTER-1/yaiwes-ui-factory from the handoff returns not found or authentication required. The Space search tool also failed. Destination remains unverified.
3. Claude run 34671762824, job 103496582130, exited 124 waiting at Paste code here. Existing Actions workflow has no input channel to return the browser code; unchanged pending an authenticated interactive runtime. Raw setup-token output must not be published, because successful output contains the credential.
4. Human account consent has not been completed here for any account.
5. No actual HF secret write or agent inference test completed here.
6. Space Secrets are write-only through the Hub API and are injected into the Space runtime. GitHub agents cannot download them from the Secrets API. They need an authenticated agent endpoint running inside that Space, or a separately authorized secret distribution mechanism. Neither is verified.
7. Codex refreshes credentials during use; the consuming runtime must persist the updated auth JSON. This setup only performs initial storage.

## Sources
- https://learn.chatgpt.com/docs/auth
- https://code.claude.com/docs/en/authentication
- https://huggingface.co/docs/huggingface_hub/main/package_reference/hf_api#huggingface_hub.HfApi.add_space_secret
- https://github.com/anthropics/claude-code/issues/42965

Overall status: PARTIALLY_REPAIRED / NOT_AUTHENTICATED / NOT_E2E_VERIFIED.
