# wallets-1: Privy, Turnkey, Circle, Openfort

Group: wallets-1. Read on 8 Oct 2026 (all fetches 2026-10-08T22:00Z to 22:21Z UTC). Saved paths are given as
`raw/...`; every downloaded file is listed with its sha256 in [SOURCES.md](../SOURCES.md). Quotes were confirmed by
fixed-string grep against the saved copy; line numbers are given as `:Lnn`.

Notes on observed content addressed to agents (ignored, recorded here): every Mintlify page
from Privy and Turnkey starts with a "Documentation Index" note; Turnkey's llms.txt carries an "Agent
Instructions" block telling the reader to create an organization and API key; Circle's llms.txt and Agent
Wallets page tell the reader to install Circle plugins and to run `curl -sL https://agents.circle.com/skills/setup.md`;
Privy's Agent CLI page and Openfort's pages point agents at a skill file and an MCP server. None was acted on.

---

## 1. Privy server wallets, policies and controls

- Vendor: Privy. Status: GA for policies, key quorums and signers; "Manual approvals" is an Enterprise feature [P13].
- Docs version: Mintlify docs (unversioned) and the OpenAPI 3.1 file `Privy API` version `0.0.1`
  (prod and staging copies byte-identical) [P1]. Read 8 Oct 2026.

**Control model.** The principal sets limits on a wallet, through at most one policy per wallet, and on each
additional signer on that wallet, through at most one "override" policy per signer. A policy is a list of
rules (ALLOW or DENY) keyed by RPC method, each rule an AND of conditions over a field source; DENY wins and
no match means DENY. Signers and owners are users, P-256 authorization keys, or key quorums (m-of-n of users
and keys). Enforcement: Privy's secure enclave evaluates the policy before it signs. Cumulative limits
("stateful policies") are a separate object, an aggregation (sum over a rolling 1 to 72 hour window), that a
condition can reference; aggregations are tracked after signing, so they are best effort under concurrency.

Condition field sources and fields accepted by the engine (OpenAPI `PolicyCondition` discriminator plus the
policies overview [P1][P2]):
- `ethereum_transaction`: `to`, `value`, `chain_id` (enum, exactly these three).
- `ethereum_calldata`: any `function_name` or `function_name.param` decoded with a required `abi`.
- `ethereum_typed_data_domain`: `chainId`, `verifyingContract` (also `chain_id`, `verifying_contract`).
- `ethereum_typed_data_message`: dot path into the EIP-712 message, with a required `typed_data` schema.
- `ethereum_7702_authorization`: `contract`.
- `tempo_transaction`: `fee_token`, `fee_payer_signature`, `nonce_key`, `valid_before`, `valid_after`.
- `solana_program_instruction`: `programId`; `solana_instruction_data` (Anchor IDL decoded args and accounts).
- `solana_system_program_instruction`: `instructionName`, `Transfer.from`, `Transfer.to`, `Transfer.lamports`.
- `solana_token_program_instruction`: Transfer, TransferChecked (incl. `.mint`), Burn, MintTo, CloseAccount, InitializeAccount3 fields.
- `tron_transaction`, `tron_trigger_smart_contract_data`, `xrpl_transaction` (Payment, OfferCreate, TrustSet fields), `sui_transaction_command`, `sui_transfer_objects_command`.
- `message`: `content`, `byte_length` (personal_sign, signMessage, signRawMessageBytes).
- `action_request_body`: request body of the wallet action APIs, for example transfer `source.amount`, `source.asset`, `source.chain`, `destination.address`.
- `system`: `current_unix_timestamp` only.
- `reference`: `aggregation.<id>` (stateful policies; Ethereum methods only).

Operators: the OpenAPI `ConditionOperator` enum lists `eq, gt, gte, lt, lte, in, in_condition_set, contains,
starts_with, ends_with`; the overview page also lists `neq`, which does not occur anywhere in the OpenAPI file
(0 matches) [P1][P2]. Aggregation metric function: `sum` only; window type: `rolling` only, 3600 to 259200
seconds; up to 2 `group_by` fields; 10 aggregations per app [P3][P4].

