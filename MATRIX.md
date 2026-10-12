# Teardown: what a principal can actually constrain about an agent's spending

Read 8 October 2026. Public documentation, public specifications and public repositories only; nothing was
signed into, created or run. Every product or standard below is one row; every cell carries a verdict and
the evidence for it. The full evidence, with every source id and quote, is in `notes/` (one file per group
of products), and the re-reads of every native cell are in `notes/spot-checks.md`. Citations of the form
`raw/...` or `file.md:40` point at the copy of a page or repository saved on 8 October; those copies are other
people's work and are not published here, but [SOURCES.md](SOURCES.md) gives each one's URL, fetch time and
sha256 or commit, so every citation can be followed to the live source.

## The question and the test case

What can a principal (a person or a company) constrain, natively, about what its agent may spend? The test
case: "pay only the counterparties this task names, up to this task's budget, until this task ends, and let
me revoke it in one verifiable step." Split into five parts:

- (a) named counterparties only
- (b) a per-task budget
- (c) the authority ends when the task ends
- (d) one-step revocation that a third party (payee or auditor) can verify
- (e) a credential per task, narrower than the agent's main key

## Dimensions

| Code | Dimension |
|---|---|
| D1 | per-transaction cap |
| D2 | per-period cap |
| D3 | total budget (lifetime cap on the grant) |
| D4 | counterparty allowlist |
| D5 | per-counterparty cap |
| D6 | asset, network or merchant-category limits |
| D7 | expiry or time window |
| D8 | per-task key or credential, separate from the agent's main key |
| D9 | revocation: who, how, how fast, and whether a third party can verify it |
| D10 | human step-up or approval above a threshold |
| D11 | binding of a payment to a task, purpose or intent identifier a counterparty or auditor can see |
| D12 | exportable audit record (transactions, and policy allow or deny decisions) |
| D13 | one policy spanning more than one rail |

## Verdict codes

- **N** native: enforced through a documented built-in field, rule type, parameter or setting.
- **C** by configuration: enforced, but only by composing several built-in controls, or by a setting that
  sits outside the agent's credential.
- **CODE** only by writing code: the product offers a hook (custom contract, enforcer, webhook, callback)
  and the principal writes the logic.
- **X** not possible: the documentation, spec or code excludes it.
- **ND** not documented, or could not be verified from public sources.

Qualifiers used in the matrix: **N(client)** enforced only inside the payer's own process, so whoever runs
that process can turn it off; **N(vendor)** documented by the vendor but the enforcing code is not public
and was not verified; **N(pp)** private preview only; **N(spec)** defined in a specification, enforcement
left to implementers. "on-chain" means a third party can read the state or event from a public chain.

## Method and its limits

The 42 were read in nine groups by product type, from API references, OpenAPI files, SDK types, specifications and contract code,
saved every page they relied on, and confirmed every quote against the saved copy. Marketing pages and
press releases were not used to award a verdict; where they were the only source, the cell says so. Every
cell marked N was then re-read against the raw copy or the code before it went into this file (log in
`notes/spot-checks.md`). Limits: nothing was executed, so contract behaviour is read from code, not tested;
"not documented" means not found in the sources listed, not proven absent; vendor documentation moves, so
every claim carries its fetch date or commit.

## The matrix

One row per item; the evidence for every cell is in the item's section below (and in full in `notes/`).
D9 is split by what matters most for the test case: **N+** revocable in one step and a third party can
verify it on a public chain; **N** revocable in one step, but only the principal or the vendor can see it.
"TC" gives the five test-case parts (a) to (e): Y yes, p partly, - no, ? unknown. "Full" is the verdict on
the whole test case.

| # | Item (status, date read 8 Oct 2026) | D1 | D2 | D3 | D4 | D5 | D6 | D7 | D8 | D9 | D10 | D11 | D12 | D13 | TC a b c d e | Full |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
| A1 | Coinbase CDP Policy Engine (GA) | N | X | X | N | C | N | X | ND | C | X | ND | ND | N | Y - - - - | no |
| A2 | Coinbase Spend Permissions (deployed; consumer app "coming soon") | X | N | C | X | C | N | N | N | N+ | X | N | N | X | - Y Y Y Y | no |
| A3 | Coinbase AgentKit (library) | C | X | X | C | X | C | X | C | C | CODE | X | X | X | - - - - - | no |
| A4 | Coinbase CdpX402Client spend controls | N(client) | N(client) | N(client) | N(client) | X | N(client) | X | CODE | X | CODE | X | CODE | C | p p - - - | no |
| A5 | AWS AgentCore payments (GA since 18 Aug 2026) | C | X | N | C | C | C | N | C | N | CODE | ND | N | N | - Y p - p | no |
| A6 | Privy policies (GA) | N | N (72 h, sign methods only) | C | N | N | N | N | N | N | C | ND | N | N (EVM) | Y p Y - Y | no |
| A7 | Turnkey policy engine (GA) | N | ND | ND | N | N | N | N | N | N | N | ND | N | N | Y - Y - Y | no |
| A8a | Circle Agent Wallets | N | N | ND | N | ND | ND | ND | ND | ND | ND | ND | N | N (EVM) | Y p - - - | no |
| A8b | Circle developer-controlled wallets | CODE | CODE | CODE | C | CODE | CODE | CODE | C | C | ND | ND | N | ND | - - - p p | no |
| A9 | Openfort (backend policies; session keys) | N / CODE | ND | ND | N / CODE | N / CODE | N | N (keys) | N (keys) | N+ (keys) | ND | ND | N | N (EVM) | p - Y Y Y | no |
| A10 | Crossmint wallet signer scopes | X | N | N | N | ND | N | N | N | N+ Stellar; N(vendor) EVM | ND | N (Stellar) | N | X | Y Y Y Y Y | yes on Stellar; EVM by vendor statement |
| A10b | Crossmint agent cards (`/unstable/`) | C | X | N | N (one) | C | ND | N | N | N | C | ND | N | C | Y Y Y - Y | no |
| A11 | Lit Vincent framework (idle since Jan 2026) | CODE | CODE | CODE | C | CODE | C | CODE | X | N+ | CODE | ND | ND | C | p - - Y - | no |
| A11b | HeyVincent hosted (server code not public) | N(vendor) | N(vendor) | ND | N(vendor) | ND | N(vendor) | ND | ND | N(vendor) | N(vendor) | ND | ND | ND | Y p - - - | no |
| A12 | Fireblocks TAP (editor API beta) | N | N | C | N (not x402) | C | N | ND | C | C | N | C | N | N | Y p - - p | no |
| A13 | thirdweb MinimalAccount session keys | N | N | N | N / C | N / X | N | N | N | C, on-chain | ND | ND | ND | X | p Y Y p Y | yes for native or one ERC-20 payee |
| B1 | ERC-7715 (Draft, rev. 16 Jan 2026) | ND | ND | ND | ND | ND | N (chain) | N | N | ND | ND | ND | ND | X | - - Y - Y | no |
| B2 | MetaMask Advanced Permissions (shipped) | X | N | N | N (one ERC-20 payee) | C | N | N | N | N+ (user only) | X | C | C | X | p Y Y Y Y | partly |
| B3 | ERC-7710 (Draft) | ND | ND | ND | ND | ND | ND | ND | ND | ND | ND | ND | ND | ND | - - - - - | no |
| B4 | MetaMask Delegation Framework (v1.3.0) | N / C | N | N | N / C | C / CODE | N | N | N | N+ (reversible) | CODE | C | C | X | Y Y Y Y Y | yes, by configuration, one chain |
| B5 | Rhinestone Smart Sessions v1 (beta) | N | C | N | N | C | N | N | N | N+ (contract) | C | C | N | C | Y Y Y Y Y | yes, one chain, contract level |
| B6 | ZeroDev Kernel v3.3 permissions | N | C | C | N | C | N | N | N | N+ (state only) | C | C | N | C | Y p Y Y Y | partly |
| B7 | Biconomy (uses B5) | N | C | N | N | C | N | N | N | C | CODE | C | N | C | Y Y Y p Y | yes at contract level |
| B8 | Safe Allowance module | X | N | N | X | X | N | X | N | N+ | C | C | N | X | - Y - Y Y | no |
| B9 | Zodiac Roles Modifier v2 | N | N | N | N | C | N | CODE | N | N+ | C | C | N | X | Y Y - Y Y | no (expiry needs code) |
| C1 | Visa Intelligent Commerce (pilot) | N | C | C | ND | ND | C | N | N | N | N | ND | C | ND | ? p Y - Y | no |
| C2 | Mastercard Agent Pay + MDES spend controls (issuer-set) | N | N | N | N | X | N | ND | ND | N | ND | ND | C | ND | p p ? - - | no |
| C3 | American Express ACE (specs under NDA) | ND | ND | ND | ND | ND | ND | ND | ND | ND | ND | ND | ND | ND | ? ? ? ? ? | unknown |
| C4 | Stripe Issuing for agents | N | N | N | CODE | CODE | N | C | N | N | CODE | ND | N | ND | - Y p - Y | no |
| C5 | Stripe Shared Payment Tokens (preview) | C | N(pp) | N | N (one seller) | C | N | N | N | N (payee sees it, inside Stripe) | CODE | N | C | X | p Y Y p Y | close, one seller per token |
| C6 | ACP delegate payment allowance (beta) | N | X | N | N (one merchant) | C | N | N | N | ND | ND | N | ND | X | p Y Y - Y | no |
| C7 | Stripe agent toolkit and MCP | C | C | ND | ND | ND | ND | C | C | N | N | ND | N | ND | - - - - p | no |
| C8 | Ramp funds and Agent Cards | N | N | N (soft) | N | C | N | N | C | N | C | ND | N | C | Y Y Y - p | no |
| C9 | Brex cards and spend limits | C | N | N (soft) | N (by name) | C | C | N | N | N | ND | ND | N | C | Y Y Y - Y | no |
| C10 | PayPal Agent Toolkit | ND | ND | ND | ND | ND | ND | ND | ND | ND | ND | ND | ND | ND | - - - - - | no |
| D1 | Skyfire / KYAPay | C | ND | N | N (per token) | C | ND | N (max 24 h) | N | X | C | N | N | ND | p p p - Y | no |
| D2 | Payman (archived docs only) | N | N | C | C | ND | C | ND | C | ND | N | N | N | ND | p - - - - | no |
| D3 | Nekuda (SDK only) | ND | ND | ND | ND | ND | ND | ND | ND | ND | ND | ND | ND | ND | ? ? ? ? ? | unknown |
| D4 | AP2 v0.2 (Draft, at FIDO) | N(spec) | C | N(spec) | N(spec) | C | N(spec) | N(spec) | N(spec) | X | C | N(spec) | N(spec) | N(spec) | Y p Y - Y | no |
| D5 | x402 v2 and reference client | N(client) | CODE | CODE | CODE | CODE | N(client) | N (per payment) | ND | ND | CODE | N | CODE | N(client) | - - - - - | no |
| D6 | Nevermined delegations | C | C | N | N (one plan) | C | C | N | N | N (via Nevermined) | C | N | N | N (x402 and MPP) | p Y Y p Y | nearly |
| D7 | Kite (whitepaper; testnet docs) | ND | N(vendor) | N(vendor) | N(vendor) | ND | ND | N(vendor) | N(vendor) | N(vendor) | ND | ND | ND | ND | claimed | claimed, unverified |

