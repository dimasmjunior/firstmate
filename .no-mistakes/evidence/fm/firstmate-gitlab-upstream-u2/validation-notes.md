# GitLab validation

Real product checks used GitLab CE 19.4.1 in a rootless Podman container with graph storage and runtime storage inside the validation worktree, exposed only at 127.0.0.1:18080, and the installed glab 1.114.0. A disposable root account token was created inside that container. No operator credentials or shared GitLab projects were used. Firstmate ran with a marked disposable lab home. Cleanup used real Treehouse and an isolated tmux socket.

The CLI transcripts demonstrate host detection and explicit binding, generated GitLab worker instructions, local-only and asynchronous-argument refusal, draft registration and independent merge refusal, ready registration, required/optional pipeline absence, pending/failed/current-success/stale-head pipelines, unreadable authenticated MR refusal, merged-state polling, host-specific authentication diagnostics, missing GitLab prerequisites, successful cleanup and preservation of unlanded work.

Focused regression checks:
- Full fm-pr-check-security and fm-pr-merge suites passed. The security suite used a disposable shasum adapter delegating SHA-256 to sha256sum.
- fm-forge-detect and fm-bootstrap passed after setting GIT_CEILING_DIRECTORIES to the temporary fixture root. Without that setting, plain fixture directories inherited the enclosing repository.
- Full fm-task-delivery stopped at the shell-metacharacter branch fixture: its absolute marker path contains the .no-mistakes directory component, which Git forbids in ref names. A disposable copy of that selector passed with a relative marker and the absence assertion rooted in the execution directory. The GitLab delivery selector also passed.
- Full fm-teardown stopped in an unrelated secondmate-source fixture because its nested home is inside the active code/home root and was correctly refused before reaching the expected missing-source diagnostic. The GitLab teardown selector passed independently.
- fm-backlog-atomicity passed the added GitLab recovery scenario, then stopped at its final persistent-secondmate fixture because that fixture home is inside the repository.
- These workspace-induced limitations were diagnosed without changing tracked code or weakening product guards. No complete repository suite, linters, formatters, or other pipeline phases ran.

The product changes are CLI and instruction changes; no rendered UI was changed. Evidence consists of actual CLI transcripts and the generated worker brief. Temporary infrastructure, credentials, test adapters, repositories, and container images were removed after testing.
