# Spot-checks of N (native) cells before assembly, 8 Oct 2026

Each line: item, cell, what was re-read, result. "OK" means the raw copy or code says what the notes say.

## sa-delegation
- ERC-7715 D7: raw/ERCs/ERCS/erc-7715.md, the ExpiryRule type (`type: "expiry"`, unix `timestamp`), and permission
  types left as "enum defined by ERCs". OK.
- ERC-7715 enforcement left to wallets: line 463 "Wallets MUST correctly enforce permissions." OK.
- MetaMask Advanced Permissions D4: snap-7715-permissions@60c8a92 payeeCaveat.ts, the comment "For ERC-20 permissions,
  allowedCalldataEnforcer supports one target." and the throw when an ERC-20 permission names more than one payee. OK.
- MetaMask Advanced Permissions rule set: 7715-permissions-supported.ts lists seven types, each with rules expiry,
  redeemer, payee only (approval revocation: expiry, redeemer). OK; no per-transaction rule, so D1 X stands.
- Delegation Framework D9: DelegationManager.sol disableDelegation (onlyDeleGator, sets disabledDelegations, emits
  DisabledDelegation) and enableDelegation (re-enables). OK, revocation is reversible.
- Delegation Framework D5: MultiTokenPeriodEnforcer.sol header, "does not support restrictions on the recipient
  address". OK.
- Independent read, same repo: ERC20TransferAmountEnforcer keys spent amount by (manager, delegation hash) and reads
  only the amount bytes of the calldata. OK, no recipient in the counter.

## Read independently before the group notes arrived (used to check sa-modules and coinbase-aws)
- Coinbase Spend Permissions (spend-permissions@e0004e6): SpendPermission has account, spender, token, allowance,
  period, start, end, salt, extraData. `spend` transfers from account to the SPENDER itself
  (SpendPermissionManager.sol:420-426). There is no payee field. `revoke` is callable by the account, `revokeAsSpender`
  by the spender; both emit SpendPermissionRevoked(hash). The repo also holds SpendRouter.sol, which reads an executor
  and ONE recipient from extraData and forwards the pulled funds to that recipient, emitting SpendRouted.
- Safe AllowanceModule (safe-modules@9e5f3d0 modules/allowances/contracts/AllowanceModule.sol): Allowance is
  {amount, spent, resetTimeMin, lastResetMin, nonce} per (safe, delegate, token); executeAllowanceTransfer takes `to`
  from the delegate's signed request and never checks it against any list. No expiry field.
- Zodiac Roles (zodiac-modifier-roles@820e5bc packages/evm/contracts): Allowance {refill, maxRefill, period, balance,
  timestamp}; operators include EqualTo, Or, WithinAllowance, EtherWithinAllowance, CallWithinAllowance and Custom;
  no time-comparison operator; block.timestamp used only for allowance refill. assignRoles(module, roleKeys,
  memberOf) by owner assigns or revokes membership, emits AssignRoles.
- Rhinestone Smart Sessions (smartsessions@f5aaf86): ERC20SpendingLimitPolicy notice "allows transferring and
  approving ERC20 tokens up to a certain limit", per token, cumulative, no period in that contract.

## coinbase-aws
- CDP Policy Engine D4: cdp-sdk@993de49 openapi.yaml:29344, "There is a limit of 300 addresses per criterion." on the
  transaction `to` comparison. OK.
- CDP precedence: openapi.yaml:346, "A decision in the project-level policy is final." OK.
- CDP rule actions: the action enum lists accept and reject (openapi.yaml around 29732, 29821, 29873). OK, so D10 X.
- Spend Permissions D9: SpendPermissionManager.sol:392 "Revoke a spend permission to disable its use indefinitely."
  OK. README.md:32 "`SpendRouter`: TBD", with two Cantina SpendRouter audits dated March 2026 at README lines 157-158.
  OK. Consumer app: raw/docs.cdp.coinbase.com/cw-spend-permissions.md:18, "coming soon". OK.
- AgentCore payments D3 and D7: botocore bedrock-agentcore service-2.json, SessionLimits has only maxSpendAmount;
  CreatePaymentSessionRequest.expiryTimeInMinutes documented "Must be between 15 and 480 minutes." OK. The payment
  operations are CreatePaymentInstrument, CreatePaymentSession, DeletePaymentInstrument, DeletePaymentSession,
  GetPaymentInstrument, GetPaymentInstrumentBalance, GetPaymentSession, GetResourcePaymentToken,
  ListPaymentInstruments, ListPaymentSessions, ProcessPayment. OK.