Also read and summarized in the sections (not given rows): Coinbase Agentic Wallet MCP, Wallet MCP,
Coinbase for Agents, CDP delegated signing and CDP Mandates (A4); Stripe Link Agent Wallet (C10); Mastercard
Verifiable Intent v0.1 (C2).

## Can anything express the full test case?

**Short answer: only smart-account delegation systems, each on one EVM chain (or Stellar) at a time, and
each only by composing several modules correctly.** Nothing off chain lets a third party verify a
revocation, and nothing expresses the test case across rails.

### Items that express all five parts

| Item | How | What still falls short |
|---|---|---|
| B4 MetaMask Delegation Framework | Delegation to a per-task key with AllowedCalldataEnforcer or AllowedTargetsEnforcer (payees), ERC20TransferAmountEnforcer (budget), TimestampEnforcer (end), `disableDelegation` (revoke). Verdict C: four to six enforcers, chosen and ordered by the principal. | Revocation is reversible (`enableDelegation`); a principal cannot disable a child delegation its agent signed, only its own link; per-payee caps need one delegation per payee; the DelegationManager owner can pause every redemption; one chain. |
| B5 Rhinestone Smart Sessions v1 | A session per task with an ArgPolicy or UniActionPolicy recipient rule, ERC20SpendingLimitPolicy, TimeFramePolicy; `removeSession` emits `SessionRemoved`. | Beta; on 8 Oct the vendor's app SDK had no self-service revoke and pointed integrators to support (a revoke is documented since 12 Oct, see B5 D9); the SDK defaults to sudo; a multi-chain grant must be removed chain by chain. |
| B7 Biconomy | Same contracts as B5. | The documented agent path has no revoke step and defaults unconfigured actions to sudo. |
| A13 thirdweb MinimalAccount | Session spec per key with transfer or call policies, lifetime limits, `expiresAt`. | Only native-token payees or one ERC-20 payee per token per session; no revoke function (replace the session); the SDK defaults new keys to wildcard. |
| A10 Crossmint wallet scopes | Signer per task with `recipients`, lifetime `spendingLimit`, `expiresAt`; signer removal. | Confirmed in public code on Stellar only; the EVM and Solana contracts are not public; no per-transaction cap; coverage of x402 typed-data signatures not documented. |

Kite (D7) claims the whole test case in its whitepaper, on its own chain; the public developer docs show a
testnet vault with budget, time window and provider list, and the contract source is not public.

### Items that miss exactly one or two parts

| Item | Has | Missing |
|---|---|---|
| A2 Coinbase Spend Permissions | budget, end, per-task spender key, on-chain revocation | a payee list: funds go only to the spender; the SpendRouter that would fix one recipient is undeployed |
| B2 MetaMask Advanced Permissions | budget, expiry, session account, on-chain revocation | more than one ERC-20 payee per grant; revocation is user-only, from the MetaMask client |
| B9 Zodiac Roles v2 | payees with per-payee allowances, budgets, on-chain revocation | expiry (needs a custom condition contract; time-bound memberships only on an unreleased branch) |
| B8 Safe Allowance module | budget, delegate per task, on-chain revocation | any payee restriction and any expiry |
| D6 Nevermined | budget, duration, one seller plan, per-task delegation, immediate revocation | several payees in one delegation; revocation visible only by asking Nevermined |
| C5 Stripe SPT | one seller, budget, expiry, per-task token, revocation the payee can see | several payees per token; visibility outside Stripe; GA status |
| C9 Brex, C8 Ramp | merchant list (by name, or vendor id), lifetime limit, lock date, card per task | revocation a third party can check; limits that cannot be exceeded (soft limits, overage) |
| A5 AWS AgentCore payments | USD budget per session, expiry up to 8 hours, one-call delete | any payee restriction, per-task credential, third-party view |

### Items that look like mandates but cannot be revoked

AP2 v0.2 (D4), the ACP allowance (C6), Mastercard Verifiable Intent v0.1 (C2) and Skyfire KYAPay (D1) all
carry payee, amount and expiry constraints in a signed object, and none defines revocation: AP2 puts
management of delegated mandates out of scope, ACP defines no revoke operation, Verifiable Intent "does not
define a credential-layer revocation protocol", and Skyfire says deactivating an account "does not void
tokens that were already issued". Each ends only at expiry or single use.

### What no item does

- **One policy across rails (D13) together with the rest.** The widest single policies are Fireblocks
  (chains plus exchange and fiat accounts, no card), AWS AgentCore (EVM and Solana, x402 and MPP, crypto
  only), Ramp and Brex (card, reimbursement, bill pay; Ramp's x402 wallet sits outside), Nevermined (x402
  and MPP), and AP2 on paper (an instrument list that may mix card and UPI). None combines that with a
  payee list, a task budget and verifiable revocation.