| Dim | Verdict | What is supported | Source | Quote (confirmed unless marked) |
|---|---|---|---|---|
| D1 | N | `lte` on `ethereum_transaction.value`, on decoded calldata amounts (`transfer.amount`), on Solana `Transfer.lamports` / `TransferChecked.amount`, on typed-data message fields (so EIP-3009 x402 authorizations can be capped), and on `action_request_body.source.amount`. | P2, P1 | "If no rules resolve, the policy will default to `DENY`." (P2:L44) |
| D2 | N (narrow) | Aggregation (`sum`, rolling 1 to 72 h) referenced by a `reference` condition. Only `eth_signTransaction` and `eth_signUserOperation` are tracked: spend via `eth_sendTransaction`, typed-data signatures (x402), Solana and other chains is not counted. Values are recorded after signing, so concurrent requests can overshoot. | P3, P4 | "Minimum value is `3600` (1 hour), and maximum is `259200` (72 hours)." (P3:L150); "Aggregations only track `eth_signTransaction` and `eth_signUserOperation` requests." (P4:L270) |
| D3 | C (72 h max) / X beyond | A lifetime budget exists only if the grant lives at most 72 h: a 259200 s aggregation plus a time-bound condition on the same override policy. Longer budgets are excluded by the schema maximum. | P1, P3, P6 | "Currently, only `'rolling'` windows are supported." (P3:L146) |
| D4 | N | `in` (up to 100 values) or `in_condition_set` on `to`, on calldata recipient, on Solana `Transfer.to`, on typed-data `to`, on transfer `destination.address`. Condition sets are owner-controlled lists. | P2, P5 | "Operators include `eq`, `neq`, `lt`, `lte`, `gt`, `gte`, `in`, `in_condition_set`, `contains`, `starts_with`, and `ends_with`." (P2:L216) |
| D5 | N | Per transaction: one ALLOW rule per payee with its own amount condition. Per period: aggregation with `group_by` recipient (EVM sign methods only, as D2). | P3 | "With this configuration, each unique recipient address has its own rolling 24-hour budget of 1000 OUSD." (P3:L302) |
| D6 | N | `chain_id` on EVM, token contract via `to`, SPL `TransferChecked.mint`, transfer API `source.asset` and `source.chain`. No merchant categories (not a card product). | P1, P2 | (field list above, from P1 enums) |
| D7 | N (valid-from/until) / ND (hours of day) | `system.current_unix_timestamp` compared with `lt`/`gte` gives start and end; there is no time-of-day or recurring construct. | P2, P6 | "Chain-agnostic system fields, such as the current timestamp at the time of the request." (P2:L211) |
| D8 | N | The principal can create a key quorum from a fresh P-256 key (`POST /v1/key_quorums`) and add it to the wallet as an additional signer with `override_policy_ids` (max 1). The override REPLACES the wallet's base policy, so narrowness is the principal's job. The docs disagree on what an override-less signer gets: React and Expo say no policy applies, Swift and Android say the wallet's policy applies. A separate device-grant flow gives a self-hosted agent the user's wallet access (15 min access token, 30 day refresh) with no per-grant policy documented. | P1, P7, P8, P9 | "If specified, this will override the base policy IDs set on the wallet. Currently, only one policy is supported per signer." (P1:L1); "This is an optional field, if not provided, no policies will apply to the signers requests." (P7:L48) |
| D9 | N (one step) / ND (third party) | Who: the wallet owner (user, key or quorum, signing the request), or the user via `removeSigners`; for device grants the user via `DELETE /api/oauth/v2/grants/{id}`. How: `PATCH /v1/wallets/{id}` without the signer, or delete the key quorum. How fast: signer removal timing not documented; device-grant refresh tokens die at once but the access token lives up to 15 min. Third party: nothing documented; state lives in Privy's backend, no public status endpoint. | P7, P9, P10 | "Revoking a grant immediately invalidates all refresh tokens associated with it. The corresponding access token (JWT) remains valid until its natural expiry of up to 15 minutes." (P9:L385) |
| D10 | C | Policy actions are only ALLOW and DENY. A threshold step-up is built by giving the agent's signer a capped override policy and requiring the owner quorum (which can include a human user) for anything else, or by proposing an intent that a reviewer quorum approves in the Dashboard (Enterprise). The routing decision is app code. | P1, P11, P12, P13 | "Manual approvals is an Enterprise feature." (P13:L10) |
| D11 | ND | `reference_id` exists on wallet actions and filters `GET /v1/transactions`, but it stays inside Privy; nothing is documented as carried to the payee. | P1 | (OpenAPI parameter "Developer-provided reference ID to filter transactions by.") |
| D12 | N (transactions) / ND (RPC deny log) | `GET /v1/wallets/{id}/transactions`, `transaction.*` and `intent.*` webhooks, Dashboard activity logs for configuration. Denials are recorded only for wallet action APIs (`wallet_action.*.rejected`); no log of RPC policy denials is documented. | P1, P14 | "Fired when a wallet action fails before any onchain effects (e.g. policy rejection, simulation failure)." (P1:L1) |
| D13 | N (EVM chains) / X (across chain types, card) | One `ethereum` policy covers every EVM chain unless a `chain_id` condition narrows it, and an aggregation can sum across chains. A policy has one `chain_type` and a wallet takes one policy, so EVM plus Solana cannot share one policy. Privy cards are Bridge plus Stripe Issuing, whose spend controls sit in Stripe. | P1, P2, P15 | "An optional list of up to one policy ID to enforce on the wallet." (P1:L1); "Stripe Issuing creates the card and handles authorization, spend controls, and webhooks." (P15:L13) |

**Test case.**
(a) Named counterparties only: yes, allowlist on `to`, calldata recipient or typed-data recipient.
(b) Per-task budget: partly. One aggregation referenced only by the task signer's override policy works for
`eth_signTransaction` and `eth_signUserOperation`, for at most 72 h, with at most 10 aggregations per app (so at
most 10 concurrent task budgets), and it is checked against a total recorded after signing. Spend by
`eth_sendTransaction`, by x402 typed-data signatures and on Solana is not counted.
(c) Ends when the task ends: yes, `current_unix_timestamp` bound in the override policy.
(d) One-step revocation that a third party can verify: one step yes, third-party verification no.
(e) Credential per task: yes, key quorum per task as an additional signer.
Full test case: no. Missing: a budget that covers every spend path (send, typed data, Solana) and lasts longer
than 72 h at more than 10 tasks per app, and any revocation signal a payee or auditor can check.

