# wallets-2: Crossmint, Lit Protocol Vincent, Fireblocks, thirdweb

Group wallets-2. Read on 8 October 2026 (all fetches 2026-10-08 UTC; see SOURCES.md).
Read-only: public docs, public OpenAPI files and public repositories. Nothing was signed into, created or run.
Verdict codes and dimensions D1 to D13 are those of MATRIX.md. Where one product has two separate
control surfaces (for example a wallet signer and a card allowance), the verdict cell gives one code per surface.

---

## 1. Crossmint agent wallets, agent cards and agent checkouts

- Vendor: Crossmint.
- Status: wallets and signer scopes are in the main docs with no beta label. Agent Cards (order intents) and
  Agent Checkouts are served under the `/api/unstable/` path [C12][C14][C15]. Agent Checkouts "runs in
  production only" with no staging environment [C16]. The encrypted-card fallback in production needs sales
  approval [C11].
- Docs version: docs.crossmint.com markdown pages fetched 2026-10-08; Wallets API `2025-06-09`.
- Code read: Crossmint/crossmint-sdk@532851f (wallet SDK types), Crossmint/stellar-smart-account@bee3339
  (Soroban account contract that holds the Stellar signer policies).

### Control model

There are three agent surfaces. (1) Agent Wallet: a smart wallet (ERC-4337 with ERC-7579 modules on EVM,
PDAs on Solana, a Soroban contract on Stellar) [C3]. The principal adds the agent's key as an operational
signer, approved by the wallet's recovery method (for a user wallet, an email or phone one-time code) [C7].
At registration the signer can carry `scopes` (type `transfer` only: one token on one chain, an optional
cumulative `spendingLimit` with optional reset `interval`, and an optional `recipients` list) and a
signer-level `expiresAt` [C1][C19][C22]. The docs say enforcement is onchain by the wallet contract [C3][C6],
and the scopes guide also says scopes are checked at validation time before broadcast and refers to a "policy
contract" [C1]. On Stellar this is confirmed in public contract code (TokenTransferPolicy, spend tracker,
signer expiry, revoke event) [C23][C24][C25][C26]. For EVM and Solana the contract source is not public, so
onchain enforcement there is the vendor's statement only. (2) Agent Card: an "order intent" created from a
saved card, with a total `amount`, a required `expiresAt`, a `description` and an optional single `merchant`;
the user approves each one with a passkey or a network-hosted step [C10][C11][C12]. The agent then mints a
one-time card-network credential (Visa Intelligent Commerce or Mastercard Agent Pay) for a specific amount,
and the network enforces amount and merchant; on the encrypted-card fallback nobody but the integrator
enforces the allowance [C11][C13]. (3) Agent Checkout: a Crossmint-run purchase agent with a per-run
`constraints.maxCost`, enforced by Crossmint's service [C15].

### D1 to D13