- **Third-party-verifiable revocation off chain.** Every card, bank and hosted-wallet product revokes in
  one call that only the principal, the issuer or the vendor can see. The two partial exceptions are Stripe
  SPT (the payee gets a webhook and a `deactivated_reason`, inside Stripe) and Nevermined (a seller learns
  of it through Nevermined's verify).
- **A task identifier the payee can see, defined as such.** What exists links a payment to a checkout or a
  grant, or is a free field the principal may fill: Spend Permission `extraData`, SPT `shared_metadata`,
  Skyfire `buyerTag`, ACP `checkout_session_id`, AP2 `transaction_id` (the hash of the merchant's checkout),
  Nevermined's delegation JWT, the x402 payment identifier. Card networks carry agent identity to the
  merchant, not task identity.
- **A grant that ends when the task ends**, rather than at a timestamp. Every expiry found in the items above
  is a clock time. Outside them, Ant International's Agentic Mobile Protocol spec defines a `finished` mandate
  state for a completed task, inside Alipay+ only (see `novelty.md`).

## Gaps worth printing

Each is verified in the item's section and in `notes/spot-checks.md`.

1. **Revocation nobody else can check, and mandates nobody can revoke.** Off chain, every product revokes in
   one call that only the principal or vendor sees. The signed-mandate designs (AP2 v0.2, ACP, Mastercard
   Verifiable Intent v0.1, KYAPay) define no revocation at all. On chain, where a third party can check,
   MetaMask's `disableDelegation` can be undone with `enableDelegation`, Rhinestone's app SDK had no
   self-service revoke on 8 Oct (one is documented since 12 Oct, see B5), ZeroDev's nonce revocation emits no event, and thirdweb has no revoke function.
2. **The payee is the weakest dimension.** Coinbase Spend Permissions can only pay the spender; AWS
   AgentCore "does not enforce `payTo` restrictions server-side"; the Safe Allowance module never checks
   the recipient; MetaMask's ERC-20 payee rule takes one address and throws on two; Stripe Issuing has no
   GA merchant-ID allowlist; CDP's address rule matches the token contract, not the payee, unless the
   principal writes a calldata rule; Brex matches merchants by name; Mastercard's merchant-ID list can be
   set only by the issuer. On the x402 path, Fireblocks rules for typed messages take no destination, and
   Crossmint does not say whether its scopes bound typed-data signatures.
3. **Budgets are stateless, short, or soft.** CDP's Policy Engine has no time or cumulative rule at all;
   Privy's cumulative caps last at most 72 hours and miss sends, x402 signatures and Solana; Turnkey
   documents no cumulative limit; AP2 requires a running total but assigns no role to keep it, and its
   sample keeps the ledger in a file written by the shopping agent; card limits lag (Stripe, up to 30 s) or
   flex (Ramp overage, Brex soft limits); Mastercard's lifetime budget cannot sit beside any other limit.
4. **Defaults are open.** Rhinestone's and Biconomy's SDKs install a sudo policy when none is given;
   thirdweb's SDK makes a new session key a wildcard unless told otherwise; `CdpX402Client` removes the
   upstream $1 cap; a hosted Vincent wallet has no policy until a human claims it; Openfort's backend send
   path skips the policy engine; Vincent's framework installs the agent key with sudo authority.
5. **The authority to mint a per-task credential is the authority to loosen all of them.** Stripe
   restricted keys, Ramp `funds:write`, Brex `cards`, AWS's session-writing role and the CDP
   `policies#manage` scope all cover both creating a narrow credential and widening any credential.
6. **Several products have changed since they were last widely described.** AWS AgentCore payments is GA (18 Aug
   2026), not preview. ERC-7715 no longer defines any permission type and the method is now
   `wallet_requestExecutionPermissions`. AP2 v0.2 has Checkout and Payment Mandates, not Intent and Cart.
   Payman's and Nekuda's agent-payment docs are gone. ZeroDev deleted its v3 policy sources from the plugins
   repo in January 2026. Lit's hosted Vincent docs and dashboard were down on 8 Oct 2026.

## A. Crypto wallets and policy engines

Full evidence: `notes/coinbase-aws.md`, `notes/wallets-1.md`, `notes/wallets-2.md`.

### A1. Coinbase CDP Server Wallets (v2) and the CDP Policy Engine

GA (OpenAPI tags carry `x-slo-tier: ga`). The principal (the CDP project) writes a policy of up to 100
accept or reject rules over signing and sending operations; Coinbase's server evaluates each request
statelessly before it signs. One project policy plus at most one policy per account; the project policy's
decision is final. Source: coinbase/cdp-sdk@993de49 `openapi.yaml` (cloned 8 Oct 2026), docs at
https://docs.cdp.coinbase.com/wallets/security-and-policies/policy-engine/overview.md (fetched 8 Oct 2026).

| Dim | Verdict | Evidence |
|---|---|---|
| D1 | N | `ethValue`, `solValue`, `splValue`, `evmData` (ERC-20 `transfer.value`) and `netUSDChange` in cents (openapi.yaml, Rule.oneOf, 29299 to 31650). |
| D2 | X | No time, counter or cumulative criterion exists in any of the 22 rule types; evaluation is per request. |
| D3 | X | Same reason. |
| D4 | N | `evmAddress in [...]`, 300 addresses per criterion (openapi.yaml:29344). Trap: `evmAddress` compares the transaction's `to`, which for a USDC payment is the token contract; a token payee list needs an `evmData` rule on the transfer's `to` argument. |
| D5 | C | One accept rule per payee with its own value bound; per transaction only. |
| D6 | N | Token contract, `mintAddress`, `evmNetwork` / `solNetwork` (send operations only). No merchant category (not a card product). |
| D7 | X | No time criterion. |
| D8 | ND | A server account per task can carry its own policy, but the API key and Wallet Secret that sign are project-wide; no per-account key scoping is documented. |
| D9 | C | Who: a key with `policies#manage` or a Portal user. How: edit, detach or delete the policy, or rotate keys. How fast: not stated. Third party: no; policies are private. |
| D10 | X | `action` is only `accept` or `reject`. |
| D11 | ND | No field carries a task or purpose id to the payee. |
| D12 | ND | Transaction webhooks yes; no documented log or export of policy accept or reject decisions. |
| D13 | N | One project policy holds EVM and Solana rules and many EVM networks. Crypto only. |

Test case: (a) yes, (b) no, (c) no, (d) no, (e) no. Not expressible.

### A2. Coinbase Spend Permissions (Coinbase Smart Wallet)

Contract `SpendPermissionManager` deployed on eight mainnets; the consumer Coinbase Wallet app says support
is "coming soon" (https://docs.cdp.coinbase.com/coinbase-wallet/improve-ux/spend-permissions.md, line 18,
fetched 8 Oct 2026). The principal's smart account signs an EIP-712 `SpendPermission {account, spender,
token, allowance, period, start, end, salt, extraData}`; the contract checks every spend on chain. Source:
coinbase/spend-permissions@e0004e6 `src/SpendPermissionManager.sol`.

| Dim | Verdict | Evidence |
|---|---|---|
| D1 | X | No per-spend field; one spend may take the whole period allowance. |
| D2 | N | `allowance` per `period` seconds, fixed windows from `start` (SpendPermissionManager.sol:29-49, 516-551). |
| D3 | C | Set `period` at least `end - start`, so the single window becomes a lifetime cap. |
| D4 | X | `spend` transfers from the account to the spender itself (SpendPermissionManager.sol:420-426); there is no payee field. A SpendRouter that forwards to one recipient named in `extraData` is in the repo, audited March 2026, and listed as "`SpendRouter`: TBD" for deployment (README.md:32). |
| D5 | C | Only when each payee is itself the spender, one permission per payee (batch-approvable). |
| D6 | N | One `token` per permission; one chain per EIP-712 domain. |
| D7 | N | `start` inclusive, `end` exclusive, checked on every spend. |
| D8 | N | `spender` is any address the principal chooses; a fresh key plus `salt` per task. |
| D9 | N | Who: the account (`revoke`) or the spender (`revokeAsSpender`). How: one transaction. How fast: from the including block. Third party: yes, `SpendPermissionRevoked(hash)` event and public `isRevoked` (SpendPermissionManager.sol:138, 392-411, 485). |
| D10 | X | Over-allowance spends revert; a larger grant needs a new owner signature. |
| D11 | N | `extraData` and `salt` are signed and emitted in `SpendPermissionApproved`; each `SpendPermissionUsed` carries the permission hash. Free-form, no schema. |
| D12 | N | Approval, use and revocation are chain events. Denials revert and leave nothing. |
| D13 | X | One token on one chain per permission. |

Test case: (a) no, unless the payee is the spender; (b) yes; (c) yes; (d) yes; (e) yes. Not expressible:
the one missing piece is the payee list.

### A3. Coinbase AgentKit

Open-source library (coinbase/agentkit@2e6dbaf, TypeScript package 0.11.0). It enforces no spend control
on transfers; its README says so: "AgentKit does not gate transfers behind human approval, enforce spend
caps, or allowlist destinations." (README.md:200). Transfers go straight to the wallet provider
(walletActionProvider.ts:101-125), so limits come from the CDP Policy Engine (A1) or Spend Permissions
(A2). Its x402 action has an in-process `maxPaymentUsdc` (default 1.0) and a service URL allowlist, checked
only on the two-step payment path (x402ActionProvider.ts:416; the one-step path at :572 does not call it).
D1 C, D4 C (URLs only), D6 C; D2, D3, D5, D7, D11, D12, D13 X; D8 and D9 C (inherited from A2); D10 CODE.
Test case: none of (a) to (e) by itself.

### A4. Coinbase CDP x402 client spend controls (`CdpX402Client`)

cdp-sdk@993de49 TypeScript 1.58.0. `SpendControls` has `maxAmountPerPayment`, `maxCumulativeSpend` with a
rolling window, `allowedNetworks`, `allowedAssets`, `allowedPayees` and an `onApproachingLimit` callback
(src/x402/guardrails/types.ts:150-180). The ledger is "in-memory and process-local" (types.ts:121), and the
client deliberately removes the upstream $1 per-payment default (CHANGELOG 1.56.0). D1, D2, D3, D4, D6
N(client); D5 X; D7 X (rolling window, no end date); D8 CODE (one client per task); D9 X (nothing to
revoke); D10 CODE; D11 X; D12 CODE; D13 C. Every native cell runs in the payer's process.

Other Coinbase agent surfaces read (details in `notes/coinbase-aws.md` section 5): Agentic Wallet MCP
(beta; "Max per call" and "Max per session" set by the user, enforcement location not documented); Wallet
MCP (every write returns an approval URL, so D10 N but no unattended spend at all); Coinbase for Agents
(fixed 5 USDC per payment, "A prompt budget is not a server-enforced session or daily limit.");
CDP embedded-wallet delegated signing (a time-bound grant with only `expiresAt`); CDP Mandates (beta,
merchant pull payments with `maxPerAuthorization`, rolling `maxPerPeriod`, `expiresAt`, fixed payee).

### A5. Amazon Bedrock AgentCore payments (AWS)

**Generally available since 18 August 2026** ("AgentCore payments is now generally available in Amazon
Bedrock AgentCore", aws.amazon.com what's new, posted 2026-08-18; preview announced 2026-05-07). Rails:
x402 and the Machine Payments Protocol, USDC, through Coinbase CDP or Stripe Privy embedded wallets; no
card rail. Per interaction the developer creates a PaymentSession; AWS checks the session budget before
the wallet signs. Sources: botocore `bedrock-agentcore` service-2.json (develop, last change 3cb0216,
2026-09-21), developer guide pages under https://docs.aws.amazon.com/bedrock-agentcore/latest/devguide/
(fetched 8 Oct 2026).

| Dim | Verdict | Evidence |
|---|---|---|
| D1 | C | `SessionLimits` has only `maxSpendAmount`; a per-payment cap needs the wallet provider's policy (A1 or A6). |
| D2 | X | A session is one budget over 15 to 480 minutes; no recurring period. |
| D3 | N | `limits.maxSpendAmount` in USD per session (service-2.json, SessionLimits). |
| D4 | C | "AgentCore payments does not enforce `payTo` restrictions server-side, so your application must validate the address before calling the `ProcessPayment` API." (payments-security-best-practices.md:306). Only via Gateway Cedar policies or the wallet provider. |
| D5 | C | Only through the wallet provider, per transaction. |
| D6 | C | Instrument network ETHEREUM or SOLANA; no principal-set asset or chain filter in Payments itself. |
| D7 | N | `expiryTimeInMinutes`, "Must be between 15 and 480 minutes." (service-2.json). |
| D8 | C | The session is per task, the credential is an IAM role; AWS warns that a role holding both `CreatePaymentSession` and `ProcessPayment` "can bypass payment limits by creating new sessions with elevated budgets" (payments-iam-roles.md:188). |
| D9 | N | `DeletePaymentSession` by the management role, one call; latency not stated. Third party: no (IAM-protected state, logs in the principal's own account). |
| D10 | CODE | No approval step in Payments. |
| D11 | ND | `userId` and `agentName` are for observability; nothing documented reaches the payee. |
| D12 | N | CloudWatch vended logs, X-Ray spans with amount, remaining budget and `payTo`, CloudTrail. |
| D13 | N | One USD session budget is independent of instrument, so it spans EVM and Solana instruments, both connectors, x402 and MPP (read from the schema). Crypto only. |

Test case: (a) no, (b) yes, (c) yes but at most 8 hours, (d) one step, not verifiable, (e) session yes,
credential no. AWS's own line: "Session limits bound how much an agent can spend, not who it can pay."
(payments-security-best-practices.md:313).

### A6. Privy server wallets and policies

GA (manual approvals are Enterprise). Policies on a wallet and an "override" policy per additional signer,
evaluated in Privy's enclave before signing. Sources: https://api.privy.io/v1/openapi.json and
https://docs.privy.io/controls/policies/ pages (fetched 8 Oct 2026).

| Dim | Verdict | Evidence |
|---|---|---|
| D1 | N | `lte` on transaction value, decoded calldata amounts, Solana amounts, typed-data fields and transfer `source.amount`. |
| D2 | N, narrow | Aggregations (`sum`, rolling 1 to 72 h): "Minimum value is `3600` (1 hour), and maximum is `259200` (72 hours)." (stateful-policies.md:150). They count only `eth_signTransaction` and `eth_signUserOperation` (recipes_using-stateful-policies.md:270), so sends, x402 typed-data signatures and Solana are not counted; 10 aggregations per app; totals recorded after signing. |
| D3 | C (72 h max) | Only as a 72 h aggregation on a grant that itself ends within 72 h. |
| D4 | N | `in` and `in_condition_set` on `to`, calldata recipient, Solana `Transfer.to`, typed-data recipient. |
| D5 | N | Per transaction by one rule per payee; per period by an aggregation grouped by recipient (stateful-policies.md:302). |
| D6 | N | `chain_id`, token contract, SPL mint, transfer `source.asset` and `source.chain`. |
| D7 | N | `system.current_unix_timestamp` compared with `lt` and `gte`; no hours of day. |
| D8 | N | A key quorum per task added as a signer with an override policy. The override replaces the wallet policy; the add-signers docs say that without one "no policies will apply to the signers requests" (add-signers.md:48), while the Swift and Android docs say the wallet policy applies. |
| D9 | N one step, ND third party | Remove the signer or delete the key quorum; device grants: refresh tokens die at once, the access token "remains valid until its natural expiry of up to 15 minutes" (agent-authorization.md:385). Nothing a payee can check. |
| D10 | C | Allow and deny only; step-up by routing to an owner quorum that includes a human, or Enterprise manual approvals. |
| D11 | ND | `reference_id` stays inside Privy. |
| D12 | N transactions, ND deny log | Transactions API and webhooks; rejections logged only for wallet action APIs. |
| D13 | N (EVM chains), X (chain types) | One `ethereum` policy covers every EVM chain; a policy has one `chain_type`. |

Test case: (a) yes, (b) partly (72 h, sign methods only), (c) yes, (d) not verifiable, (e) yes. Not
expressible.

### A7. Turnkey policy engine

GA. Organization-wide policies (`effect`, `consensus`, `condition`, optional `time`) evaluated in an
enclave, with optional signed App Proofs of each outcome. Sources: https://docs.turnkey.com/features/policies/
pages and https://docs.turnkey.com/public_api.swagger.json (fetched 8 Oct 2026); tkhq/sdk@1363a6d.

| Dim | Verdict | Evidence |
|---|---|---|
| D1 | N | `eth.tx.value`, decoded ERC-20 args, Solana and SPL amounts, EIP-712 fields; Turnkey's own wording is "Bound transaction values per-signing" (agentic-wallets.md:80). |
| D2 | ND | Nothing in the policy language or docs. A velocity-control API appears in the SDK's generated client but has no path in the docs swagger and no docs page. |
| D3 | ND | Same. |
| D4 | N | `eth.tx.to in [...]`, calldata recipient, Solana transfer recipients. |
| D5 | N | One condition per payee joined with `||`, each with its own amount bound (per signing). |
| D6 | N | Chain id, EIP-712 domain, token contract, SPL mint. |
| D7 | N | Top-level `time` field, one-shot windows and recurring `CronSpan` windows (time-based-policies.md:24, 62-64). |
| D8 | N | An API-only user per task with its own key (optional expiry) and policies naming it. Limit: 5 policies per organization below Enterprise (resource-limits.md:37). |
| D9 | N one step, C third party | Delete the user, key or policy. Speed not stated. A signed App Proof of the decision exists, but only if the principal hands it over. |
| D10 | N | `consensus` requiring both the agent and a named human above a value; the activity waits for approval. |
| D11 | ND | Nothing reaches the payee. |
| D12 | N | Activities by status (rejected included), `get_policy_evaluations` with per-policy outcome, webhooks. |
| D13 | N | One expression can test EVM and Solana payloads (Turnkey's agentic payments guide nonetheless says they need separate policies). |

Test case: (a) yes, (b) no documented cumulative control, (c) yes, (d) only via App Proofs the principal
shares, (e) yes. Not expressible. The root quorum bypasses every policy (overview.md:67).

### A8. Circle

Two products. **Circle Agent Wallets** (CLI-driven user-controlled wallets): per-transaction, daily,
weekly and monthly rolling caps and recipient or contract allowlists per wallet, mainnet only, enforced by
Circle's backend; caps cover stablecoin transfers only (CLI 1.2.0 source: native and wrapped-asset policies
"are planned in a follow-up PR", limit-set.ts:33-34). No expiry, no per-task credential (one 28-day login
session per email), no server-side revocation documented (`circle wallet logout` clears local files). D1,
D2, D4 N; D3, D5, D6, D7, D8, D9, D10, D11 ND; D12 N (transactions); D13 N (one budget across nine EVM
chains). **Circle developer-controlled wallets**: the Wallets API has no spend-policy object; D1 to D7
CODE (Compliance Engine screening and an entity-wide blocklist only); Gateway delegates give an on-chain
revocable per-task key with a full allowance, and "This revocation is not respected for burn intents that
have already been" signed (gateway contract interfaces page:319). Sources:
https://developers.circle.com/agent-stack/ pages, developer-controlled-wallets OpenAPI, npm
@circle-fin/cli 1.2.0 (fetched 8 Oct 2026). Test case: not expressible in either.

### A9. Openfort

Backend wallets (custodial, TEE) under project or account policies with value, address, network, calldata
and Solana criteria; embedded smart accounts can grant EIP-7715 session keys. The trap: a backend
`sendTransaction()` reaches the policy engine only as a hash, and "Rules on `signEvmTransaction`,
`sendEvmTransaction` and `sponsorEvmTransaction` do not run for a send" (configuration/policies.md:59), so
the documented agent flow relies on a pre-flight `policies.evaluate()` the agent itself calls. Session keys
carry contracts, expiry and a use count, and "`gas-limit`, `rate-limit`, `token-allowance` and
`native-token-transfer` are not supported by embedded wallets" (user-and-server-signers.md:79). D1, D4, D5
N on the sign path, CODE on the send path; D2, D3 ND (X for session keys); D6 N; D7 N (session keys only);
D8 N (session keys); D9 N and on-chain verifiable for session keys (`SessionKeyRevoked`,
openfort-contracts@b0ed06c BaseOpenfortAccount.sol:258-265), not for policies, and the cross-app wallet SDK
"does not forward `wallet_revokePermissions`" (wallet_revokePermissions.md:14); D10, D11 ND; D12 N
(transactions); D13 N (EVM chains). Test case: not expressible (no amount limit on session keys).

### A10. Crossmint (agent wallet signer scopes; agent cards)

Wallet signer scopes: type `transfer` only, one token on one chain, cumulative `spendingLimit` with
optional reset `interval`, optional `recipients`, signer-level `expiresAt`
(https://docs.crossmint.com/wallets/guides/signers/scopes.md, lines 21, 493, 517, 543, fetched 8 Oct 2026).
Enforcement is stated as on-chain; it is confirmed in public code only for Stellar
(Crossmint/stellar-smart-account@bee3339: `revoke_signer` publishes `SignerRevokedEvent`, account.rs:214-242).
The EVM and Solana policy contracts are not public. Agent cards (order intents, under `/unstable/`): total
`amount`, required `expiresAt`, optional single `merchant`, user approval per intent; card networks
enforce amount and merchant "only for `agentic-token` rails" (create-agent-card.md:188).

| Dim | Verdict | Evidence |
|---|---|---|
| D1 | Wallet X; card C | Scopes have only a cumulative limit; cards: one intent per purchase. |
| D2 | Wallet N | `spendingLimit.interval` in seconds. |
| D3 | Wallet N; card N | Omit `interval` for "an absolute, non-resetting cap" (scopes.md:493); intent `amount`. |
| D4 | Wallet N; card N (one merchant) | `recipients` array (scopes.md:517); intent `merchant`, network-enforced only on agentic-token rails. |
| D5 | Wallet ND; card C | Whether two scopes on one token with different recipients are accepted is not documented. |
| D6 | Wallet N | One token on one chain per scope. |
| D7 | N | Signer `expiresAt` (REST only); intent `expiresAt` required. |
| D8 | N | Signer key per agent or task; "Create one per agent, per task, or per purchase." (agents/cards/overview.md:57). |
| D9 | N; third party on Stellar only | Remove the signer via the recovery method; cancel the intent with one DELETE. Verifiable on Stellar (event, `has_signer`); EVM and Solana ND; cards ND. |
| D10 | Wallet ND; card C | User approves each intent at creation; no threshold. |
| D11 | N on Stellar only | Transfer `memo` is Stellar-only. |
| D12 | N transactions, ND denials | Transactions API, webhooks for success and failure. |
| D13 | Wallet X; card C | One scope is one token on one chain; one intent can mint on several card rails of one saved card. |

Test case: (a) yes, (b) yes, (c) yes by timestamp, (d) yes on Stellar from code, EVM and Solana by vendor
statement, (e) yes. **Expressible on the Stellar wallet path; on EVM only if the unpublished contract
behaves as documented.** Open question: whether scopes bound EIP-712 typed-data (x402) signatures is not
documented.

### A11. Lit Protocol Vincent

The open framework (LIT-Protocol/Vincent@1fa0a48, last pushed 31 Jan 2026) installs the agent's PKP on
the user's smart account with an unrestricted policy (`toSudoPolicy({})`, completeInstallation.ts:230)
and puts every limit in off-chain Lit Actions. The only published value policy (daily USD) is declared by
no published ability; the transfer ability supports only a send count. One agent account per user per
app, so D8 X. Revocation is an on-chain registry call (`AppVersionUnPermitted`, LibVincentUserFacet.sol:38),
so D9 N and third-party readable, with the caveat that the sudo key stays installed. The hosted docs timed
out and the dashboard returned HTTP 503 `DEPLOYMENT_PAUSED` on 8 Oct 2026. The separate hosted product at
heyvincent.ai documents per-transaction and rolling USD limits, address and token allowlists and Telegram
approval above a USD threshold in its public skill files (HeyVincent-ai/agent-skills@76ae07b
wallet/SKILL.md:241-250), but its server code returned 404, so those cells are N(vendor), and "Before the
wallet is claimed, the agent can operate without policy restrictions." (SKILL.md:250). Test case: not
expressible in either.

### A12. Fireblocks Transaction Authorization Policy

Workspace-wide ordered rules matched on initiator, asset, source, destination, single-transaction amount,
amount over a time period, with ALLOW, BLOCK or 2-TIER approval verdicts; enforced by Fireblocks' signing
service. Policy Editor API endpoints are labelled beta (openapi.yaml:7308). Agent-specific material is a
reference x402 Agent whose spending page says "The agent enforces no spending limit of its own."
(x402-agent-spending-controls.md:14). Sources: https://swagger.fireblocks.com/openapi.yaml and
https://developers.fireblocks.com/ pages (fetched 8 Oct 2026).

| Dim | Verdict | Evidence |
|---|---|---|
| D1 | N | `amountScope: SINGLE_TX` (openapi.yaml:56480). |
| D2 | N | `TIMEFRAME` with a period (openapi.yaml:56481). |
| D3 | C | No lifetime field; the vault balance is the ceiling. |
| D4 | N (transfers), ND (x402) | Whitelisted destinations with Admin Quorum approval. The x402 Agent signs `TYPED_MESSAGE` requests, and Typed Message rules "should not include a destination limitation" (TAP reference:85). |
| D5 | C | One rule per destination, or the per-destination accumulation mode. |
| D6 | N | Asset per rule, assets are per network. |
| D7 | ND | No validity window on rules or API users found. |
| D8 | C | A dedicated API user and vault per agent, created by admins under quorum. |
| D9 | C | Admins disable the API user or publish a policy change; workspace audit log only. |
| D10 | N | 2-TIER verdict, approval groups and thresholds, approvals in the mobile app. |
| D11 | C (auditor), ND (payee) | `note`, `externalTxId`, `customerRefId` stay in the workspace. |
| D12 | N | Audit log API including `Transaction_BlockedByPolicy`; blocked transactions carry the rule number. |
| D13 | N | One workspace policy covers all assets and networks plus exchange and fiat-account sources. No card. |

Test case: (a) yes for transfers, (b) C, (c) no, (d) no, (e) C. Not expressible.

### A13. thirdweb session keys (added)

Chosen as the most used wallet SDK not covered elsewhere. EIP-7702 `MinimalAccount`
(thirdweb-dev/contracts-modular-account@e7222af src/7702/MinimalAccount.sol, src/lib/SessionLib.sol): an
owner-signed `SessionSpec` per session-key address with `expiresAt`, call policies (target, selector,
`maxValuePerUse`, `valueLimit`, argument constraints) and native transfer policies; usage limits are
Unlimited, Lifetime or a fixed-period Allowance. D1, D2, D3, D6, D7, D8 N; D4 N (native) and C (ERC-20, one
payee per token per session); D5 N (native), X (ERC-20); D9 C (no revoke function; replace the session or
wait for expiry; state and `SessionCreated` are public); D10, D11, D12 ND; D13 X. The SDK sets
`isWildcard: grantFullPermissions ?? true` (thirdweb-dev/js@3b6c18d createSessionKey.ts:126) and the
contract skips all checks for a wildcard session, so a caller who passes policies but omits the flag gets
an unrestricted key. Test case: expressible for native-token payees or a single ERC-20 payee, with
revocation by replacement.

## B. Smart-account standards and modules

Full evidence: `notes/sa-delegation.md`, `notes/sa-modules.md`. All of these enforce in contract code on
one EVM chain at a time; a denied action reverts and leaves no on-chain record, so no item here has a deny
log, and none has one budget shared across chains.

### B1. ERC-7715 (now `wallet_requestExecutionPermissions`)

Draft. ethereum/ERCs@ee5363b `ERCS/erc-7715.md`, last changed by 2adc378 (16 Jan 2026). The January
revision renamed the method from `wallet_grantPermissions`, removed the `signer` object and every
permission type. It now defines only a base permission, a base rule and one rule, `expiry`; types are an
"enum defined by ERCs", and "Wallets MUST correctly enforce permissions." (erc-7715.md:463). Four methods
(request, revoke, get supported, get granted).

D1, D2, D3, D4, D5 ND (no types defined); D6 N for chain only (one `chainId` per request); D7 N (expiry
rule); D8 N (a grant to a named session account); D9 a revoke method exists, enforcement and verification
unspecified; D10, D11 ND; D12 ND (lists current grants only); D13 X (one chain per permission). Test case:
only (c) and (e) are defined. Not expressible in the standard itself.

### B2. MetaMask Advanced Permissions (MetaMask's ERC-7715 implementation)

Shipped in MetaMask (periodic and stream types from v13.23.0, allowance types from v13.32.1, per
https://docs.metamask.io/smart-accounts-kit/get-started/supported-advanced-permissions.md, fetched 8 Oct
2026). The user's account must be upgraded to a MetaMask smart account. A grant becomes one ERC-7710
delegation with Delegation Framework caveats (B4). Closed list: seven permission types, each with rules
`expiry`, `redeemer`, `payee` only (MetaMask/snap-7715-permissions@60c8a92
packages/shared/src/types/7715-permissions-supported.ts:9-17).

| Dim | Verdict | Evidence |
|---|---|---|
| D1 | X | No type or rule caps a single transfer, and other rule types are rejected. |
| D2 | N | `erc20-token-periodic`, `native-token-periodic`; streams. |
| D3 | N | `erc20-token-allowance`, `native-token-allowance`. |
| D4 | N, with a limit | `payee` rule. Native: a list. ERC-20: "For ERC-20 permissions, allowedCalldataEnforcer supports one target." (payeeCaveat.ts:75), and two addresses throw. |
| D5 | C | One permission per payee, each with its own user approval. |
| D6 | N | Token address per permission, one chain per request. |
| D7 | N | `expiry` rule maps to TimestampEnforcer; `startTime` gives valid-from. |
| D8 | N | A session account per grant. |
| D9 | N | Who: only the user, from the MetaMask client; the kernel snap does not route `wallet_revokeExecutionPermission`, so a dapp or agent cannot revoke. How: on-chain `disableDelegation`. Third party: yes (B4). |
| D10 | X | Approval once, at grant time. |
| D11 | C | The delegation hash is on chain with every redemption; the `justification` string is not signed, and the salt is random. |
| D12 | C | Grants per site origin; spends are chain events; no deny record. |
| D13 | X | One chain per permission. |

Test case: (a) yes for native-token payees or exactly one ERC-20 payee; (b) yes; (c) yes; (d) yes, but
only the user can trigger it; (e) yes. Partly expressible: not for "pay these three merchants in USDC".

### B3. ERC-7710 (smart contract delegation)

Draft (ERCS/erc-7710.md, last changed be46db7, 10 Jun 2025). One interface, `redeemDelegations`; no
caveats, no revocation interface, no events; the security section ends "Needs discussion." D1 to D13 ND.
It is a redemption interface; everything in the test case lives in an implementation such as B4.

### B4. MetaMask Delegation Framework

Deployed on 26 mainnets per its Deployments.md; latest tag v1.3.0 (24 Jul 2025); read at main bff4b08
(11 Sep 2026); the cited files are byte-identical at the tag. The principal's smart account signs a
`Delegation {delegate, delegator, authority, caveats[], salt, signature}`; the DelegationManager runs every
caveat enforcer on every link of a delegation chain at redemption. 37 enforcers are listed with line
numbers in `notes/sa-delegation.md`.

| Dim | Verdict | Evidence |
|---|---|---|
| D1 | N (native), C (ERC-20) | ValueLteEnforcer; ERC20BalanceChangeEnforcer on the delegator's balance. |
| D2 | N | ERC20PeriodTransferEnforcer, NativeTokenPeriodTransferEnforcer, MultiTokenPeriodEnforcer. |
| D3 | N | ERC20TransferAmountEnforcer, NativeTokenTransferAmountEnforcer (lifetime per delegation). |
| D4 | N (native, one ERC-20 payee), C (several ERC-20 payees) | AllowedTargetsEnforcer; AllowedCalldataEnforcer pinning the `to` word at offset 4 plus a selector pin; several payees by LogicalOrWrapperEnforcer groups. |
| D5 | C (one delegation per payee), CODE (inside one delegation) | No enforcer caps spend per recipient; MultiTokenPeriodEnforcer says it "does not support restrictions on the recipient address" (MultiTokenPeriodEnforcer.sol:25). Groups in LogicalOrWrapperEnforcer that reuse one amount enforcer share one counter (read from code, not run). |
| D6 | N | Token address in terms; chain fixed by the EIP-712 domain. |
| D7 | N | TimestampEnforcer, BlockNumberEnforcer. |
| D8 | N | Any delegate address; narrower re-delegation in chains, since a child can only add caveats. |
| D9 | N | Who: the delegator of that link. How: `disableDelegation` or a NonceEnforcer increment. How fast: next block. Third party: yes, public `disabledDelegations(hash)` and `DisabledDelegation` event (DelegationManager.sol:90-95). Two caveats: `enableDelegation` undoes it (DelegationManager.sol:103-108), and a principal cannot disable a child delegation its agent signed, only its own link. The DelegationManager owner can pause every redemption on a chain. |
| D10 | CODE | Needs a custom enforcer. |
| D11 | C | Delegation hash in events; `RedeemedDelegation` emits the whole signed delegation, including a free `salt`. |
| D12 | C | Allowed spends leave events; denials revert. |
| D13 | X | One DelegationManager domain per chain. |

Test case: (a) yes, (b) yes, (c) yes, (d) yes with the two caveats, (e) yes. **Expressible by
configuration** (four to six enforcers chosen and ordered correctly), on one chain.

### B5. Rhinestone Smart Sessions (ERC-7579)

erc7579/smartsessions@f5aaf86; the README says "This software is in beta" (README.md:48); audited
(Cantina, Renascence, ChainLight). Rhinestone's own SDK now targets Smart Sessions v2
(rhinestonewtf/smart-sessions-v2@7c0e8d7). A session (`permissionId`) has its own validator (key,
multisig), user-op policies, per-action policies and a salt.

| Dim | Verdict | Evidence |
|---|---|---|
| D1 | N | UniActionPolicy or ArgPolicy `LESS_THAN_OR_EQUAL` on the amount; `valueLimitPerUse`. |
| D2 | C | No shipped policy resets by period; one session per period, or a custom policy. |
| D3 | N | ERC20SpendingLimitPolicy (lifetime per token), ValueLimitPolicy, limited UniAction rules. Counters are per action and per chain: "They do not create one shared session-wide counter." (docs.rhinestone.dev session-limits.md:91). |
| D4 | N | Native: one action per payee; ERC-20: EQUAL on the recipient argument, or an ArgPolicy OR tree. |
| D5 | C | ArgPolicy tree, each branch binding a recipient and its own limited amount (composition read from code). |
| D6 | N | Token by action target; chain by where the session is enabled. |
| D7 | N | TimeFramePolicy `validAfter`, `validUntil`. |
| D8 | N | A fresh `permissionId` per task. The SDK defaults to sudo when no permissions are given. |
| D9 | N in the contract | `removeSession(permissionId)` by the account, emits `SessionRemoved`, public `isPermissionEnabled` (SmartSessionBase.sol:329-355). But Rhinestone's app-facing SDK "has no app-origin revoke method" and tells integrators to contact support (docs.rhinestone.dev security.md), and "For a multi-chain grant, authority can remain active on one chain after it has been removed from another." (security.md:78). **Update 12 Oct 2026:** Rhinestone's docs now show a self-service revoke, `revokeSessionGrant()` in the `@rhinestone/wallet` client, which runs on every chain the grant is enabled on and reports success only when it lands on all of them; "authority stays active on any chain whose revoke failed" (docs.rhinestone.dev/wallets/session-keys/security, read 12 Oct, lines 68 and 79). Verdicts unchanged. |
| D10 | C | A second, higher-cap session whose validator is a multisig that includes a human. |
| D11 | C | `permissionId` (salt can encode a task id) travels in the user operation; nothing reaches the payee. |
| D12 | N allows, X denials | Session and TokenSpent events. |
| D13 | C | One signature can enable sessions on several chains; each chain counts separately. |

Test case: (a) to (e) yes on a single chain, at contract level. **Expressible on one chain**, but the
vendor's own SDK path offered no self-service revoke on 8 Oct (see the 12 Oct update in D9).

### B6. ZeroDev Kernel permissions

Kernel v3.3 (tag cd697c7) with v3 policies from zerodevapp/kernel-7579-plugins@581985f, the last commit
before those policy sources were deleted from the repo on 26 Jan 2026 (88a4d4c); addresses remain in the
SDK. D1, D4, D6, D7, D8 N (CallPolicy `valueLimit` and argument rules incl. ONE_OF, TimestampPolicy, a
signer per permission); D2 C (call count per interval times a per-call cap; the reset variant "won't work
with all bundler"); D3 C (only an undocumented SpendingLimit hook); D5 C or CODE; D9 N (`uninstallValidation`
or `invalidateNonce` by the root; the `NonceInvalidated` event is declared at ValidationManager.sol:64 and
never emitted, so third parties must read state); D10 C; D11 C (permission id in the user op nonce); D12 N
allows, X denials; D13 C. Test case: partial (no documented cumulative budget).

### B7. Biconomy (Nexus account, AbstractJS sessions)

Biconomy ships no policies of its own: bcnmy/abstractjs@fd61054 imports Rhinestone's Smart Sessions v1
address and policy builders. Verdicts follow B5 at contract level, with three differences in the
documented developer path: unconfigured actions get sudo ("If no policies are configured, sudo policy will
be added by default which is a unrestricted policy", buildSessionAction.ts:234); revocation is not in the
agent or SDK reference pages (D9 C); and the docs card "Single permission works across all chains."
(agents-automation.md:310) is marketing, since the code installs one session per chain. Test case:
expressible at contract level; the documented path lacks the revocation step.

### B8. Safe Allowance module

safe-global/safe-modules@9e5f3d0 AllowanceModule.sol (v1.0.0 in the repo; the deployments registry lists
v0.1.0 and v0.1.1). One record per (Safe, delegate, token): amount, spent, reset period in minutes.
`executeAllowanceTransfer` takes `to` from the delegate's own signed request and checks only signature,
nonce and the remaining allowance.

D1 X; D2 N (`resetTimeMin`, at most about 45 days); D3 N ("If the `resetTimeMin` time of an allowance is
`0` then the allowance will not automatically renew.", README.md:62); D4 X; D5 X (no recipient field or
check); D6 N; D7 X; D8 N (a delegate per task); D9 N (Safe transaction `deleteAllowance` or
`removeDelegate`, events and views public, owner threshold needed); D10 C (larger moves are ordinary Safe
transactions); D11 C (the delegate address appears in each transfer event); D12 N allows; D13 X. Test case:
not expressible (no payee restriction, no expiry).

### B9. Zodiac Roles Modifier v2

gnosisguild/zodiac-modifier-roles@820e5bc; v2 mastercopy deployed on 16 mainnets. Roles scope targets,
functions and parameters with condition trees; allowances keyed by bytes32 with refill, period and
balance.

D1 N (LessThan on the amount argument); D2 N (allowance refill per period); D3 N (period 0); D4 N (EqualTo
on the recipient, Or for several); D5 C (Or of branches, each with its own allowance key; "If the
condition evaluates to `false` or executing the call reverts, allowances will not be updated.",
conditions.mdx:121); D6 N; D7 CODE (no time operator in v2; a Custom condition contract is needed; an
unreleased `contracts-v3` branch under BUSL-1.1 adds time-bound memberships); D8 N; D9 N (owner
`assignRoles(..., false)`, events; no membership getter in v2); D10 C; D11 C (role key); D12 N allows; D13
X. Test case: not expressible in deployed v2 without custom code (expiry). It is the only item in this
section with native per-recipient allowances and native refill periods together.

## C. Card and fiat rails

Full evidence: `notes/cards-networks.md`, `notes/cards-stripe-corporate.md`. Common to every card product
here: revocation is one call for the issuer, token requestor or account holder, and no payee or auditor can
check it; the merchant sees a decline.

### C1. Visa Intelligent Commerce (VIC) and Trusted Agent Protocol

**Pilot.** The product page says "This product is in the process of development and deployment." and the
VIC developer docs are restricted behind sign-in; the API was read from the public Cybersource REST spec
(CyberSource/cybersource-rest-client-python@7349130 generator/cybersource-rest-spec.json, `/icc/v1/*`) and
Visa's public sample repos (visa/ai@1c544e5, visa/vic-reference-agent@39bc93d). The cardholder does not set
limits on the agent token; per purchase the agent creates a purchase instruction carrying mandates
(`mandateId`, `declineThreshold`, `effectiveUntilTime` required; `preferredMerchantName`,
`merchantCategoryCode` optional), the cardholder approves it with a passkey, and the agent retrieves a
per-transaction credential against it. Who enforces which field is stated only on the product page. Visa
Transaction Controls (an issuer product) can put period limits, counts and category blocks on a token, but
no public document ties it to VIC tokens. Trusted Agent Protocol is agent identity to merchants (RFC 9421
signatures) and carries no spending control.

| Dim | Verdict | Evidence |
|---|---|---|
| D1 | N (pilot) | `mandates[].declineThreshold`: "Defines the maximum transaction amount the consumer is willing to authorize under this mandate." (spec:208985). |
| D2 | C | Not in VIC; only issuer-set Visa Transaction Controls `spendLimit` LMT_DAY, LMT_WEEK, LMT_MONTH. |
| D3 | C | No cumulative cap per instruction; issuer VTC LMT_DATE_RANGE only. |
| D4 | ND | `preferredMerchantName` is described as "User merchant preference." (spec:208966); enforcement claimed only on the product page. |
| D5 | ND | Mandates are an array, but pairing a merchant with its own threshold is not documented as enforced. |
| D6 | C | `merchantCategoryCode` field, enforcement not documented; VTC category blocks, issuer-set. |
| D7 | N (pilot) | `effectiveUntilTime` required on every mandate. |
| D8 | N (pilot) | The purchase instruction is the per-task object; each credential is bound to an `instructionId`. The agent token itself is per agent and card. |
| D9 | N one step, not verifiable | `PUT .../instructions/{id}/cancel` by the agent platform; it may return PENDING until the cardholder re-authenticates (spec:210614). No GET or list endpoint for instructions. |
| D10 | N | Cardholder passkey assurance on create, update and cancel; Visa decides when step-up is needed, no principal-set threshold. |
| D11 | ND | Inside Visa, `mandateId` and `instructionId`; what reaches the merchant via TAP is agent identity, a tag and a nonce, not a task id. |
| D12 | C | No read endpoint for instructions or decisions; issuer-side alert history only. |
| D13 | ND | Intelligent Commerce Connect is described as rail-agnostic; press release only for "spend controls". |

Test case: (a) not verifiable, (b) per-transaction only, (c) yes, (d) no, (e) yes. Not expressible.
The 30 Apr 2025 press release's "set spending limits and conditions" is not matched by any public API field
beyond the per-mandate threshold.

### C2. Mastercard Agent Pay (agentic tokens) and MDES Token Spend Controls

Agent Pay documentation is an early preview with no public intent API. The token-level controls live in the
MDES Customer Service API (v4.0.1, https://static.developer.mastercard.com/content/mdes-customer-service/swagger/mdes-customer-service.yaml,
fetched 8 Oct 2026), in production since 5 Aug 2026, **set by the issuer** "based on the issuer's decision
after cardholder authentication" (yaml:434), and issuers "can optionally support the new APIs" (release
notes July 2026:190). Mastercard enforces them at authorization.

| Dim | Verdict | Evidence |
|---|---|---|
| D1 | N (issuer-set) | `TRANSACTION_SPEND_LIMIT`; the use-case page says per transaction, the OpenAPI text says "Cumulative transaction spend limit" (yaml:3941). |
| D2 | N (issuer-set) | `DAILY_AMOUNT_LIMIT`, `WEEKLY_AMOUNT_LIMIT`, `MONTHLY_AMOUNT_LIMIT`. |
| D3 | N (issuer-set) | `ABSOLUTE_SPEND_LIMIT` with an expiry up to a year ahead; it "cannot coexist with other LIMIT type" (yaml:3936). `SINGLE_TIME_USE`. |
| D4 | N (issuer-set) | `ALLOW_LST_MID` merchant-ID allowlist (yaml:3993). |
| D5 | X | Limit rules and list rules are separate objects with no link between an amount and a merchant. |
| D6 | N (issuer-set) | MCC, transaction category, transaction type and country allow and block lists. |
| D7 | ND | The absolute limit's `expirationDate` ends the rule; the token's behaviour afterwards is not documented. |
| D8 | ND | The agentic token is per agent and card; no public API mints one per task. |
| D9 | N one step, not verifiable | Suspend, unsuspend or delete through MDES by the issuer, token requestor or cardholder; "All authorizations for a SUSPENDED token will be declined." (yaml:162). Status visible to the issuer and token requestor only. |
| D10 | ND | Passkey authentication of consumer intent is named, with no API or threshold. |
| D11 | ND | A Digital Service Provider ID and solution indicators mark a transaction as agentic, not a task. |
| D12 | C | Issuer-side transaction and status history (30 days). |
| D13 | ND | Card only; Agent Pay for Machines (June 2026) claims multi-rail limits in a press release only. |

Test case: (a) yes but issuer-only and per agent, (b) yes but then no per-transaction cap on the same token,
(c) not documented, (d) no, (e) no. Not expressible by the principal. Mastercard also maintains Verifiable
Intent (agent-intent/verifiable-intent@356c296, "Draft (v0.1)"), a mandate vocabulary close to AP2's
(allowed payees, amount range, cumulative budget); "VI v0.1 does not define a credential-layer revocation
protocol." (spec/security-model.md:319).

### C3. American Express Agentic Commerce Experiences (ACE) developer kit

Limited access: the API guide and specifications are released only after a request form and a
confidentiality agreement (developer.americanexpress.com overview, read 8 Oct 2026); no OpenAPI, SDK or
repository is public. Vendor descriptions mention budget limits, merchant preferences, per-intent credentials
"scoped for limited use" and Card Members who will "view, manage, or revoke intents". D1 to D13 ND. Test
case: unknown.

### C4. Stripe Issuing used for agents

Issuing is GA in the US, UK and EU after approval; "Issuing for agents" (https://docs.stripe.com/issuing/agents.md)
is a use-case guide over the same APIs, recommending one virtual card per agent or task. Stripe evaluates
`spending_controls` at authorization, then optionally calls the principal's real-time webhook (2 s budget).
Field names confirmed in stripe/openapi@52ca110 `openapi/spec3.json` (GA, 2026-09-30).

| Dim | Verdict | Evidence |
|---|---|---|
| D1 | N | `spending_limits[].interval = per_authorization`. |
| D2 | N | `daily`, `weekly`, `monthly`, `yearly` (calendar periods); "Spending aggregation is done on a best-effort basis." with up to 30 s lag (issuing-spending-controls.md:40). |
| D3 | N | `all_time`; `lifecycle_controls.cancel_after.payment_count`. |
| D4 | CODE (GA) | GA controls have categories, countries and card presence, no merchant identifier; "Merchant ID spending controls is in private preview." (issuing-spending-controls.md:7). In GA the webhook must check `merchant_data`. |
| D5 | CODE | Per-category limits only; per-merchant needs the webhook or one card per payee. |
| D6 | N | `allowed_categories` / `blocked_categories` (MCC-derived), merchant countries, card presence. |
| D7 | C | Card expiry is month-granular; task end needs an explicit cancel or `payment_count`. |
| D8 | N | "Issue virtual cards scoped to a single task or session." (issuing-agents.md:39). The key that mints cards can also loosen any card, since restricted keys are scoped by resource type. |
| D9 | N one step, ND third party | `status=canceled` (or `inactive`, reversible); force posts still settle; the merchant sees only declines. |
| D10 | CODE | No threshold field; a 2 s webhook cannot wait for a human; SMS fraud challenges are public preview. |
| D11 | ND | Card `metadata` stays with the issuer. |
| D12 | N | Authorizations API records approvals and declines with reasons (`spending_controls`, `webhook_declined`). |
| D13 | ND | Card authorizations only. |

Test case: (a) not in GA without code, (b) yes, (c) partly, (d) one step, not verifiable, (e) yes. Not
expressible.

### C5. Stripe Shared Payment Tokens (SPT)

Preview; agent-side issuance "is in private preview" with a waitlist (agentic-commerce.md:17); not in the GA
OpenAPI file. The agent business mints a token from a PaymentMethod, bound to one seller profile, with
`usage_limits` (`currency`, `max_amount` required, `expires_at`).
Sources: https://docs.stripe.com/agentic-commerce/concepts/shared-payment-tokens.md and
https://docs.stripe.com/api/shared-payment/issued-token/ pages (fetched 8 Oct 2026); preview SDK specs at
stripe/openapi@52ca110.

| Dim | Verdict | Evidence |
|---|---|---|
| D1 | C | No separate per-payment field; `max_amount` bounds any one payment; a card underneath adds `per_authorization`. |
| D2 | N(pp) | `usage_limits.recurring` only in the private-preview spec. |
| D3 | N | "An SPT remains usable until it expires, you revoke it, or cumulative captured payments reach `usage_limits[max_amount]`." (programmatic-checkout.md:25). |
| D4 | N | `seller_details.network_business_profile` required: exactly one seller, on Stripe. |
| D5 | C | One token per seller. |
| D6 | N | `usage_limits.currency`. |
| D7 | N | `usage_limits.expires_at`. |
| D8 | N | A token per purchase, minted with a restricted key. |
| D9 | N, payee-verifiable inside Stripe | `POST .../issued_tokens/{id}/revoke`; the seller receives `shared_payment.granted_token.deactivated` and can read `deactivated_reason`. Not visible to an independent auditor. |
| D10 | CODE | No approval field on the token. |
| D11 | N | `shared_metadata` is "visible by default with the party that you share this SharedPaymentIssuedToken with" (api-spt-issued-token-create.md:74). |
| D12 | C | Token usage and deactivation fields and webhooks; no record of refused attempts. |
| D13 | X | One token wraps exactly one payment method. |

Test case: (a) one seller per token, (b) yes per token, (c) yes, (d) one call, verifiable by the payee
through Stripe, (e) yes. **Closest card-side object, but one seller per token, preview only, and inside
Stripe's network.**

### C6. Agentic Commerce Protocol (ACP) delegate payment

Beta, maintained by OpenAI and Stripe (README.md:10); spec 2026-04-17, read at
agentic-commerce-protocol@7fdd78d. The agent platform sends the buyer's card credential with an `Allowance`
to the merchant's PSP, which mints a single-use vault token. `Allowance` has exactly six required fields
and `additionalProperties: false`: `reason` (enum `one_time` only), `max_amount`, `currency`,
`checkout_session_id`, `merchant_id`, `expires_at` (spec/2026-04-17/openapi/openapi.delegate_payment.yaml).
"The returned token MUST ONLY be usable within the provided Allowance (reason, max_amount, currency,
expiry)." (rfcs/rfc.delegate_payment.md:64).

D1 N; D2 X (one-time only); D3 N; D4 N (one merchant); D5 C; D6 N (currency; card is the only credential
type); D7 N; D8 N (one token per checkout); D9 ND (the RFC defines no revoke operation; only expiry ends a
token); D10 ND; D11 N (`checkout_session_id`); D12 ND; D13 X. Who sets the limits: the agent platform; the
buyer has no field in the protocol. Test case: not expressible (no revocation; one purchase).

### C7. Stripe agent toolkit and Stripe MCP

stripe/agent-toolkit@08d371a adds no spend controls; tools follow the restricted key's per-resource
permissions. Account-level approval rules for agent-tagged keys can require approval above an amount for
payment intents and refunds, and the MCP server requires human confirmation for certain writes ("Stripe
requires human confirmation before it takes certain `stripe_api_write` actions, such as refunds and
outbound payments.", mcp.md:373). From 31 Oct 2026 the MCP server accepts only OAuth or agent-tagged keys
(mcp.md:186). These govern what an agent does inside the principal's own Stripe account, not what it buys.
D1 C, D2 C (request count), D3 to D6 ND, D7 C, D8 C, D9 N (no third party), D10 N, D11 ND, D12 N, D13 ND.

### C8. Ramp (funds, Agent Cards)

Developer API v1; agent identities separate from a user are "in limited early access"
(agents.ramp.com llms-full.txt:523). Every card draws on a Fund with `spending_restrictions`; an Agent Card
is a one-time credential requested against one fund. Source: https://docs.ramp.com/openapi/developer-api.json
(fetched 8 Oct 2026).

| Dim | Verdict | Evidence |
|---|---|---|
| D1 | N | `transaction_amount_limit`. |
| D2 | N | `interval` DAILY to YEARLY. |
| D3 | N, soft | `interval = TOTAL`; overage percentages and temporary increases can exceed it by design. |
| D4 | N | `allowed_vendor_ids` / `blocked_vendor_ids`; Ramp's own data guide says card merchants and vendors are separate objects, so the identifier space is unclear. |
| D5 | C | One fund per payee. |
| D6 | N | Category codes and blocked MCCs. |
| D7 | N | `lock_date` (date-time). |
| D8 | C | Per-task fund is possible, but by default the agent acts as the signed-in user and can draw on every fund that user can. |
| D9 | N one step, ND third party | Suspend or terminate the fund. |
| D10 | C | Approval routing above a threshold is an app setting, not an API field. |
| D11 | ND | Memo and receipt fields are filled in after purchase, inside Ramp. |
| D12 | N | Declined transactions with reasons; audit logs API. |
| D13 | C | One fund governs cards, reimbursements, bills and MPP; "x402 purchases draw from a separately funded x402 wallet, rather than a user's card or fund." (guide-agent-payments.txt:39). |

Test case: (a) yes with the identifier caveat, (b) yes unless overage is set, (c) yes, (d) not verifiable,
(e) one-time card yes, confinement of the agent to one fund only in early access. Not expressible.

### C9. Brex

Team API and Budgets API v2 (GA naming). No agent-specific product found; Brex MCP is beta and "Actions
like approvals and card management are not yet available via MCP." (mcp.md:146). Sources:
https://developer.brex.com/_bundle/openapi/team_api.yaml and budgets_api.yaml (fetched 8 Oct 2026).
D1 C (only on a Spend Limit); D2 N (`spend_duration` monthly to yearly; no daily); D3 N, soft (`ONE_TIME`,
but `SOFT` authorization and a percentage buffer exist); D4 N by merchant name only (`allowed_merchant_details`,
up to 50); D5 C; D6 C; D7 N (`lock_after_date`, a date); D8 N (vendor card per task via API, not via MCP);
D9 N one step (lock or terminate), ND third party; D10 ND; D11 ND; D12 N (decline reasons in webhooks); D13
C (cards, reimbursement and bill pay on one Spend Limit). Test case: not expressible.

### C10. PayPal and Stripe Link (short)

PayPal Agent Toolkit (paypal/agent-toolkit@a3aa963) is merchant-side (invoices, orders, refunds); its only
control is a boolean per tool. No public PayPal API was found for capping what an agent spends; D1 to D13
ND. Stripe's Link Agent Wallet (consumer, US and Canada): an agent files a spend request with amount,
context and merchant; the customer approves in Link (10-minute window) and Link returns a one-time
credential. D1, D3, D4, D7, D8, D10 N; D9 cancel of an unused request only; third party ND
(https://docs.stripe.com/agentic-commerce/agents/link-agent-wallet.md, fetched 8 Oct 2026).

## D. Agent-payment startups and mandates

Full evidence: `notes/startups-mandates.md`; Kite from `notes/novelty-notes.md` and a check of Kite's
public repositories (listed in SOURCES.md).

### D1. Skyfire and KYAPay

Skyfire API in production; the token format is an individual Internet-Draft,
draft-skyfire-oauth-kyapay-token-02 (2 Oct 2026, not adopted). Whoever holds the buyer agent's API key mints
`pay` tokens: a signed JWT bound to one seller (`aud`) and service (`ssi`), with `tokenAmount` and an
expiry of 10 seconds to 24 hours; Skyfire holds funds at mint and enforces the cap on each charge. Sources:
https://docs.skyfire.xyz/ pages (fetched 8 Oct 2026; one other page, agent-spending-limits, returned a
CloudFront 403 and was recorded as blocked).

| Dim | Verdict | Evidence |
|---|---|---|
| D1 | C | "The token amount is the maximum a seller can charge." (payments-settlement.md); a per-purchase cap means one token per purchase. |
| D2 | ND | No period limit on wallet, agent or key. |
| D3 | N | `tokenAmount` per token; across tokens only the wallet balance. |
| D4 | N (per token) | One seller per token; the API key itself can mint for any seller. |
| D5 | C | One token per seller. |
| D6 | ND | No asset, chain or category setting. |
| D7 | N | `expiresAt`, up to 24 h; a validated token stays chargeable 24 h after expiry. |
| D8 | N | The pay token is per task and separate from the API key, if the principal keeps the key from the agent. Skyfire's own MCP tool lets the agent choose the amount. |
| D9 | X (issued tokens) | "Deactivating an account does not void tokens that were already issued." (payments-settlement.md); the companion draft says "This specification does not define a revocation mechanism." (draft-skyfire-oauth-using-kyapay-tokens-01:684; CORRECTED 8 Oct from :1445). |
| D10 | C | Card-funded tokens need the cardholder's passkey for the exact amount; no threshold rule. |
| D11 | N | `buyerTag` reaches the seller as a claim. |
| D12 | N transactions | Token and charge lists; no refused-mint log. |
| D13 | ND | No policy object. |

Test case: (a) per token, (b) per single seller, (c) up to 24 h plus 24 h, (d) no, (e) yes. Not
expressible.

### D2. Payman

**Last documented state only.** docs.paymanai.com returned HTTP 526 on 8 Oct 2026 and the homepage now
markets banking software to banks; evidence is Internet Archive snapshots dated 12 Oct 2025 to 12 Jan 2026,
which describe an invite-only platform. Policies held an approval threshold, a per-transaction maximum,
and daily and monthly limits; payments went only to registered payees. D1, D2 N; D3 C; D4 C (payee registry
plus withholding the create-payee scope); D5 ND; D6 C; D7 ND; D8 C; D9 ND; D10 N ("Payman pauses the
transaction until you approve or deny."); D11 N inside Payman (`memo`, `metadata`); D12 N transactions; D13
ND. Test case: not expressible.

### D3. Nekuda

**Payment product no longer documented**; docs.nekuda.ai covers only a WebMCP kit. The still-published SDKs
(PyPI `nekuda` 0.2.10, npm `@nekuda/nekuda-js` 0.2.14) show a "mandate" that describes one purchase (price,
merchant, context) and a reveal flow that returns the full card number, expiry and CVV (or Visa
credentials) to the agent developer's backend; the SDK shows no user-approval step and no enforcement of
the mandate's fields. D1 to D13 ND. Test case: none of (a) to (e) verifiable.

### D4. AP2, Agent Payments Protocol v0.2

Draft v0.2; tag v0.2.0 (b4587ac, 28 Apr 2026); read at google-agentic-commerce/AP2@e1ea56d, whose spec and
schemas match the tag. The core specification went to the FIDO Alliance on 28 Apr 2026; FIDO's
specifications pages listed no AP2 document on 8 Oct 2026. **Current names:** Checkout Mandate and Payment
Mandate, each open (user-signed, carries constraints and the agent's key) or closed (agent-signed for one
checkout), plus Checkout and Payment Receipts. The v0.1 Cart and Intent Mandates are gone. **Format:**
SD-JWT (RFC 9901) delegation chains with key binding, OpenID4VP `transaction_data` in the user-credential
model; no W3C Verifiable Credentials and no DIDs (zero matches in docs and SDK).

| Dim | Verdict | Evidence |
|---|---|---|
| D1 | N(spec) | `payment.amount_range` `max` (open_payment_mandate.json). |
| D2 | C | `agent_recurrence` (frequency, `max_occurrences`) times `amount_range`; no per-period amount. The SDK checks only `max_occurrences`. |
| D3 | N(spec), no owner | `payment.budget`; "Evaluating the budget requires tracking the total amount spent using this Payment Mandate." (payment_mandate.md), but no role is assigned the ledger; the reference credential provider verifies without usage context, and the sample's ledger is a file written by the shopping agent. |
| D4 | N(spec) | `payment.allowed_payees`, `checkout.allowed_merchants`; "The `payee` property of the Payment Mandate MUST be present in the `allowed` array." (payment_mandate.md). |
| D5 | C | One open mandate per payee. |
| D6 | N(spec) | Allowed instruments, PISPs, ISO 4217 currency, SKU line items. No category, chain or token field. |
| D7 | N(spec) | `exp`, recommended "to the smallest value that will allow the Shopping Agent to complete the assigned task" (specification.md); `execution_date` window. |
| D8 | N(spec) | Each open mandate binds one agent key via `cnf`. |
| D9 | X | No role has a revoke operation: "In the case of external Trusted Surfaces it could make sense to allow for management of delegated Mandates but that is outside the scope of this specification." (implementation_considerations.md). Only `exp` or single use ends a mandate. |
| D10 | C | Human-present mandates per checkout; threshold only by composition. |
| D11 | N(spec) | Closed Payment Mandate `transaction_id` is the hash of the merchant-signed checkout; receipts reference mandate hashes; seen by merchant, credential provider, network and processor. |
| D12 | N(spec) | "Upon acceptance or rejection of the Mandate, the Verifier MUST return a signed Mandate Receipt." (agent_authorization.md). |
| D13 | N(spec) | One instrument list can name instruments of different types (spec example: card and UPI); x402 appears only in samples. |

Test case: (a) yes, (b) yes on paper with no ledger owner, (c) by `exp`, (d) no, (e) yes. Not expressible:
no revocation.

### D5. x402 (protocol) and its reference client

The most used agent payment protocol by package downloads (npm `x402` 1,803,939 and `@x402/core` 1,289,470
from 8 Sep to 7 Oct 2026, api.npmjs.org). x402-foundation/x402@7f2b2f1, spec v2: "Client-side budget
management" is listed out of scope (specs/x402-specification-v2.md:19). The reference client's
`spendControls` (per-payment USD cap, default $1; asset allowlist) run in the payer's process and can be
set to `false` (x402Client.ts:167-190). D1, D6, D13 N(client); D2, D3, D4, D5, D10, D12 CODE (hooks);
D7 N per authorization only; D8, D9 ND (single-use, short-lived authorizations; no grant object); D11 N
(`payment-identifier` extension, off chain). Test case: not expressible; x402 is a per-payment rail.

### D6. Nevermined delegations (added)

Picked by package downloads. The user enrolls a card or an ERC-4337 account and creates a delegation:
`spendingLimitCents` over its life, `durationSecs`, optional `maxTransactions`, optional `planId` (one
seller plan) and `apiKeyId`; Nevermined's facilitator signs it and checks status, usage and expiry on
every verify and settle (https://nevermined.ai/docs/products/payments/mandates.md, fetched 8 Oct 2026; the
x402 delegation extension is "Version: 0.1, Status: Draft").

D1 C; D2 C (group budgets, paid tiers); D3 N; D4 N (one plan); D5 C; D6 C; D7 N; D8 N; D9 N ("Revocation
is immediate", DELETE on the delegation; a seller learns of it only through Nevermined's verify result); D10
C (at creation); D11 N (delegation JWT carried in the x402 payload); D12 N; D13 N for protocols ("A single
Delegation covers x402 and MPP alike.", router overview); whether one delegation spans a card and a crypto
account at once is not shown. Test case: (a) one seller plan, (b) yes, (c) yes, (d) one step, verifiable
only by asking Nevermined, (e) yes. **Nearly expressible.**

### D7. Kite (Agent Passport, session keys; added from the novelty sweep)

Kite's whitepaper (https://www.gokite.ai/kite-whitepaper, undated, fetched 8 Oct 2026) states the closest
design to the test case: one principal-owned account, agents operating it through task-scoped, random,
expiring session keys limited to named providers, amounts and time windows, and revocation of every
delegation in one transaction. "Permissions are scoped at the task level, not the agent level." Kite's
public developer docs (gokite-ai/developer-docs@4afe23c, 4 Jun 2026) show less: a `ClientAgentVault` on
Kite testnet with spending rules `{timeWindow, budget, initialWindowStartTime, targetProviders}`
(kite-chain/5-advanced/account-abstraction-sdk.md:158-196), and an agent MCP tool list that includes
`revoke_payment_delegation` and `terminate_session`, with the server URL "will be provided". The vault
contract source was not found in Kite's public repositories (gokite-ai org listing, 8 Oct 2026). Verdicts:
D2, D3, D4 N(vendor) from the docs; D7, D8, D9 N(vendor) from the whitepaper only; the rest ND. Test case:
claimed in full by the whitepaper, on Kite's own chain only; not verifiable from public code.

## Sources

Each section names its primary sources with URL and fetch date or repository and commit. The complete
lists, with every quote and line number, are in:

- `notes/coinbase-aws.md` (A1 to A5)
- `notes/wallets-1.md` (A6 to A9)
- `notes/wallets-2.md` (A10 to A13)
- `notes/sa-delegation.md` (B1 to B4)
- `notes/sa-modules.md` (B5 to B9)
- `notes/cards-networks.md` (C1 to C3)
- `notes/cards-stripe-corporate.md` (C4 to C10)
- `notes/startups-mandates.md` (D1 to D6)
- `notes/novelty-notes.md` and SOURCES.md (D7)
- `notes/spot-checks.md` (the re-read of every native cell)

Blocked or gated during this teardown: Visa VIC and VTS docs (sign-in), American Express ACE specifications
(request form and NDA, not requested), Mastercard Agent Pay documentation pages (not public), the Fireblocks
Help Center rule-parameter article (403), docs.heyvincent.ai (timeout), docs.paymanai.com (526), one
Skyfire page (CloudFront 403), Catena Labs' site (TLS error). No bot check was bypassed.