**Sources.**
- [P1] https://api.privy.io/v1/openapi.json (identical to the staging copy), raw/docs.privy.io/openapi-prod.json, openapi-staging.json
- [P2] https://docs.privy.io/controls/policies/overview.md, raw/docs.privy.io/controls_policies_overview.md
- [P3] https://docs.privy.io/controls/policies/stateful-policies.md, raw/docs.privy.io/controls_policies_stateful-policies.md
- [P4] https://docs.privy.io/recipes/using-stateful-policies.md, raw/docs.privy.io/recipes_using-stateful-policies.md
- [P5] https://docs.privy.io/controls/policies/condition-sets.md, raw/docs.privy.io/controls_policies_condition-sets.md
- [P6] https://docs.privy.io/controls/policies/example-policies/timebound.md, raw/docs.privy.io/controls_policies_example-policies_timebound.md
- [P7] https://docs.privy.io/wallets/using-wallets/signers/add-signers.md and .../remove-signers.md, raw/docs.privy.io/wallets_using-wallets_signers_add-signers.md, wallets_using-wallets_signers_remove-signers.md
- [P8] https://docs.privy.io/recipes/wallets/conditional-signer-policies.md, raw/docs.privy.io/recipes_wallets_conditional-signer-policies.md
- [P9] https://docs.privy.io/recipes/agent-integrations/agent-authorization.md, raw/docs.privy.io/recipes_agent-integrations_agent-authorization.md
- [P10] https://docs.privy.io/wallets/wallets/update-a-wallet.md, raw/docs.privy.io/wallets_wallets_update-a-wallet.md
- [P11] https://docs.privy.io/controls/dashboard/approvals.md, raw/docs.privy.io/controls_dashboard_approvals.md
- [P12] https://docs.privy.io/recipes/policy-based-mfa.md, raw/docs.privy.io/recipes_policy-based-mfa.md
- [P13] https://docs.privy.io/controls/dashboard/overview.md, raw/docs.privy.io/controls_dashboard_overview.md
- [P14] https://docs.privy.io/security/implementation-guide/activity-logs.md, raw/docs.privy.io/security_implementation-guide_activity-logs.md
- [P15] https://docs.privy.io/financial-flows/cards/overview.md, raw/docs.privy.io/financial-flows_cards_overview.md
- Also read: controls_overview, key quorum pages, x402 recipe (its `maxValue` is a client-side SDK option: raw/docs.privy.io/recipes_agent-integrations_x402.md:L128), agentic-wallets, agent-cli, x402-sanctions-screening, changelog.

**Blocked or unverifiable.** Nothing blocked. Unverified: the time a signer removal takes to apply; whether a
per-wallet aggregation can be grouped by wallet address (the recipe suggests it, P4:L92, but no wallet-address
field appears among the documented group-by sources).

---

## 2. Turnkey policy engine

- Vendor: Turnkey. Status: GA (policy engine, time-based policies, session profiles, consensus). Velocity
  controls: present in SDK generated code only, undocumented (see D2).
- Docs version: Mintlify docs, swagger `API Reference` 1.0 at docs.turnkey.com (186 paths) [T1]; SDK repo
  tkhq/sdk@1363a6d (8 Oct 2026) [T10]. Read 8 Oct 2026.

**Control model.** The principal sets limits on users (each with credentials such as API keys) inside an
organization or sub-organization. Every policy in the organization is evaluated on every activity: `effect`
(ALLOW or DENY), `consensus` (who approved: `approvers`, `credentials`), `condition` (what: `activity`,
`eth.tx`, `eth.eip_712`, `eth.eip_7702_authorization`, `solana.tx`, `tron.tx`, `bitcoin.tx`, `tempo.tx`,
`wallet`, `wallets`, `wallet_account`, `private_key`), and an optional `time` (when: `time.now`, `Timestamp()`,
`CronSpan()`). Explicit DENY wins; no ALLOW means implicit DENY; the root quorum bypasses all policies. Grammar:
`&&`, `||`, `==`, `!=`, `<`, `>`, `<=`, `>=`, `in`, indexing and slicing, `.all`, `.any`, `.contains`,
`.count`, `.filter`. Enforcement: the policy engine runs in a secure enclave and can emit signed App Proofs of
each outcome [T2][T3][T4][T9].

Fields relevant to spend: `eth.tx.{from,to,data,value,chain_id,function_name,function_signature,contract_call_args}`;
`eth.eip_712.{primary_type,domain.{name,version,chain_id,verifying_contract},message[...]}`;
`solana.tx.{transfers[].{from,to,amount},spl_transfers[].{from,to,amount,owner,token_mint},instructions,program_keys,account_keys}`;
`tron.tx.contract[].{to_address,amount,contract_address,call_value}`; `bitcoin.tx.outputs[].{value,address}`;
`tempo.tx.{calls,fee_token,valid_before,valid_after}` [T3].