| Dim | Verdict | What is supported | Source | Quote (confirmed in raw unless marked) |
|---|---|---|---|---|
| D1 per-transaction cap | Wallet: X. Card: C. Checkout: N | Wallet scope has only a cumulative `spendingLimit` (amount plus optional interval); no per-transaction field in the API schema, SDK type or Stellar policy struct. Card: create one order intent per purchase, and each minted credential is for a requested amount. Checkout: `maxCost` per run. | C1, C19, C22, C23, C13, C15 | C23: "Maximum cumulative amount (in token's smallest unit) allowed per window." |
| D2 per-period cap | Wallet: N. Card: X | `spendingLimit.interval` in seconds; the counter resets on the first transfer after the interval, measured from onchain registration. Order intent schema has only a total `amount` and `expiresAt`. | C1, C12 | C1: "Set `interval` to the number of seconds in the period (for example, `86400` for 24 hours)." |
| D3 total budget | Wallet: N. Card: N. Checkout: N | Omit `interval` for a lifetime cap. Order intent `amount` is the total (response tracks total, spent, reserved, available). | C1, C11, C12 | C1: "Omit `interval` to set an absolute, non-resetting cap." |
| D4 counterparty allowlist | Wallet: N (payees only). Card: N (one merchant) | Wallet `recipients` list of addresses or wallet locators. No contract allowlist: the only scope type is `transfer`, although one agent page says policies include "allowed contracts". Card: optional single `merchant` (name, url, countryCode, categoryCode, acquirerBin), fixed for the order intent; network-enforced only on `agentic-token` rails. | C1, C9, C11, C12 | C1: "Pass a non-empty `recipients` array to restrict transfers to specific addresses." C11: "Card networks enforce `amount` and `merchant` only for `agentic-token` rails." |
| D5 per-counterparty cap | Wallet: ND. Card: C | API docs do not say whether two `transfer` scopes for the same token with different recipients and limits are accepted. The Stellar contract would allow it: a Standard signer passes if any one of its policies authorizes the whole transaction. Card: one order intent per merchant, each with its own amount. | C1, C25, C11 | C25 (code comment): "At least one policy must authorize the full transaction" |
| D6 asset, network, MCC | Wallet: N. Card: ND | Each scope is one `tokenLocator` on one chain; a scoped signer can transfer only the listed tokens. Card: `merchant.categoryCode` and `amount.currency` exist in the schema, but a category-only restriction is not documented. | C1, C12 | C1: "A scope applies to a single token on a single chain and can combine two optional restrictions:" |
| D7 expiry or window | Wallet: N. Card: N | Signer-level `expiresAt` (REST only, not in the TypeScript SDK `addSigner`). Order intent `expiresAt` is required. No valid-from or hours-of-day field on either. | C1, C11, C12 | C1: "After the timestamp, every transaction signed by this signer is rejected." |
| D8 per-task credential | Wallet: N. Card: N | Wallet: a separate signer key per agent, with its own scopes and expiry, added by the recovery method; scopes are immutable for the signer's life. Card: one order intent per agent or task; credentials are one-time. | C2, C7, C10 | C10: "Create one per agent, per task, or per purchase." |
| D9 revocation | Wallet: N. Card: N | **Who:** wallet: a recovery method (the user's OTP, or a server recovery signer); the agent signer cannot revoke itself. Card: the holder of the client key plus the user's JWT. **How:** wallet: `removeSigner()` or REST DELETE, then sign and submit the approval transaction; removal is per wallet. Card: `DELETE /unstable/order-intents/{id}` returns 204. **How fast:** wallet: once the removal transaction confirms (docs say "immediately"). Card: later reads show `cancelled` and no new credentials can be minted; docs say network credentials are revoked with the agent card. **Third-party verifiable:** Stellar yes (onchain signer storage, `has_signer` view, `signer revoked` event). EVM and Solana: onchain per docs, contract source not public (ND). Card: no public status endpoint for a merchant or auditor (ND). | C4, C8, C14, C10, C26 | C8: "The user authorizes removal with their recovery method (one-time email code), and the server signer is immediately removed from the wallet's signer set." C14: "Subsequent reads return `status: "cancelled"`, and no additional credentials can be minted from its rails." |
| D10 human step-up | Wallet: ND. Card: C | No amount-threshold approval on a scoped signer. A treasury concept page says multiple signers can co-approve high-value transactions but documents no threshold field. Card: the user approves each order intent at creation (grant-time approval, not a per-payment threshold). | C11, C27 | C11: "The first Visa verification on a device can create a passkey; later order intents authenticate with the existing passkey when the device remains bound." |
| D11 task or intent binding | Wallet: N on Stellar only. Card: ND | Transfer API `memo` (text up to 28 chars, id or hash) is Stellar-only. Order intent `description` is shown in the user approval flow; whether it reaches the merchant or network is not documented. | C17, C11 | C17: "Memo for the transaction. Only supported for Stellar" |
| D12 audit export | N (transactions). ND (policy decisions) | Wallet transactions API and webhooks; `wallets.transfer.out` fires for successful and failed attempts. Order intent reads return spent, reserved, available. A log of scope denials is not documented. Checkout ends with `blocked` and a policy result code. | C18, C28, C12, C15 | C18: "This event is sent for both successful and failed transfer attempts, allowing you to track the complete lifecycle of outgoing transactions." |
| D13 cross-rail policy | Wallet: X. Card: C | A scope is one token on one chain. One order intent can mint on Visa, Mastercard, Stripe SPT and encrypted-card rails of one saved card. No object spans card and stablecoin. | C1, C11 | C10: "One agent card can mint credentials on several rails." |

Notes on contradictions found in the Crossmint docs:
- "Enforced onchain" [C3][C6] versus the scopes guide, which says scopes are checked before broadcast and an
  out-of-scope transfer is rejected at validation time (paraphrase of [C1]). Both can be true; only the
  Stellar contract lets a reader confirm the onchain half.
- On EVM the default registration (`deployImmediately: false`) records a signature and installs the signer
  "on its first transaction" [C5]. Until then the signer, and so its scopes, are not in onchain state.
- The on-chain-actions page says server-signer policies include "allowed contracts" [C9]; the API schema
  has only `transfer` scopes [C19].
- The x402 guide pays by having the agent signer produce an EIP-712 typed-data signature [C20]. Whether a
  `transfer` scope bounds a typed-data authorization, as opposed to a wallet transfer, is not documented.
  On Stellar the TokenTransferPolicy rejects any authorization context other than `transfer` on its token
  [C24].
- Stellar contract policies can be updated in place (`update_signer` keeps spend trackers) [C26 area,
  account.rs:451-466], while the docs say scopes are immutable for the signer's lifetime [C2].

### Test case

- (a) Named counterparties only: yes. Wallet `recipients`; card single `merchant`.
- (b) Per-task budget: yes. Wallet lifetime `spendingLimit`; card order intent `amount`; checkout `maxCost`.
- (c) Ends when the task ends: yes, as a timestamp (`expiresAt`), not tied to a task state.
- (d) One-step revocation a third party can verify: wallet yes on Stellar (code-confirmed); EVM and Solana
  by vendor statement only. Card: revocation is one API call but has no public verification.
- (e) Credential per task: yes (signer per task, or order intent per task).
- Full test case: yes on paper for the Stellar wallet path, and for EVM if the unpublished policy contract
  behaves as documented. Missing: per-transaction cap on the wallet, a payee plus per-payee cap in one
  documented object, a task identifier carried to the payee outside Stellar, a public revocation proof for
  cards, and documented coverage of typed-data (x402) payments by wallet scopes.

### Sources

- [C1] https://docs.crossmint.com/wallets/guides/signers/scopes.md, 2026-10-08, raw/docs.crossmint.com/wallets_guides_signers_scopes.md
- [C2] https://docs.crossmint.com/wallets/concepts/signers.md, 2026-10-08, raw/docs.crossmint.com/wallets_concepts_signers.md
- [C3] https://docs.crossmint.com/wallets/architecture.md, 2026-10-08, raw/docs.crossmint.com/wallets_architecture.md
- [C4] https://docs.crossmint.com/wallets/guides/signers/remove-signer.md, 2026-10-08, raw/docs.crossmint.com/wallets_guides_signers_remove-signer.md
- [C5] https://docs.crossmint.com/wallets/guides/signers/add-signers.md, 2026-10-08, raw/docs.crossmint.com/wallets_guides_signers_add-signers.md
- [C6] https://docs.crossmint.com/agents/wallets/overview.md, 2026-10-08, raw/docs.crossmint.com/agents_wallets_overview.md
- [C7] https://docs.crossmint.com/agents/payment-methods/stablecoin-wallets/authorize-agent.md, 2026-10-08, raw/docs.crossmint.com/agents_payment-methods_stablecoin-wallets_authorize-agent.md
- [C8] https://docs.crossmint.com/agents/payment-methods/stablecoin-wallets/remove-agent-access.md, 2026-10-08, raw/docs.crossmint.com/agents_payment-methods_stablecoin-wallets_remove-agent-access.md
- [C9] https://docs.crossmint.com/agents/payment-methods/stablecoin-wallets/on-chain-actions.md, 2026-10-08, raw/docs.crossmint.com/agents_payment-methods_stablecoin-wallets_on-chain-actions.md
- [C10] https://docs.crossmint.com/agents/cards/overview.md, 2026-10-08, raw/docs.crossmint.com/agents_cards_overview.md
- [C11] https://docs.crossmint.com/agents/payment-methods/cards/create-agent-card.md, 2026-10-08, raw/docs.crossmint.com/agents_payment-methods_cards_create-agent-card.md
- [C12] https://docs.crossmint.com/api-reference/agentic-commerce/order-intents/create-order-intent.md (OpenAPI `POST /unstable/order-intents`), 2026-10-08, raw/docs.crossmint.com/api-reference_agentic-commerce_order-intents_create-order-intent.md
- [C13] https://docs.crossmint.com/agents/payment-methods/cards/retrieve-agent-card.md, 2026-10-08, raw/docs.crossmint.com/agents_payment-methods_cards_retrieve-agent-card.md
- [C14] https://docs.crossmint.com/agents/payment-methods/cards/remove-cards.md, 2026-10-08, raw/docs.crossmint.com/agents_payment-methods_cards_remove-cards.md (also the revoke API ref, raw/docs.crossmint.com/api-reference_agentic-commerce_order-intents_revoke-order-intent.md)
- [C15] https://docs.crossmint.com/agents/checkouts/configure.md, 2026-10-08, raw/docs.crossmint.com/agents_checkouts_configure.md
- [C16] https://docs.crossmint.com/agents/checkouts/overview.md, 2026-10-08, raw/docs.crossmint.com/agents_checkouts_overview.md
- [C17] https://docs.crossmint.com/api-reference/wallets/transfer-token.md, 2026-10-08, raw/docs.crossmint.com/api-reference_wallets_transfer-token.md (lines 135-171)
- [C18] https://docs.crossmint.com/wallets/guides/webhooks.md, 2026-10-08, raw/docs.crossmint.com/wallets_guides_webhooks.md
- [C19] https://docs.crossmint.com/api-reference/wallets/register-delegated-key.md (OpenAPI `POST /2025-06-09/wallets/{walletLocator}/signers`), 2026-10-08, raw/docs.crossmint.com/api-reference_wallets_register-delegated-key.md (lines 163-215)
- [C20] https://docs.crossmint.com/agents/payment-flows/x402.md, 2026-10-08, raw/docs.crossmint.com/agents_payment-flows_x402.md
- [C21] https://docs.crossmint.com/agents/how-agents-pay.md, 2026-10-08, raw/docs.crossmint.com/agents_how-agents-pay.md
- [C22] Crossmint/crossmint-sdk@532851f packages/wallets/src/api/types.ts:84-102
- [C23] Crossmint/stellar-smart-account@bee3339 contracts/smart-account-interfaces/src/auth/types.rs:11-27, 48-62
- [C24] Crossmint/stellar-smart-account@bee3339 contracts/smart-account/src/auth/policy/token_transfer.rs:28-82 (contexts other than `transfer` on the policy token are rejected), 86-127 (cumulative limit and reset window), 146-167
- [C25] Crossmint/stellar-smart-account@bee3339 contracts/smart-account/src/auth/permissions.rs:74-112
- [C26] Crossmint/stellar-smart-account@bee3339 contracts/smart-account/src/account.rs:214-244 (revoke_signer, SignerRevokedEvent at 232, has_signer at 242); contracts/smart-account/src/events.rs:36-40
- [C27] https://docs.crossmint.com/llms-full.txt, treasury concept section (Source: https://docs.crossmint.com/wallets/concepts/treasury), 2026-10-08, raw/docs.crossmint.com/llms-full.txt
- [C28] https://docs.crossmint.com/api-reference/wallets/get-transactions.md, 2026-10-08, raw/docs.crossmint.com/api-reference_wallets_get-transactions.md

### Blocked or unverifiable

- EVM and Solana smart wallet and policy contract sources: not found in Crossmint's public GitHub
  organization on 2026-10-08 (the only Solidity repo, crossmint-solidity, was last pushed 2022). Onchain
  enforcement on those chains is unverified.
- Behaviour of scopes for EIP-712 typed-data signatures (x402) on EVM: not documented.

---

## 2. Lit Protocol Vincent

Two things now carry the Vincent name, and they work differently, so this item has two parts.

### 2a. Vincent framework (LIT-Protocol/Vincent): abilities, policies, onchain registry

- Vendor: Lit Protocol.
- Status: the repository was last pushed 2026-01-31 (GitHub API, 2026-10-08), with contracts-sdk 8.1.0
  dated 2026-01-17 and a "Vincent 2.0 architecture" breaking change on 2026-01-14 [V1]. On 2026-10-08
  `docs.heyvincent.ai` timed out and `dashboard.heyvincent.ai` returned HTTP 503 with `DEPLOYMENT_PAUSED`
  [V21]. The SDK targets Lit's Datil network [V18]. Lit's 5 March 2026 post says Datil stays up for
  migrations for at least 30 days after Lit v3 launches [V19], and Lit v3 was announced as generally
  available on 1 April 2026 [V20]. Whether Datil, and so this framework, still executes on 8 October 2026
  could not be verified. Treat 2a as the documented design, not a live service.
- Docs version: the docs site source in the repo (`docs/`, Mintlify), read at LIT-Protocol/Vincent@1fa0a48.

#### Control model

An app developer registers a Vincent App on the onchain registry (a diamond contract; the ability SDK's
default registry chain is `base`) with a set of delegatee addresses and, per app version, a fixed list of
abilities (immutable Lit Actions identified by IPFS CID) and the policies each ability supports
[V10][V22]. The user (an EOA) installs the app. In the 2.0 design this creates a per-app ZeroDev Kernel
smart account (the "agent address", derived from user address and app ID) and mints a Lit PKP whose only
permitted auth methods are the app version's ability CIDs; the PKP NFT is sent to address 0x...01 [V12][V15].
The user signs a session-key approval that installs the PKP on the smart account with ZeroDev's sudo policy,
meaning no onchain limit [V11]. Limits come from Vincent policies: the user may set parameters for the
policies the app version registered, stored per agent in the registry [V8]. At execution, the ability Lit
Action, running on Lit's node network (MPC threshold signing inside TEEs, per the docs [V1]), calls the
registry's `validateAbilityExecutionAndGetPolicies(delegatee, agent, abilityCid)` and runs each policy's
precheck, evaluate and commit before the PKP signs [V9][V13]. The delegatee is the app's operator key, not
a key the user mints. Published policies in the repo: spending limit (daily USD), contract whitelist, send
counter (count per window) [V2][V4][V5]. At this commit only two published abilities declare policy support:
`erc20-transfer` (send counter) and `evm-transaction-signer` (contract whitelist). No ability in the repo
declares the spending-limit policy, and the docs say a policy can be enabled only for an ability configured
for it [V6][V7][V14].

#### D1 to D13

| Dim | Verdict | What is supported | Source | Quote |
|---|---|---|---|---|
| D1 per-transaction cap | CODE | No published per-transaction policy. A custom policy (Lit Action) must be written, and an ability must declare support for it. | V2, V5, V14 | V14: "Your Vincent App can only enable this Policy for Abilities that have been specifically configured to support it." |
| D2 per-period cap | CODE (for transfers) | The spending-limit policy has one user parameter, `maxDailySpendingLimitInUsdCents`, with the window hard-coded to 86400 s, USD priced via Uniswap and Chainlink, spends recorded on a Chronicle Yellowstone contract. No published ability declares it, so a transfer app needs new or forked ability code. Send counter caps the number of sends per `timeWindowSeconds`, not value. | V2, V3, V5, V6 | V2: "The maximum daily spending limit in USD cents, as a BigInt." V6: "Ability to transfer ERC20 tokens with a limit on how many transfers are allowed in a time window" |
| D3 total budget | CODE | No lifetime-cap policy published. | V2, V5 | none |
| D4 counterparty allowlist | C (contracts). CODE (payees) | Contract whitelist: `whitelist[chainId][contractAddress].functionSelectors` (wildcard `*` allowed), checked against the serialized transaction's `to` and selector, on the `evm-transaction-signer` ability only. The payee inside ERC-20 `transfer` calldata is not checked by any published policy. | V4, V7 | none (code, V4 schemas.ts:9-19, vincent-policy.ts:30-70) |
| D5 per-counterparty cap | CODE | None published. | V2, V4, V5 | none |
| D6 asset, network | C | Contract whitelist is keyed by chain ID, so allowing a token contract on a chain is the only asset control. Spending limit prices one `tokenAddress` given per call. | V4, V2 | none |
| D7 expiry or window | CODE | No validity-window or expiry policy published; the registry permit has no expiry field. | V8, V5 | none |
| D8 per-task credential | X | One agent smart account and one PKP per user per app. The agent address is derived from user address and app ID, a PKP signer can be registered once, and an agent can have only one permitted app. | V8 (VincentUserFacet.sol:129-143), V15 | V15: "Each Agent Wallet has a one-to-one relationship with a Vincent App and maintains persistent identity even when permissions are revoked and re-granted." |
| D9 revocation | N | **Who:** the user's EOA (the registered agent owner) calls `unPermitAppVersion`; the app manager can also disable an app version or remove a delegatee. **How:** a registry transaction, sent directly or relayed (ERC-2771, Gelato) through the registry backend's uninstall endpoints. **How fast:** effective for the next execution, because every ability execution reads the registry; no SLA stated. **Third-party verifiable:** yes: public view functions and an `AppVersionUnPermitted` event on the registry. Caveat: the PKP stays installed with sudo authority on the user's smart account; revocation holds only while Lit nodes honour the registry. | V8 (220-257), V9, V10, V11, V16 | V16: "If access is revoked, the user will need to repermit the app before they can generate a new JWT for it. Execution of Vincent Abilities on their behalf will also fail." |
| D10 human step-up | CODE | The README names multi-factor authentication as an example policy; none is published. | V1 | none |
| D11 task or intent binding | ND | Nothing in the registry or policies carries a task or purpose identifier. | V8 | none |
| D12 audit export | ND | Onchain registry events and the spending-limit `Spent` event are public, but allow and deny decisions are returned to the delegatee only, not logged. | V3, V8 | none |
| D13 cross-rail policy | C | One contract-whitelist parameter can list several EVM chains; the spending-limit tracker is per user and app, not per chain. Solana signing ability exists with no policy support. | V4, V3 | none |

#### Test case

- (a) Named counterparties: contracts yes (C); payee addresses for token transfers only with new code.
- (b) Per-task budget: only with new code.
- (c) Expiry: only with new code.
- (d) One-step revocation a third party can verify: yes, onchain registry, with the sudo-session caveat.
- (e) Credential per task: no (X).
- Full test case: no. Missing: any published value cap usable with the published transfer ability, expiry,
  per-task keys, and an onchain limit on the smart account itself.

### 2b. Hosted Vincent at heyvincent.ai (2026)

- Vendor: HeyVincent (heyvincent.ai). The relationship to Lit Protocol is stated only by the site text
  "Agent key airgapped in Lit HSM" [V22].
- Status: heyvincent.ai served an app on 2026-10-08 titled "Vincent - Safe wallets and secrets for agents"
  [V22]. Policy details are documented only in the vendor's public agent-skill files
  (HeyVincent-ai/agent-skills@76ae07b, last pushed 2026-03-09) [V23], with matching enum names in the site's
  JavaScript bundle. The skill file says the enforcing server code is open source at
  github.com/HeyVincent-ai/Vincent; that repository returned 404 on 2026-10-08 [V24]. Enforcement is
  therefore unverified. The skill files contain instructions addressed to AI agents; they were read as data
  and not followed.

#### Control model

The agent creates a wallet (`EVM_WALLET`, a ZeroDev smart account, or `RAW_SIGNER`) through the vendor API
and receives a scoped bearer API key; a human later claims the wallet by URL and sets policies on the
dashboard; the vendor's server enforces them and holds approvals for Telegram confirmation [V23]. Before the
claim the agent runs with no policy.

| Dim | Verdict | What is supported (vendor skill file only, server code not public) | Source | Quote |
|---|---|---|---|---|
| D1 | N | Spending limit (per tx), USD. | V23 | V23: "Max USD value per transaction" |
| D2 | N | Daily (rolling 24 h) and weekly (rolling 7 days) USD limits. | V23 | V23: "Max USD value per rolling 24 hours" |
| D3 | ND | No lifetime cap listed. | V23 | none |
| D4 | N | Address allowlist; function allowlist by 4-byte selector. | V23 | V23: "Only allow transfers/calls to specific addresses" |
| D5 | ND | Not listed. | V23 | none |
| D6 | N | Token allowlist (ERC-20). | V23 | V23: "Only allow transfers of specific ERC-20 tokens" |
| D7 | ND | No expiry or window listed. | V23 | none |
| D8 | ND | One API key per created secret; re-link tokens expire after 10 minutes. A per-task key minted by the owner is not documented. | V23 | none |
| D9 | N | **Who:** wallet owner. **How:** revoke the API key on heyvincent.ai. **How fast:** "rejected immediately by the server". **Third-party verifiable:** no (server state only). | V23 | V23: "Revoked keys are rejected immediately by the server." |
| D10 | N | Require approval (every transaction) and approval threshold (USD), via Telegram. | V23 | V23: "Transactions above a USD amount need human approval via Telegram" |
| D11 | ND | Not documented. | V23 | none |
| D12 | ND | The site mentions an audit trail; no export API is documented in public files. | V22 | none |
| D13 | ND | Policies apply per secret; cross-chain or cross-secret policy not documented. | V23 | none |

Test case 2b: (a) yes, (b) only as rolling caps, no task budget, (c) no, (d) not third-party verifiable,
(e) not documented. Full test case: no. The design is also open before the human claims the wallet:
V23: "Before the wallet is claimed, the agent can operate without policy restrictions."

### Sources (item 2)

- [V1] LIT-Protocol/Vincent@1fa0a48 README.md; packages/libs/contracts-sdk/CHANGELOG.md (8.1.0, 8.0.0); docs/concepts/introduction/security.mdx
- [V2] LIT-Protocol/Vincent@1fa0a48 packages/apps/policy-spending-limit/src/lib/schemas.ts:30-34
- [V3] LIT-Protocol/Vincent@1fa0a48 packages/apps/policy-spending-limit/src/lib/vincent-policy.ts:160-171; src/lib/policy-helpers/spending-limit-contract.ts:3-26; src/lib/policy-helpers/check-spending-limit.ts:45-53
- [V4] LIT-Protocol/Vincent@1fa0a48 packages/apps/policy-contract-whitelist/src/lib/schemas.ts:9-19; src/lib/vincent-policy.ts:25-84
- [V5] LIT-Protocol/Vincent@1fa0a48 packages/apps/policy-send-counter/src/lib/schemas.ts:20-29
- [V6] LIT-Protocol/Vincent@1fa0a48 packages/apps/ability-erc20-transfer/src/lib/vincent-ability.ts:7, 21-35
- [V7] LIT-Protocol/Vincent@1fa0a48 packages/apps/ability-evm-transaction-signer/src/lib/vincent-ability.ts:7, 22-34
- [V8] LIT-Protocol/Vincent@1fa0a48 packages/libs/contracts-sdk/contracts/facets/VincentUserFacet.sol:82-206 (permitAppVersion), 220-257 (unPermitAppVersion), 268-325 (rePermitApp), 340-368 (setAbilityPolicyParameters)
- [V9] LIT-Protocol/Vincent@1fa0a48 packages/libs/contracts-sdk/contracts/facets/VincentUserViewFacet.sol:316-405
- [V10] LIT-Protocol/Vincent@1fa0a48 packages/libs/contracts-sdk/contracts/facets/VincentAppFacet.sol:52 (registerApp with delegatees), 89 (enableAppVersion), 116, 148, 173 (delegatee management)
- [V11] LIT-Protocol/Vincent@1fa0a48 packages/apps/registry-backend/src/lib/completeInstallation.ts:188-238 (`toSudoPolicy({})` at 230)
- [V12] LIT-Protocol/Vincent@1fa0a48 packages/apps/registry-backend/src/lib/installApp.ts:284-307 (mint params, NFT to 0x...01 at 307), 470-485 (auth methods are the ability CIDs)
- [V13] LIT-Protocol/Vincent@1fa0a48 packages/libs/ability-sdk/src/lib/policyCore/policyParameters/getOnchainPolicyParams.ts:60-79; src/lib/handlers/vincentAbilityHandler.ts:156-157
- [V14] LIT-Protocol/Vincent@1fa0a48 docs/ability/policy/official-policies/spending-limit.mdx
- [V15] LIT-Protocol/Vincent@1fa0a48 docs/concepts/wallets/agent-wallets.mdx:5; docs/wallet-providers/introduction.mdx (smart account index derivation)
- [V16] LIT-Protocol/Vincent@1fa0a48 docs/app/authenticating-users.mdx:254-256
- [V17] LIT-Protocol/Vincent@1fa0a48 packages/libs/contracts-sdk/src/constants.ts:9 (default diamond address 0x1599E2c248C34833A606EB1dFeA86b839170d49f)
- [V18] LIT-Protocol/Vincent@1fa0a48 packages/libs/app-sdk/src/abilityClient/vincentAbilityClient.ts:167 (`LIT_NETWORK.Datil`); packages/libs/ability-sdk/src/lib/handlers/constants.ts:3-8
- [V19] https://spark.litprotocol.com/naga-network-sunset (published 2026-03-05), 2026-10-08, raw/spark.litprotocol.com/naga-sunset.html. Quote: "For legacy users, Datil will remain operational for migrations for at least 30 days after Chipotle launches."
- [V20] https://spark.litprotocol.com/lit-v3-is-live-confidential-compute-and-key-management-in-one-api/ (published 2026-04-01), 2026-10-08, raw/spark.litprotocol.com/lit-v3-live.html. Quote: "It is now generally available."
- [V21] https://dashboard.heyvincent.ai/, 2026-10-08, raw/dashboard.heyvincent.ai/index-503.txt (HTTP 503, `DEPLOYMENT_PAUSED`); docs.heyvincent.ai timed out (no file)
- [V22] https://heyvincent.ai/ and its bundle https://heyvincent.ai/assets/index-c4NP-83I.js, 2026-10-08, raw/heyvincent.ai/index.html, raw/heyvincent.ai/index-c4NP-83I.js
- [V23] HeyVincent-ai/agent-skills@76ae07b wallet/SKILL.md:27-51, 235-250; README.md:53-66
- [V24] https://api.github.com/repos/HeyVincent-ai/Vincent, 2026-10-08, raw/api.github.com/HeyVincent-ai_Vincent-repo.json (404 Not Found)
- [V25] LIT-Protocol/Vincent@1fa0a48 docs/app/explaining-apps.mdx:61-63 (delegatees are "Ethereum addresses authorized to execute Abilities on behalf of users")

### Blocked or unverifiable (item 2)

- blocked: https://docs.heyvincent.ai/ (connection timed out, 2026-10-08). Used the repo's docs/ source instead.
- https://dashboard.heyvincent.ai/ returned 503 DEPLOYMENT_PAUSED.
- https://spark.litprotocol.com/sunsetting-lit-v0-datil-migrate-to-v1-naga-within-30-days returned the blog's
  404 page (raw/spark.litprotocol.com/datil-sunset.html); the actual Datil shutdown date is unverified.
- github.com/HeyVincent-ai/Vincent (the server code the hosted product cites) is not public.

---

## 3. Fireblocks

- Vendor: Fireblocks.
- Status: the Transaction Authorization Policy (TAP, "Policies") is the workspace policy engine. The Policy
  Editor API endpoints are labelled beta in the OpenAPI file [F5]. The x402 Agent is an open-source
  reference client (fireblocks/x402-agent@d6dbcc1, last pushed 2026-05-18) with an MCP server and a CLI
  [F2][F10]. fireblocks/fireblocks-mcp@e9f7f05 is a general Fireblocks API MCP server with write operations
  off by default [F11]. An "Agentic Payments Suite" with "Agentic Wallets" was announced on 20 May 2026;
  that product name appears only in press coverage, not in the developer docs index [F12][F13]. The
  developer docs do document agent spending controls, as TAP rules applied to an agent's vault and API user
  [F1].
- Docs version: developers.fireblocks.com markdown pages and https://swagger.fireblocks.com/openapi.yaml,
  fetched 2026-10-08.

### Control model

The object is a workspace policy (an ordered rule list), not a per-agent credential. Each agent gets a
dedicated API user (role Signer) and a dedicated vault; rules match on initiator (users, groups, services),
asset, source, destination (ids, tags, `addressType` WHITELISTED or ONE_TIME), amount (single transaction),
amount over time (`timePeriod.seconds` with per-initiator, per-source and per-destination accumulation
modes), method for contract calls, and give a verdict (ALLOW, BLOCK, 2-TIER) with approval groups,
thresholds and designated signers [F4][F5]. Fireblocks' MPC signing service enforces the rules. Policy
changes, new users and new whitelisted addresses need Admin Quorum approval [F6][F7]. The x402 Agent does
not sign a transfer: it asks Fireblocks to sign an EIP-712 payment authorization as a `TYPED_MESSAGE`
operation with a source vault and no destination [F10]. The policy reference says Typed Message rules
"should not include a destination limitation" [F4]. Whether TAP amount conditions read the token amount
inside an EIP-3009 typed message is not documented; the agent spending page states that they do [F1][F2].
The Help Center article it links for rule parameters is 403 to an anonymous reader [F14].

### D1 to D13 (TRANSFER and CONTRACT_CALL paths; x402 typed-message path noted where it differs)

| Dim | Verdict | What is supported | Source | Quote |
|---|---|---|---|---|
| D1 per-transaction cap | N | `amountScope: SINGLE_TX` with `amount` and `amountCurrency` (USD, EUR, NATIVE), or v2 `amount.range` min and max. For x402 typed messages: ND (see above). | F4, F5 | F5: "SINGLE_TX - limit applies to a single transaction" |
| D2 per-period cap | N | `amountScope: TIMEFRAME` with `periodSec`, or v2 `amountOverTime` with `timePeriod.seconds`; a quota endpoint returns window start and end. | F4, F5 | F5: "TIMEFRAME - limit applies to all transactions within the defined time period" |
| D3 total budget | C | No lifetime field. Docs make the vault balance the hard ceiling and pair it with a velocity cap. | F1 | F1: "A vault's balance is a hard ceiling on what the agent can ever spend." |
| D4 counterparty allowlist | N (transfers). ND (x402) | Destination ids, tags and `addressType: WHITELISTED`; whitelisted external, internal and contract wallets need Admin Quorum approval. Typed Message rules carry no destination limitation. | F4, F5, F7 | F7: "Each whitelisting request needs approval from the Admin Quorum before funds can be transferred to that address." F4: "Exceptions to these rules, where the rule should not include a destination limitation, are Typed Message, RAW and Burn rule types." |
| D5 per-counterparty cap | C | One rule per destination, or the per-destination accumulation mode (`TimePeriodMatchType` PER_SINGLE_MATCH versus ACROSS_ALL_MATCHES); the mode's exact semantics are in the blocked Help Center article. | F5 | F5: "Defines the method by which the Policy Engine calculates accumulation." |
| D6 asset, network | N | `asset` / `assetTypes` per rule, asset IDs are per network. No MCC. | F4, F5 | none |
| D7 expiry or window | ND | No validity-window field in the v2 PolicyRule schema; nothing found on time-boxed rules or API users. | F5 | none |
| D8 per-task credential | C | Dedicated API user per agent (Create API Key endpoint, admin only), scoped by rules that name it as initiator and its vault as source. New users and policy changes need Admin Quorum, so per-task minting is not a one-step operation. | F2, F5, F6 | none |
| D9 revocation | C | **Who:** workspace admins. **How:** deactivate or rotate the agent's API user, or publish a policy change (Admin Quorum, Owner review). **How fast:** not stated. **Third-party verifiable:** no; the record is the workspace audit log (user disabled, policy published), visible to workspace roles only. | F1, F6, F8 | F1: "Separate vaults and API users mean a compromised agent cannot touch another agent's funds, and you can revoke or rotate one agent's credentials without affecting the rest." |
| D10 human step-up | N | Verdict 2-TIER, approval groups with `threshold`, AND/OR logic, designated signers; approvals in the mobile app. | F4, F5, F1 | F1: "Approvals are pushed to the Fireblocks mobile app and enforced cryptographically by the Policy rule, not by trust in the agent code." |
| D11 task or intent binding | C (auditor). ND (payee) | `note` (workspace only), `externalTxId` (deduplication), `customerRefId` (AML), Travel Rule message to the counterparty VASP. Nothing documented that reaches an x402 merchant or onchain payee. | F5 | F5: "Custom note, not sent to the blockchain, to describe the transaction at your Fireblocks workspace." |
| D12 audit export | N | `GET /management/audit_logs` (events include `Transaction_BlockedByPolicy` and policy state changes); blocked transactions carry sub-status `BLOCKED_BY_POLICY` with the rule number; transactions API. | F5, F8, F9 | F9: "Transactions that are blocked by the policy include the Policy rule number as it appears in your workspace Policy settings." |
| D13 cross-rail policy | N | One workspace policy covers all assets and networks and also exchange, fiat-account and network-connection sources and destinations. No card rail. | F4, F5 | none |

### Test case

- (a) Named counterparties only: yes for transfers (whitelisted destinations). For the documented x402 agent
  path (typed messages): not documented.
- (b) Per-task budget: by configuration (fund the vault to the budget, plus a velocity cap).
- (c) Ends when the task ends: no documented expiry.
- (d) One-step revocation verifiable by a third party: no.
- (e) Credential per task: by configuration, with quorum approvals.
- Full test case: no. Missing: expiry, a task-scoped credential mintable in one step, external revocation
  proof, and a documented way to apply payee and amount limits to x402 typed-data signatures.

### Sources (item 3)

- [F1] https://developers.fireblocks.com/docs/x402-agent-spending-controls.md, 2026-10-08, raw/developers.fireblocks.com/docs_x402-agent-spending-controls.md. Also quoted: "The agent enforces no spending limit of its own."
- [F2] https://developers.fireblocks.com/docs/x402-agent.md, 2026-10-08, raw/developers.fireblocks.com/docs_x402-agent.md ("Secure deployment" and "Enforce human-in-the-loop signing via the Policy Engine" sections). Also: "ERC-7710 delegation is not supported"
- [F3] https://developers.fireblocks.com/docs/set-transaction-authorization-policy.md, 2026-10-08, raw/developers.fireblocks.com/docs_set-transaction-authorization-policy.md
- [F4] https://developers.fireblocks.com/reference/configure-transaction-authorization-policy.md, 2026-10-08, raw/developers.fireblocks.com/reference_configure-transaction-authorization-policy.md
- [F5] https://swagger.fireblocks.com/openapi.yaml, 2026-10-08, raw/swagger.fireblocks.com/openapi.yaml: PolicyRule v2 at lines 57700-57777; InitiatorConfig 57100; SourceConfig 57210; DestinationConfig 57247; ApproversConfig 57335; DesignatedSignersConfig 57377; VerdictConfig 57395; TimePeriodMatchType 57446; TimePeriodConfig 57453; AmountOverTimeConfig 57472; LegacyPolicyRule 56301-56580 (amountScope, periodSec, amountAggregation, applyForTypedMessage); `/tap/active_policy` beta note 15524-15534 ("These endpoints are currently in beta and might be subject to changes."); `/policy/rules/quota` 16002; `/management/audit_logs` 762; `/management/api_users` POST createApiUser 129; TransactionRequest `note`
- [F6] https://developers.fireblocks.com/docs/define-approval-quorums.md, 2026-10-08, raw/developers.fireblocks.com/docs_define-approval-quorums.md
- [F7] https://developers.fireblocks.com/docs/whitelist-addresses.md, 2026-10-08, raw/developers.fireblocks.com/docs_whitelist-addresses.md
- [F8] https://developers.fireblocks.com/reference/audit-log-events.md, 2026-10-08, raw/developers.fireblocks.com/reference_audit-log-events.md
- [F9] https://developers.fireblocks.com/reference/sub-statuses.md, 2026-10-08, raw/developers.fireblocks.com/reference_sub-statuses.md
- [F10] fireblocks/x402-agent@d6dbcc1 src/FireblocksService.ts:250-290 (`operation: TransactionOperation.TYPED_MESSAGE`, source vault only)
- [F11] fireblocks/fireblocks-mcp@e9f7f05 README.md:83, 281 and src/config.ts:73 (write operations such as `create_transaction` are off unless `ENABLE_WRITE_OPERATIONS` is `true` or `1`)
- [F12] https://cointelegraph.com/news/fireblocks-launches-agent-payment-support-for-ai-agents (published 2026-05-20), 2026-10-08, raw/cointelegraph.com/fireblocks-agentic-payments.html (press only)
- [F13] https://developers.fireblocks.com/_llms/guides.md, 2026-10-08, raw/developers.fireblocks.com/_llms_guides.md (x402 Facilitator and Agent sections; Dynamic embedded wallets "now part of Fireblocks")
- [F14] blocked, see below

### Blocked or unverifiable (item 3)

- blocked: https://support.fireblocks.io/hc/en-us/articles/29211687914268-Policy-rule-parameters (HTTP 403,
  2026-10-08). This is the rule-parameter schema the x402 Agent page points to. The OpenAPI file was used
  instead.
