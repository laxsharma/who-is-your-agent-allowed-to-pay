# Group sa-delegation: ERC-7715, ERC-7710 and the MetaMask Delegation Framework

Read on 8 October 2026. Four blocks: 1a ERC-7715 (the standard), 1b MetaMask Advanced Permissions (the shipped
ERC-7715 implementation), 2a ERC-7710 (the standard), 2b MetaMask Delegation Framework (the contracts).
Line numbers refer to the commits named in each header. Source ids resolve in the list at the end.
"Inference from code" marks a conclusion read from the code but not executed (no code from any clone was run).

---

## 1a. ERC-7715 "Request Permissions from Wallets"

- Vendor: Ethereum ERC, ten authors listed in the header [S1:5].
- Status: Draft [S1:7], requires ERC-4337 and ERC-7710 [S1:11].
- Version read: ethereum/ERCs@ee5363b `ERCS/erc-7715.md`. The file was last changed by commit 2adc378
  (2026-01-16, "Website: Simplify specification to ease wallet implementation") [S3].
- Date read: 8 Oct 2026.

**Control model.** The current text defines four JSON-RPC methods. `wallet_requestExecutionPermissions` [S1:73-104]
lets a dapp ask the wallet for a permission held by the user's account (`from`) and granted to a DApp session account
(`to`) [S1:98-100]. `wallet_revokeExecutionPermission` [S1:189-207], `wallet_getSupportedExecutionPermissions`
[S1:209-255] and `wallet_getGrantedExecutionPermissions` [S1:257-305] complete the set. A request carries one
`chainId`, one `permission` (type, `isAdjustmentAllowed`, free `data`) and optional `rules` [S1:79-94]. The wallet
returns an opaque `context` and a `delegationManager`, and the session account redeems through ERC-7710
`redeemDelegations` [S1:138-154, 309]. The January 2026 revision **defines no permission types at all**. It defines
only `BasePermission`, `BaseRule` and one rule, `expiry` [S1:36-71]. Type names such as `native-token-allowance`
appear only in examples [S1:116-121, 242-253]. Enforcement is left wholly to the wallet: the rationale says the ERC
covers the wallet to dapp interaction, not how the wallet enforces permissions [S1:434], and "Wallets MUST correctly
enforce permissions." [S1:463]. There is no `signer` object in the current text. The previous revision (e1d58b0,
2025-02-20) used the method name `wallet_grantPermissions`, a `signer` with types `wallet`, `key`, `keys` and
`account`, and permission types `native-token-transfer`, `erc20-token-transfer`, `erc721-token-transfer`,
`erc1155-token-transfer`, `gas-limit`, `call-limit` and `rate-limit` [S2:16, 179-292]. All of those were removed.
The stream, periodic and allowance types and the `payee` and `redeemer` rules exist only in MetaMask's implementation
(block 1b), not in the ERC.

| Dim | Verdict | What exactly | Source | Quote (confirmed against raw copy) |
|---|---|---|---|---|
| D1 per-transaction cap | ND | No permission or rule type is defined. Types are open and are to be defined in further ERCs [S1:38-40]. The previous revision had none either. | S1:36-71, S2:229-292 | |
| D2 per-period cap | ND | Not defined. The previous revision had `rate-limit` (calls per interval), not an amount per period [S2:284-290]. | S1, S2 | |
| D3 total budget | ND | Not defined. Only the examples show `native-token-allowance` with an `allowance` value. | S1:116-121 | |
| D4 counterparty allowlist | ND | No payee rule in the ERC. `to` is the redeeming session account, not a payee. | S1:79-104 | |
| D5 per-counterparty cap | ND | Not defined. | S1 | |
| D6 asset, network, MCC | N (chain) / ND (asset) | One `chainId` per request [S1:81, 96]. Assets appear only in examples. No merchant category concept. | S1:81-96 | |
| D7 expiry | N | `ExpiryRule` with a unix `timestamp`, the only rule the ERC defines. No valid-from. | S1:64-71 | |
| D8 per-task credential | N | Each grant names a session account `to` that redeems; a dapp can request a fresh grant for a fresh account. Narrower authority depends on the (undefined) types. | S1:100-104, 309 | |
| D9 revocation | N (method) / ND (rest) | Who: the caller of `wallet_revokeExecutionPermission` (the dapp, through the provider). How: pass `permissionContext`; empty response on success [S1:191], although the response block shows a type named `GetPermissionsInfoResultParams` with `chainIds` [S1:203-207], an internal inconsistency. How fast: not specified. Third-party verifiable: not specified; the ERC does not say how a wallet enforces revocation [S1:434]. | S1:189-207, 434 | |
| D10 step-up above threshold | ND | The user approves or rejects each request at grant time [S1:404-405] and the wallet may attenuate it [S1:44, 148]. No runtime threshold. | S1:44, 148, 404-405 | |
| D11 task or intent id | ND | `context` identifies a permission for the dapp and wallet [S1:150]; nothing is carried to a payee. | S1:150 | |
| D12 audit export | ND | `wallet_getGrantedExecutionPermissions` lists current, non-revoked grants only. No transaction or decision log. | S1:257-305 | "The wallet MUST include all granted permissions that are not yet revoked." [S1:274] |
| D13 multi-rail policy | X | The data model binds each permission to one `chainId`; a request array can ask for several chains but each element is a separate grant with no shared budget. | S1:79-94 | |