| Dim | Verdict | What is supported | Source | Quote |
|---|---|---|---|---|
| D1 | N | `eth.tx.value`, decoded ERC-20 args (`contract_call_args`), Solana `transfers[].amount` and `spl_transfers[].amount`, EIP-712 message fields (an x402 EIP-3009 `TransferWithAuthorization` can be matched and its `value` compared). Turnkey's own "spending caps" are per signing. | T3, T5, T6 | "\| Spending caps \| Bound transaction values per-signing to limit blast radius if the agent misbehaves \|" (T6:L80) |
| D2 | ND | Nothing in the policy language, the feature docs or the docs swagger paths. The SDK's generated client (@turnkey/http 6.6.0) has `create_velocity_control` (sum or count, rolling window, group by organization, user or wallet, referenced from policies as `controls.<id>`); the docs swagger has the schemas but no endpoint path, and no docs page explains it. Not usable as evidence of a shipped feature. | T1, T10 | "Identifier for the Velocity Control. Policies reference it as `controls.<identifier>`." (T1:L8434, quoted with the escaped angle brackets decoded) |
| D3 | ND | Same velocity-control schema has an `infinite` window, also undocumented. | T1 | "Uses all matching data without a time limit." (T1:L21667) |
| D4 | N | `eth.tx.to in [...]`, `contract_call_args['to']`, `solana.tx.transfers.all(t, t.to in [...])`, EIP-712 message recipient. | T3, T5 | (language reference, T3) |
| D5 | N | One condition per payee joined with `||`, each with its own amount bound, or one policy per payee. | T3 | (language reference, T3) |
| D6 | N | `eth.tx.chain_id`, `eth.eip_712.domain.chain_id` and `verifying_contract`, ERC-20 contract via `eth.tx.to`, SPL `token_mint`. No merchant categories. | T3, T5 | (language reference, T3) |
| D7 | N | Top-level `time` field against trusted server time: one-shot windows and recurring `CronSpan` windows (hours of day, time zone aware, duration up to 7 days per fire). | T4 | "When it evaluates to `false`, the policy is skipped entirely for that request: it neither allows nor denies, and does not participate in the outcome." (T4:L24) |
| D8 | N | An API-only user per task with its own API key (optional `expirationSeconds`) and policies whose `consensus` names that user, or a session profile (scope in policy language, expiration ceiling). Limits: 100 users per organization, 5 policies per organization on Free, Pay-as-you-go and Pro, session profiles cannot be edited or deleted; sub-organizations are unlimited. | T1, T7, T8, T11, T12 | "Policy limits vary by plan: 5 policies per organization on Free, Pay-as-you-go, and Pro," (T11:L37); "**Key point**: The DA user has zero permissions by default." (T7:L118) |
| D9 | N (one step) / ND (payee-queryable status) | Who: root quorum, or any user a policy permits (the agent can be allowed to delete itself). How: `DELETE_USERS`, `DELETE_API_KEYS` or `DELETE_POLICY` activities, or a DENY policy as a circuit breaker. How fast: not documented. Third party: the delete activity can carry an enclave-signed policy-outcome App Proof, verifiable against a Boot Proof, but the principal has to hand it over; it proves the authorized decision, not a revocation state a payee can query. | T7, T9, T1 | "Policy outcome proofs verify that policy decisions for your activity requests were properly evaluated against your org's policies by Turnkey's **policy engine application** in a secure enclave." (T9:L83) |
| D10 | N | `consensus` requiring both the agent and a named human, with a `condition` such as value above a threshold; the activity waits in `ACTIVITY_STATUS_CONSENSUS_NEEDED`. MFA policies can also require extra factors per condition. | T7, T1, T13 | "\"consensus\": \"approvers.any(user, user.id == '<AGENT_ID>') && approvers.any(user, user.id == '<HUMAN_ID>')\"," (T7:L220) |
| D11 | ND | `requestContext` ("Bind metadata to the request.") exists only on secret export. Nothing reaches the payee. | T1 | (swagger, `ExportSecretParams`) |
| D12 | N | `list_activities` filtered by status (including REJECTED and FAILED), `get_policy_evaluations` with per-policy outcome (`OUTCOME_ALLOW`, `OUTCOME_DENY_EXPLICIT`, `OUTCOME_DENY_IMPLICIT`, `OUTCOME_TIME_INACTIVE`, ...), signed `ACTIVITY_UPDATES` webhooks, optional App Proofs. | T1, T14 | (swagger paths `/public/v1/query/get_policy_evaluations` T1:L730, enum value `OUTCOME_DENY_EXPLICIT` T1:L16466) |
| D13 | N | Policies are organization-wide and one expression may test both EVM and Solana payloads. Turnkey's agentic payments guide nonetheless says EVM and SVM need separate policies. No card rail. | T13, T15 | "\"condition\": \"eth.tx.value > 0 \|\| solana.tx.transfers.count() > 0\"," (T13:L225); "EVM and SVM have different transaction models and require separate policies." (T15:L75) |

**Test case.**
(a) Named counterparties: yes. (b) Per-task budget: no documented cumulative control; only per-signing caps.
(c) Expiry: yes, `time` field plus expiring API key. (d) One-step revocation: yes; third-party verification
only through App Proofs the principal chooses to share. (e) Credential per task: yes, API-only user per task,
bounded by plan limits (5 policies outside Enterprise).
Full test case: no. Missing: a budget (velocity controls are not documented), and a revocation status a payee
can query.

**Sources.**
- [T1] https://docs.turnkey.com/public_api.swagger.json, raw/docs.turnkey.com/public_api.swagger.json
- [T2] https://docs.turnkey.com/features/policies/overview.md, raw/docs.turnkey.com/features_policies_overview.md (L36 "All policies defined within an Organization are evaluated on each request."; L67 "The Root Quorum bypasses any policies.")
- [T3] https://docs.turnkey.com/features/policies/language.md, raw/docs.turnkey.com/features_policies_language.md
- [T4] https://docs.turnkey.com/features/policies/time-based-policies.md, raw/docs.turnkey.com/features_policies_time-based-policies.md
- [T5] https://docs.turnkey.com/features/policies/examples/ethereum.md, raw/docs.turnkey.com/features_policies_examples_ethereum.md (L275, EIP-3009 example)
- [T6] https://docs.turnkey.com/solutions/company-wallets/agentic-wallets.md, raw/docs.turnkey.com/solutions_company-wallets_agentic-wallets.md
- [T7] https://docs.turnkey.com/features/policies/delegated-access/agentic-wallets.md, raw/docs.turnkey.com/features_policies_delegated-access_agentic-wallets.md
- [T8] https://docs.turnkey.com/features/authentication/sessions/session-profiles.md, raw/docs.turnkey.com/features_authentication_sessions_session-profiles.md (L18 immutability)
- [T9] https://docs.turnkey.com/security/turnkey-verified.md, raw/docs.turnkey.com/security_turnkey-verified.md
- [T10] tkhq/sdk@1363a6d packages/http/src/__generated__/services/coordinator/public/v1/public_api.swagger.json:3339 (`/public/v1/submit/create_velocity_control`), public_api.client.ts:3994-4004
- [T11] https://docs.turnkey.com/reference/resource-limits.md, raw/docs.turnkey.com/reference_resource-limits.md
- [T12] https://docs.turnkey.com/features/users/credentials.md, raw/docs.turnkey.com/features_users_credentials.md
- [T13] https://docs.turnkey.com/features/authentication/mfa/overview.md, raw/docs.turnkey.com/features_authentication_mfa_overview.md
- [T14] https://docs.turnkey.com/features/webhooks/overview.md, raw/docs.turnkey.com/features_webhooks_overview.md
- [T15] https://docs.turnkey.com/solutions/company-wallets/agentic-payments.md, raw/docs.turnkey.com/solutions_company-wallets_agentic-payments.md
- Also: https://docs.turnkey.com/llms-full.txt (raw/docs.turnkey.com/llms-full.txt) used for keyword sweeps.

**Blocked or unverifiable.** Nothing blocked. Unverified: whether velocity controls are live; how fast a
deleted user or key stops signing.

