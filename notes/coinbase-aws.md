# Group coinbase-aws: Coinbase CDP, Spend Permissions, AgentKit, AWS AgentCore payments

Read 8 October 2026. All quotes below were confirmed by grep against the saved raw copy named in the
source list; anything not quoted is a paraphrase with a file and line pointer. Raw files and clones are
listed in [SOURCES.md](../SOURCES.md).

Cross-cutting finding first: three of the products here stack. AWS AgentCore payments signs through a
Coinbase CDP (or Stripe Privy) embedded wallet; that wallet's own spend rules live in the CDP Policy
Engine; and Coinbase Spend Permissions is the only piece whose grant and revocation live on chain. No
single one of them expresses the full test case.

---

## 1. Coinbase CDP Server Wallets (v2) and the CDP Policy Engine

- Vendor: Coinbase (Coinbase Developer Platform, CDP)
- Status: GA. The OpenAPI tags "Policy Engine", "EVM Accounts", "EVM Smart Accounts", "Solana Accounts"
  and "Wallet Webhooks" all carry `x-slo-tier: ga` [S1 lines 156, 191, 303, 685, 786].
- Version read: OpenAPI 3.1 file `openapi.yaml`, info.version 2.0.0, in coinbase/cdp-sdk@993de49
  (commit of 2026-10-06); docs pages fetched 2026-10-08.

**Control model.** The principal (the CDP project owner) writes a policy: a list of up to 100 rules, each
an `action` (accept or reject), an `operation` (one CDP signing or sending API) and a list of `criteria`
that must all match. A policy is either project scope (exactly one per project, applies to every account,
retroactively) or account scope (at most one per account, attached via `accountPolicy` on create or
update of an EVM or Solana account). Enforcement is on Coinbase's server at the moment an account asks
CDP to sign or send: the request is accepted or refused (the error enum has `policy_violation`, while the
sign endpoints document only a 403 `forbidden` example, so the exact error is not stated). Evaluation is
stateless and per request. The project policy is evaluated first and its decision is final: an account
policy can never tighten something the project policy accepts [S1 lines 329 to 347]. End-user (embedded
wallet) operations are governed only by project-scope policies [S1 line 335].

**Every operation and criterion the schema accepts** (from `Rule.oneOf`, 22 rule types, extracted by
`coinbase_aws_policy_rules.py` from S1 lines 29299 to 31650):

| Operation (rule type) | Criteria accepted |
|---|---|
| signEvmTransaction | ethValue, evmAddress, evmData, netUSDChange |
| sendEvmTransaction | ethValue, evmAddress, evmNetwork, evmData, netUSDChange |
| signEvmMessage | evmMessage (RE2 regex) |
| signEvmTypedData | evmTypedDataField (address, numeric, string conditions on EIP-712 paths), evmTypedDataVerifyingContract |
| signEvmHash | none (accept or reject only) |
| prepareUserOperation, sendUserOperation (smart accounts) | ethValue, evmAddress, evmNetwork, evmData, netUSDChange |
| signSolTransaction | solAddress, solValue, splAddress, splValue, mintAddress, solData (IDL), programId |
| sendSolTransaction | the same plus solNetwork |
| signSolMessage | solMessage (regex) |
| signEndUserEvmTransaction / sendEndUserEvmTransaction | as the server-account EVM equivalents |
| signEndUserEvmMessage, signEndUserEvmTypedData, signEndUserEvmHash | as above |
| signEndUserSolTransaction / sendEndUserSolTransaction / signEndUserSolMessage | as above |
| sendEndUserEvmAsset | evmNetwork, evmData, netUSDChange (no evmAddress) |
| sendEndUserSolAsset | splAddress, splValue, solData, solNetwork |
| sendEndUserOperation | ethValue, evmAddress, evmNetwork, evmData, netUSDChange |
| createEndUserEvmSwap | evmNetwork, evmData, netUSDChange |

Operators: numeric `>`, `>=`, `<`, `<=`, `==`; lists `in`, `not in` (max 300 addresses per criterion).
`netUSDChange` (cents, market price, EVM only, ignored on testnets) is the only USD-denominated rule.
`evmNetwork` values: base, base-sepolia, ethereum, ethereum-sepolia, avalanche, polygon, optimism,
arbitrum, arbitrum-sepolia, zora, bnb, world, world-sepolia [S1 EvmNetworkCriterion]. The SDK's own zod
schemas match this set [S5]. **No criterion takes a time, a date, a counter, a rolling window or a
cumulative amount.** The error enum does list `daily_transaction_limit_exceeded` and
`daily_amount_limit_exceeded` [S1 lines 19241 to 19242], but no policy field sets them; they read as
Coinbase-imposed limits on another product (unverified which API returns them).

A trap worth printing: `evmAddress` compares the transaction's `to` field [S1 line 402]. For a USDC
payment `to` is the USDC contract, not the payee, so a payee allowlist for tokens needs an `evmData`
condition on the ERC-20 `transfer` parameter `to` (the OpenAPI's own example does this, S1 lines 618 to
680).