- AgentCore payTo: payments-security-best-practices.md:306 and :313 quotes present. OK.
- AgentCore status: GA headline "AgentCore payments is now generally available in Amazon Bedrock AgentCore",
  postDateTime 2026-08-18T19:15:00Z; preview headline postDateTime 2026-05-07T12:00:00Z. OK. The brief's "preview"
  label is out of date.
- CdpX402Client spend controls: cdp-sdk types.ts, SpendControls fields maxAmountPerPayment, maxCumulativeSpend,
  maxCumulativeSpendWindow, allowedNetworks, allowedAssets, allowedPayees, onApproachingLimit; ledger note "The
  default implementation is in-memory and process-local." OK. These are client-side, so in the matrix they are
  marked N(client), not N.

## sa-modules
- Smart Sessions D9: SmartSessionBase.sol removeSession keyed by msg.sender, emits SessionRemoved(permissionId,
  msg.sender). OK. D1: UniActionPolicy LESS_THAN_OR_EQUAL and valueLimitPerUse. OK. D7: TimeFramePolicy validAfter,
  validUntil against block.timestamp. OK.
- Rhinestone docs (raw/docs.rhinestone.dev/wallets_session-keys_security.md): "The public wallet SDK has no
  app-origin revoke method" and the instruction to contact Rhinestone support; line 78 multi-chain residual
  authority. OK. Session limits page line 91: "They do not create one shared session-wide counter." OK.
- ZeroDev (kernel-7579-plugins@581985f): CallPolicy valueLimit and ONE_OF; TimestampPolicy validAfter, validUntil.
  OK. Kernel v3.3: NonceInvalidated declared at ValidationManager.sol:64 and no emit found; comment at :182
  recommends nonce revoke; uninstallValidation and invalidateNonce in Kernel.sol. OK.
- Biconomy: abstractjs buildSessionAction.ts:234 sudo default comment. OK. "Single permission works across all
  chains." at agents-automation.md:310. OK (marketing; code shows per-chain sessions).
- Safe Allowance D3: README.md:62 "will not automatically renew", and a reset needs a Safe transaction. OK.
- Zodiac v2 D5 quote, conditions.mdx:121. OK. v3 branch Membership.sol header: BUSL-1.1, "Memberships can be
  time-bound and usage-limited." OK (unreleased branch).

## wallets-1
- Privy D2 and D3: stateful-policies.md:150, window maximum `259200` (72 hours); recipes_using-stateful-policies.md:270,
  aggregations only track eth_signTransaction and eth_signUserOperation. OK. D5: stateful-policies.md:302 per-recipient
  rolling budget. OK. D8: add-signers.md:48 "if not provided, no policies will apply to the signers requests". OK.
  D9: agent-authorization.md:385, access token valid up to 15 minutes after grant revocation. OK. D10 Enterprise:
  dashboard overview.md:10. OK. Operators: the OpenAPI ConditionOperator enum is eq, gt, gte, lt, lte, in,
  in_condition_set, contains, starts_with, ends_with (no neq); system field current_unix_timestamp present. OK.
- Turnkey D1: agentic-wallets.md:80 "per-signing" caps. OK. D7: time-based-policies.md:24 and CronSpan at :62-64. OK.
  D8 limit: resource-limits.md:37, 5 policies per organization below Enterprise. OK. D10: delegated-access agentic
  wallets page shows consensus on approvers. OK. D12: get_policy_evaluations present in the docs swagger;
  create_velocity_control absent from the docs swagger (0 matches), so D2 and D3 stay ND. OK. D13: agentic-payments
  page says EVM and SVM need separate policies. OK. Root quorum bypass: overview.md:67. OK.
- Circle Agent Wallets D2: custom-policies.md:24 rolling caps; :26 mainnet only; command-reference.md:347 EVM-wide.
  OK. Stablecoin only: CLI 1.2.0 source limit-set.ts:33-34 "planned in a follow-up PR". OK. Gateway D9:
  contract-interfaces-and-events.md:319, revocation not respected for burn intents already signed. OK.
- Openfort D1 and D4 caveat: configuration_policies.md:59, rules "do not run for a send". OK. Session keys:
  user-and-server-signers.md:79, rate-limit, token-allowance and native-token-transfer "return an error". OK.
  D9: openfort-contracts BaseOpenfortAccount.sol (coreV9) revokeSessionKey emits SessionKeyRevoked, whitelist < 11.
  OK. Cross-app wallet: wallet_revokePermissions.md:14, not forwarded. OK.