---

## 3. Circle (Agent Wallets, developer-controlled wallets, Gateway, modular wallets)

Two blocks: 3a for the agent-specific product, 3b for the general developer-controlled stack.

### 3a. Circle Agent Wallets and Agent Nanopayments (Circle CLI)

- Vendor: Circle. Status: not labelled beta in the docs; spending policies are mainnet only [C1]. CLI
  `@circle-fin/cli` 1.2.0 (npm, Apache-2.0; sources read from the package's source map) [C4].
- Read 8 Oct 2026.

**Control model.** Agent Wallets are Circle user-controlled wallets (2-of-2 MPC) that the agent drives through
Circle CLI after an email-OTP login (session lasts 28 days). The principal sets a spending policy per agent
wallet and chain: per-transaction, daily, weekly and monthly rolling caps on stablecoin transfers, and recipient
or contract allowlists or blocklists. Changing a policy needs a second email OTP. Policy rows are stored and
re-validated by Circle's agentic-wallet backend (`/v1/policy/limit`, `/v1/policy/budget`), so enforcement is on
Circle's server, though Circle's own skill file describes the caps as enforced by the CLI [C1][C2][C4][C5].

| Dim | Verdict | What is supported | Source | Quote |
|---|---|---|---|---|
| D1 | N | `--per-tx` cap on USDC transfers. The live backend policy type is `STABLECOIN_TRANSFER` only; native and wrapped-asset policies are "planned". | C2, C4 | "narrowed the oneof to just `STABLECOIN_TRANSFER`; `NATIVE_TRANSFER` and" / "`WRAPPED_ASSET_TRANSFER` are planned in a follow-up PR." (C4 limit-set.ts:L33-34) |
| D2 | N | `--daily`, `--weekly`, `--monthly` rolling-window caps, monotonic, shared across all EVM chains for one address. | C1, C2 | "Spending policies let you cap your agent wallet's USDC transfers over a rolling" (C1:L24); "\| `--daily` \| Daily rolling-window cap. Used with `--rule-type transfer-limit`. \|" (C2:L282) |
| D3 | ND | No lifetime cap among the five documented rule types; the longest window is monthly. | C2, C4 | (rule types: transfer-limit, recipient-allowlist, recipient-blocklist, contract-allowlist, contract-blocklist) |
| D4 | N | `recipient-allowlist` and `contract-allowlist` (EVM addresses) per wallet. | C1, C2 | (C1 rule-type list) |
| D5 | ND | Caps are per wallet; no per-recipient amount. | C2 | |
| D6 | ND | No rule that restricts asset or chain; caps apply to stablecoin transfers only (see D1). | C4 | |
| D7 | ND | Policies carry no validity window; only the login session expires (28 days). | C3 | "Sessions last 28" (C3:L26, sentence continues "days.") |
| D8 | ND | No per-task credential: one session per email login, with full wallet authority within the wallet's policy. Up to 5 agent wallets per user, which cannot be deleted. | C2, C3 | "Each user can have up to 5 agent wallets. You can't delete agent wallets." (C2:L166) |
| D9 | ND | `circle wallet logout` only clears local credentials (its source makes no network call); no server-side session revocation is documented; anyone who can read the inbox can log in and change policies. Third party: nothing. | C2, C3, C4 | "Log out of Circle CLI and clear stored credentials." (C4 logout.ts:L8) |
| D10 | ND (payments) | A human OTP is required to set or reset a policy, not to approve a payment above a threshold. `--max-amount` on `services pay` is a client-side refusal in the CLI. | C2, C4, C5 | "\| `--max-amount <usdc>` \| Refuse to pay more than this amount in USDC (for example, `0.01`). \|" (C2:L746; check at C4 pay.ts:L1370) |
| D11 | ND | Nothing carried to the payee. | | |
| D12 | N (transactions) / ND (policy decisions) | `circle transaction list` with states including `denied`; `limit budget` shows remaining budget. Failed x402 payments log locally. No policy decision log documented. | C2 | |
| D13 | N (EVM) | One budget is shared across the nine supported EVM chains. All supported chains are EVM; no card rail. | C2, C6 | "are EVM-wide and not blockchain-specific. Mainnet only." (C2:L347) |

x402: the Agent Wallets page says limits cover "outbound transfers and x402 payments" (C7:L98), but nanopayments
are paid from a Gateway balance that is deposited first; whether the policy applies to each x402 authorization
is not shown in any API reference or CLI source read. Marked unverified.

### 3b. Circle developer-controlled wallets, Compliance Engine, Gateway delegates, modular wallets

- Status: developer-controlled wallets GA; Compliance Engine "only available for eligible customers" [C9].
  OpenAPI generated from Circle's internal repo commit e1810617 [C8]. Read 8 Oct 2026.

**Control model.** Developer-controlled wallets are custodial MPC wallets driven by an API key plus an entity
secret. The Wallets API has no spend-policy object at all (no policy or limit endpoints among its 29 paths).
Circle's Compliance Engine screens transactions by risk category, plus an entity-wide blocklist and an
allowlist that overrides screening, and can deny a transaction or freeze a wallet. Gateway lets a depositor add
a delegate key on-chain with a full allowance over its deposit. Modular wallets (ERC-6900) have one spend-related
module, an on-chain Address Book allowlist; anything else is a custom module. Circle's Gas Station "policy" is
gas sponsorship, not spend [C8][C9][C10][C11][C12][C13].

| Dim | Verdict | What is supported | Source | Quote |
|---|---|---|---|---|
| D1 | CODE | No amount rule in the Wallets API; Circle tells developers to enforce rules in their own backend. | C8, C10 | "transactions on retired wallets, or enforce equivalent rules in your own" (C10:L72) |
| D2 | CODE | Same. | C8 | |
| D3 | CODE | Same; for Gateway, the deposit size bounds what a delegate can spend (C: dedicated depositor wallet funded with the task budget). | C11 | |
| D4 | C (deny) / CODE (allow only) | Compliance Engine blocklist is entity-wide; its allowlist only overrides screening, it does not restrict to listed payees. Modular wallets: Address Book module restricts token transfers to an on-chain allowlist. | C9, C12 | "* *Your allowlist* will allow any transaction where the associated address has" (C9:L203); "\| Address Book \| Restricts transfers (ERC-20, ERC-721, ERC-1155) to a list of onchain allowlisted addresses." (C12:L93) |
| D5 | CODE | None. | | |
| D6 | CODE | Wallets are per blockchain; no asset rule. | C8 | |
| D7 | CODE | None. | | |
| D8 | C (Gateway only) | A Gateway delegate key is per-key and can be added per task, but it holds a full allowance over the depositor's token balance. No scoped API keys for wallets documented. | C11 | "acts as a full allowance for `delegate` on the `token` balance of the function" (C11:L302) |
| D9 | N (Gateway, on chain) / C (wallets) | Wallets: freeze through Compliance Engine or console, no delete or disable endpoint. Gateway: `removeDelegate` on-chain, checkable by anyone with `isAuthorizedForBalance` and the `DelegateRemoved` event, effective once final; burn intents the delegate already signed stay valid. | C10, C11, C14 | "This revocation is not respected for burn intents that have already been" (C11:L319); "* The Gateway API reflects revocations once they are finalized onchain" (C14:L162) |
| D10 | ND | Compliance alerts are after the fact; no approval step documented. | C9 | |
| D11 | ND | `refId` on transactions is internal. | C8 | "description: Optional reference or description used to identify the transaction." (C8:L1768) |
| D12 | N | Transactions API with states including `DENIED` and risk evaluation; Compliance Engine alerts. | C8 | |
| D13 | ND | | | |

**Test case (Circle).**
3a Agent Wallets: (a) yes, recipient allowlist per wallet; (b) partly, rolling caps per wallet, not per task,
no lifetime cap, stablecoin only; (c) no; (d) no documented server-side revocation, nothing for third parties;
(e) no. 3b developer-controlled: all by own code; Gateway delegates give (d) on-chain verifiable revocation and
(e) a per-task key, but with full allowance and with pre-signed intents surviving revocation.
Full test case: no. Missing: per-task credential, expiry, task budget, revocation.

**Sources.**
- [C1] https://developers.circle.com/agent-stack/agent-wallets/wallet-operations/custom-policies.md, raw/developers.circle.com/agent-stack_agent-wallets_wallet-operations_custom-policies.md (L26 "Policies apply to mainnet agent wallets only.")
- [C2] https://developers.circle.com/agent-stack/circle-cli/command-reference.md, raw/developers.circle.com/agent-stack_circle-cli_command-reference.md
- [C3] https://developers.circle.com/agent-stack/agent-wallets/wallet-operations/authenticate.md, raw/developers.circle.com/agent-stack_agent-wallets_wallet-operations_authenticate.md (L40 "perform any wallet operation, including changing your spending policies.")
- [C4] npm @circle-fin/cli 1.2.0, https://registry.npmjs.org/@circle-fin/cli/-/cli-1.2.0.tgz, raw/registry.npmjs.org/circle-fin-cli-1.2.0/; sources extracted to src-extract/src/commands/wallet/{limit-set.ts,limit-reset.ts,logout.ts,budget.ts}, commands/services/pay.ts (limit-reset.ts:L64-65 "soft-deleting every custom policy row bound to (wallet_id, blockchain)"; limit-set.ts:L562 backend re-validation)
- [C5] circlefin/skills@58ab864 plugins/circle/skills/agent-wallet-policy/SKILL.md:13 ("per-wallet caps that the CLI enforces on every payment and transfer.")
- [C6] https://developers.circle.com/agent-stack/agent-wallets/supported-blockchains.md, raw/developers.circle.com/agent-stack_agent-wallets_supported-blockchains.md
- [C7] https://developers.circle.com/agent-stack/agent-wallets.md, raw/developers.circle.com/agent-stack_agent-wallets.md
- [C8] https://developers.circle.com/openapi/developer-controlled-wallets.yaml, raw/developers.circle.com/openapi_developer-controlled-wallets.yaml
- [C9] https://developers.circle.com/wallets/compliance-engine/tx-screening-rule-management.md, raw/developers.circle.com/wallets_compliance-engine_tx-screening-rule-management.md (L30 eligibility)
- [C10] https://developers.circle.com/wallets/dev-controlled/retire-existing-wallets.md, raw/developers.circle.com/wallets_dev-controlled_retire-existing-wallets.md
- [C11] https://developers.circle.com/gateway/references/contract-interfaces-and-events.md, raw/developers.circle.com/gateway_references_contract-interfaces-and-events.md
- [C12] https://developers.circle.com/wallets/modular/how-passkeys-and-modules-work.md, raw/developers.circle.com/wallets_modular_how-passkeys-and-modules-work.md
- [C13] https://developers.circle.com/wallets/gas-station/policy-management.md, raw/developers.circle.com/wallets_gas-station_policy-management.md (L22)
- [C14] https://developers.circle.com/gateway/howtos/manage-delegates.md, raw/developers.circle.com/gateway_howtos_manage-delegates.md
- Also read: agent-stack, agent nanopayments pages, gateway-nanopayments, compliance OpenAPI (one screening path), gateway and nanopayments OpenAPI files.

**Blocked or unverifiable.** Nothing blocked. Unverified: the default ("code-defined") caps on a new agent
wallet; whether policies apply to x402 nanopayment authorizations; whether a session token can be revoked
server side.

---

## 4. Openfort (backend wallets, signing policies, session keys)

- Vendor: Openfort. Status: backend wallets and policies not labelled beta; the open-source EIP-7702 account
  with spend caps is "unaudited" work in progress and is not what the embedded-wallet grant flow documents [O10].
- Docs: markdown pages served by www.openfort.io/docs (unversioned); openfort-xyz/openfort-node@bf4388c (26 Sept
  2026), openfort-xyz/openfort-contracts@b0ed06c, openfort-xyz/openfort-7702-account@8fd6545. Read 8 Oct 2026.

**Are Openfort's policies about gas?** Both kinds exist. Signing policies (operations `signEvmTransaction`,
`sendEvmTransaction`, `signEvmMessage`, `signEvmTypedData`, `signEvmHash`, and Solana equivalents) govern backend
wallets; gas sponsorship policies use `sponsorEvmTransaction` / `sponsorSolTransaction`, and linking a signing
policy to a fee sponsorship turns it into a sponsorship policy. The x402 recipe's "Openfort policy" is the gas
paymaster [O1][O3][O8].