**Who can change or delete a policy, and how.** Anyone holding a CDP Secret API key with the
`policies#manage` scope [S1 lines 13516, 13626, 13682], shown in the Portal as "Non-custodial > Manage
(modify policies)" [S2], or a Portal user with access to the project. Calls: `PUT` and `DELETE
/v2/policy-engine/policies/{policyId}`; an account's policy is swapped with `updateEvmAccount` /
`updateSolanaAccount`. An update applies at once to every account using the policy; a delete removes it
from them [S1 lines 13619, 13675], although the delete's 400 example is `policy_in_use`, so the two
statements in the file pull in different directions. The only defence against the agent rewriting its own
policy is to give the agent a key without that scope. A second trap: deleting a policy is not a
revocation. When no rule in either policy targets an operation, the request is accepted [S1 line 347], so
removing an allowlist policy opens the account; "revoking" means writing a reject rule or killing the key.

| Dim | Code | What exactly is supported | Source | Quote |
|---|---|---|---|---|
| D1 per-transaction cap | N | `ethValue`, `solValue`, `splValue`, `evmData` (e.g. ERC-20 `transfer.value <= x`), and `netUSDChange` in cents. | S1, S2 | paraphrase (S1 lines 406, 29299 to 29330) |
| D2 per-period cap | X | No time, counter or cumulative criterion exists in any of the 22 rule types; evaluation is per request. | S1 Rule.oneOf (31514 to 31538) | paraphrase |
| D3 total budget | X | Same reason; no lifetime counter on an account or policy. | S1 | paraphrase |
| D4 counterparty allowlist | N | `evmAddress in [...]` on `to` (native or contract), `evmData` on the ERC-20 `to` argument for token payees, `solAddress`, `splAddress`, `programId`; 300 addresses per criterion, 100 rules per policy. | S1 | "There is a limit of 300 addresses per criterion." (S1 line 29344) |
| D5 per-counterparty cap | C | One accept rule per payee, each pairing the payee address with its own value or USD bound. Per transaction only, since there is no cumulative rule. | S1 | paraphrase |
| D6 asset / network / MCC | N | Asset by token contract (`evmAddress`), `mintAddress` (SPL), or `evmData` ABI; chain by `evmNetwork` / `solNetwork` (send operations only; sign-only operations cannot filter by network). No MCC (not a card product). | S1 | paraphrase |
| D7 expiry / time window | X | No time criterion; a rule is valid until the policy is edited or deleted. | S1 | paraphrase |
| D8 per-task credential | ND | A separate server account per task with its own account policy is possible, but the API key plus Wallet Secret that signs is project-wide, and no per-account key scoping is documented (keys have IP allowlists and "permission restrictions" only, S4 lines 84 to 96). Closest real option: CDP smart account plus a Spend Permission to a per-task spender (item 2), which is C. | S1, S4 | paraphrase |
| D9 revocation | C | Who: holder of a `policies#manage` key or a Portal user. How: edit the policy to reject, detach it, delete the account's key or rotate the Wallet Secret. How fast: effective on the next request per the API text; no latency is stated (ND). Third-party verifiable: no; policies are readable only with the project's API key and nothing is published. There is no grant object to revoke, only rules to rewrite. | S1, S2, S4 | "A decision in the project-level policy is final." (S1 line 346) |
| D10 human step-up | X | `action` is only `accept` or `reject`; no pending, approval or threshold-escalation action. | S1 lines 29728, 29817 | paraphrase |
| D11 task or intent binding | ND | No policy or API field carries a task, mandate or purpose id to the counterparty; the principal could encode data in calldata themselves. | S1 | paraphrase |
| D12 audit export | ND | Transactions: yes, `wallet.transaction.*`, `wallet.*.signed` and delegation webhooks (GA). Policy decisions: no documented log, webhook or export of accept or reject decisions; a reject is only an error returned to the caller. | S1 lines 786 to 790, 17349 to 17525 | paraphrase |
| D13 one policy across rails | N | One project policy holds EVM and Solana rules, and one `evmNetwork` list spans many chains. Crypto only; `netUSDChange` covers EVM but not Solana. | S1 | paraphrase |

**Test case.** (a) Named counterparties only: yes (D4), with the ERC-20 caveat. (b) Per-task budget: no;
only per-transaction amounts. (c) Ends when the task ends: no; the principal must edit or delete the
policy. (d) One-step revocation a third party can verify: no; revocation is a private rule edit.
(e) Credential per task: no documented per-account key. **Full test case: no.** Missing: any cumulative or
time-bounded limit, any grant object with an expiry, any third-party-visible revocation, and per-task key
scoping. Also, the precedence rule means an account policy cannot narrow a matching project accept.

---

## 2. Coinbase Spend Permissions (Coinbase Smart Wallet, Base Account SDK, now "Coinbase Wallet SDK")

- Vendor: Coinbase
- Status: contract deployed on mainnets (Base, Ethereum, Optimism, Arbitrum, Polygon, Zora, BNB Smart
  Chain, Avalanche) at `0xf85210B21cC50302F477BA56686d2019dC9b67Ad` [S8 lines 9 to 28]; audited by Cantina
  (Oct, Nov, Dec 2024; two SpendRouter audits March 2026, PDFs in the repo). The companion `SpendRouter`
  is not deployed: "`SpendRouter`: TBD" [S8 line 32]. The SDK docs have moved from docs.base.org to CDP,
  where "Base Account SDK" is now "Coinbase Wallet SDK" [S10]; and the consumer app does not support the
  feature yet: "Spend Permissions in Coinbase Wallet (formerly known as Base App) are coming soon and will
  be supported in a future update." [S9 line 18]. CDP also exposes create, list and revoke for its own
  smart accounts [S1 lines 12749 to 12892, tag tier ga].
- Version read: coinbase/spend-permissions@e0004e6 (commit of 2026-03-24, default branch HEAD on
  2026-10-08).

