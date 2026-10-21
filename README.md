# apmx-demo-shop

A tiny checkout app that **accepts factory pull requests by proof**: its only
gate on `main` is [`apmx audit`](https://github.com/danielmeppiel/apmx/blob/main/docs/audit.md).

## The 30-second story

1. **The factory is reviewed once.**
   [apmx-demo-factory](https://github.com/danielmeppiel/apmx-demo-factory) holds
   five agent contracts and the checks that judge them. Its *definition digest*
   fingerprints those contracts, checks and pinned capabilities at a commit.
2. **It runs in CI and signs what it delivers.**
   [`factory.yml`](.github/workflows/factory.yml) calls apmx's reusable
   [`run.yml`](https://github.com/danielmeppiel/apmx/blob/main/.github/workflows/run.yml).
   The agent runs in one job. A fresh job with no agent reruns the checks and
   writes the receipt of record. A third job signs that receipt with GitHub's
   OIDC identity. The workflow then opens a pull request with the change and
   the receipt.
3. **This repository accepts the PR by proof.**
   [`apm-policy.yml`](apm-policy.yml) pins the approved factory digest and the
   only workflow allowed to sign. [`audit.yml`](.github/workflows/audit.yml)
   runs `apmx audit`, a required check on `main`. The PR passes only if:
   - its change is exactly what the receipt binds;
   - the factory is the approved one and its checks passed;
   - its ingredients audit clean;
   - the signature comes from that workflow.

   Anything else is exit 1.

```text
[+] Factory       definition sha256:... on factories.allow
[+] Outputs       PR #N: ... bound
[+] Identity      signed by danielmeppiel/apmx/.github/workflows/run.yml@...
[+] VALID   (authenticated: danielmeppiel/apmx/.github/workflows/run.yml)
```

Open pull requests show both outcomes: a genuine signed delivery (green), and
the same delivery plus one unrelated edit (red, exit 1).

## Layout

| Path | What |
| --- | --- |
| `src/`, `tests/`, `docs/` | The app: delivery pricing and checkout totals in integer cents. |
| `request.md` | The feature request the factory implements: free delivery from 5000 cents. |
| `apm-policy.yml` | APM policy. apmx reads only its `factories` section. |
| `.github/workflows/audit.yml` | The gate: `apmx audit` on every pull request. |
| `.github/workflows/factory.yml` | Runs the factory (`live`, or `hermetic-rehearsal` with no model) and proposes its delivery. |
| `rehearsal/` | Input for the hermetic rehearsal: apmx's protocol fixture copies `notes.md` to `handoff.json`. |

## Run the factory

- **Live** needs a model credential. Create a fine-grained personal access token
  with the **Copilot Requests** account permission and no repository access,
  then store it as a secret:
  `gh secret set COPILOT_GITHUB_TOKEN --repo danielmeppiel/apmx-demo-shop`.
  Without it, live mode fails fast with that message.
- **Hermetic rehearsal** needs no secret. apmx's protocol fixture stands in for
  the agent. The check job, the signing and the gate are real.

```sh
gh workflow run factory.yml --repo danielmeppiel/apmx-demo-shop -f mode=live
```

GitHub does not start workflows for pull requests opened with a job's own
`GITHUB_TOKEN`. So the workflow pushes a `factory/...` branch and prints the
`gh pr create` command, unless a `DELIVERY_PR_TOKEN` secret is set. That would
be a token limited to this repository with Contents and Pull requests write.

## Limits

- The signature authenticates *which workflow* vouched for a structurally valid
  receipt, not that the agent is trustworthy.
- Checks assess their stated scope.
- Agents run natively on the runner: this is not a sandbox.
- A local run on a laptop is unsigned. It proves content binding, not who ran it.