**Control model.** Backend wallets (custodial, keys in a GCP Confidential Space TEE) are bounded by project- or
account-scoped policies: ordered rules, first match wins, fail closed. Criteria: `ethValue` (`<=,>=,<,>`),
`evmAddress` (`in`, `not in`), `evmNetwork` (chain IDs), `evmData` (ABI-decoded function and args), `evmMessage`
(regex), `evmTypedDataVerifyingContract`, `evmTypedDataField`; Solana `solAddress`, `solValue`, `splAddress`,
`splValue`, `mintAddress`, `solData`, `programId`, `solNetwork`, `solMessage` (SDK zod schemas confirm the set).
No time, rate or cumulative criterion exists. The catch: a backend `sendTransaction()` reaches the engine only as
a `signEvmHash` with no fields, so on the main EVM send path the criteria do not apply and the docs tell the app
(or the agent) to call `policies.evaluate()` first. For user-owned embedded smart accounts, the user can grant a
backend signer an EIP-7715 session key (contracts, expiry, call count) that the account contract enforces on
chain [O1][O2][O4][O5][O6][O11].

| Dim | Verdict | What is supported | Source | Quote |
|---|---|---|---|---|
| D1 | N (signTransaction) / CODE (sendTransaction) / X (session keys) | `ethValue`, `solValue`, `splValue`, decoded ERC-20 args bound per signing; not applied to backend sends; embedded-wallet session keys reject `token-allowance` and `native-token-transfer`. | O1, O4 | "Rules on `signEvmTransaction`, `sendEvmTransaction` and `sponsorEvmTransaction` do not run for a send, so their `evmAddress`, `ethValue`, `evmNetwork` and `evmData` criteria cannot block one." (O1:L59) |
| D2 | ND (policies) / X (session keys) | No window criterion in the SDK schemas or docs; session keys reject `rate-limit`. | O4, O11 | "`gas-limit`, `rate-limit`, `token-allowance` and `native-token-transfer` are not supported by embedded wallets and return an error." (O4:L79) |
| D3 | ND (policies) / X (value) for session keys | Session key `limit` counts uses, not value. | O5, O4 | "- `limit` `integer <int32>` _(required)_: Maximum number of times the session key can be used." (O5:L45) |
| D4 | N (signTransaction) / CODE (sendTransaction) / partial (session keys) | `evmAddress in` (up to 100 per criterion). Session keys whitelist call targets (at most 10 on chain), so for an ERC-20 payment they can name the token contract but not the payee; the `calls` list is not enforced. | O1, O4, O6 | "The `calls` list is not enforced, so scope with contract addresses." (O4:L75) |
| D5 | N (signTransaction) / CODE (send) | One rule per address with its own `ethValue` bound. | O1 | |
| D6 | N | `evmNetwork` chain IDs, `mintAddress`, `splAddress`, token contract via `evmAddress`/`evmData`. | O3 | |
| D7 | ND (policies) / N (session keys) | Session keys carry `validAfter`/`validUntil` checked on chain; policies have no time criterion. | O5, O6 | |
| D8 | N (session keys) / C (backend) | Per task: a fresh backend wallet as signer, granted a session key by the user's smart account (needs a smart or 7702 account, not an EOA). Backend wallets: one account-scoped policy per wallet; secret keys carry scopes by operation type (for example withhold `policies:write`), not by wallet. | O4, O7, O2 | "The SDK creates EOA wallets by default, and an EOA cannot enforce a session key." (O4:L12) |
| D9 | N, verifiable on chain (session keys) / N, not verifiable (policies) | Who: the user (`useRevokePermissions`) or the server (`POST /v1/sessions/revoke`, which takes a chain ID and a gas policy). How: an on-chain `revokeSessionKey` that emits `SessionKeyRevoked`. How fast: when the transaction lands (an `optimistic` flag resolves earlier). Third party: yes, account state and event, for Openfort ERC-4337 accounts. Cross-app wallet SDK 0.1.50 does not forward revocation, so grants stay usable until expiry. Backend policies: update or delete via API, no external signal. | O5, O6, O9 | "does not forward `wallet_revokePermissions` to the Wallet yet." (O9:L14) |
| D10 | ND | No approval or step-up flow documented for backend wallets or session keys. | | |
| D11 | ND | Nothing carried to the payee. | | |
| D12 | N (transactions) / ND (policy decisions) | Transactions API and webhooks (`transaction.*`, `transaction_intent.*`); `policies.evaluate()` returns a decision with matched policy and rule IDs, but no decision log or deny event is documented. | O2, O12 | |
| D13 | N (EVM chains) | One rule can list many `chainIds`; project scope covers all backend wallets. EVM plus Solana in one policy not verified. | O1, O3 | |