**Test case.** (a) named counterparties: no, nothing defined. (b) per-task budget: not defined in the ERC.
(c) expiry: yes, `expiry` rule. (d) one-step revocation verifiable by a third party: a revoke method exists, but
verification is not specified. (e) credential per task: yes, a grant per session account.
**Full test case: no.** The ERC is now a transport for wallet-defined types; everything except expiry and the
revoke call is left to the wallet.

---

## 1b. MetaMask Advanced Permissions (MetaMask's ERC-7715 implementation)

- Vendor: MetaMask (Consensys).
- Status: shipped in MetaMask production according to the docs table [S11:9-17]: `erc20-token-periodic`,
  `erc20-token-stream`, `native-token-periodic` and `native-token-stream` from MetaMask v13.23.0;
  `erc20-token-allowance` and `native-token-allowance` from v13.32.1; `token-approval-revocation` from Smart Accounts
  Kit v1.6.0 with no MetaMask version listed. The concepts page frames it as permission sharing via the MetaMask
  browser extension [S10:23]. The user's account must be a MetaMask smart account: "The MetaMask user that the
  session account requests permissions from must be upgraded to a MetaMask smart account." [S10:19, link markup removed]
- Version read: docs.metamask.io/smart-accounts-kit (current, unversioned pages and the single-file docs bundle), fetched
  8 Oct 2026 [S10 to S17]. Code: MetaMask/snap-7715-permissions@60c8a92 (gator-permissions-snap 2.5.0,
  permissions-kernel-snap 1.3.0) [S18 to S20]; MetaMask/smart-accounts-kit@555dd20 (@metamask/smart-accounts-kit
  2.0.0, @metamask/7715-permission-types 2.0.0) [S21]; MetaMask/core@54294ae (gator-permissions-controller 6.0.1) [S22].
- Not verified: which MetaMask extension release bundles which snap version (the payee and redeemer rules arrived
  in gator-permissions-snap 2.0.0 [S18 CHANGELOG:70-75]).