**Control model.** The object is a signed EIP-712 `SpendPermission` struct: `account` (the smart wallet),
`spender`, `token`, `allowance` (uint160, per period), `period` (seconds), `start`, `end`, `salt`,
`extraData` [S6 lines 29 to 49]. The wallet owner signs it once; the spender submits it
(`approveWithSignature`) or the wallet calls `approve`. Enforcement is the `SpendPermissionManager`
contract, which is added as an owner of the Coinbase Smart Wallet [S8 line 38] and checks every `spend`
on chain: valid (approved and not revoked), inside `[start, end)`, and the period's running total plus
this spend at most `allowance` [S6 lines 690 to 715]. Periods are fixed windows `start + n * period`,
with the last window cut at `end` [S6 lines 516 to 551]. Funds always move from `account` to `spender`
[S6 line 425]. ERC-721 tokens are refused [S6 line 637].

**The four questions.**
- Several tokens or payees in one permission? No. One permission names one `spender` and one `token`. A
  `SpendPermissionBatch` lets one signature approve several permissions that share `period`, `start` and
  `end`, each with its own spender, token and allowance [S6 lines 54 to 80, 317 to 351]. There is no payee
  field at all: the recipient of `spend` is always the spender. The undeployed `SpendRouter` would read an
  `(executor, recipient)` pair from `extraData` and forward to that one recipient [S7 lines 13, 105 to 115].
- Spender as a per-task key? Yes. `spender` is any address (EOA or contract, `ZeroSpender` is the only
  check), and `salt` makes otherwise identical permissions distinct, so a principal can mint a fresh key
  and permission per task.
- Who can revoke? The account, via `revoke` (requireSender account) [S6 line 397], and the spender, via
  `revokeAsSpender` [S6 line 406]; `approveWithRevoke` swaps one for another atomically, guarded against
  a front-running spend [S6 lines 367 to 390]. The SDK offers a user-prompted `requestRevoke` and a silent
  spender-side `prepareRevokeCallData` [S9].
- On-chain event a third party can read? Yes. `SpendPermissionRevoked(bytes32 indexed hash,
  SpendPermission)` is emitted once [S6 line 138], and `isRevoked` / `isValid` are public views [S6 lines
  485, 494]. Approval and every use also emit events (`SpendPermissionApproved` with the full struct,
  `SpendPermissionUsed` with the hash and period spend) [S6 lines 132 to 150].

| Dim | Code | What exactly is supported | Source | Quote |
|---|---|---|---|---|
| D1 per-transaction cap | X | No per-spend field. One spend may take the whole remaining period allowance. | S6 lines 29 to 49, 690 to 705 | paraphrase |
| D2 per-period cap | N | `allowance` per `period` seconds, fixed windows anchored at `start`. In token units, not USD. | S6 | paraphrase |
| D3 total budget | C | Set `period >= end - start`: the single window is cut at `end`, so `allowance` becomes a lifetime cap. | S6 lines 546 to 549 | paraphrase |
| D4 counterparty allowlist | X | Funds go only to `spender`. If the agent is the spender it can forward to anyone. Only when each payee is itself the spender is the payee fixed (one permission per payee). SpendRouter (one bound recipient per permission) is not deployed. | S6 line 425, S7, S8 line 32 | paraphrase |
| D5 per-counterparty cap | C | One permission per payee-as-spender, each with its own allowance, batch-approvable with one signature. Not available when an agent pays third parties. | S6 lines 54 to 80 | paraphrase |
| D6 asset / network | N | One `token` per permission (native via ERC-7528 address or ERC-20; ERC-721 refused). Approved and spent on one chain's manager; the signature's chain binding comes from the EIP-712 domain (Solady `EIP712`, a submodule not present in the shallow clone, so the chainId binding is standard EIP-712 but not read here). | S6 | paraphrase |
| D7 expiry / window | N | `start` (inclusive) and `end` (exclusive), unix seconds; checked on every spend. | S6 lines 516 to 523 | paraphrase |
| D8 per-task credential | N | `spender` is an arbitrary address the principal chooses; a fresh key plus `salt` per task gives authority limited to that permission. | S6 | paraphrase |
| D9 revocation | N | Who: account (`revoke`) or spender (`revokeAsSpender`). How: one on-chain call, batchable via the wallet's `executeBatch`. How fast: from the block that includes the revoke; the next `spend` fails `isValid` [S6 line 695]. Third party: yes, event plus public `isRevoked`. | S6, S8 line 119 | "Revoke a spend permission to disable its use indefinitely." (S6 line 392) |
| D10 human step-up | X | No threshold approval inside a permission; a spend over the allowance reverts. A new, larger permission needs a fresh owner signature (that is the only human step). | S6 | paraphrase |
| D11 task or intent binding | N | `extraData` (arbitrary bytes, signed, emitted in `SpendPermissionApproved`) and `salt` can carry a task id; each `SpendPermissionUsed` carries the permission hash, so an auditor can join spends to the signed grant. Free-form, no standard schema. | S6 lines 46 to 48, 132 to 150 | paraphrase |
| D12 audit export | N | All approvals, uses and revocations are chain events; CDP also lists permissions per smart account via API. | S6, S1 line 12813 | paraphrase |
| D13 one policy across rails | X | One permission is one token, held in one chain's manager contract; a batch is approved on one chain too. A multi-chain grant means one signed permission per chain. | S6 | paraphrase |

