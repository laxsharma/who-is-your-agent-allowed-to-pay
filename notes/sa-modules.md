# Group sa-modules: smart-account permission modules (read 8 Oct 2026)

Scope: Rhinestone Smart Sessions, ZeroDev Kernel permissions, Biconomy (Nexus plus sessions), Safe Allowance
module, Zodiac Roles Modifier v2. Everything below is from contract code at a pinned commit unless a cell says
it comes from docs. No repository code was run. Clones were shallow, are cited as raw/<project>, and are
listed in [SOURCES.md](../SOURCES.md). Source ids resolve in the Sources list at the end.

Common facts for all five items (all EVM smart-contract enforcement):
- The object the principal limits is an on-chain grant attached to a smart account (Safe, ERC-7579 account,
  Kernel). Enforcement is the smart contract during ERC-4337 validation or during the module call. No vendor
  server sits in the enforcement path for items 1, 2, 4, 5 (Rhinestone's newer v2 flow adds an orchestrator,
  see item 1 notes).
- A refused action reverts. Nothing is written on chain for a denial, so no item has a deny log (D12).
- Each grant lives on one chain. Several items let one owner signature authorize grants on several chains,
  but every chain keeps its own counters, so no item has a single budget shared across chains (D13).

---

## 1. Rhinestone Smart Sessions (ERC-7579 validator module)

Header
- Vendor: Rhinestone, co-authored with Biconomy (README authors line).
- Status: the repo README says beta: "This software is in beta and should be used at your own risk." [S1
  README.md:48]. Audited (see below). Tag v1.0.0 points at dc20f0b, a different commit from the main head read here.
- Code read: erc7579/smartsessions@f5aaf86 (main, last commit 2025-08-04) [S1]. Also read the newer
  rhinestonewtf/smart-sessions-v2@7c0e8d7 (SmartSessionEmissary) [S2], because Rhinestone's own SDK now points
  at v2, not v1 [S3 src/modules/validators/smart-sessions/module.ts:4-7]. Biconomy (item 3) still uses v1.
- Docs read: docs.rhinestone.dev pages saved 2026-10-08 [S4 to S11].
- Who installs: the account itself (ERC-7579 installModule, so the account owner's validator must approve), or
  "enable mode", where the session is enabled inside the first user operation under a signature from the
  account [S1 contracts/SmartSession.sol:146-156].
- Chains: not stated per module. Rhinestone's orchestrator catalog lists 24 mainnets and 6 testnets [S10
  chains.json], but it includes non-EVM chains (Solana, Tron, Stellar), so it is a routing catalog and not a
  Smart Sessions deployment list. The v2 SDK keeps per-chain address lists for some policies [S3
  policies/addresses.ts:30-40].
- Audits listed: Cantina core and external-policies reports (Oct 2024), Renascence v1 and update (Nov and Dec
  2024), ChainLight (Jul 2025, PRs 122, 159, 162, which include ArgPolicy and ContractWhitelistPolicy), all in
  the repo audits/ folder [S1 audits/; S9]. Smart Sessions v2: ChainLight Q4 2025 report [S2 audits/; S9].

Control model
- A session (identified by `permissionId`) is the per-task credential. `Session` holds: `sessionValidator` plus
  `sessionValidatorInitData` (who signs, for example one ECDSA key or a multisig of keys), a `salt`,
  `userOpPolicies` (checked on every user operation), `erc7739Policies` (which off-chain ERC-1271 signatures the
  session may produce: allowed EIP-712 app domains and content types plus ERC-1271 policies), `actions` (one
  entry per target contract plus function selector, each with its own action policies) and
  `permitERC4337Paymaster` [S1 contracts/DataTypes.sol:56-64, 76-86, 103-106].
- `permissionId = keccak256(sessionValidator, sessionValidatorInitData, salt)` [S1 contracts/lib/IdLib.sol:79-82],
  so the principal can mint one session per task by choosing a fresh key or salt.
- An action is keyed by `keccak256(target, selector)`. A native-coin send with empty calldata is keyed on the
  payee address with a special VALUE selector [S1 contracts/lib/PolicyLib.sol:189-191, 214-215], so a native
  payee allowlist is one action per payee. A session may not call the Smart Sessions module itself unless a
  special sentinel action is set [S1 PolicyLib.sol:209-211].
- Every policy must pass; a failing policy reverts validation [S1 PolicyLib.sol:157]. Each execution must match
  at least one action policy [S1 SmartSession.sol:285, 299].
- Policy contracts shipped in the repo [S1 contracts/external/policies/]:
  - SudoPolicy: always passes (user op, action and ERC-1271) [SudoPolicy.sol:22-50].
  - ERC20SpendingLimitPolicy: per token, a lifetime cap on transfer, transferFrom, approve and
    increaseAllowance amounts; rejects any native value; no reset; emits TokenSpent per spend
    [ERC20SpendingLimitPolicy.sol:48-83, 94-157]. It does not look at the recipient.
  - ValueLimitPolicy: lifetime cap on native value, as a user-op policy (whole op) or per action
    [ValueLimitPolicy.sol:34-91].
  - UsageLimitPolicy: lifetime count of uses [UsageLimitPolicy.sol:47-57].
  - TimeFramePolicy: validAfter and validUntil, returned to the EntryPoint as ERC-4337 validation data; works as
    user-op, action or ERC-1271 policy [TimeFramePolicy.sol:36-95, 107-116].
  - UniActionPolicy: up to 16 calldata argument rules (EQUAL, GREATER_THAN, LESS_THAN, GTE, LTE, NOT_EQUAL,
    IN_RANGE), all ANDed, each optionally "limited" (adds the argument value to a lifetime counter), plus
    `valueLimitPerUse` for native value [UniActionPolicy.sol:11-42, 84-92, 126-159].
  - ArgPolicy: the same rules combined in an AND, OR, NOT expression tree of up to 128 rules, with short-circuit
    evaluation, plus `valueLimitPerUse` [ArgPolicy/ArgPolicy.sol:128-153; lib/ArgPolicyTreeLib.sol:195-245].
  - ContractWhitelistPolicy: action policy that passes only listed targets, meant for the fallback action
    [ContractWhitelistPolicy.sol:10-42].
  - SimpleGasPolicy: lifetime cap on gas units and on gas cost for the session [SimpleGasPolicy.sol:34-66].
  - No shipped policy resets a counter by period: grep for period, reset, refill or interval in contracts/
    returns nothing [S1].