## cards-stripe-corporate
- Stripe Issuing D1 to D3: stripe-openapi@52ca110 spec3.json, issuing_card_spending_limit.interval enum is all_time,
  daily, monthly, per_authorization, weekly, yearly. OK. D6: issuing_card_authorization_controls properties are
  allowed and blocked card presences, categories, merchant countries, plus spending_limits; no merchant id field
  in GA. OK, so D4 is CODE in GA. Merchant ID controls private preview: issuing-spending-controls.md:7. OK.
  Best-effort aggregation with up to 30 s lag: :40. OK. D8: issuing-agents.md:39. OK.
- Stripe SPT: no /v1/shared_payment paths in the GA spec3.json. OK (preview only). D3: programmatic-checkout.md:25.
  OK. D11: api-spt-issued-token-create.md:74, shared metadata visible to the other party by default. OK. D9:
  spt-concept-seller.md:160. OK. Agent side private preview: agentic-commerce-index.md:17. OK.
- ACP (agentic-commerce-protocol@7fdd78d): Allowance has additionalProperties false; reason enum one_time; required
  reason, max_amount, currency, checkout_session_id, merchant_id, expires_at. OK. RFC line 64 "MUST ONLY be usable
  within the provided Allowance" and line 65 expiry. OK. No revoke operation in the RFC (no match). OK. README:10
  maintainers OpenAI and Stripe, beta. OK.
- Stripe MCP D10: mcp.md:373 human confirmation for certain writes; :186 the 31 Oct 2026 key change. OK.
- Ramp: openapi-developer-api.json, fund spending restrictions have allowed_category_codes, allowed_vendor_ids,
  blocked_category_codes, blocked_mcc_codes, blocked_vendor_ids, interval, limit, lock_date,
  transaction_amount_limit; interval enum includes TOTAL. OK. Early access line agents.ramp.com llms-full.txt:523.
  OK. x402 wallet outside fund controls: guide-agent-payments.txt:39. OK.
- Brex: team_api.yaml has allowed_merchant_details, lock_after_date, ONE_TIME, spend_duration. OK. MCP cannot manage
  cards: mcp.md:146. OK.

## novelty
- arXiv 2609.27452: abs page title "Issuer-Sovereign Agentic Payments"; citation_author order Sharma, Dishant;
  Kaushal, Rajneesh; Kanaujia, Ashu (the notes table had the order wrong; fixed in novelty.md); citation_date
  2026/09/23. PDF text: the rule holds the spending cap, the set of allowed merchants and the time window; it may
  permit more than one payment, each checked against the current state of the rule; zero matches for revoc or
  revok in the extracted text. OK.
- arXiv 2501.09674: title matches; submission history shows only [v1]. "explicit spending limits can be enforced"
  and "revocation endpoints" present in the PDF text. OK.
- Kite whitepaper (raw/www.gokite.ai/kite-whitepaper.html, tags stripped): "Permissions are scoped at the task level,
  not the agent level."; "Multiple agents operate this account via session keys, but only within their authorized
  limits."; the example session key for providers A, B, or C between 2:00 PM and 2:05 PM; removeSessionKeyPermission;
  "instantly revoke all delegated permissions with a single transaction". OK. The source writes several phrases
  with a dash character other than a hyphen (in "one-time, task-scoped session key"), so those are paraphrased,
  not quoted, in novelty.md.
- Lead Bank blog: "Each task gets its own account number; controls are defined by rail and enforced on every
  payment; and access can be revoked when the mandate ends." and "illustrative only". OK. Lead API controls page:
  title line "Block or allow transactions at the account number level."; no limit, amount, cap or expiry field
  (grep). OK.
- Anchorage: "An agent can hold a wallet, but it cannot open an account, pass identity checks, carry a compliance
  obligation, offer recourse when it errs, or run treasury." OK.
- Ant AMP@a4fe50c (2026-09-23): IntentConstraints budgetAmount and merchantNameList; Alipay+ MUST record lifecycle
  and return the latest status; `finished` when the task completes or budget is exhausted; terminal states cannot
  revert. OK.

## wallets-2
- Crossmint scopes (raw/docs.crossmint.com/wallets_guides_signers_scopes.md): :21 one token on one chain; :493 omit
  interval for an absolute cap; :517 recipients array; :543 signer-level expiresAt. OK. Agent card overview :57
  "Create one per agent, per task, or per purchase." OK. create-agent-card :188, networks enforce amount and
  merchant only on agentic-token rails. OK. Stellar contract (stellar-smart-account): revoke_signer publishes
  SignerRevokedEvent (account.rs:214-232), has_signer view at :242, cumulative amount per window in types.rs:16. OK.
  EVM and Solana policy contracts not public, so EVM on-chain enforcement stays vendor statement.