**Test case.** (a) Named counterparties: no, unless the counterparty is the spender. (b) Per-task budget:
yes (D3 configuration). (c) Ends when the task ends: yes (`end`). (d) One-step revocation a third party
can verify: yes. (e) Credential per task: yes. **Full test case: no.** Missing: a payee list. The closest
composition is a CDP smart account granting a spend permission to a per-task CDP server account whose
account policy allows only `transfer` to the named payees (item 1, D4). That gives (a) to (e), but the
payee check then sits in Coinbase's off-chain Policy Engine, the payee sees a payment from the
intermediate spender address rather than from the principal, and the two hops are not linked on chain.

---

## 3. Coinbase AgentKit

- Vendor: Coinbase
- Status: open source, TypeScript package version 0.11.0 [S13 package.json line 5]; no GA or beta label.
- Version read: coinbase/agentkit@2e6dbaf (commit of 2026-09-03).

**Control model.** AgentKit is a library of "actions" an agent can call, run in the developer's own
process over a wallet provider (CDP server wallet, CDP smart wallet, Privy, viem, ZeroDev, Solana
keypair). It does not enforce spend control on transfers; its README says so plainly: "AgentKit does not
gate transfers behind human approval, enforce spend caps, or allowlist destinations." [S11 line 200].
The code path confirms it: `native_transfer` parses the amount and calls
`walletProvider.nativeTransfer(args.to, amount)` with no check [S13 walletActionProvider.ts lines 101 to
125]; for the CDP provider that becomes `sendTransaction`, which calls `this.#cdp.evm.sendTransaction`
[S13 cdpEvmWalletProvider.ts lines 195 to 197, 296 to 297], so the only enforcement is CDP's Policy
Engine on the server (item 1). The provider config takes only key, secret, Wallet Secret, address,
network, idempotency key and RPC URL; no policy field [S13 cdpShared.ts lines 4 to 61].

One exception: the x402 action provider has its own in-process guards. A service URL allowlist
(`registeredServices`, empty by default, agent self-registration off by default), USDC-only options, and
`maxPaymentUsdc` (default 1.0, or env `X402_MAX_PAYMENT_USDC`) [S12 x402ActionProvider.ts lines 59 to 70,
287 to 300]. The cap is checked only in `retry_http_request_with_x402` [S12 line 416]. The one-step
`make_http_request_with_x402` (line 572) builds a plain x402 client [S12 lines 844 to 870] and never calls
`validatePaymentLimit`, so on that path any cap comes from the upstream x402 library's defaults, not from
`maxPaymentUsdc` (upstream default not verified here). The README's guardrail example adds human approval
through a third-party agent framework's middleware, which is the developer's code [S11 line 204].
AgentKit also ships `use_spend_permission` and Base Account spend, list and revoke actions [S14], so an
agent can act as a Spend Permission spender (item 2).

| Dim | Code | What exactly is supported | Source | Quote |
|---|---|---|---|---|
| D1 per-transaction cap | C | Transfers: none in AgentKit; relies on the wallet provider (CDP Policy Engine). x402 only: `maxPaymentUsdc`, in-process, and only on the two-step path. | S11, S12, S13 | "AgentKit does not gate transfers behind human approval, enforce spend caps, or allowlist destinations." (S11 line 200) |
| D2 per-period cap | X | None in AgentKit; via Spend Permissions if the agent is a spender. | S11 | paraphrase |
| D3 total budget | X | None in AgentKit. | S11 | paraphrase |
| D4 counterparty allowlist | C | Transfers: none (README). x402: service URL allowlist only, not payee address. Payee lists come from the CDP Policy Engine. | S11, S12 | paraphrase |
| D5 per-counterparty cap | X | None in AgentKit. | S11 | paraphrase |
| D6 asset / network | C | x402 restricted to USDC options; otherwise the wallet provider's network. | S12 lines 287 to 300 | paraphrase |
| D7 expiry | X | None in AgentKit; via Spend Permission `end`. | S11 | paraphrase |
| D8 per-task credential | C | Only by composing with Spend Permissions (`use_spend_permission`). | S14 | paraphrase |
| D9 revocation | C | Inherited: CDP key or policy changes, or on-chain Spend Permission revoke (an action exists). AgentKit has no revocation of its own. | S14 | paraphrase |
| D10 human step-up | CODE | Not in AgentKit; the example uses external framework middleware that the developer wires in. | S11 line 204 | paraphrase |
| D11 task binding | X | None. | S11 | paraphrase |
| D12 audit export | X | None in AgentKit; the wallet provider's records apply. | S11 | paraphrase |
| D13 multi-rail policy | X | None in AgentKit. | S11 | paraphrase |

**Test case.** AgentKit by itself expresses none of (a) to (e). **Full test case: no.** Everything comes
from the wallet provider underneath.

---

## 4. Amazon Bedrock AgentCore payments (AWS)

- Vendor: Amazon Web Services, built with Coinbase and Stripe (Privy)
- Status: **generally available since 18 August 2026** [S26]. The preview was announced 7 May 2026 (the
  page sits under a /2026/04/ path) for us-east-1, us-west-2, eu-central-1 and ap-southeast-2 [S25]. The
  developer guide pages fetched on 8 Oct carry no preview banner (grep for "preview" in all saved pages:
  no hit). The Coinbase connector needs an AWS Marketplace subscription to "Coinbase Wallets for AgentCore
  Payments" [S20].