**Control model.** The dapp (or agent) calls `wallet_requestExecutionPermissions`. The permissions kernel snap routes
it to the gator permissions snap, which shows a confirmation and, on approval, has the user's smart account sign one
ERC-7710 root delegation from the user's account (`from`) to the session account (`to`) [S18
GrantedPermissionResolutionService.ts:118-175]. The delegation carries the caveats for the permission type, then
`TimestampEnforcer` for an expiry rule, `RedeemerEnforcer` for a redeemer rule, a payee caveat for a payee rule,
and always a `NonceEnforcer` caveat [S18 GrantedPermissionResolutionService.ts:128-163]. The salt is random
[same file:165-167]. Enforcement is by the Delegation Framework contracts on chain (block 2b). The wallet accepts a
closed list: seven permission types, each with the rule types `expiry`, `redeemer` and `payee` (approval revocation:
`expiry`, `redeemer` only) [S20 7715-permissions-supported.ts:9-17]. Any other rule type and any duplicate rule type
is rejected [S20 7715-permissions-request.ts:35-46, 60-70]. Mapping to enforcers [S21 caveats/*.ts]: an allowance is
`ERC20PeriodTransferEnforcer` with `periodDuration` set to UINT256_MAX plus `ValueLteEnforcer(0)` [S21
erc20TokenAllowance.ts:44-57, 97-101]; the native allowance uses `NativeTokenPeriodTransferEnforcer` with
`ExactCalldataEnforcer` [S21 nativeTokenAllowance.ts:35-56]. The docs still describe a required `signer`
parameter [S10:15], a field the ERC removed in January 2026; the API reference uses `to` instead [S15].

| Dim | Verdict | What exactly | Source | Quote |
|---|---|---|---|---|
| D1 per-transaction cap | X | None of the seven types or three rules caps one transfer, and the snap rejects rule types outside its list. | S20 7715-permissions-supported.ts:9-17; 7715-permissions-request.ts:60-70; S14 | |
| D2 per-period cap | N | `erc20-token-periodic` and `native-token-periodic`: `periodAmount`, `periodDuration`, optional `startTime`. Unused allowance is forfeited each period (enforcer). Streams accrue per second. | S14; S12:70-127; S5 ERC20PeriodTransferEnforcer.sol:10-18 | |
| D3 total budget | N | `erc20-token-allowance` (`allowanceAmount`) and `native-token-allowance`; stream `maxAmount`. Allowance types need MetaMask v13.32.1. | S14; S11:11, 14; S21 erc20TokenAllowance.ts:97-101 | |
| D4 counterparty allowlist | N (with limit) | `payee` rule with `addresses`. Native token: a list, enforced by `AllowedTargetsEnforcer`. ERC-20: **exactly one payee per permission**, pinned with `AllowedCalldataEnforcer` at calldata offset 4; more than one address throws. | S13:59-79; S18 payeeCaveat.ts:40-69, 109-111; validation.ts:6-7 | "For ERC-20 permissions, allowedCalldataEnforcer supports one target." [S18 payeeCaveat.ts:75] |
| D5 per-counterparty cap | C | Only by requesting one permission per payee (each with its own payee rule and amount), each needing its own user approval. Within one permission all payees share one cap. | S18 payeeCaveat.ts:83-116; S20 7715-permissions-request.ts:36-45 | |
| D6 asset, network, MCC | N | `tokenAddress` per permission; one `chainId` per request; ERC-20 types force zero native value (`ValueLteEnforcer(0)`). No merchant category concept. | S14; S15; S21 erc20TokenAllowance.ts:52-57, 75-81 | |
| D7 expiry | N | `expiry` rule maps to `TimestampEnforcer`; `startTime` gives a valid-from. The kit makes a top-level `expiry` required. | S13:9-30; S15; S18 expiryCaveat.ts:9, 36 | |
| D8 per-task credential | N | The session account `to` is a separate key or smart account that "doesn't contain tokens" [S10:17]; each grant is its own delegation. A new task means a new grant and a new user approval. Narrower re-delegation by the session account is possible at the framework level (block 2b), not through the MetaMask confirmation. | S10:17; S18 GrantedPermissionResolutionService.ts:169-175 | |
| D9 revocation | N | Who: the user, through the MetaMask client; the snap accepts revocation records only from the `metamask` origin [S18 permissions.ts:14-17], and the kernel snap routes no `wallet_revokeExecutionPermission`, so a dapp or agent cannot revoke through the wallet RPC [S19 rpcMethod.ts:4-19]. How: an on-chain `disableDelegation` transaction; the snap refuses to record a revocation unless the delegation is already disabled on chain [S18 rpcHandler.ts:260-274], and the client submits it after the transaction confirms [S22 GatorPermissionsController.ts:729, 859-864]. Every grant also carries a `NonceEnforcer` caveat, so a nonce increment would revoke all of the account's grants at once; whether the MetaMask UI offers that: ND. How fast: from the block that includes the transaction. Third-party verifiable: yes, `disabledDelegations(hash)` and the `DisabledDelegation` event on the DelegationManager (block 2b). | S18, S19, S22, S5 | |
| D10 step-up above threshold | X | Approval happens once, at grant time, in the snap's confirmation (the user may adjust values if `isAdjustmentAllowed`). No rule type triggers approval above an amount during use. | S10:27; S20 7715-permissions-supported.ts:9-17 | |
| D11 task or intent id | C | Each redemption emits the signed delegation on chain (block 2b), so a payment links to the grant's delegation hash. The `justification` string is shown to the user but is not part of the signed delegation, and the salt is random, so a dapp cannot place a task id on chain through this API. | S14 (justification); S18 GrantedPermissionResolutionService.ts:165-175; S5 Types.sol:24-31 | |
| D12 audit export | C | `getGrantedExecutionPermissions` returns grants per site origin; the snap stores revocation metadata (tx hash, time) [S18 rpcHandler.ts:291-299]. Spends are on-chain events. No record of denied attempts. | S15; S18 rpcHandler.ts:291-299 | |
| D13 multi-rail policy | X | One chain per permission; the delegation signature is bound to that chain's DelegationManager domain (block 2b). | S15; S5 DelegationManager.sol:64-67 | |

**Test case.** (a) named counterparties only: yes for native ETH (a list); for an ERC-20 such as USDC only if the task
names exactly one payee, otherwise one permission per payee. (b) per-task budget: yes, an allowance type.
(c) ends when the task ends: yes, the expiry rule. (d) one-step revocation a third party can verify: yes, but only
the user can trigger it, from the MetaMask client, with an on-chain transaction; the agent or dapp cannot.
(e) a credential per task: yes, one grant per session account, each needing a fresh user approval.
**Full test case: partly.** It holds for a single ERC-20 payee or a native-token payee list. Missing: several ERC-20
payees in one grant, any per-payee cap inside one grant, a dapp or agent initiated revocation, and a task identifier
the payee can read.

---

## 2a. ERC-7710 "Smart Contract Delegation"

- Vendor: Ethereum ERC, four authors [S4:5]. Status: Draft [S4:7], requires ERC-1271 and ERC-7579 [S4:11].
- Version read: ethereum/ERCs@ee5363b `ERCS/erc-7710.md`, last changed by be46db7 (2025-06-10) [S3]. Read 8 Oct 2026.

**Control model.** The ERC defines one interface, `ERC7710Manager.redeemDelegations(bytes[] _permissionContexts,
bytes32[] _modes, bytes[] _executionCallData)`, with atomic batches [S4:90-131]. Terms: delegator, Delegation
Manager, delegation, delegate, redeemer [S4:63-69]. How delegations are obtained is out of scope [S4:71-73], and the
structure of a permission context is implementation-defined [S4:120]. There are no caveats, no revocation interface
and no events in the ERC. It only warns: "dApps MUST NOT assume that having received a delegation in the past
guarantees future execution rights. Delegations can be revoked, expire, or become invalid due to state changes."
[S4:197]. The security section ends with an open discussion marker [S4:204]. The motivation lists bounded permissions for AI
agents as a use [S4:44].

| Dim | Verdict | What exactly | Source |
|---|---|---|---|
| D1 to D7 | ND | No restriction vocabulary; contexts are opaque and implementation-defined. | S4:93-131 |
| D8 per-task credential | ND | A delegate distinct from the delegator is the core concept, but the scope of authority is left to the implementation. | S4:63-69, 120 |
| D9 revocation | ND | Revocation is mentioned as possible [S4:197]; no interface, actor or verification is defined. | S4:195-204 |
| D10 to D13 | ND | Not addressed. | S4 |

**Test case:** none of (a) to (e) is defined by the ERC itself. **Full test case: no.** It is a redemption
interface only; everything in the test case lives in an implementation such as block 2b.

---

## 2b. MetaMask Delegation Framework (DelegationManager, DeleGator accounts, caveat enforcers)

- Vendor: MetaMask (Consensys). Repository: github.com/MetaMask/delegation-framework.
- Status: Deployments.md lists 25 distinct mainnets (26 lines; Arbitrum One appears twice, once misspelt) and 25
  testnets [S8]; deployments not checked on chain. Latest tag v1.3.0 (released 2025-07-24) [S9];
  `DelegationManager.VERSION` is "1.3.0" [S5 DelegationManager.sol:32]. The README says tags are the audited
  versions and `main` is the development branch [S5 README.md:4].
- Version read: main at bff4b08 (2026-09-11). Compared with tag v1.3.0 (bfbdf97) by diff: the DelegationManager,
  interfaces, Types, Constants, EncoderLib, DeleGatorCore and every enforcer present in the tag are byte-identical,
  except SpecificActionERC20TransferBatchEnforcer.sol (main adds a configurable value for the first call) and
  documents/CaveatEnforcers.md (main adds the balance-change, approval-revocation and LogicalOrWrapper sections cited
  as S7). Five enforcers exist only on main (marked "main only"); Deployments.md nevertheless lists addresses for them
  under its v1.3.0 heading [S8]. Read 8 Oct 2026.

**Control model.** The principal's smart account (a DeleGator, or an EIP-7702 upgraded EOA) signs an EIP-712
`Delegation {delegate, delegator, authority, caveats[], salt, signature}` off chain [S5 Types.sol:24-31]. The
delegate redeems it by calling `DelegationManager.redeemDelegations` [S5 DelegationManager.sol:126-309], which checks
each signature (ECDSA for EOAs, ERC-1271 for contracts) [164-180], refuses any disabled delegation in the chain
[184-188], checks the chain of authority [191-202], runs every caveat's `beforeAllHook`/`beforeHook` for every link
[207-249], executes on the root delegator's account [252-253], then runs `afterHook`/`afterAllHook` [255-296] and
emits `RedeemedDelegation` per link [298-308]. A caveat is `{enforcer, terms, args}`: the enforcer contract holds the
rule, `terms` are signed, `args` are supplied by the redeemer and excluded from the hash [S5 Types.sol:33-42;
Constants.sol:12-16]. With no caveats a delegation allows any action [S5 README.md "Caveat Enforcers"]. Enforcement is
entirely on chain, by the DelegationManager and the enforcer contracts. The DelegationManager owner can pause all
redemptions [S5 DelegationManager.sol:74-83]; who holds that key on each chain was not verified.

### Every caveat enforcer in src/enforcers/ (37 concrete contracts plus the abstract base)

All read from the contract code at bff4b08. "Per delegation" state is keyed by (calling DelegationManager, delegation
hash).

| # | Enforcer | What it restricts (from the code) | Lines |
|---|---|---|---|
| 0 | CaveatEnforcer (abstract) | Base with empty hooks and call-type and exec-type modifiers. | CaveatEnforcer.sol:14-69 |
| 1 | AllowedCalldataEnforcer | One contiguous byte range of the calldata must equal a fixed value (one value per caveat). | AllowedCalldataEnforcer.sol:9-16, 77-89 |
| 2 | AllowedMethodsEnforcer | Function selector must be in a list. | AllowedMethodsEnforcer.sol:10-14, 69-84 |
| 3 | AllowedTargetsEnforcer | Call target address must be in a list (for a native transfer the target is the payee; for an ERC-20 transfer it is the token contract). | AllowedTargetsEnforcer.sol:9-13, 41-50 |
| 4 | ApprovalRevocationEnforcer (main only) | Delegate may only clear existing approvals (ERC-20 approve 0, ERC-721 approve, setApprovalForAll false, Permit2 approve 0, lockdown, invalidateNonces), chosen by bitmask. | ApprovalRevocationEnforcer.sol:11-35, 73-76 |
| 5 | ArgsEqualityCheckEnforcer | Redeemer-supplied `args` must equal the signed `terms`. | ArgsEqualityCheckEnforcer.sol:7-16, 46-49 |
| 6 | BlockNumberEnforcer | Valid only after and/or before given block numbers (exclusive). | BlockNumberEnforcer.sol:7-11, 36-46 |
| 7 | DeployedEnforcer | Deploys a contract by CREATE2 if not yet deployed and checks the address. | DeployedEnforcer.sol:10-14, 77 |
| 8 | ERC1155BalanceChangeEnforcer | Per execution, a named address's ERC-1155 balance may fall at most X or must rise at least X. | ERC1155BalanceChangeEnforcer.sol:9-22, 117-119 |
| 9 | ERC1155MultiOperationIncreaseBalanceEnforcer (main only) | A recipient's ERC-1155 balance must rise at least X across a whole redemption. | ERC1155MultiOperationIncreaseBalanceEnforcer.sol:9-26 |
| 10 | ERC20BalanceChangeEnforcer | Per execution, a named address's ERC-20 balance may fall at most X (`enforceDecrease`) or must rise at least X. | ERC20BalanceChangeEnforcer.sol:9-22, 44-104 |
| 11 | ERC20MultiOperationIncreaseBalanceEnforcer (main only) | A recipient's ERC-20 balance must rise at least X across a whole redemption. | ERC20MultiOperationIncreaseBalanceEnforcer.sol:9-26 |
| 12 | ERC20PeriodTransferEnforcer | One token, `transfer` only, at most `periodAmount` per `periodDuration` from `startDate`; unused amount lapses. | ERC20PeriodTransferEnforcer.sol:10-18, 181-218 |
| 13 | ERC20StreamingEnforcer | One token, `transfer` only: `initialAmount` at `startTime`, then linear accrual, capped by `maxAmount`. | ERC20StreamingEnforcer.sol:10-24, 160-184 |
| 14 | ERC20TransferAmountEnforcer | One token, `transfer` only, lifetime total per delegation. | ERC20TransferAmountEnforcer.sol:10-14, 85-97 |
| 15 | ERC721BalanceChangeEnforcer | Per execution, a named address's ERC-721 balance may fall at most X or must rise at least X. | ERC721BalanceChangeEnforcer.sol:9-22, 113-115 |
| 16 | ERC721MultiOperationIncreaseBalanceEnforcer (main only) | A recipient's ERC-721 balance must rise at least X across a whole redemption. | ERC721MultiOperationIncreaseBalanceEnforcer.sol:9-26 |
| 17 | ERC721TransferEnforcer | Only a transfer of one specific token id of one contract (any recipient except zero). | ERC721TransferEnforcer.sol:9-13, 39-70 |
| 18 | ExactCalldataBatchEnforcer | Batch: each execution's calldata must match exactly. | ExactCalldataBatchEnforcer.sol:10-14, 46-50 |
| 19 | ExactCalldataEnforcer | Calldata must match exactly. | ExactCalldataEnforcer.sol:9-13, 40-44 |
| 20 | ExactExecutionBatchEnforcer | Batch: each execution's target, value and calldata must match exactly. | ExactExecutionBatchEnforcer.sol:10-14, 46-49 |
| 21 | ExactExecutionEnforcer | Target, value and calldata must match exactly. | ExactExecutionEnforcer.sol:10-14, 65 |
| 22 | IdEnforcer | An id may be redeemed once per delegator; other delegations with the same id then fail (mutual exclusion). | IdEnforcer.sol:9-15, 46-49 |
| 23 | LimitedCallsEnforcer | Lifetime number of redemptions per delegation. | LimitedCallsEnforcer.sol:7-12, 45-48 |
| 24 | LogicalOrWrapperEnforcer | OR over groups of caveats; the redeemer picks the group at execution time. | LogicalOrWrapperEnforcer.sol:11-51, 250-275 |
| 25 | MultiTokenPeriodEnforcer | Per-period caps for several tokens (address 0 = native), config chosen by an index in `args`; explicitly no recipient restriction. | MultiTokenPeriodEnforcer.sol:10-31, 259-303 |
| 26 | NativeBalanceChangeEnforcer | Per execution, a named address's ETH balance may fall at most X or must rise at least X. | NativeBalanceChangeEnforcer.sol:7-20, 96-98 |
| 27 | NativeTokenMultiOperationIncreaseBalanceEnforcer (main only) | A recipient's ETH balance must rise at least X across a whole redemption. | NativeTokenMultiOperationIncreaseBalanceEnforcer.sol:7-24 |
| 28 | NativeTokenPaymentEnforcer | The redeemer must pay a fixed ETH amount to a fixed recipient (through a second, allowance delegation) for the right to use this delegation. | NativeTokenPaymentEnforcer.sol:11-23, 65-114 |
| 29 | NativeTokenPeriodTransferEnforcer | ETH value at most `periodAmount` per period. | NativeTokenPeriodTransferEnforcer.sol:9-17, 161-200 |
| 30 | NativeTokenStreamingEnforcer | ETH linear stream with initial amount and `maxAmount`. | NativeTokenStreamingEnforcer.sol:8-22, 141-165 |
| 31 | NativeTokenTransferAmountEnforcer | Lifetime total ETH value per delegation. | NativeTokenTransferAmountEnforcer.sol:9-13, 51-57 |
| 32 | NonceEnforcer | Delegation valid only while the delegator's current nonce equals the signed nonce; `incrementNonce` invalidates all older ones. | NonceEnforcer.sol:7-12, 43-44, 62-68 |
| 33 | OwnershipTransferEnforcer | Only `transferOwnership` on one ERC-173 contract. | OwnershipTransferEnforcer.sol:10-14, 77-83 |
| 34 | RedeemerEnforcer | `msg.sender` of `redeemDelegations` must be in a list (a DeleGator redeemer can be driven by its own delegations). | RedeemerEnforcer.sol:7-12, 37-42 |
| 35 | SpecificActionERC20TransferBatchEnforcer | One-shot two-call batch: an exact first call, then an ERC-20 `transfer` of an exact amount to one named recipient. | SpecificActionERC20TransferBatchEnforcer.sol:11-18, 72-107 |
| 36 | TimestampEnforcer | Valid only after and/or before given unix times (exclusive). | TimestampEnforcer.sol:7-12, 36-46 |
| 37 | ValueLteEnforcer | Native value of each call at most X. | ValueLteEnforcer.sol:9-14, 40-42 |

### Answers to the specific questions

**Per-recipient cap (D5).** No enforcer caps the amount per recipient. The amount enforcers (#12, #13, #14, #29, #30,
#31, #25) read the amount from the calldata or the value and never read the recipient (for example
ERC20TransferAmountEnforcer.sol:85-97 reads only bytes 36 to 68). MultiTokenPeriodEnforcer says so in its header:
"Additionally, the enforcer does not support restrictions on the recipient address or arbitrary calldata."
[MultiTokenPeriodEnforcer.sol:25-26]. The only enforcer that names a recipient and an amount together is #35, which
is single-use, exact-amount and needs a fixed two-call batch. So a per-counterparty cap needs either one delegation
per payee (payee pin plus amount enforcer in each), or a custom enforcer. Composing per-payee groups inside one
delegation with LogicalOrWrapperEnforcer does not give independent budgets when each group reuses the same amount
enforcer: the wrapper calls inner enforcers itself and passes the same delegation hash [LogicalOrWrapperEnforcer.sol:
260-272], and the amount enforcers key their counter by caller and delegation hash [ERC20TransferAmountEnforcer.sol:
20, 96], so the groups share one counter (inference from code). The framework's own docs describe this context switch
[S7:316-323], and the redeemer chooses the group [LogicalOrWrapperEnforcer.sol:40-43].

**Revocation (D9).** (1) `DelegationManager.disableDelegation(delegation)` sets `disabledDelegations[hash] = true` and
emits `DisabledDelegation(hash indexed, delegator indexed, delegate indexed, delegation)` [DelegationManager.sol:
90-95; IDelegationManager.sol:22-24]. Only the delegator of that delegation can call it [DelegationManager.sol:53-56,
90]; a DeleGator account exposes it to its owner or the EntryPoint [DeleGatorCore.sol:364-366]. The docs: "Delegators
can disable a delegation by calling the function `disableDelegation(delegation)` of the DelegationManager, this is an
onchain operation that requires paying gas." [S6:27]. Every redemption checks every link of the chain
[DelegationManager.sol:184-188], so disabling a parent kills all children. The delegator can undo it with
`enableDelegation` [103-108]. (2) `NonceEnforcer.incrementNonce(delegationManager)` bumps the caller's own nonce, emits
`UsedNonce` and invalidates every delegation of that delegator carrying the old nonce [NonceEnforcer.sol:16-20, 62-68].
(3) The DelegationManager owner can `pause()` all redemptions [DelegationManager.sol:74-76], a global stop outside the
principal's control. Third-party check: yes. `disabledDelegations(bytes32)` and `getDelegationHash` are public
[DelegationManager.sol:44, 324-326], `currentNonce` is public [NonceEnforcer.sol:16], and both actions emit events. A
payee needs the delegation (or its hash) to check; it appears in `RedeemedDelegation` logs of earlier payments.
Effective from the block that includes the transaction.

**Chains and narrower re-delegation (per-task keys).** Yes. A chain is ordered leaf to root; each link's `authority`
must equal the parent's hash and the parent's `delegate` must be the child's `delegator` (or `ANY_DELEGATE`)
[DelegationManager.sol:183-203]. The caveats of every link run on every redemption [207-249], so a child can only add
restrictions, never remove the parent's. The docs: "Bob can add extra restrictions when he re-delegates to Carol in
addition to what the initial delegation had, to understand what the delegation can do, it is necessary to analyze all
the enforcers being used in the entire delegation chain." [S6:64]. Limits: only a link's own delegator can disable that
link, so a principal cannot revoke one per-task child its agent signed, only the agent's parent delegation (all tasks)
or its nonce. Stateful caveats placed inside a LogicalOrWrapperEnforcer get a separate state namespace [S7:323-343].

**Identifier a payee or auditor can see (D11).** The delegation hash is indexed in the amount enforcers' events
(`IncreasedSpentMap`, `TransferredInPeriod`) and in `DisabledDelegation`; `RedeemedDelegation(rootDelegator indexed,
redeemer indexed, Delegation)` carries the whole signed struct, including `salt` and caveat terms
[IDelegationManager.sol:14; DelegationManager.sol:298-308]. `salt` is a free signed uint256 [Types.sol:29;
Constants.sol:12-14], so a principal could encode a task id there, but no document defines that use. IdEnforcer's id is
logged in `UsedId` [IdEnforcer.sol:24, 49], but its meaning is single use among delegations, not a purpose code. One
trap for auditors: the period enforcers document their event field `redeemer` as "The address that receives the
tokens" [ERC20PeriodTransferEnforcer.sol:42], but it is the redeemer passed by the DelegationManager
[DelegationManager.sol:239-247]; the actual payee in the calldata is neither checked nor logged by those enforcers.

| Dim | Verdict | What exactly | Source | Quote |
|---|---|---|---|---|
| D1 per-transaction cap | N (native) / C (ERC-20) | ValueLteEnforcer caps native value per call. For ERC-20, ERC20BalanceChangeEnforcer with `enforceDecrease` on the delegator's own address caps the fall per execution. | ValueLteEnforcer.sol:40-42; ERC20BalanceChangeEnforcer.sol:44-104 | |
| D2 per-period cap | N | ERC20PeriodTransferEnforcer, NativeTokenPeriodTransferEnforcer, MultiTokenPeriodEnforcer (fixed periods from a start date); streaming enforcers for rates. | enforcers #12, #25, #29, #13, #30 | |
| D3 total budget | N | ERC20TransferAmountEnforcer and NativeTokenTransferAmountEnforcer (lifetime per delegation); stream `maxAmount`; LimitedCallsEnforcer for a call count. | ERC20TransferAmountEnforcer.sol:85-97; NativeTokenTransferAmountEnforcer.sol:51-57 | |
| D4 counterparty allowlist | N (native, ERC-20 single) / C (ERC-20 several) | Native: AllowedTargetsEnforcer with the payee list. ERC-20: AllowedCalldataEnforcer pinning the `to` word at offset 4, one payee per caveat; pair it with an enforcer that fixes the `transfer` selector, since `approve(payee, x)` has the same layout. Several ERC-20 payees: one group per payee in LogicalOrWrapperEnforcer. | AllowedTargetsEnforcer.sol:41-50; AllowedCalldataEnforcer.sol:77-89; LogicalOrWrapperEnforcer.sol:11-51 | |
| D5 per-counterparty cap | C (one delegation per payee) / CODE (one delegation) | No per-recipient enforcer; see the answer above. | MultiTokenPeriodEnforcer.sol:25-28; LogicalOrWrapperEnforcer.sol:260-272 | "Additionally, the enforcer does not support restrictions on the recipient address or arbitrary calldata." [MultiTokenPeriodEnforcer.sol:25-26] |
| D6 asset, network, MCC | N | Token address in each ERC-20 enforcer's terms; native vs token; the chain is fixed by the EIP-712 domain of the DelegationManager the delegation was signed for. No merchant category concept. | ERC20PeriodTransferEnforcer.sol:149-160; DelegationManager.sol:64-67, 166-176 | |
| D7 expiry | N | TimestampEnforcer (after/before), BlockNumberEnforcer. Hours of day would need code. | TimestampEnforcer.sol:36-46 | |
| D8 per-task credential | N | `delegate` is any address, one delegation per task key; narrower re-delegation in chains; `ANY_DELEGATE` for open delegations. | Types.sol:24-31; DelegationManager.sol:41, 183-203 | |
| D9 revocation | N | Who: the delegator of that delegation (and, globally, the DelegationManager owner by pause). How: `disableDelegation` or `NonceEnforcer.incrementNonce`, on-chain transactions paying gas. How fast: from inclusion in a block. Third-party verifiable: yes, public `disabledDelegations` and `currentNonce` plus events; reversible by `enableDelegation`. | DelegationManager.sol:44, 53-56, 74-76, 90-108; NonceEnforcer.sol:16-20, 62-68; S6:27 | |
| D10 step-up above threshold | CODE | No enforcer pauses for a human above an amount; a custom enforcer would be needed. | enforcer list above | |
| D11 task or intent id | C | Delegation hash in events, full signed delegation in `RedeemedDelegation`, free `salt`; nothing in the token transfer itself. | IDelegationManager.sol:14-24; Types.sol:29 | |
| D12 audit export | C | Allowed spends leave events (`RedeemedDelegation`, `IncreasedSpentMap`, `TransferredInPeriod`, `IncreasedCount`, `UsedId`). A denied redemption reverts and leaves no event (EVM rule; for example ArgsEqualityCheckEnforcer emits `DifferentArgsAndTerms` and then reverts, which discards it). | DelegationManager.sol:298-308; ArgsEqualityCheckEnforcer.sol:46-49 | |
| D13 multi-rail policy | X | A delegation's signature is checked against one DelegationManager's EIP-712 domain, which includes the chain id, so one delegation works on one chain; budgets on other chains are separate delegations with separate counters. | DelegationManager.sol:64-67, 164-180 | |

**Test case.** (a) named counterparties only: yes, natively for native ETH (AllowedTargetsEnforcer) and for one ERC-20
payee (AllowedCalldataEnforcer at offset 4), by composition for several ERC-20 payees (LogicalOrWrapperEnforcer).
(b) per-task budget: yes, ERC20TransferAmountEnforcer on the task's delegation. (c) ends when the task ends: yes,
TimestampEnforcer. (d) one-step revocation a third party can verify: yes, `disableDelegation` plus the public
`disabledDelegations` mapping; but the delegator can re-enable it, and only the signer of that delegation can disable
it. (e) credential per task: yes, a delegation to a per-task key, or a narrower re-delegation from the agent's key.
**Full test case: yes, by configuration (C).** Nothing packages it as one object; the principal must pick and order
four to six enforcers correctly. Missing natively: a per-payee cap inside one delegation, a revocation that cannot be
undone, a principal-side revoke of a child delegation the agent signed, and a task identifier carried with the
payment.

---

## Sources

- [S1] ethereum/ERCs@ee5363b `ERCS/erc-7715.md` (raw/ERCs/ERCS/erc-7715.md), cloned 2026-10-08.
- [S2] https://raw.githubusercontent.com/ethereum/ERCs/e1d58b0afa/ERCS/erc-7715.md (previous revision, 2025-02-20),
  fetched 2026-10-08, raw/raw.githubusercontent.com/erc-7715-at-e1d58b0.md.
- [S3] https://api.github.com/repos/ethereum/ERCs/commits?path=ERCS/erc-7715.md and ?path=ERCS/erc-7710.md, fetched
  2026-10-08, raw/api.github.com/ercs-commits-erc-7715.json and ercs-commits-erc-7710.json.
- [S4] ethereum/ERCs@ee5363b `ERCS/erc-7710.md` (raw/ERCs/ERCS/erc-7710.md).
- [S5] MetaMask/delegation-framework@bff4b08 (main; tag v1.3.0 = bfbdf97): `src/DelegationManager.sol`,
  `src/interfaces/IDelegationManager.sol`, `src/utils/Types.sol`, `src/utils/Constants.sol`, `src/DeleGatorCore.sol`,
  `src/enforcers/*.sol`, `README.md` (raw/delegation-framework/).
- [S6] MetaMask/delegation-framework@bff4b08 `documents/DelegationManager.md`.
- [S7] MetaMask/delegation-framework@bff4b08 `documents/CaveatEnforcers.md`.
- [S8] MetaMask/delegation-framework@bff4b08 `documents/Deployments.md`.
- [S9] https://api.github.com/repos/MetaMask/delegation-framework/tags and /releases, fetched 2026-10-08,
  raw/api.github.com/delegation-framework-tags.json and delegation-framework-releases.json.
- [S10] https://docs.metamask.io/smart-accounts-kit/concepts/advanced-permissions.md, fetched 2026-10-08,
  raw/docs.metamask.io/sak-concepts-advanced-permissions.md.
- [S11] https://docs.metamask.io/smart-accounts-kit/get-started/supported-advanced-permissions.md, fetched 2026-10-08,
  raw/docs.metamask.io/sak-supported-advanced-permissions.md.
- [S12] https://docs.metamask.io/smart-accounts-kit/guides/advanced-permissions/use-permissions/erc20-token.md, fetched
  2026-10-08, raw/docs.metamask.io/sak-erc20-token-permissions.md (native token page:
  raw/docs.metamask.io/sak-native-token-permissions.md).
- [S13] https://docs.metamask.io/smart-accounts-kit/reference/advanced-permissions/rules.md, fetched 2026-10-08,
  raw/docs.metamask.io/sak-ref-rules.md.
- [S14] https://docs.metamask.io/smart-accounts-kit/reference/advanced-permissions/permissions.md, fetched 2026-10-08,
  raw/docs.metamask.io/sak-ref-permissions.md.
- [S15] https://docs.metamask.io/smart-accounts-kit/reference/advanced-permissions/wallet-client.md, fetched
  2026-10-08, raw/docs.metamask.io/sak-ref-wallet-client.md.
- [S16] https://docs.metamask.io/smart-accounts-kit/guides/delegation/disable-delegation.md, fetched 2026-10-08,
  raw/docs.metamask.io/sak-disable-delegation.md (caveat builders reference: raw/docs.metamask.io/sak-ref-caveats.md).
- [S17] https://docs.metamask.io/llms-smart-accounts-kit-full.txt, fetched 2026-10-08,
  raw/docs.metamask.io/llms-smart-accounts-kit-full.txt (whole docs set in one file, used for searching).
- [S18] MetaMask/snap-7715-permissions@60c8a92 `packages/gator-permissions-snap/` (src/core/payeeCaveat.ts,
  src/core/expiryCaveat.ts, src/core/grant/GrantedPermissionResolutionService.ts, src/rpc/rpcHandler.ts,
  src/rpc/permissions.ts, src/permissions/validation.ts, CHANGELOG.md).
- [S19] MetaMask/snap-7715-permissions@60c8a92 `packages/permissions-kernel-snap/src/rpc/rpcMethod.ts`.
- [S20] MetaMask/snap-7715-permissions@60c8a92 `packages/shared/src/types/7715-permissions-supported.ts` and
  `7715-permissions-request.ts`.
- [S21] MetaMask/smart-accounts-kit@555dd20 `packages/7715-permission-types/src/permissions/caveats/*.ts` and
  `src/types.ts` (lines 288-301 type `wallet_revokeExecutionPermission` without a wallet route).
- [S22] MetaMask/core@54294ae `packages/gator-permissions-controller/src/GatorPermissionsController.ts` (sparse clone).

## Blocked or unverifiable

- GitHub REST API rate limit hit once (contents listing of the v1.3.0 tag); replaced by `git fetch --depth 1 origin
  tag v1.3.0` and `git ls-tree`. No pages were blocked.
- Not verified: which MetaMask extension release ships which gator-permissions-snap version; whether the MetaMask UI
  exposes a nonce increment; who holds the DelegationManager owner key on each chain; MetaMask mobile support.
- No page addressed instructions to the reader.

## Most surprising gaps

1. ERC-7715 now defines no permission types. Since the January 2026 revision it carries only an `expiry` rule; every
   spending type and the `payee` rule are MetaMask-specific names that another wallet need not honour.
2. MetaMask's ERC-20 `payee` rule takes exactly one address and throws on two, so paying three named merchants in
   USDC needs three separate grants and three user approvals.
3. Among 37 enforcers none caps spend per recipient, and MultiTokenPeriodEnforcer says outright that it cannot restrict
   the recipient. Reusing one amount enforcer across LogicalOrWrapperEnforcer groups shares a single counter
   (inference from code).
4. Revocation is checkable on chain but reversible (`enableDelegation`), and only the delegator of that exact link can
   do it, so a principal cannot revoke a single per-task key its agent created.
5. In MetaMask only the user, inside the MetaMask client, can revoke; the ERC's `wallet_revokeExecutionPermission` is
   not routed by the kernel snap, so the agent cannot hand back its own authority.
6. The DelegationManager owner can pause every redemption on a chain, and denied attempts leave no on-chain trace.
7. Period enforcer events document the redeemer field as the token recipient, which misleads an auditor
   reconstructing payees from enforcer logs.

## Possibly missing from the teardown

- Zodiac Roles Modifier (Gnosis Guild): widely used on Safe; parameter conditions with allowances that refill per
  period, a candidate for per-counterparty caps. https://docs.roles.gnosisguild.org/
- Safe Allowance Module: per-delegate, per-token spending limits with a reset period on Safe accounts.
  https://github.com/safe-global/safe-modules/tree/main/modules/allowances
- ZeroDev permissions (Kernel): ERC-7579 permission validators with call and rate policies, used for agent session
  keys. https://docs.zerodev.app/sdk/permissions/intro