- Whether TAP amount and destination conditions apply to EIP-712 `TYPED_MESSAGE` payment authorizations
  (the x402 Agent's signing path): not documented in public sources.
- "Agentic Wallets" in the Agentic Payments Suite: press coverage only, no developer documentation found.

---

## 4. Added: thirdweb session keys (EIP-7702 MinimalAccount, and the ERC-4337 Account)

- Vendor: thirdweb. Chosen as the most used of the candidates not covered by other groups (Privy, Turnkey,
  Circle, Coinbase, ZeroDev, Biconomy, Rhinestone, Safe and MetaMask are covered elsewhere).
- Status: SDK v5 reference pages, no product status label found [T5]. Contract:
  thirdweb-dev/contracts-modular-account@e7222af src/7702/MinimalAccount.sol and src/lib/SessionLib.sol
  (repo last pushed 2025-10-01). SDK: thirdweb-dev/js@3b6c18d.
- Not agent-branded in the reference pages; listed because a session key is the per-task agent credential
  the test case asks for.

### Control model

The owner (an EOA delegated to MinimalAccount via EIP-7702) signs a `SessionSpec` for a session-key address:
`expiresAt`, `isWildcard`, `callPolicies` (target, selector, `maxValuePerUse`, `valueLimit`, and calldata
`constraints` with conditions and their own usage limits) and `transferPolicies` (native-value recipient
`target`, `maxValuePerUse`, `valueLimit`). `UsageLimit` is Unlimited, Lifetime, or Allowance with a fixed
`period` [T1][T2][T3]. The account contract enforces every call by the session key. The older ERC-4337
Account offers `approvedTargets`, `nativeTokenLimitPerTransaction` and start and end timestamps per signer
[T4].

| Dim | Verdict | What is supported | Source | Quote |
|---|---|---|---|---|
| D1 | N | `maxValuePerUse` for native value; for ERC-20, a `LessOrEqual` constraint on the amount argument. | T2, T3 | none (code) |
| D2 | N | `LimitType.Allowance` with `period`; windows are fixed buckets of `block.timestamp / period`, not rolling. | T2:214-221 | none (code) |
| D3 | N | `LimitType.Lifetime` on value or on a constrained argument. | T2:209-213 | none (code) |
| D4 | N (native). C (ERC-20) | `transferPolicies` list native recipients. ERC-20: one CallSpec per target and selector, with an `Equal` constraint on the recipient argument, so one allowed payee per token per session. | T1:304-335, T2:249-263 | none (code) |
| D5 | N (native). X (ERC-20, one session) | Each native `TransferSpec` has its own `valueLimit`. A second CallSpec for the same token and selector overwrites the first in `targetCallPolicy`. | T1:316-324 | none (code) |
| D6 | N | Token by call-policy target; chain fixed by the EIP-712 domain `chainId`. | T1, T3 | none |
| D7 | N | `expiresAt` (must be more than 60 s ahead). No valid-from. ERC-4337 Account has start and end timestamps. | T1:304-310, T4 | T4: "The UNIX timestamp at and after which a signer no longer has permission to use the smart wallet." |
| D8 | N | One session per session-key address; a new key per task gets its own spec. | T1:313 | none |
| D9 | C | **Who:** the account owner. **How:** MinimalAccount has no revoke function; the owner replaces the key's session with a new `createSessionWithSig` (for example no policies, expiry 61 s ahead) or waits for expiry. **How fast:** next block. **Third-party verifiable:** yes, `getSessionExpirationForSigner`, `getSessionStateForSigner` and the `SessionCreated` event. | T1 | none |
| D10 | ND | No approval or threshold in the session model. | T1, T2 | none |
| D11 | ND | Session `uid` is internal; no payee-visible task field. | T1 | none |
| D12 | ND | `Executed` and `SessionCreated` events; denials revert and leave no record. | T1 | none |
| D13 | X | Session spec is signed per chain. | T3 | none |

Footgun found in the SDK: `createSessionKey` sets `isWildcard: grantFullPermissions ?? true` [T3
createSessionKey.ts:126], and the contract skips all policy checks for a wildcard session [T1:261-263]. A
caller who passes `callPolicies` but leaves out `grantFullPermissions` gets an unrestricted session key.

Test case: (a) native payees yes, ERC-20 one payee per token per session; (b) yes; (c) yes; (d) by
replacement, verifiable onchain; (e) yes. Full test case: yes for a single ERC-20 payee or for native-value
payees. Missing: several ERC-20 payees with separate caps in one session, a dedicated revoke call, and any
cross-chain budget.

### Sources (item 4)

- [T1] thirdweb-dev/contracts-modular-account@e7222af src/7702/MinimalAccount.sol:100-108 (createSessionWithSig), 140-166 (views), 245-285 (validation; wildcard skip at 261-263), 304-335 (_createSessionKey)
- [T2] thirdweb-dev/contracts-modular-account@e7222af src/lib/SessionLib.sol:12-60 (types), 208-292 (checkAndUpdate, checkCallPolicy, validate)
- [T3] thirdweb-dev/js@3b6c18d packages/thirdweb/src/extensions/erc7702/account/types.ts:5-94 and createSessionKey.ts:24-160, fetched 2026-10-08 as raw/raw.githubusercontent.com/thirdweb-js-3b6c18df5ae140272ab775eedd7259807235682c-types.ts and -createSessionKey.ts
- [T4] thirdweb-dev/contracts@0da770f contracts/extension/interface/IAccountPermissions.sol:15-33, fetched 2026-10-08 as raw/raw.githubusercontent.com/thirdweb-contracts-0da770f27209774061e118401e8b9796ead97ced-IAccountPermissions.sol
- [T5] https://portal.thirdweb.com/llms.txt, https://portal.thirdweb.com/references/typescript/v5/erc7702/createSessionKey, https://portal.thirdweb.com/references/typescript/v5/erc4337/addSessionKey, 2026-10-08, raw/portal.thirdweb.com/

---

## Most surprising gaps

1. Vincent 2.0 installs the agent's PKP on the user's smart account with an unrestricted (sudo) session
   policy, and every limit lives in offchain Lit Actions. At this commit the only published value-cap policy
   (daily USD) is declared by none of the published abilities. The transfer ability supports only a send
   count, and the hosted docs and dashboard were down on 8 Oct 2026.
2. Fireblocks documents agent spending limits, destination allowlists and approval thresholds for its x402
   Agent, but that agent signs `TYPED_MESSAGE` requests with no destination. The same docs say Typed
   Message rules take no destination limitation, so payee control on the documented agent path is not
   shown anywhere public.
3. The same typed-data question applies to Crossmint: its x402 guide signs EIP-712 with the agent signer,
   and nothing says whether `transfer` scopes bound that signature. Crossmint's EVM policy contract is not
   public, so "enforced onchain" is checkable only on Stellar.
4. No product here has a per-transaction cap and a per-period cap and a payee list and an expiry and a
   third-party-verifiable revocation on one object. thirdweb's MinimalAccount comes closest, but allows only
   one ERC-20 payee per token per session and has no revoke call. Its SDK defaults a new session key to
   wildcard (full) permissions.
5. Crossmint's agent card is the only item with a native per-task object (order intent: amount, merchant,
   expiry, description). Its revocation has no public status a merchant or auditor can check, and on the
   encrypted-card fallback nobody but the integrator enforces the allowance.
6. The hosted Vincent product lets an agent spend with no policy at all until a human claims the wallet.

## Widely used products the teardown may be missing

- Alchemy Smart Wallets session keys (`wallet_createSession` with native and ERC-20 spend limits, contract
  allowlists and expiry on Modular Account v2): https://www.alchemy.com/docs/wallets (not read in this pass).
- Dynamic embedded wallets, now part of Fireblocks per Fireblocks' docs index, so the Fireblocks policy
  story may soon reach consumer wallets: https://developers.fireblocks.com/docs/dynamic-embedded-wallets.md
  (not read in this pass).