- Version read: developer guide .md pages fetched 2026-10-08; botocore service models at develop,
  `bedrock-agentcore` 2024-02-28 (last commit 3cb0216, 2026-09-21) and `bedrock-agentcore-control`
  2023-06-05 (last commit 053554b, 2026-09-30) [S23, S24].

**Rails.** Protocols: x402 (v1 and v2, `exact` and `upto` schemes) and the Machine Payments Protocol
(methods `evm`, `tempo`, `solana`) [S19, S23 `PaymentType` = CRYPTO_X402, MPP]. Instrument: only
`EMBEDDED_CRYPTO_WALLET`, network `ETHEREUM` (all EVM chains) or `SOLANA` [S16, S23]. Connectors:
`CoinbaseCDP` and `StripePrivy` [S24]. Money: USDC (MPP `evm` is canonical USDC only) [S19]. No card rail
for payments; cards, Apple Pay, Google Pay and ACH appear only as ways for the end user to fund the wallet
in the provider's wallet hub [S17].

**Control model.** The principal (agent developer) creates a PaymentManager and connector (control plane),
then per interaction a PaymentSession with `expiryTimeInMinutes` (required, 15 to 480) and optional
`limits.maxSpendAmount` (`value`, `currency` = USD only) [S23]. Every `ProcessPayment` names a session and
an instrument; AWS checks the session's remaining budget before signing and denies once the budget or the
expiry is reached [S15, S17]. Enforcement is AWS's managed service; signing is then done by the wallet
provider under a separate end-user delegation (for Coinbase: a CDP account-scoped delegated-signing grant
with an `expiresAt`, granted and revocable by the end user in the wallet hub [S17, S27, S28]). AWS is
explicit that it does not check the payee: "AgentCore payments does not enforce `payTo`
restrictions server-side, so your application must validate the address before calling the
`ProcessPayment` API." [S21 line 306]. The budget is only as strong as IAM separation, because whoever
can create sessions can create a bigger one [S20 line 188].

| Dim | Code | What exactly is supported | Source | Quote |
|---|---|---|---|---|
| D1 per-transaction cap | C | No per-payment field in `SessionLimits` (only `maxSpendAmount`). Possible only through the wallet provider's own policy (CDP Policy Engine or Privy policies), which AWS points to. | S23, S21 | paraphrase |
| D2 per-period cap | X | No recurring period: a session is one budget over at most 480 minutes. | S23 | "The session expiry time in minutes. Must be between 15 and 480 minutes." (S23, CreatePaymentSessionRequest.expiryTimeInMinutes) |
| D3 total budget | N | `maxSpendAmount` per session in USD; failed signings roll back the deduction. | S15, S16, S23 | "Each PaymentSession has a configurable budget limit (maxSpendAmount, currency) and an expiry time." (S15 line 35) |
| D4 counterparty allowlist | C | Not enforced by Payments. Only by Cedar policies on tool calls routed through AgentCore Gateway, or by the wallet provider's policy. | S21 lines 306 to 314 | "AgentCore payments does not enforce `payTo` restrictions server-side, so your application must validate the address before calling the `ProcessPayment` API." (S21 line 306) |
| D5 per-counterparty cap | C | Only through the wallet provider's per-address rules, per transaction. | S21 | paraphrase |
| D6 asset / network | C | Instrument network ETHEREUM or SOLANA (ETHEREUM covers all EVM L2s); USDC only by protocol. No principal-set chain or asset filter inside Payments; via provider policy. | S16, S19, S36 | paraphrase |
| D7 expiry | N | `expiryTimeInMinutes` 15 to 480; session status ACTIVE, EXPIRED, DELETED. | S23 | (quoted under D2) |
| D8 per-task credential | C | The session is a per-task budget object, but the agent's credential is an IAM role, not per task. AWS's recommended split: a management role that creates sessions and is denied `ProcessPayment`, and an execution role that may only `ProcessPayment` and read. | S20 lines 114 to 190 | "Do not include PaymentSession *write* permissions (for example, `CreatePaymentSession`) and `ProcessPayment` in the same role, or the caller can bypass payment limits by creating new sessions with elevated budgets." (S20 line 188) |
| D9 revocation | N | Who: the holder of the management role (`DeletePaymentSession`, a hard delete), or expiry; separately the end user can revoke the wallet delegation in the provider's hub. How: one API call. How fast: ND (no latency documented). Third party: no; session state needs IAM to read and the logs land in the principal's own CloudWatch and CloudTrail. | S23, S20, S17, S21 line 268 | paraphrase (S21 line 268 warns that end users can revoke the delegation at any time) |
| D10 human step-up | CODE | No approval step in Payments; human-in-the-loop means the developer's own code in the management role. | S20 line 118 | paraphrase |
| D11 task binding | ND | `userId` and `agentName` exist for observability; nothing documented reaches the merchant. | S23 | paraphrase |
| D12 audit export | N | Vended CloudWatch logs for every data-plane call, X-Ray spans with amount, remaining budget and merchant `payTo`, metrics including `OperationFailure`, plus CloudTrail. | S22, S21 | paraphrase |
| D13 one policy across rails | N | One USD session budget is not tied to an instrument (`ProcessPayment` takes session and instrument separately), so it spans EVM and Solana instruments, both connectors and both x402 and MPP. Crypto only. Inferred from the schema. | S23 | paraphrase |