- Lit Vincent@1fa0a48: completeInstallation.ts:230 installs `toSudoPolicy({})`. OK. AppVersionUnPermitted event in
  LibVincentUserFacet.sol:38. OK. Spending-limit policy parameter maxDailySpendingLimitInUsdCents. OK.
- HeyVincent skills (wallet/SKILL.md): per-tx, rolling 24 h, address allowlist, Telegram approval threshold,
  revocation line :49 and the unclaimed-wallet line :250. OK, but these are vendor skill files and the server code
  is not public, so the matrix marks those cells N(vendor doc), not N.
- Fireblocks openapi.yaml: SINGLE_TX and TIMEFRAME amount scopes (:56480-56481), 2-TIER verdict, Policy Editor beta
  note (:7308). OK. Audit event Transaction_BlockedByPolicy. OK. x402 agent page :14 "The agent enforces no
  spending limit of its own." and :21 vault balance as ceiling. OK. TAP reference :85, Typed Message rules take no
  destination limitation. OK.
- thirdweb: createSessionKey.ts:126 `isWildcard: grantFullPermissions ?? true`; MinimalAccount skips policy checks
  for a wildcard session. OK.

## startups-mandates (quotes re-checked with whitespace and markdown markers normalized)
- Skyfire: docs-payments-settlement.md, "The token amount is the maximum a seller can charge." and "Deactivating an
  account does not void tokens that were already issued." OK. create-token reference has buyerTag and expiresAt.
  OK. draft-skyfire-oauth-using-kyapay-tokens-01:1445 "does not define a revocation mechanism". OK.
- AP2@e1ea56d: payment_mandate.md allowed-payee MUST and budget tracking sentence; implementation_considerations.md
  delegated-mandate management out of scope; agent_authorization.md signed Mandate Receipt MUST; specification.md
  exp RECOMMENDED as short as the task; vct mandate type identifiers at :138; no "revoc" or "revoke" match in
  docs/ap2/*.md; SDK constraints.py:307 multiplies budget max by 100. OK.
- x402@7f2b2f1: spec v2 lists client-side budget management as out of scope (:19, :668); x402Client.ts
  maxAmountPerPayment and `spendControls: false`. OK (client-side only).
- Nevermined: mandates.md, spendingLimitCents is cumulative not per transaction; "Revocation is immediate"; router
  overview "A single Delegation covers x402 and MPP alike." OK.
- Payman: docs host now returns error 526; evidence is Internet Archive snapshots, so the matrix marks Payman
  "archived docs, last documented state".

## cards-networks
- Visa VIC D1: cybersource-rest-client-python@7349130 generator/cybersource-rest-spec.json:208985, declineThreshold
  "Defines the maximum transaction amount the consumer is willing to authorize under this mandate." OK. D4:
  :208966 "User merchant preference." OK (so D4 stays ND). D7: effectiveUntilTime required (:208948). OK. D9:
  :210614 cancel returns CANCELLED or PENDING if cardholder authentication is needed. OK. Product page disclaimer
  "This product is in the process of development and deployment." present in raw/developer.visa.com/vic-overview.html.
  OK. VIC verdicts are labelled pilot.
- Mastercard MDES Customer Service v4.0.1 (raw/static.developer.mastercard.com/mdes-customer-service.yaml): :3936
  ABSOLUTE_SPEND_LIMIT cannot coexist with other limit types; :3938 DAILY_AMOUNT_LIMIT; :3941 TRANSACTION_SPEND_LIMIT
  described as cumulative (contradiction with the use-case page noted); :3993 ALLOW_LST_MID; :162 suspended tokens
  declined; :434 rules are created "based on the issuer's decision after cardholder authentication". OK. Release
  notes July 2026 :40 network declines violating transactions; :190 issuers "can optionally support" the APIs. OK.
  So every Mastercard N is labelled issuer-set.
- Verifiable Intent (agent-intent/verifiable-intent@356c296) security-model.md:319, no credential-layer revocation
  protocol in v0.1. OK.
- American Express: no API, spec or repository is public; every cell stays ND.

## Second pass, all remaining native cells
A script confirms that the field, rule, endpoint or sentence
behind each remaining N cell appears in the raw copy or code: 62 checks across A1 to D7, 62 found. One check
first missed because the Turnkey language table escapes underscores (`chain\_id`); the docs example
`eth.tx.chain_id == 11155111` (features_policies_examples_ethereum.md:141) confirms the field.