**Test case.**
(a) Named counterparties: only on the `signTransaction` path or by an app-run pre-flight; session keys name
contracts, not payees. (b) Per-task budget: no. (c) Expiry: yes for session keys. (d) One-step revocation a
third party can verify: yes for session keys on Openfort smart accounts (on-chain event), not for backend
policies, and not for the cross-app wallet. (e) Credential per task: yes, a session key per task, but it cannot
carry an amount limit.
Full test case: no. Missing: any amount limit on session keys, any cumulative limit, and enforcement of policy
criteria on the default backend send path.

**Sources.**
- [O1] https://www.openfort.io/docs/configuration/policies.md, raw/www.openfort.io/configuration_policies.md (L62 "A send needs an `accept` rule on `signEvmHash`, and that rule lets every send through.")
- [O2] https://www.openfort.io/docs/products/server/workflows/agentic-wallets.md, raw/www.openfort.io/products_server_workflows_agentic-wallets.md (L39 "so the contract allowlist below is enforced by the `policies_evaluate` pre-flight, not by the send itself"; L147 "The CLI MCP server acts with your secret key")
- [O3] https://www.openfort.io/docs/configuration/policies/ethereum-rules.md, raw/www.openfort.io/configuration_policies_ethereum-rules.md (L20 `signEvmHash` "None (accept or reject only)"), and .../solana-rules.md, .../rules-reference.md (L184 "Rules per policy | 50")
- [O4] https://www.openfort.io/docs/products/server/workflows/user-and-server-signers.md, raw/www.openfort.io/products_server_workflows_user-and-server-signers.md
- [O5] https://www.openfort.io/docs/api-reference/sessions.md, raw/www.openfort.io/api-reference_sessions.md (L174 revoke endpoint, L184 `optimistic`)
- [O6] openfort-xyz/openfort-contracts@b0ed06c contracts/core/base/BaseOpenfortAccount.sol:211-260 (`registerSessionKey(_key, _validAfter, _validUntil, _limit, _whitelist)`, `require(_whitelist.length < 11, ...)`, `revokeSessionKey` emits `SessionKeyRevoked`)
- [O7] https://www.openfort.io/docs/api-reference/authentication.md, raw/www.openfort.io/api-reference_authentication.md (L100 policy scopes, L108 default scope set)
- [O8] https://www.openfort.io/docs/configuration/gas-sponsorship.md and https://www.openfort.io/docs/recipes/x402.md, raw/www.openfort.io/configuration_gas-sponsorship.md, recipes_x402.md
- [O9] https://www.openfort.io/docs/products/cross-app-wallet/rpc/wallet_revokePermissions.md, raw/www.openfort.io/products_cross-app-wallet_rpc_wallet_revokePermissions.md
- [O10] openfort-xyz/openfort-7702-account@8fd6545 README.md:8 ("Contracts are unaudited and may change without notice."); src/core/OPF7702.sol has per-key ETH and token spend limits with periods, not referenced by the embedded-wallet docs read
- [O11] openfort-xyz/openfort-node@bf4388c src/policies/evmSchema.ts:67-170, src/policies/solanaSchema.ts:79-163
- [O12] https://www.openfort.io/docs/configuration/webhooks.md, raw/www.openfort.io/configuration_webhooks.md (L35-55 event table)
- Also read: products/server/policies.md (L31 account scope), server security page (policy evaluation location is not stated; the TEE trust boundary lists signing and JWT verification), session key pages, useGrantPermissions, wallet_grantPermissions, MPP recipe, API key page.