**Test case.** (a) Named counterparties: not in Payments (C via Gateway Cedar or provider policy).
(b) Per-task budget: yes. (c) Ends when the task ends: yes, up to 8 hours, or delete the session.
(d) One-step revocation a third party can verify: one step yes, third-party verifiable no. (e) Credential
per task: the session is per task, the credential is not (C via IAM split). **Full test case: no.**
Missing: a native payee list, a per-payment cap, any externally verifiable revocation, and task budgets
longer than 8 hours. AWS's own wording sums it up: "Session limits bound how much an agent can spend, not
who it can pay." [S21 line 313].

---

## 5. Additional Coinbase agent-payment products (short blocks)

### 5a. CDP SDK x402 client spend controls (`CdpX402Client`, `spendControls`)

- cdp-sdk@993de49, TypeScript package 1.58.0; x402 support added in 1.53.0 [S30]. Client-side library.
- Fields: `maxAmountPerPayment`, `maxCumulativeSpend` with optional rolling `maxCumulativeSpendWindow`,
  `allowedNetworks`, `allowedAssets`, `allowedPayees`, `onApproachingLimit`, and a pluggable `store`
  [S29 types.ts lines 155 to 177]; it also caps `maxTimeoutSeconds` at 3600 [S29 apply.ts line 41].
- Enforced as a before-payment hook inside the payer's process, ledger in memory by default: "**The
  default implementation is in-memory and process-local.**" [S29 types.ts line 121]. An agent that holds
  the CDP key and calls the signing API directly is not bound by it.
- Default is no cap: "Unlike upstream `x402Client` (which defaults to a $1 per-payment cap),
  `CdpX402Client` disables that upstream default and applies no per-payment cap of its own unless one is
  set via `spendControls`." [S30 line 47, release 1.56.0]. Construction only logs a warning [S29 client.ts
  lines 527 to 537].
- Verdicts: D1 N, D2 N, D3 N (cumulative cap without a window), D4 N, D6 N, D5 X, D7 X (rolling window,
  no end date), D8 CODE (instantiate one client per task), D9 X (nothing to revoke but the process),
  D10 CODE (`onApproachingLimit` callback only), D11 X, D12 CODE (ledger entries, no export), D13 C (one
  config spans the networks listed). All N verdicts are client-side only.

### 5b. Agentic Wallet (MCP "Payments MCP", beta; and the `awal` CLI)

- Docs: the MCP card is tagged Beta [S31 welcome line 16]; installer `npx @coinbase/payments-mcp`;
  embedded wallet with email OTP; USDC on Base, Polygon, Solana; MCP agents can only discover and pay x402
  services, not send or trade [S31].
- Limits: "Max per call" and "Max per session", set by the user in the wallet UI; "Agents respect these
  limits but can't change them." [S31 faq line 53]. Where they are enforced is not documented: the public
  repo coinbase/payments-mcp@dddbf89 is only an installer that downloads a bundle [S32].
- CLI: the welcome page claims per-session and per-transaction caps [S31 cli welcome], but the skills
  reference documents only `x402 pay --max-amount`, a per-call flag the agent itself passes [S33
  references/x402-pay.md line 21]. Treat the CLI's session cap as marketing only (ND).
- Verdicts (MCP, per the FAQ; enforcement point ND): D1 N, D3 N (per session), D2 ND, D4 ND, D5 ND, D6 N (USDC, three chains, vendor-fixed),
  D7 ND, D8 ND, D9 ND, D10 ND, D11 ND, D12 ND, D13 N (one wallet, three chains).

### 5c. Wallet MCP (formerly "Base MCP", remote server)

- Every write is human-approved: "In approval mode, every write call (send, swap, sign, batched calls, and
  any plugin-prepared transaction routed through Wallet MCP) returns an **approval URL** plus a **request
  ID**." [S34 approval-mode line 13]. It is the only execution mode today and "Other modes may be added
  later" [S34 line 9].
- Verdicts: D10 N (per transaction, not threshold-based, so no unattended spend at all); no budget,
  payee, expiry or per-task fields documented: D1 to D9 and D11 to D13 ND.

### 5d. Coinbase for Agents (remote MCP on a Coinbase retail account, OAuth)

- The user connects an agent client by OAuth, picks which portfolios it can use, and revokes under
  Coinbase Account > Security > Connections [S35 lines 65, 111]. x402 payments from the Coinbase USDC
  balance carry a vendor-fixed 5 USDC per-payment cap, USDC on Base only [S35 line 173], and the caller's
  `max_amount` can only tighten it: "A prompt budget is not a server-enforced session or daily limit."
  [S35 line 174]. The page is written as instructions to an agent; it was read as data.
- Verdicts: D1 ND for a principal-set cap (fixed 5 USDC by Coinbase), D2 ND and D3 ND (no principal-set
  session or daily limit is documented, and the quoted line says a prompt budget is not one), D6 N (vendor-fixed), D8 C (portfolio-scoped OAuth grant, so an isolated agent portfolio is the
  budget), D9 N (user revokes the connection in account settings; speed and third-party view ND),
  others ND.

### 5e. CDP embedded wallets: delegated signing (the grant AgentCore's Coinbase connector uses)

- "The end user grants a time-bound delegation from your frontend, and your server can then take actions
  on their account using only your CDP API key and Wallet Secret." [S28]. Scopes: user (all accounts) or
  account (one); one active grant per scope; revocable early by the end user or the developer
  [S28; S1 lines 141 to 155]. The grant carries only `expiresAt`, no amount or payee; those must come
  from project-scope end-user policies (item 1). Revocation emits a `wallet.delegation.revoked` webhook to
  the developer, not a public record [S1 webhook list].