- Removal: `removeSession(permissionId)` deletes every policy list, the validator and the paymaster flag for
  `msg.sender`, and emits `SessionRemoved(permissionId, smartAccount)` [S1 contracts/core/SmartSessionBase.sol:
  329-355]. Because storage is keyed by `msg.sender`, only the account itself can remove its sessions, which
  means the owner (or anyone the owner lets execute calls to the module). Uninstalling the module removes all
  sessions [SmartSessionBase.sol:400-408]. A signed enable that was never used is cancelled separately with
  `revokeEnableSignature`, which bumps a nonce and emits `NonceIterated` [S1 contracts/core/NonceManager.sol:
  29-32]. Anyone can check `isPermissionEnabled(permissionId, account)` [SmartSessionBase.sol:444-446].
- Smart Sessions v2 (what Rhinestone's SDK uses): `removeConfig` disables a session and emits
  `SmartSessionEmissaryConfigDisabled`, but if an allocator is configured the allocator must co-sign the
  disable as well as the user [S2 src/core/SmartSessionLens.sol:205-214, 266-306; src/lib/SignatureLib.sol:
  54-66]. The Rhinestone SDK sets the allocator to the zero address [S3 src/modules/validators/smart-sessions/
  calls.ts:23-27], so in that path the account can disable alone. Rhinestone's embedded-wallet docs say that
  SDK has no revoke method for app integrations [S5 line 68].

| Dim | Code | What exactly is supported | Sources | Quote |
|---|---|---|---|---|
| D1 per-transaction cap | N | UniActionPolicy or ArgPolicy rule `LESS_THAN_OR_EQUAL` on the amount argument; `valueLimitPerUse` for native value. | S1 UniActionPolicy.sol:84-92, 126-159; S7 call.md | none |
| D2 per-period cap | C | No shipped policy resets by period. A principal can pre-mint one session per period, each with a TimeFramePolicy window and its own lifetime cap. Rolling windows need a custom IPolicy contract (CODE). | S1 contracts/external/policies/ (no reset logic); S1 interfaces/IPolicy.sol:17-69 | none |
| D3 total budget | N | ERC20SpendingLimitPolicy (lifetime per token), UniActionPolicy limited rule (lifetime sum of an argument), ValueLimitPolicy (lifetime native). Counters are per action and per chain, not one session-wide counter. | S1 ERC20SpendingLimitPolicy.sol:94-157; ValueLimitPolicy.sol:87-91; S4 line 91 | "They do not create one shared session-wide counter." [S4 line 91, confirmed] |
| D4 counterparty allowlist | N | Native: one action per payee address. ERC-20: EQUAL rule on the recipient argument (one payee) or ArgPolicy OR tree (several); Rhinestone SDK exposes `anyOf`. | S1 PolicyLib.sol:189-215; ArgPolicyTreeLib.sol:230-240; S7 call.md | none |
| D5 per-counterparty cap | C | ArgPolicy tree `(to==A AND amount limited LA) OR (to==B AND amount limited LB)`; short-circuit evaluation means only the matching branch's counter moves. Native: separate action per payee, each with ValueLimitPolicy. Composition is mine from code, not a documented recipe. | S1 ArgPolicyTreeLib.sol:72-124, 219-240 | none |
| D6 asset, network, MCC | N | Asset by action target (token contract) and ERC20SpendingLimitPolicy token list; chain by where the session is enabled (enable digest carries chainId). No merchant category concept. | S1 ERC20SpendingLimitPolicy.sol:48-83; contracts/lib/HashLib.sol:105-108, 318 | none |
| D7 expiry or time window | N | TimeFramePolicy validAfter and validUntil (seconds), per user op, per action or for ERC-1271. No hours-of-day rule. | S1 TimeFramePolicy.sol:88-95, 107-116; S7 timeframe.md | none |
| D8 per-task credential | N | Each session has its own validator config (one key, multisig, passkey) and salt, so a fresh permissionId per task; authority is limited to listed actions and policies. Caveat: Rhinestone's SDK defaults to sudo when no permissions are given. | S1 DataTypes.sol:56-64; IdLib.sol:79-82; S7 sudo.md line 7 | "a session with no `permissions` accepts everything" [S7 sudo.md line 7, confirmed, partial sentence] |
| D9 revocation | N | Who: the account (owner) only, since storage is keyed by msg.sender. How: `removeSession(permissionId)` per chain, or uninstall the module; `revokeEnableSignature` for a signed but unused enable. v2: `removeConfig`, allocator co-signature needed if an allocator is set. How fast: the block in which the owner's transaction lands. Third party: yes, `SessionRemoved` event and `isPermissionEnabled` view; one call per chain for a multi-chain grant. | S1 SmartSessionBase.sol:329-355, 444-446; NonceManager.sol:29-32; S2 SmartSessionLens.sol:266-306; S5 line 78 | "For a multi-chain grant, authority can remain active on one chain after it has been removed from another." [S5 line 78, confirmed] |
| D10 human step-up | C | No amount-triggered approval. By composition: a low-cap session for the agent key plus a higher-cap session whose validator is a multisig that includes a human key. Not documented as a step-up pattern. | S11 multisig.md; S1 DataTypes.sol:56-64 | none |
| D11 task or purpose binding | C | No memo field. The permissionId (which can include a principal-chosen salt such as a task hash) travels in the user operation signature, so an auditor can decode it from handleOps calldata; the payee's transfer carries nothing. | S1 SmartSession.sol:84; IdLib.sol:79-82 | none |
| D12 audit record | N for allows, X for denies | Allows: SessionCreated, PolicyEnabled, SessionRemoved events; TokenSpent per ERC-20 spend; other policies emit nothing per use. Denies: validation reverts with PolicyViolation, so nothing is recorded. No vendor export API found for v1. | S1 ISmartSession.sol:56-65; ERC20SpendingLimitPolicy.sol:155; PolicyLib.sol:157 | none |
| D13 one policy across rails | C | One owner signature can enable sessions on several EVM chains (MultiChainSession digest); each chain still enforces and counts separately. EVM only. | S1 HashLib.sol:64-67, 105-108; S8 multi-chain-sessions.md | none |

Test case
- (a) named counterparties only: yes (native per payee; ERC-20 via EQUAL or ArgPolicy OR).
- (b) per-task budget: yes, per token and per chain (ERC20SpendingLimitPolicy or a limited UniAction rule).
- (c) ends when the task ends: yes by time (TimeFramePolicy); no "task finished" trigger other than removal.
- (d) one-step, third-party-verifiable revocation: yes on one chain (`removeSession`, `SessionRemoved`,
  `isPermissionEnabled`); one call per chain for multi-chain grants; unused signed enables need a second call.
- (e) credential per task: yes.
- Full test case: yes on a single chain. Missing: a budget shared across chains, a deny log, a payee-visible
  task id. Risks: the SDK default is sudo; in Rhinestone v2 a scoped session without `restrictToActions` keeps a
  wildcard fallback that executes unmatched calls as orchestrator intents [S6 line 9].

---

## 2. ZeroDev Kernel permissions (Kernel v3.3 plus kernel-7579-plugins policies)

Header
- Vendor: ZeroDev. Status: Kernel v3.3 is the newest Kernel the ZeroDev SDK supports (`KERNEL_V3_3` constant;
  no v4 constant) [S15 packages/core/constants.ts:107-108]. Kernel main is now "Kernel v4" (release file
  v0.4.0) [S13 README.md, releases/v0.4.0.json], not yet wired into the SDK at cd7c05b.
- Code read: zerodevapp/kernel tag v3.3 (cd697c7, 2025-04-03) [S12]; policy sources from
  zerodevapp/kernel-7579-plugins at 581985f, the last commit before commit 88a4d4c (2026-01-26, "merge recent
  commits") deleted CallPolicy, GasPolicy, RateLimitPolicy, RateLimitPolicyReset, SudoPolicy and TimestampPolicy
  from the repo [S14 git history]. Master (332deed) now ships only CallerPolicy, TimelockPolicy and signers for
  v4 [S14 README.md]. Deployed addresses for the v3 policies are in the SDK [S15 plugins/permission/
  constants.ts:26-73]. CallPolicy V0_0_5 (adds SLICE_EQUAL) has no matching source in the plugins history;
  analysis uses the 581985f source (V0_0_4 behaviour).
- Docs read: docs.zerodev.app permissions pages, saved 2026-10-08 [S16 to S19].
- Who installs: the account root validator (owner), either by `installValidations` or by enable mode in the
  first user operation [S12 src/Kernel.sol:396-403; src/core/ValidationManager.sol:371-398].
- Chains: ZeroDev's network list is long (Ethereum, Base, Arbitrum and many more) [S19 chains.md]; per-policy
  deployment by chain is not stated.
- Audits: docs say "All ZeroDev contracts and plugins are audited unless otherwise noted." [S19 audits.md line 7,
  confirmed] and link to kernel/tree/dev/audits, but the dev branch (c960b42) has no audits folder. The v3.3 tag
  has ten reports; a text search of all ten finds no mention of CallPolicy, RateLimitPolicy or TimestampPolicy;
  the SpendingLimit hook appears in the v3.1 incremental audit (May to June 2024) [S12 audits/].

Control model
- A permission = 1 signer + N policies (+ optional hook), installed as a validation with a 4-byte permission
  id [S16 intro.md; S12 ValidationManager.sol:259-290]. The permission id is encoded in the user operation
  nonce [S12 src/utils/ValidationTypeLib.sol:61-77], and the SDK lets the caller set it [S15 plugins/
  permission/toPermissionValidator.ts:71-80]. A non-root validation can only call selectors granted to it
  [S12 Kernel.sol:259-268].
- Policies (v3, at 581985f) [S14 kernel-7579-plugins-581985f/policies/]:
  - CallPolicy: per (call type, target, selector) entry: `valueLimit` (per-call native cap) and argument rules
    EQUAL, GREATER_THAN, LESS_THAN, GTE, LTE, NOT_EQUAL, ONE_OF; zero address target means any target; no
    cumulative counter [call-policy/src/CallPolicy.sol:7-29, 120-179, 198-221].
  - GasPolicy: lifetime gas-spend allowance, optional required paymaster [gas/src/GasPolicy.sol:11-50].
  - RateLimitPolicy: N user ops, one per interval, from startAt [ratelimit/src/RateLimitPolicy.sol:27-41].
  - RateLimitPolicyReset: N user ops per interval, refreshed each interval [RateLimitPolicyReset.sol:65-87].
  - TimestampPolicy: validAfter and validUntil [timestamp/src/TimestampPolicy.sol:26-35].
  - SignaturePolicy ("signature caller"): list of contracts allowed to verify ERC-1271 signatures made by the
    signer [signature-caller/src/SignaturePolicy.sol:51-61].
  - SudoPolicy: always passes [sudo/src/SudoPolicy.sol:13-29].
- SpendingLimit hook: a hook (not a policy) that measures the account's balance drop per listed token across the
  execution and subtracts it from a lifetime allowance [S14 hooks/spendlingLimits/src/SpendingLimit.sol:47-82].
  Shipped in the SDK as `@zerodev/hooks` with address 0xb6D6...D70E [S15 plugins/hooks/constants.ts:1-2;
  toSpendingLimitHook.ts:15-47]. Not in the docs index [S16 llms.txt]. It counts any outflow, whoever receives it.
- Revocation: `uninstallValidation(vId, ...)` (root, EntryPoint or self only) clears the hook slot and calls
  each policy's and the signer's onUninstall, emitting `ModuleUninstalled(type, module)` for each; the event does
  not carry the permission id [S12 Kernel.sol:405-423; ValidationManager.sol:183-221]. `invalidateNonce(n)`
  invalidates every non-root validation installed with a lower nonce [S12 Kernel.sol:425-427, 250-251;
  ValidationManager.sol:146-158]. The `NonceInvalidated` event is declared but never emitted at v3.3 [S12
  ValidationManager.sol:64; no emit found]. The code comment prefers the nonce route: "it is more recommended to
  use a nonce revoke to make sure the validator has been revoked" [S12 ValidationManager.sol:182, confirmed].
  Docs show `uninstallPlugin` from a sudo (root) client [S17 lines 185-211].

| Dim | Code | What exactly is supported | Sources | Quote |
|---|---|---|---|---|
| D1 per-transaction cap | N | CallPolicy `valueLimit` (native per call) and LTE rule on an amount argument. | S14 CallPolicy.sol:146-148, 149-176; S16 call.md | none |
| D2 per-period cap | C | No amount-per-period policy. Bound only by RateLimitPolicyReset (count per interval) times the CallPolicy per-call cap; the reset variant does not work with every bundler. | S14 RateLimitPolicyReset.sol:65-87; S16 rate-limit.md line 98 | "The `reset` version technically violates ERC-4337 storage rules since it needs to access `block.timestamp`, so it won't work with all bundler, but it's known to work with [UltraRelay](/sdk/core-api/sponsor-gas#ultrarelay) and Pimlico." [S16 rate-limit.md line 98, confirmed] |
| D3 total budget | C | No documented cumulative amount policy. Options: RateLimitPolicy count times per-call cap, or the SpendingLimit hook (lifetime per token, balance-based, SDK only, source removed from plugins master). GasPolicy caps gas, not payments. | S14 RateLimitPolicy.sol:27-41; SpendingLimit.sol:47-82; S15 plugins/hooks/ | none |
| D4 counterparty allowlist | N | Native: CallPolicy entry per payee target with empty selector. ERC-20: EQUAL or ONE_OF on the recipient argument. | S14 CallPolicy.sol:128-142, 165-176 | none |
| D5 per-counterparty cap | C | Per-call caps per payee only via separate permissions (one CallPolicy entry per target and selector per permission; duplicates rejected). Cumulative per-payee caps: CODE (custom policy). | S14 CallPolicy.sol:203-205 | none |
| D6 asset, network, MCC | N | Token by CallPolicy target; chain by where the permission is installed. No MCC. | S14 CallPolicy.sol:128-142 | none |
| D7 expiry or time window | N | TimestampPolicy validAfter and validUntil. | S14 TimestampPolicy.sol:26-35; S16 timestamp.md | none |
| D8 per-task credential | N | Each permission has its own signer (ECDSA, WebAuthn, weighted multisig) and policy set; non-root validations can only call granted selectors. | S12 ValidationManager.sol:259-290; Kernel.sol:259-268 | none |
| D9 revocation | N | Who: root validator (owner) via user op, or the account itself. How: `uninstallValidation` for one permission, or `invalidateNonce` for all older ones. How fast: next included block. Third party: by state reads (`validationConfig(vId)`, `validNonceFrom()`); events name only the policy and signer modules, and nonce invalidation emits nothing. | S12 Kernel.sol:405-427; ValidationManager.sol:61-67, 110-130, 146-221 | none |
| D10 human step-up | C | No threshold rule. Composition: a second permission with a weighted ECDSA (multisig) signer and higher caps. Kernel v4 master adds TimelockPolicy (propose, delay, execute, guardian may cancel), not wired into the SDK. | S16 intro.md; S14 master src/policies/TimelockPolicy.sol:17-55 | none |
| D11 task or purpose binding | C | The 4-byte permission id is in the user op nonce, which the EntryPoint emits in UserOperationEvent; the SDK accepts a caller-chosen id. No memo reaches the payee. | S12 ValidationTypeLib.sol:61-77; src/interfaces/IEntryPoint.sol:31-39; S15 toPermissionValidator.ts:71-80 | none |
| D12 audit record | N for allows, X for denies | Allows: module install and uninstall events, EntryPoint UserOperationEvent. Denies revert in validation (CallViolatesParamRule and others), nothing recorded. No vendor export documented for permissions. | S14 CallPolicy.sol:96-117; S12 ValidationManager.sol:208, 217 | none |
| D13 one policy across rails | C | One signature can enable permissions on several chains (multi-chain signing page); counters stay per chain. | S19 multi-chain-signing.md; S17 lines 213-215 | none |

Test case
- (a) named counterparties: yes. (b) per-task budget: only approximately (count times per-call cap) or through
  the undocumented SpendingLimit hook, which counts all outflow per token. (c) expiry: yes. (d) one-step
  revocation: yes per chain, verifiable by state but not by a permission-specific event. (e) per-task
  credential: yes.
- Full test case: partial. Missing: a documented cumulative spend budget, per-payee budgets, and an event that
  names the revoked permission.
- Notable: the ZeroDev quickstart for a third-party agent toolkit gives the agent process the account owner's
  private key and configures no permission or policy [S18, the code block under "The code (index.ts)"].

---

## 3. Biconomy (Nexus account, MEE, Smart Sessions)

Header
- Vendor: Biconomy. Status: docs present it as available, with no beta label on the session pages; the MEE
  contract suite v2.2.3 is "current" and v2.3.0 is an unaudited release candidate [S24 contracts-and-audits.md
  lines 26-31, 78]. The underlying Smart Sessions repo calls itself beta [S1 README.md:48].
- Code read: bcnmy/abstractjs@fd61054 (2026-09-01) [S20]; bcnmy/nexus@9007ba1 for audits [S25].
- Docs read: docs.biconomy.io agents and sessions pages saved 2026-10-08 [S21 to S24].
- Own policies or Rhinestone's? Rhinestone's. abstractjs imports `SMART_SESSIONS_ADDRESS` and the policy
  builders (`getSudoPolicy`, `getUniversalActionPolicy`, `getTimeFramePolicy`, `getUsageLimitPolicy`,
  `getSpendingLimitsPolicy`) from `@rhinestone/module-sdk` 0.4.0, under a comment "// Rhinestone constants"
  [S20 src/sdk/constants/index.ts:1, 230-269; package.json:22; src/sdk/account/decorators/buildActionPolicy.ts:
  2-9]. It calls the v1 functions `enableSessions` and `removeSession` [S20 getSessionQuote.ts:385, 414;
  modules/validators/smartSessions/decorators/toRemoveSessionCalls.ts:1-19]. Biconomy is a co-author of
  Smart Sessions [S1 README.md:50-53]. The session validator in the MEE flow is Biconomy's MEE K1 validator
  address [S20 getSessionQuote.ts:316-324].
- Agent documentation: an "Agents & Automation" section (overview, agent types, implementation, four policy
  pages) [S21]; SDK reference "Smart Sessions" [S22].
- Who installs: the user's account installs the Smart Sessions module in the PREPARE quote the user signs
  [S22 lines 15-23].
- Chains: 22 mainnet rows listed for MEE (Ethereum, Base, Polygon, Arbitrum, OP, BSC and others) [S24
  supported-chains.md].
- Audits: Nexus (Cyfrin CodeHawks, Cantina, Zenith, Pashov) and MEE stack audits listed [S24 lines 260-297;
  S25 audits/]; the Smart Sessions module audits are Rhinestone's (item 1). No Smart Sessions address or audit
  appears on Biconomy's contracts page [S24].

Control model
- Same contract model as item 1 (v1). abstractjs builds ONE session per chain with one random salt and puts
  every action for that chain into it [S20 getSessionQuote.ts:285-348]. Actions not given policies get sudo:
  "If no policies are configured, sudo policy will be added by default which is a unrestricted policy" [S20
  src/sdk/account/decorators/buildSessionAction.ts:234, confirmed]. The transfer helper turns
  `recipientAddress`, `amountLimitPerAction`, `maxAmountLimit`, `usageLimit`, `validAfter` and `validUntil`
  into UniActionPolicy, UsageLimitPolicy and TimeFramePolicy entries; with only one of validAfter or validUntil
  set, the other defaults to now or now plus one day [S20 buildSessionAction.ts:167-240].
- `maxPaymentAmount` adds a gas-fee payment allowance; when the fee token equals the session token the SDK
  raises the effective spending limit by that amount [S22 EnableSession table and Info box].
- Revocation: not documented in the agent or SDK-reference pages read (a search for revoke, remove, disable
  and uninstall finds only the word "revocable" in a marketing sentence) [S21; S22]. The SDK has
  `toRemoveSessionCalls` (wraps Rhinestone's `getRemoveSessionAction`) [S20 toRemoveSessionCalls.ts:1-19].
- Two code-against-docs gaps (code reading, not executed):
  1. The "Subscription & Payments" example builds 12 monthly USDC transfer actions in one grant [S21
     agents-automation.md lines 146-214]. All 12 share one actionId (same token, same selector) inside the one
     per-chain session, and Smart Sessions re-initializes an already-listed policy with the newer config
     ("overwrites the config") [S1 contracts/lib/ConfigLib.sol:94-102; SmartSession.sol:195-196]. Read
     together, only the last month's window and limits would survive.
  2. The older policies page describes the UniAction rule limit as a count, "Maximum number of times this rule
     can be used" [S23 line 95, confirmed], but the contract adds the argument value, so it is a cumulative
     amount [S1 UniActionPolicy.sol:153-158]. The newer agents pages use it correctly as a spend total [S21].

| Dim | Code | What exactly is supported | Sources | Quote |
|---|---|---|---|---|
| D1 per-transaction cap | N | `amountLimitPerAction` or a universal rule `lessThanOrEqual`; `valueLimitPerUse` for native. | S20 buildSessionAction.ts:188-196; S22 Universal Policy | none |
| D2 per-period cap | C | No periodic policy. Possible only as separate grants per period (each its own session); the documented single-grant monthly example collapses to one config by code reading. | S21 lines 146-214; S1 ConfigLib.sol:94-102 | none |
| D3 total budget | N | `maxAmountLimit` (limited universal rule) or `spendingLimits` policy per token; per action and per chain. | S20 buildSessionAction.ts:179-186; S22 Spending limit policy | none |
| D4 counterparty allowlist | N | `recipientAddress` on transfer actions (one payee), or universal rules; several payees need separate actions or an ArgPolicy tree, which abstractjs does not expose. | S20 buildSessionAction.ts:169-176 | none |
| D5 per-counterparty cap | C | Not exposed by abstractjs; possible with the underlying ArgPolicy (item 1) or one grant per payee. | S20 buildActionPolicy.ts:2-9 (no ArgPolicy import) | none |
| D6 asset, network, MCC | N | Token by `contractAddress`; chains by `chainIds` per action. No MCC. | S22 Frequently Used Actions; S20 getSessionQuote.ts:285-303 | none |
| D7 expiry or time window | N | `timeframe` policy validAfter and validUntil. | S22 Timeframe policy; S20 buildSessionAction.ts:219-232 | none |
| D8 per-task credential | N | `redeemer` is the agent's own key; a new grant gives a new salt and permissionId. | S22 EnableSession table; S20 getSessionQuote.ts:335-356 | none |
| D9 revocation | C | Who: the account owner. How: `removeSession` on each chain (SDK helper exists, not in the docs pages read). How fast: next included block. Third party: `SessionRemoved` event and `isPermissionEnabled` (documented as `isPermissionEnabled` and `checkEnabledPermissions`). Marked C because the documented agent flow gives no revoke step. | S20 toRemoveSessionCalls.ts:1-19; S22 Check Permission Status; S1 SmartSessionBase.sol:329-355 | "Smart Sessions let users grant **scoped, time-limited, revocable permissions** to your agent." [S21 agents-automation.md line 26, confirmed, marketing] |
| D10 human step-up | CODE | Docs suggest "custom multisig integration" for large treasury moves; no built-in threshold. | S21 agents-automation.md lines 234-244 | none |
| D11 task or purpose binding | C | As item 1: permissionId in the user op signature; salt is random in abstractjs, so a task id would need custom session construction. | S20 getSessionQuote.ts:338 | none |
| D12 audit record | N for allows, X for denies | On-chain events as item 1; denies revert. A Biconomy-hosted export of session decisions was not found. | S1 ISmartSession.sol:56-65 | none |
| D13 one policy across rails | C | One user signature on a multi-chain quote installs a separate session per chain with separate counters. The docs card "Single permission works across all chains" is marketing; the code shows per-chain sessions. | S20 getSessionQuote.ts:285-348; S21 agents-automation.md line 310 | "Single permission works across all chains." [S21 line 310, confirmed, marketing] |

Test case
- (a) yes, one payee per action through the SDK. (b) yes, per token and per chain. (c) yes. (d) possible on
  chain and verifiable, but not documented for agents. (e) yes.
- Full test case: yes at contract level; the documented developer path is missing the revocation step, defaults
  to sudo, and its recurring-payment example does not survive the contract's overwrite rule.

---

## 4. Safe Allowance module (safe-global/safe-modules, modules/allowances)

Header
- Vendor: Safe. Code read: safe-global/safe-modules@9e5f3d0, AllowanceModule.sol VERSION "1.0.0" [S26
  modules/allowances/contracts/AllowanceModule.sol:38]. Status: final release in repo; but the deployments
  registry at d5799b5 lists only v0.1.0 (15 network entries) and v0.1.1 (53 network entries, mainnets and testnets together) [S27 src/assets/
  allowance-module/]. v1.0.0's expected address 0x691f...E331 is in the CHANGELOG only [S26 CHANGELOG.md].
  The interface read here matches v0.1.1 for every parameter used below; v1.0.0 fixes a nonce overflow,
  false-returning tokens and delegate key collisions [S26 CHANGELOG.md].
- Who installs: the Safe owners enable the module on the Safe, then the Safe calls addDelegate and setAllowance
  in Safe transactions (owner threshold) [S26 README.md:13-17].
- Audits: G0 (v0.1.0), Ackee (v0.1.1), Certora and Nethermind (v1.0.0) [S26 modules/allowances/docs/].

Control model
- One record per (Safe, delegate, token): `amount`, `spent`, `resetTimeMin` (uint16 minutes, so at most 65,535
  minutes, about 45 days), `lastResetMin`, `nonce` [S26 AllowanceModule.sol:70-76].
- `setAllowance(delegate, token, allowanceAmount, resetTimeMin, resetBaseMin)`: msg.sender is the Safe; the
  delegate must already be added; `resetBaseMin` aligns the reset grid to a chosen minute; it does not reset
  `spent` [AllowanceModule.sol:131-157; README.md:19].
- `executeAllowanceTransfer(safe, token, to, amount, paymentToken, payment, delegate, signature)`: `to` is any
  address the delegate signs for; the only checks are signature, nonce and `spent + amount <= amount`; a
  `payment` to `tx.origin` is drawn from the allowance too [AllowanceModule.sol:220-276, 339-345]. Anyone can
  submit it with the delegate's signature [README.md:54]. The transfer is a plain `transfer(to, amount)` or a
  native send [AllowanceModule.sol:384-396].
- `deleteAllowance(delegate, token)` zeroes amount, spent and reset fields but keeps the nonce; emits
  DeleteAllowance [AllowanceModule.sol:201-209]. `removeDelegate(delegate, removeAllowances)` unlinks the
  delegate (and zeroes all its allowances when asked); emits RemoveDelegate [AllowanceModule.sol:447-477].
  Both are keyed by msg.sender, so only the Safe can call them.

D4 and D5, precisely from code: there is no recipient field in the Allowance struct and no recipient check in
executeAllowanceTransfer; `to` is a free argument that is only covered by the delegate's own signature
[AllowanceModule.sol:70-76, 220-276]. So the principal cannot limit payees (D4 = X) and cannot set a different
limit per payee (D5 = X). The only per-party dimension is per delegate and per token.

| Dim | Code | What exactly is supported | Sources | Quote |
|---|---|---|---|---|
| D1 per-transaction cap | X | No per-transfer limit field; one transfer may spend the whole remaining allowance. | S26 AllowanceModule.sol:70-76, 243-246 | none |
| D2 per-period cap | N | `resetTimeMin` recurring reset, aligned by `resetBaseMin`; max period about 45 days. | S26 AllowanceModule.sol:131-157, 165-176; README.md:64-67 | none |
| D3 total budget | N | `resetTimeMin = 0` gives a one-time allowance per delegate and token. | S26 README.md:60-62 | "If the `resetTimeMin` time of an allowance is `0` then the allowance will not automatically renew." [S26 README.md:62, confirmed] |
| D4 counterparty allowlist | X | `to` is unrestricted; see the D4 and D5 note above. | S26 AllowanceModule.sol:220-276 | none |
| D5 per-counterparty cap | X | Same reason as D4. | S26 AllowanceModule.sol:70-76 | none |
| D6 asset, network, MCC | N | Per token (zero address = native). One chain per record; the signed domain includes chainId. No MCC. | S26 AllowanceModule.sol:51, 298-311 | none |
| D7 expiry or time window | X | No valid-until or valid-from field; only the reset period. | S26 AllowanceModule.sol:70-76 | none |
| D8 per-task credential | N | The delegate is any address (separate from Safe owners), authorized only for allowance transfers; a new delegate per task is one addDelegate plus setAllowance. | S26 AllowanceModule.sol:425-440; README.md:5 | none |
| D9 revocation | N | Who: the Safe, through a Safe transaction meeting the owner threshold. How: `deleteAllowance` or `removeDelegate(delegate, true)` (or disable the module). How fast: the block the Safe transaction executes in. Third party: yes, DeleteAllowance and RemoveDelegate events plus `getTokenAllowance` and `getDelegates` views. Per chain. | S26 AllowanceModule.sol:201-209, 412-421, 447-502 | none |
| D10 human step-up | C | Above the allowance, the only path is a normal Safe transaction signed by owners; this sits outside the delegate's credential. | S26 README.md:13-17 | none |
| D11 task or purpose binding | C | No memo. A per-task delegate address appears in ExecuteAllowanceTransfer, so an auditor can map payments to that delegate. | S26 AllowanceModule.sol:95, 275 | none |
| D12 audit record | N for allows, X for denies | ExecuteAllowanceTransfer, PayAllowanceTransfer, SetAllowance, ResetAllowance, DeleteAllowance events; failed checks revert with no record. | S26 AllowanceModule.sol:78-123 | none |
| D13 one policy across rails | X | Records live in one chain's contract and signatures bind chainId. | S26 AllowanceModule.sol:298-311 | none |

Test case
- (a) no. (b) yes (one-time allowance). (c) no expiry. (d) yes, one Safe transaction per chain, verifiable by
  event and view, but it needs the owner threshold. (e) yes (delegate per task).
- Full test case: no. Missing: payee restriction, per-payee caps, expiry, per-transfer cap.
- Note: the relayer refund is paid to `tx.origin` from the same allowance [S26 AllowanceModule.sol:266-271;
  README.md:69-75].

---

## 5. Zodiac Roles Modifier v2 (gnosisguild/zodiac-modifier-roles)

Header
- Vendor: Gnosis Guild. Code read: gnosisguild/zodiac-modifier-roles@820e5bc (main, 2026-08-25) [S28]. Status:
  deployed v2 mastercopy 0xF296...83D5 on 16 mainnets and 2 testnets listed in the README [S28 README.md:39-71].
  A branch `contracts-v3` (47dd69b, 2026-07-20) holds "Zodiac Roles Modifier v3" under BUSL-1.1 with time-bound
  memberships; no v3 deployment is listed in the README [S29 packages/evm/contracts/core/Membership.sol:1-4].
- Who installs: the Safe owners deploy a Roles instance with an owner (usually the Safe), enable it as a Safe
  module, then the owner defines roles and calls `assignRoles` [S28 README.md:33-37; packages/evm/contracts/
  Roles.sol:51-84].
- Audits: G0 Group (Apr 2023, Nov 2023) and Omniscia (May 2023, Nov 2023) [S28 README.md:96-102;
  packages/evm/docs/].
- Docs note: the allowances docs page says allowance management "is available for Roles Modifiers owned by a
  Zodiac OS account" [S28 packages/docs/content/general/allowances.mdx:7-15]; on chain, `setAllowance` is
  simply `onlyOwner` [S28 packages/evm/contracts/PermissionBuilder.sol:158-177].

Control model
- A role has members (addresses), target clearances (None, Target, Function) with execution options (send
  value, delegatecall), and per-function condition trees [S28 Types.sol:114-146; PermissionBuilder.sol:57-156].
- Condition operators: Pass; And, Or, Nor; Matches, ArraySome, ArrayEvery, ArraySubset; EqualToAvatar; EqualTo,
  GreaterThan, LessThan, SignedIntGreaterThan, SignedIntLessThan, Bitmask, Custom (external checker contract);
  WithinAllowance (uint argument), EtherWithinAllowance (native value), CallWithinAllowance (call count)
  [S28 Types.sol:48-105].
- Allowances are global to the Roles instance and keyed by bytes32: `refill`, `maxRefill`, `period` (seconds, 0
  = one-time), `balance`, `timestamp` [S28 Types.sol:148-160; _Core.sol:14]. Consumption is committed only if the
  condition passes and the call succeeds; an Or branch that fails leaves no consumption [S28
  PermissionChecker.sol:370-400, 688-714; docs conditions.mdx:118-121].
- A member executes through `execTransactionWithRole(to, value, data, operation, roleKey, shouldRevert)`; the
  checker requires membership of that role [S28 Roles.sol:153-174; PermissionChecker.sol:20-69].
- Revocation: owner calls `assignRoles(module, [roleKey], [false])` (emits AssignRoles), or `revokeTarget`,
  `revokeFunction` (events RevokeTarget, RevokeFunction), or sets the allowance balance to zero; or the Safe
  disables the Roles module [S28 Roles.sol:69-84; PermissionBuilder.sol:72-80, 118-124]. Role membership is in
  an internal mapping with no getter in v2 [S28 _Core.sol:13], so third parties verify through events, the
  project's subgraph [S28 README.md:73-75] or raw storage reads.

Answers asked for this item
- Per-recipient cap: yes, by conditions. On the token's `transfer(to, amount)`: `Or( Matches(to EqualTo A,
  amount WithinAllowance kA), Matches(to EqualTo B, amount WithinAllowance kB) )`, with separate allowance keys
  per recipient. Supported by Or semantics and per-key allowances [S28 PermissionChecker.sol:370-400, 652-714].
  This is a composition of built-in operators, so C.
- Total budget: yes, an allowance with `period = 0` is one-time [S28 Types.sol:151; allowances.mdx:33].
- Expiry: not in v2. There is no timestamp operator and no membership expiry on main (grep for expiry, until,
  deadline finds none in contracts) [S28 packages/evm/contracts/]. It needs a Custom condition contract (CODE);
  none of the shipped periphery contracts checks time [S28 packages/evm/contracts/periphery/]. The v3 branch adds
  start and end timestamps and a use count per membership: "Memberships can be time-bound and usage-limited."
  [S29 Membership.sol:12-13, confirmed; checks at 56-61], unreleased.

| Dim | Code | What exactly is supported | Sources | Quote |
|---|---|---|---|---|
| D1 per-transaction cap | N | LessThan (or Bitmask, EqualTo) on the amount argument of a scoped function. Native value has only a cumulative EtherWithinAllowance, not a per-call comparison. | S28 Types.sol:89-103; PermissionChecker.sol:545-566 | none |
| D2 per-period cap | N | Allowance with `refill` and `period`, capped by `maxRefill`. | S28 Types.sol:148-160; allowances.mdx:33-49 | none |
| D3 total budget | N | Allowance with `period = 0`. | S28 Types.sol:151 | none |
| D4 counterparty allowlist | N | Target clearance limits contracts; EqualTo on the recipient argument limits payees; Or for several; native sends limited by target plus Send option. | S28 PermissionChecker.sol:113-181, 370-400 | none |
| D5 per-counterparty cap | C | Or of Matches branches, each binding recipient and its own allowance key (see above). | S28 PermissionChecker.sol:370-400, 652-714 | "If the condition evaluates to `false` or executing the call reverts, allowances will not be updated." [S28 conditions.mdx:121, confirmed] |
| D6 asset, network, MCC | N | Asset by target contract; network by the instance's chain. No MCC. | S28 Types.sol:137-146 | none |
| D7 expiry or time window | CODE | v2 has no time condition; a Custom condition contract is required. v3 branch (unreleased, BUSL-1.1) adds membership start and end. | S28 Types.sol:95; S29 Membership.sol:44-61 | none |
| D8 per-task credential | N | Members are plain addresses; mint a fresh address and role per task. | S28 Roles.sol:69-84 | none |
| D9 revocation | N | Who: the Roles owner (usually the Safe, so owner threshold). How: `assignRoles(..., false)`, revoke target or function, zero the allowance, or disable the module. How fast: the block the owner's transaction executes in. Third party: AssignRoles and Revoke events, `allowances` public getter; no membership getter in v2. | S28 Roles.sol:69-84; PermissionBuilder.sol:72-80, 118-124; _Core.sol:13-14 | none |
| D10 human step-up | C | Above role limits the path is a normal Safe transaction by owners; no amount-triggered approval in the modifier. | S28 README.md:15-21 | none |
| D11 task or purpose binding | C | The bytes32 roleKey (owner-chosen, can be a task hash) is an argument of execTransactionWithRole; ConsumeAllowance carries the allowance key. Nothing reaches the payee. | S28 Roles.sol:153-160; AllowanceTracker.sol:14-18 | none |
| D12 audit record | N for allows, X for denies | ConsumeAllowance events and configuration events, plus a public subgraph; denials revert with ConditionViolation. | S28 AllowanceTracker.sol:14-18, 99; PermissionChecker.sol:64-66; README.md:73-75 | none |
| D13 one policy across rails | X | An instance and its allowances live on one chain. | S28 _Core.sol:13-14 | none |

Test case
- (a) yes. (b) yes. (c) no in v2 without custom code; yes in the unreleased v3 branch. (d) yes, one owner
  transaction per chain, verifiable by event. (e) yes.
- Full test case: no for the deployed v2 (no expiry without custom code). Closest of the five on budgets: it is
  the only one with native per-recipient allowances and native refill periods together.

---

## Sources (all fetched or cloned 2026-10-08 UTC)

Repositories (shallow clones, read only; paths relative to OUT)
- [S1] github.com/erc7579/smartsessions@f5aaf86 (main), raw/smartsessions. Audit PDFs read with a text
  extractor from raw/smartsessions/audits/.
- [S2] github.com/rhinestonewtf/smart-sessions-v2@7c0e8d7, raw/smart-sessions-v2.
- [S3] github.com/rhinestonewtf/sdk@b819bfe, raw/rhinestone-sdk.
- [S12] github.com/zerodevapp/kernel tag v3.3 @cd697c7, raw/kernel-v3.3 (audits/ read with a text extractor).
- [S13] github.com/zerodevapp/kernel@c960b42 (main and dev, Kernel v4), raw/kernel.
- [S14] github.com/zerodevapp/kernel-7579-plugins master @332deed, raw/kernel-7579-plugins (history deepened to
  find deletions); policy sources exported from commit 581985f to raw/kernel-7579-plugins-581985f; deletion
  commit 88a4d4c (2026-01-26).
- [S15] github.com/zerodevapp/sdk@cd7c05b, raw/zerodev-sdk.
- [S20] github.com/bcnmy/abstractjs@fd61054, raw/abstractjs.
- [S25] github.com/bcnmy/nexus@9007ba1, raw/nexus.
- [S26] github.com/safe-global/safe-modules@9e5f3d0, raw/safe-modules/modules/allowances.
- [S27] github.com/safe-global/safe-modules-deployments@d5799b5, raw/safe-modules-deployments.
- [S28] github.com/gnosisguild/zodiac-modifier-roles@820e5bc (main), raw/zodiac-modifier-roles.
- [S29] same repo, branch contracts-v3 @47dd69b, fetched into raw/zodiac-modifier-roles as origin/contracts-v3
  (read with git show).

Pages (curl, each listed in SOURCES.md with fetch time and sha256)
- [S4] https://docs.rhinestone.dev/wallets/session-keys/session-limits.md, raw/docs.rhinestone.dev/wallets_session-keys_session-limits.md
- [S5] https://docs.rhinestone.dev/wallets/session-keys/security.md, raw/docs.rhinestone.dev/wallets_session-keys_security.md
- [S6] https://docs.rhinestone.dev/wallets/session-keys/custom-setup/restrict-a-session.md, raw/docs.rhinestone.dev/wallets_session-keys_custom-setup_restrict-a-session.md
- [S7] Rhinestone policy pages (sudo, call, spending-limit, timeframe, usage-limit, gas-limit), raw/docs.rhinestone.dev/wallets_session-keys_custom-setup_policies_*.md
- [S8] https://docs.rhinestone.dev/wallets/session-keys/custom-setup/multi-chain-sessions.md and use-a-session.md, raw/docs.rhinestone.dev/
- [S9] https://docs.rhinestone.dev/home/resources/audits.md, raw/docs.rhinestone.dev/home_resources_audits.md
- [S10] https://docs.rhinestone.dev/home/resources/supported-chains.md and https://v1.orchestrator.rhinestone.dev/chains, raw/docs.rhinestone.dev/home_resources_supported-chains.md, raw/v1.orchestrator.rhinestone.dev/chains.json
- [S11] https://docs.rhinestone.dev/wallets/session-keys/overview.md and custom-setup/signature-validators/multisig.md, raw/docs.rhinestone.dev/
- [S16] docs.zerodev.app permissions intro, policy pages (sudo, call, gas, signature, rate-limit, timestamp), llms.txt, raw/docs.zerodev.app/
- [S17] https://docs.zerodev.app/smart-accounts/permissions/transaction-automation.md, raw/docs.zerodev.app/smart-accounts_permissions_transaction-automation.md
- [S18] docs.zerodev.app quickstart page for a third-party agent toolkit (URL in the manifest, row for the file below), raw/docs.zerodev.app/smart-accounts_permissions_agent-toolkit-quickstart.md
- [S19] https://docs.zerodev.app/api-and-toolings/faqs/audits.md, faqs/chains.md, smart-accounts/multi-chain-signing.md, raw/docs.zerodev.app/
- [S21] docs.biconomy.io agents-automation pages (overview, agent-types, implementation, policies), raw/docs.biconomy.io/agents-automation*.md
- [S22] https://docs.biconomy.io/sdk-reference/sessions.md, raw/docs.biconomy.io/sdk-reference_sessions.md
- [S23] https://docs.biconomy.io/new/smart-sessions/policies.md, raw/docs.biconomy.io/new_smart-sessions_policies.md
- [S24] https://docs.biconomy.io/contracts-and-audits.md and contracts-and-audits/supported-chains.md, raw/docs.biconomy.io/

## Blocked or unverifiable
- Nothing was blocked; every docs site served Markdown to plain curl.
- Not verified: the deployed bytecode of ZeroDev CallPolicy V0_0_5 (no matching source in the plugins history);
  whether `@rhinestone/module-sdk` 0.4.0's `SMART_SESSIONS_ADDRESS` is the same deployment as erc7579/smartsessions
  main (only the ABI names were matched); which chains each policy contract is deployed on.
- The Biconomy subscription-example collapse and the per-recipient compositions are from reading code, not from
  running it.
- Several docs index files carry text addressed to automated readers (for example Biconomy's llms.txt opens with
  a reading order "For AI agents"); treated as data and ignored.

## Most surprising gaps
1. Defaults are wide open: Rhinestone's SDK and Biconomy's abstractjs both install a sudo policy when the
   developer supplies none [S7 sudo.md line 7; S20 buildSessionAction.ts:234], and Rhinestone v2 sessions carry
   a wildcard intent fallback unless `restrictToActions` is set [S6 line 9].
2. Rhinestone's own app-facing SDK documents no revoke method and tells integrators to contact support, even
   though the contract has one [S5 lines 68-76]. In v2 a configured allocator must co-sign a disable [S2
   SmartSessionLens.sol:298].
3. Safe's Allowance module, the most widely deployed of the five, cannot restrict the payee at all.
4. ZeroDev's documented policy set has no cumulative spend budget; the only one is an undocumented hook whose
   source was deleted from the plugins repo in January 2026, and Kernel's nonce revocation emits no event.
5. No item has a deny log, a payee-visible task id, or one budget across chains.

## Possibly missing from the teardown
- Coinbase Spend Permissions (SpendPermissionManager: per-spender, per-token allowance with period, start and
  end), used by Coinbase Smart Wallet: https://github.com/coinbase/spend-permissions
- MetaMask Delegation Framework (ERC-7710 delegations with caveat enforcers, ERC-7715 permission requests):
  https://github.com/MetaMask/delegation-framework
- Alchemy Modular Account v2 permission modules (ERC-6900 native token limit, allowlist, time range):
  https://github.com/alchemyplatform/modular-account