**Blocked or unverifiable.** Nothing blocked. Unverified: which account implementation a given project's
7702 delegated accounts use (the llms.txt entry for the Swift EIP-7702 page mentions a "Calibur" account; that page was not read); whether Solana backend
sends are evaluated with full criteria (the docs imply so, not tested); where policy evaluation runs.

---

## Most surprising gaps

1. Openfort: on the documented backend send path (`sendTransaction`, EIP-7702), the policy engine sees only a
   hash, so value, address, network and calldata rules cannot block a send; the agentic-wallet guide relies on a
   pre-flight `policies.evaluate()` that the agent itself calls, with the project secret key.
2. Privy: cumulative caps count only `eth_signTransaction` and `eth_signUserOperation`, so `eth_sendTransaction`,
   x402 typed-data signatures and Solana spend are invisible to them; the window tops out at 72 h, there are 10
   aggregations per app, and totals are recorded after signing.
3. Privy: a signer's override policy replaces the wallet policy, and the SDK docs contradict each other on what
   a signer added without a policy may do (no policy in React and Expo, the wallet policy in Swift and Android).
4. Turnkey: no documented cumulative limit; its "spending caps" are per signing. A full velocity-control API
   (rolling and infinite windows, per user) sits in the SDK's generated client but nowhere in the docs.
5. Turnkey: 5 policies per organization below Enterprise, which caps per-task policies; the root quorum bypasses
   every policy.
6. Circle Agent Wallets: caps cover stablecoin transfers only (native and wrapped-asset policies are "planned" in
   the CLI source); limits attach to the wallet, not the session; logout is local only; the email inbox is the
   only gate on changing limits.
7. Circle Gateway: revoking a delegate does not stop burn intents it already signed.
8. Openfort embedded session keys: no amount, allowance or rate limits ("return an error"), the `calls` list is
   not enforced, and the cross-app wallet SDK does not forward revocation.
9. None of the four carries a task, purpose or mandate identifier to the payee (D11 is ND everywhere).
10. Third-party-verifiable revocation appears only where state is on chain: Circle Gateway delegates and Openfort
    smart-account session keys. The server-side engines (Privy, Turnkey, Circle Agent Wallets) offer none, except
    Turnkey App Proofs that the principal must share.

## Products the teardown may be missing (not verified in this pass)

- Fireblocks Transaction Authorization Policy: the institutional default for rule-based approval and amount
  thresholds across many chains; https://developers.fireblocks.com/
- Safe Allowance module: per-delegate token allowances with a reset period, enforced on chain, close to the
  per-task budget plus revocation test case; https://docs.safe.global/
- Crossmint smart wallets with delegated signers, marketed for agents; https://docs.crossmint.com/
- thirdweb server wallets and smart-account session keys with spend limits; https://portal.thirdweb.com/