- Verdicts: D7 N, D8 C (grant per account, but the developer's project key does the signing), D9 N with
  no third-party view, D1, D4, D6 via project policy (C), D2 X, D3 X.

### 5f. CDP Mandates (beta, enablement by Coinbase required) and CDP x402 Facilitator (beta)

- Mandates are a merchant-created standing debit authorization with `maxPerAuthorization`, a rolling
  `maxPerPeriod` (day, week, month or year, trailing window), `expiresAt`, customer approval by wallet
  signature, and a customer revoke that removes the on-chain allowance; merchant "cancel" is off-chain and
  leaves the allowance live until the customer revokes [S1 lines 247 to 258, 24825 to 24890]. The payee
  is fixed (the merchant), so it is a pull-payment control, not an agent budget; listed because it is the
  only CDP object here with a native rolling-period cap.
- The x402 Facilitator (`/v2/x402/verify`, `/v2/x402/settle`) is seller-side; nothing in it limits a
  payer [S1 lines 796 to 805].

---

## Sources

- [S1] coinbase/cdp-sdk@993de49 `openapi.yaml` (raw/cdp-sdk/openapi.yaml), cloned 2026-10-08.
- [S2] https://docs.cdp.coinbase.com/wallets/security-and-policies/policy-engine/overview.md, fetched
  2026-10-08, raw/docs.cdp.coinbase.com/cdp-policy-engine-overview.md. Quote: "To manage policies via SDK
  or API, your API key must have the **Non-custodial > Manage (modify policies)** scope enabled under **API
  restrictions > API-specific restrictions**."
- [S3] https://docs.cdp.coinbase.com/api-reference/v2/rest-api/policy-engine/policy-engine.md and
  .../create-policy.md, fetched 2026-10-08, raw/docs.cdp.coinbase.com/cdp-api-ref-*.md (cross-check: same
  evaluation text as S1).
- [S4] https://docs.cdp.coinbase.com/get-started/authentication/cdp-api-keys.md, fetched 2026-10-08,
  raw/docs.cdp.coinbase.com/cdp-api-keys.md.
- [S5] coinbase/cdp-sdk@993de49 `typescript/packages/cdp-sdk/src/policies/evmSchema.ts`, `solanaSchema.ts`.
- [S6] coinbase/spend-permissions@e0004e6 `src/SpendPermissionManager.sol`.
- [S7] coinbase/spend-permissions@e0004e6 `src/SpendRouter.sol`.
- [S8] coinbase/spend-permissions@e0004e6 `README.md`; audits in `audits/`.
- [S9] https://docs.cdp.coinbase.com/coinbase-wallet/improve-ux/spend-permissions.md, fetched 2026-10-08,
  raw/docs.cdp.coinbase.com/cw-spend-permissions.md.
- [S10] https://docs.base.org/base-account/improve-ux/spend-permissions.md (and four other Base URLs, all
  the same "has moved" page), fetched 2026-10-08, raw/docs.base.org/base-*.md.
- [S11] coinbase/agentkit@2e6dbaf `README.md`.
- [S12] coinbase/agentkit@2e6dbaf `typescript/agentkit/src/action-providers/x402/x402ActionProvider.ts`,
  `utils.ts`, `README.md`.
- [S13] coinbase/agentkit@2e6dbaf `typescript/agentkit/src/action-providers/wallet/walletActionProvider.ts`,
  `wallet-providers/cdpEvmWalletProvider.ts`, `wallet-providers/cdpShared.ts`, `package.json`.
- [S14] coinbase/agentkit@2e6dbaf `typescript/agentkit/src/action-providers/cdp/cdpEvmWalletActionProvider.ts`
  (lines 39, 75), `cdpSmartWalletActionProvider.ts` (37, 70), `baseAccount/baseAccountActionProvider.ts`
  (75, 179, 353).
- [S15] https://docs.aws.amazon.com/bedrock-agentcore/latest/devguide/payments.md, fetched 2026-10-08,
  raw/docs.aws.amazon.com/agentcore-payments.md.
- [S16] .../devguide/payments-concepts.md, raw/docs.aws.amazon.com/agentcore-payments-concepts.md.
- [S17] .../devguide/payments-how-it-works.md, raw/docs.aws.amazon.com/agentcore-payments-how-it-works.md.
  Quote: "Within the same wallet hub, the user can grant or revoke permissions to the agent, which allows
  or denies the agent to operate on the user’s newly created crypto wallet." (line 93)
- [S18] .../devguide/payments-create-session.md, raw/docs.aws.amazon.com/agentcore-payments-create-session.md.
- [S19] .../devguide/payments-process-payment.md, raw/docs.aws.amazon.com/agentcore-payments-process-payment.md.
- [S20] .../devguide/payments-iam-roles.md, raw/docs.aws.amazon.com/agentcore-payments-iam-roles.md.
- [S21] .../devguide/payments-security-best-practices.md,
  raw/docs.aws.amazon.com/agentcore-payments-security-best-practices.md. (Two sentences quoted: line 306
  under D4 and in the control model, line 313 in the test case.)
- [S22] .../devguide/payments-observability.md, raw/docs.aws.amazon.com/agentcore-payments-observability.md.
- [S23] https://raw.githubusercontent.com/boto/botocore/develop/botocore/data/bedrock-agentcore/2024-02-28/service-2.json
  (last commit on that path 3cb0216, 2026-09-21), fetched 2026-10-08,
  raw/raw.githubusercontent.com/botocore-bedrock-agentcore-service-2.json.
- [S24] https://raw.githubusercontent.com/boto/botocore/develop/botocore/data/bedrock-agentcore-control/2023-06-05/service-2.json
  (last commit 053554b, 2026-09-30), fetched 2026-10-08,
  raw/raw.githubusercontent.com/botocore-bedrock-agentcore-control-service-2.json.
- [S25] https://aws.amazon.com/about-aws/whats-new/2026/04/amazon-bedrock-agentcore-payments-preview/
  (posted 7 May 2026), fetched 2026-10-08, raw/aws.amazon.com/whats-new-agentcore-payments-preview.html.
- [S26] https://aws.amazon.com/about-aws/whats-new/2026/08/bedrock-agentcore-payments-ga/ (posted 18 Aug
  2026), fetched 2026-10-08, raw/aws.amazon.com/whats-new-agentcore-payments-ga.html.
- [S27] coinbase/cdp-agentcore-template@c635df0 `README.md`, `src/hooks/useDelegation.ts`,
  `src/components/permissions/GrantPermission.tsx`.
- [S28] https://docs.cdp.coinbase.com/wallets/using-wallets/delegated-signing.md, fetched 2026-10-08,
  raw/docs.cdp.coinbase.com/cdp-delegated-signing.md.
- [S29] coinbase/cdp-sdk@993de49 `typescript/packages/cdp-sdk/src/x402/guardrails/types.ts`, `apply.ts`,
  `spend-tracker.ts`, `src/x402/client.ts`.
- [S30] coinbase/cdp-sdk@993de49 `typescript/packages/cdp-sdk/CHANGELOG.md`.
- [S31] https://docs.cdp.coinbase.com/agentic-wallet/welcome.md, .../mcp/faq.md, .../cli/welcome.md,
  .../mcp/welcome.md, .../cli/skills/pay-for-service.md, fetched 2026-10-08,
  raw/docs.cdp.coinbase.com/agentic-wallet-*.md.
- [S32] coinbase/payments-mcp@dddbf89 (installer source only).
- [S33] coinbase/agentic-wallet-skills@70cb79c `skills/agentic-wallet/references/x402-pay.md`.
- [S34] https://docs.cdp.coinbase.com/coinbase-for-agents/wallet-mcp/references/approval-mode.md and
  .../wallet-mcp/skill.md, fetched 2026-10-08, raw/docs.cdp.coinbase.com/wallet-mcp-*.md.
- [S35] https://docs.cdp.coinbase.com/coinbase-for-agents/skill.md, fetched 2026-10-08,
  raw/docs.cdp.coinbase.com/coinbase-for-agents-skill.md.
- [S36] .../devguide/payments-create-instrument.md, payments-getting-started.md, payments-create-manager.md,
  payments-prerequisites.md, payments-fund-wallet.md, payments-troubleshooting.md, payments-processing.md,
  toc-contents.json, raw/docs.aws.amazon.com/.
- [S37] https://docs.cdp.coinbase.com/llms.txt (docs index), raw/docs.cdp.coinbase.com/cdp-llms.txt.

## Blocked or unverifiable

- Nothing was blocked; every fetch returned HTTP 200 with content, and no bot check was met.
- docs.base.org spend-permission pages now return a "has moved" stub [S10]; the content is read from the
  CDP copy [S9].
- The Agentic Wallet MCP server code is not public (the repo is an installer), so where its per-call and
  per-session limits are enforced is unverified.
- AWS API Reference HTML pages were not fetched; the botocore service models were used as the schema.
- Several CDP doc pages and repos contain text addressed to coding agents (a docs-index preamble, skill
  pages, agent-instruction files in the repos). It was treated as data and not acted on.
- Whether CDP end-user typed-data policies apply to the signatures AgentCore requests through delegated
  signing (which would give AgentCore a payee check via `signEndUserEvmTypedData` rules on the
  TransferWithAuthorization `to` field) is plausible from the schema but not documented end to end.
- Upstream `@x402` client default cap (cited only through the cdp-sdk changelog) was not checked in the
  upstream source.

## Most surprising gaps

1. CDP Policy Engine has no notion of time or accumulation at all: no daily cap, no budget, no expiry.
   Per-transaction rules only, and the project policy's accept overrides any account-level reject.
2. Coinbase Spend Permissions cannot name a payee: the spender is the payee. The router that would bind
   a recipient (SpendRouter) was audited in March 2026 but is still "TBD" for deployment, and the consumer
   Coinbase Wallet app does not support spend permissions yet.
3. `CdpX402Client` ships with no per-payment cap by default, deliberately removing the upstream $1 default,
   and its controls are in-process only.
4. AgentKit says in its README that it enforces no caps, approvals or allowlists on transfers; its x402
   per-request cap is skipped on the one-step payment path.
5. AWS AgentCore payments (GA, not preview) enforces only a USD budget and an expiry of at most 8 hours
   per session; AWS states it does not restrict `payTo`, and the budget holds only if the agent's IAM role
   cannot create sessions.

## Possibly missing from the teardown

- Stripe Privy wallet policies, the other AgentCore connector:
  https://docs.privy.io/controls/policies/overview (AWS's own docs send principals there for payee rules).
- Policy in AgentCore (Cedar policies on AgentCore Gateway tool calls), the AWS-side payee control AWS
  recommends: https://docs.aws.amazon.com/bedrock-agentcore/latest/devguide/policy.html
