# Group: cards-networks (Visa, Mastercard, American Express)

Read on 8 October 2026 (UTC). Saved copies and clones are cited as `raw/...` and listed in [SOURCES.md](../SOURCES.md).
Source ids [S..] resolve in the source list at the end of each item. Line numbers are 1-based in the saved raw file.

A note on method. Two pages (Mastercard Agent Pay overview, American Express ACE overview) are JavaScript apps: curl
returns only an empty app shell. Their text was read in a browser without signing in and without submitting any form,
and saved as a text capture (`rendered-*.txt`, listed in SOURCES.md). Quotes from them are confirmed against
those captures.

---

## 1. Visa Intelligent Commerce (VIC), with Trusted Agent Protocol (TAP)

- Vendor: Visa (APIs also exposed through Cybersource / Visa Acceptance as "Intelligent Commerce" and "Intelligent
  Commerce Connect").
- Status: pilot / restricted. The VIC product page carries a disclaimer that "This product is in the process of
  development and deployment." [S1]. The VIC developer docs on developer.visa.com are a "restricted product" behind
  sign-in [S2]. The Cybersource developer guide lists revision 25.09.01 as "Pilot release." and marks the Passkey
  Service as pilot [S4]. Intelligent Commerce Connect was announced 8 April 2026 as "Currently in pilot with select
  partners" [S11].
- Versions read: Cybersource REST spec in CyberSource/cybersource-rest-client-python@7349130 (spec `info.version`
  0.0.1, commit date 2026-10-05) [S3]; Cybersource Intelligent Commerce developer guide revision 25.12.01 [S4];
  visa/ai@1c544e5 [S5]; visa/vic-reference-agent@39bc93d [S6]; TAP merchant specification page (no version shown)
  [S7]; visa/trusted-agent-protocol@16d59bd [S8]; Visa Transaction Controls API reference, `info.version` 1 [S9].

### Control model

The principal (cardholder) does not set limits on the card or on the agent token directly. The agent platform first
provisions a Visa Token Service (VTS) token for the card with presentation type `AI_AGENT` (sample code [S6]
`reference-agent-backend/src/utils/constants.py:34`), enrolls it in VIC, and binds a cardholder passkey. For each
purchase the agent then creates a **purchase instruction** (`POST .../instructions`) that carries one or more
**mandates**: `mandateId`, `declineThreshold {amount, currencyCode}`, `effectiveUntilTime` (all required), plus
optional `preferredMerchantName`, `merchantCategory`, `merchantCategoryCode`, `quantity`, `recurringPaymentInformation`
and a `consumerPrompt` recap [S3 lines 208941 to 209079]. The cardholder approves the instruction with passkey
assurance data. The agent then retrieves a per-transaction credential against the instruction
(`POST .../instructions/{id}/credentials`, naming merchant, amount and `mandateReferenceData`) and reports the outcome
(`.../confirmations`). Who enforces: the API reference does not say. Only the product page states that Visa validates
credential requests against the instruction and that VisaNet checks merchant and amount at authorization [S1]. A
separate issuer product, Visa Transaction Controls (VTC), lets an issuer put period limits, transaction counts and
merchant-category blocks on a specific payment token [S9], but no public document ties VTC to VIC agent tokens. TAP is
separate: it is an RFC 9421 HTTP message signature scheme by which a Visa-registered agent proves its identity to a
merchant; it carries no spending control.

The same instruction API appears under three paths: `/vacp/v1/instructions` in Visa's own sample code [S5]
`packages/api-client/src/clients/vic-client.ts:166-238` and [S6] `vdp_client.py:491`, `/acp/v1/instructions` in the
Cybersource guide [S4], and `/icc/v1/instructions` in the Cybersource REST spec [S3 line 208675].

### Dimensions

| Dim | Verdict | What exactly is supported | Source | Quote (confirmed unless marked) |
|---|---|---|---|---|
| D1 per-transaction cap | N | `mandates[].declineThreshold` (required) on each purchase instruction. Where it is enforced (Visa platform at credential retrieval, VisaNet at authorization) is stated only on the product page. Pilot. | S3 l.208983; S1 | S3: "Decline Threshold data. Defines the maximum transaction amount the consumer is willing to authorize under this mandate." |
| D2 per-period cap | C | Not in the VIC mandate (only `recurringPaymentInformation.occurrence` WEEKLY/MONTHLY/YEARLY, a frequency, not a cap). Only through the issuer product VTC: `spendLimit.type` LMT_DAY, LMT_WEEK, LMT_MONTH, LMT_RECURRING with a `declineThreshold`, settable on a payment token. Issuer-operated, not documented for VIC tokens. | S3 l.209003; S9 schema SpendLimit | S3: "Frequency of the transaction. Specifies how often the transaction occurs." |
| D3 total budget | C | No cumulative cap per instruction in the VIC schema. VTC `spendLimit.type` LMT_DATE_RANGE plus `declineThreshold` caps total approved spend in a date window, and `transactionLimit.maxTransactionCount` caps uses (Global control only). Issuer-operated. | S3; S9 schemas SpendLimit, TransactionLimit | S9 (SpendLimit.declineThreshold): "Maximum total value of approved purchases within the time period before triggering a decline." |
| D4 counterparty allowlist | ND | `mandates[].preferredMerchantName` is a free-text name described as a preference. The credential request names the merchant (name, URL, country). Enforcement of "intended merchant" is stated only on the product page. VTC has merchant-category groups only, no merchant-ID allowlist found. | S3 l.208961; S1; S9 | S3: "User merchant preference." S1: "When authorization requests are received by VisaNet, controls will be enforce to ensure that the request originates from the intended merchant for the correct amount." |
| D5 per-counterparty cap | ND | `mandates` is an array, so each mandate can pair a `preferredMerchantName` with its own `declineThreshold`, but no document says the pairing is enforced. | S3 l.208941 | none |
| D6 asset/network/MCC limits | C | VIC: `mandates[].merchantCategoryCode` field exists, enforcement not documented. VTC: merchant-category groups (MCT_ELECTRONICS, MCT_GAMBLING and others) and transaction types (TCT_E_COMMERCE, TCT_CROSS_BORDER and others) on a token, issuer-set. | S3 l.208976; S9 | S3: "Merchant category Code. Once it is checked, it has to be valid merchant category code." |
| D7 expiry/time window | N | `mandates[].effectiveUntilTime` is required on every mandate (Unix epoch). Sample code defaults it to one year. No hours-of-day control in VIC (VTC has time ranges, issuer-set). | S3 l.209013; S5 `apps/shared-utils/payload-helpers.ts:19-23,45-78` | S3: "UTC time in Unix epoch format." |
| D8 per-task credential | N | The purchase instruction is the per-task object; each credential retrieval is bound to an `instructionId` and returns a signed payload with a per-transaction cryptogram (`dynamicDataType` TAVV, `dpaDynamicDataTtlMinutes`). The agent token itself is per agent and card, not per task. Pilot. | S3 l.208681, 211417; S4 | S3: "The instructionId returned is used in all subsequent operations - update, cancel, retrieve credentials, and confirm transaction." |
| D9 revocation | N | **Who:** the agent platform calls cancel on the instruction; the agent platform (token requestor) can delete the VTS token (sample code); the issuer can decline via VTC. No principal-direct cancel channel is documented. **How:** `PUT .../instructions/{id}/cancel` (may return PENDING until the cardholder re-authenticates); `PUT /vts/provisionedTokens/{id}/delete` in sample code (VTS docs restricted). **How fast:** not documented. **Third-party verifiable:** no. There is no GET or list endpoint for instructions in the published spec, and no status list. (TAP agent keys in Visa's registry have status active/deactivated/expired and a default 14-day expiry, but that revokes agent identity, not a payment grant.) | S3 l.210608-210614, 214709-214805; S6 `vdp_client.py:322-327` | S3: "Returns status CANCELLED (HTTP 200) on success, or PENDING (HTTP 202) with pendingEvents if cardholder authentication is required before cancellation can proceed." |
| D10 human step-up | N | Every instruction create, update and cancel carries cardholder `assuranceData` (passkey / FIDO); any call can return HTTP 202 with `pendingEvents` (for example PENDING_CARDHOLDER_AUTHENTICATION). Visa decides when step-up is needed; no principal-set amount threshold is documented. | S3; S4 | S4 shows `"pendingEvents": ["PENDING_CARDHOLDER_AUTHENTICATION"]` in the enroll response example |
| D11 task/intent binding visible to counterparty | ND | Inside Visa the binding is explicit: `mandateId`, `instructionId`, `consumerPrompt` recap, `mandateReferenceData` on each credential request, and confirmations with order data. What reaches the merchant via TAP is agent `keyid`, a `tag` (agent-browser-auth or agent-payer-auth), a session `nonce`, timestamps (8-minute window), a consumer ID token with obfuscated email and phone, and a payment container (credential hash, encrypted payload, or a 402 "browsing IOU" with `invoiceId`). None of the defined TAP fields is an instruction or mandate id; the spec allows extra fields. | S3 l.209079; S7 sections "Required Message Signature Fields", "Payment" | S3: "Recap - A summary or condensed version of user prompts that leads to the purchase." S7: "An Agent or a Payment Scheme may optionally define additional fields that could be part of the signature." |
| D12 audit export | C | No read or list endpoint for instructions or decisions in the VIC spec; confirmations are pushed by the agent. Issuer only: VTC Alert History API queries notifications by `paymentTokens`, and decline alerts carry `alertReason` (for example DECLINE_TRANS_LIMIT) and `ruleCategory`. Principal export: ND. | S3; S9 (operationId getCustomerNotificationsV3) | none |
| D13 multi-rail policy | ND | Intelligent Commerce Connect is described as network-, protocol- and token-vault-agnostic, and the spec has an MPP credential endpoint (`/icc/v1/mpp/credentials`, a network token for HTTP 402 flows), but no single policy object across rails is documented. Press release only for "spend controls". | S11; S3 l.214137 | S11: "Intelligent Commerce Connect enables secure payment initiation, tokenization, spend controls, and authentication." |

### Test case

- (a) Named counterparties only: not verifiable. The merchant field is a "preference" string; enforcement appears only
  on a product page with a development disclaimer.
- (b) Per-task budget: partly. A per-transaction ceiling per mandate (`declineThreshold`) exists; no cumulative cap per
  instruction. A cumulative cap exists only in the issuer's VTC.
- (c) Ends when the task ends: yes, `effectiveUntilTime` is required per mandate.
- (d) One-step revocation a third party can verify: no. Cancel exists but goes through the agent platform, may need
  cardholder re-authentication, and has no status endpoint.
- (e) Credential per task: yes, the purchase instruction plus per-transaction credentials.
- Full test case: **no**. Missing: an enforced payee allowlist in the API reference, a cumulative per-task budget,
  principal-direct and third-party-verifiable revocation; plus pilot status and restricted documentation.

### Sources (item 1)

- [S1] https://developer.visa.com/capabilities/visa-intelligent-commerce/overview, fetched 2026-10-08, raw/developer.visa.com/vic-overview.html
- [S2] https://developer.visa.com/capabilities/visa-intelligent-commerce/docs, fetched 2026-10-08, raw/developer.visa.com/vic-docs.html (restricted notice)
- [S3] CyberSource/cybersource-rest-client-python@7349130 generator/cybersource-rest-spec.json (paths `/icc/v1/*`), raw/cybersource-rest-client-python/generator/cybersource-rest-spec.json
- [S4] https://developer.cybersource.com/docs/cybs/en-us/intelligent-commerce/developer/all/rest/intelligent-commerce.html, fetched 2026-10-08, raw/developer.cybersource.com/ic-guide.html (same content at developer.visaacceptance.com, raw/developer.visaacceptance.com/ic-guide.html)
- [S5] visa/ai@1c544e5 apps/shared-utils/payload-helpers.ts, apps/shared-utils/payload-builders/*.ts, packages/api-client/src/clients/vic-client.ts, skills/visa-best-practices/references/visa-intelligent-commerce.md
- [S6] visa/vic-reference-agent@39bc93d reference-agent-backend/src/services/vdp_client.py, reference-agent-backend/src/utils/constants.py
- [S7] https://developer.visa.com/capabilities/trusted-agent-protocol/trusted-agent-protocol-specifications, fetched 2026-10-08, raw/developer.visa.com/tap-specs.html
- [S8] visa/trusted-agent-protocol@16d59bd README.md (last commit 2025-10-28)
- [S9] https://developer.visa.com/capabilities/vctc/reference, fetched 2026-10-08, raw/developer.visa.com/vctc-reference.html (embedded OpenAPI, "Visa Transaction Controls" version 1); product page raw/developer.visa.com/vctc.html
- [S10] https://usa.visa.com/about-visa/newsroom/press-releases.releaseId.21361.html (30 Apr 2025), fetched 2026-10-08, raw/usa.visa.com/pr-21361-vic.html. Press release only: "Allows consumers to easily set spending limits and conditions, providing clear guidelines for agent transactions."
- [S11] https://usa.visa.com/about-visa/newsroom/press-releases.releaseId.22276.html (8 Apr 2026), fetched 2026-10-08, raw/usa.visa.com/pr-22276-icc.html
- [S12] https://mcp.visa.com/.well-known/jwks, fetched 2026-10-08, raw/mcp.visa.com/jwks.json (one RSA key; no Ed25519 agent keys, although the TAP spec names this URL as the key directory)
- [S13] https://sandbox.mcp.visa.com/mcp/doc/llms.txt, fetched 2026-10-08, raw/sandbox.mcp.visa.com/llms.txt
- [S14] https://developer.visa.com/capabilities/vts/docs and /vts/reference, fetched 2026-10-08, raw/developer.visa.com/vts-docs.html, vts-reference.html (restricted)

### Blocked or unverifiable (item 1)

- restricted: https://developer.visa.com/capabilities/visa-intelligent-commerce/docs (VIC API docs) and
  https://developer.visa.com/capabilities/vts/docs, /vts/reference (VTS token lifecycle, incl. suspend and delete).
- unreachable: https://apihub.visa.com/cybs/internal/Spec-Branches/DOCRSTAPI_1374_acp_api_spec/acp_rest.html, linked
  from the Cybersource guide as the field reference; the host does not resolve (an internal spec branch).
- blocked: https://www.businesswire.com/news/home/20250430580204/en (Access Denied); the usa.visa.com copy was used.
- Text addressed to AI agents: S13 and visa/ai `skills/` contain instructions for coding assistants on which files to
  use. Treated as data and not followed.
- VTC rule category `PCT_AGENT` appears in the program-administration schema (`availablePaymentRuleTypes`) with no
  definition anywhere in the public reference [S9]. Could not determine what it does.

---

## 2. Mastercard Agent Pay (agentic tokens), with MDES Token Spend Controls and Verifiable Intent

- Vendor: Mastercard.
- Status: Agent Pay documentation is early preview. The Checkout Solutions release history says the initial Agent Pay
  pages went live on 16 October 2025 "providing preliminary guidance and reference for early preview" [S21 l.1285].
  The Agent Pay page lists the workflow (enrollment, ID&V, bind, intent creation, authentication, checkout) but no
  public API for intent creation [S20]. The token-level spend control APIs went to production on 5 August 2026 and are
  optional for issuers [S22 l.31, l.190]. Verifiable Intent is a draft v0.1 spec [S27].
- Versions read: MDES Customer Service OpenAPI 3.0.3, `info.version` 4.0.1 [S24]; MDES Customer Service release notes
  July 2026 [S22]; Agent Pay overview page (rendered capture) [S20]; agent-intent/verifiable-intent@356c296 (last
  commit 2026-04-20) [S27].

### Control model

The agent platform registers with Mastercard as a Token Requestor and obtains an agentic token (an MDES network token)
for the cardholder's card [S20]. Limits are not set by the agent platform or by the cardholder directly through any
public Agent Pay API. They are set by the **issuer** on the token through the MDES Customer Service API, "after
cardholder authentication", usually because the cardholder asked in the issuer's app [S23, S24 l.434]. The rule set
(Token Spend Controls) has six limit types (daily, weekly, monthly, per transaction, single use, absolute lifetime) and
five allow/block list types (merchant ID, MCC, transaction category code, transaction type, geography) [S24
l.3914-4047]. **Mastercard enforces** them at authorization and declines violating transactions [S22 l.40]. The token
itself is suspended or deleted through MDES (issuer, token requestor or cardholder as "suspenders"). What reaches
issuers and acquirers to mark a transaction as agentic is a Digital Service Provider ID and Digital Commerce Solution
Indicators [S20]. Verifiable Intent, a Mastercard-maintained draft, defines signed mandates with budget, payee and
amount constraints, but no public document shows it wired into the Agent Pay APIs.

### Dimensions

| Dim | Verdict | What exactly is supported | Source | Quote (confirmed unless marked) |
|---|---|---|---|---|
| D1 per-transaction cap | N | `TRANSACTION_SPEND_LIMIT` on the token, issuer-set, network-enforced. Conflict: the use-case page says per transaction, the OpenAPI enum text says "Cumulative transaction spend limit". | S23 l.12; S24 l.3941; S22 l.39-40 | S23: "Specify the maximum amount allowed for an individual transaction." |
| D2 per-period cap | N | `DAILY_AMOUNT_LIMIT`, `WEEKLY_AMOUNT_LIMIT`, `MONTHLY_AMOUNT_LIMIT` (calendar week and month per S23). Issuer-set. | S24 l.3936-3945; S23; S22 l.40 | S22: "Mastercard evaluates each tokenized transaction against these rules and declines the tokenized transactions violating these rules." |
| D3 total budget | N | `ABSOLUTE_SPEND_LIMIT` with a required `expirationDate` up to one year ahead; `consumedThreshold` reports spend so far. It cannot be combined with any other limit type on the same token. `SINGLE_TIME_USE` makes the token one-use. | S24 l.3936, 3961, 3971-3972 | S24: "The ABSOLUTE_SPEND_LIMIT cannot coexist with other LIMIT type." |
| D4 counterparty allowlist | N | `ALLOW_LST_MID` (and `BLOCK_LST_MID`), merchant IDs up to 15 characters. Issuer-set on the token. | S24 l.3993 | S24: "ALLOW_LST_MID - MID Allow List" (tab characters in the raw line) |
| D5 per-counterparty cap | X | On one token, limit rules (`limitRuleType`, `ruleThreshold`, `consumedThreshold`, `expirationDate`) and list rules (`listRuleType`, `ruleValueList`) are separate objects with no field linking an amount to a merchant. A token per payee could approximate it, but no document says one card can carry several agentic tokens for one agent (ND). | S24 l.3928-4046 (schemas TokenSpendControlsLimit, TokenSpendControlsList) | none |
| D6 asset/network/MCC limits | N | `ALLOW_LST_MCC` / `BLOCK_LST_MCC`, `ALLOW_LST_GEO` / `BLOCK_LST_GEO` (3-letter country), `ALLOW_LST_TCC` / `BLOCK_LST_TCC`, `ALLOW_LST_TRAN_TYPE` / `BLOCK_LST_TRAN_TYPE`. Issuer-set. | S24 l.3981-4040; S22 | S22: "Acceptor Business Code (MCC) -- Allow or restrict transactions based on Merchant Category Codes." (bold markers removed) |
| D7 expiry/time window | ND | The only principal-relevant date is the `expirationDate` of an `ABSOLUTE_SPEND_LIMIT` rule, which ends the *rule*; the spec does not say whether the token stops or runs unlimited afterwards. S23 says single use comes "with an expiration date" but the OpenAPI says `expirationDate` applies only to ABSOLUTE_SPEND_LIMIT. No valid-from or hours-of-day control. | S24 l.3971-3972; S23 l.13 | S24: "The date and time when the limit expires only applicable and mandatory in case of the ABSOLUTE_SPEND_LIMIT." |
| D8 per-task credential | ND | The agentic token is per agent (token requestor) and card. Per transaction there is a DSRP cryptogram or a one-time DTVC; `SINGLE_TIME_USE` exists as a rule. No public API lets the principal mint a token per task; the intent-creation step has no public reference. | S20; S21 l.1893; S24 | S20: "Most Agentic Commerce Providers and Enablers register as Token Requestors." |
| D9 revocation | N | **Who:** issuer, token requestor (the agent platform) and cardholder appear as suspenders; for card-on-file tokens only issuer and token requestor. **How:** MDES Customer Service `/{id}/token/suspend`, `/unsuspend`, `/delete` (issuer API); Checkout Solutions `DELETE /cards/{cardId}` for integrators (not shown to apply to agentic tokens); spend rules can also be deleted. **How fast:** not stated beyond "will be declined". **Third-party verifiable:** no; status and history are visible only to the issuer (and token requestor via its own APIs), a merchant sees only a decline. Delete is irreversible. | S24 l.152-236, 2223-2240; S25 deleteCard | S24: "All authorizations for a SUSPENDED token will be declined." S24: "For CoF tokens, the only two supported suspenders are issuer and token requestor." (line-wrapped in raw) |
| D10 human step-up | ND | The workflow includes "Authenticate consumer intent" with Mastercard Payment Passkeys, but there is no public API and no documented threshold. Spend control rules have no approval-above-threshold type. | S20 | S20 workflow row: "Authentication	Authenticate consumer intent" |
| D11 task/intent binding visible to counterparty | ND | Live, documented: a Digital Service Provider ID and Digital Commerce Solution Indicators identify an agentic transaction to issuers and acquirers, not a task. Verifiable Intent (draft) defines `mandate.payment.reference` binding the payment to the approved checkout, with selective disclosure to merchant and issuer; not shown as live in Agent Pay. Mastercard's own merchant tutorial calls agent-to-merchant intent exchange "future facing". | S20; S27 spec/constraints.md l.793; S26 | S20: "Agentic Commerce Identifiers: Digital Service Provider ID and Digital Commerce Solution Indicators help issuers and acquirers identify agentic transactions." |
| D12 audit export | C | Issuer only: `/{id}/transactions` (last 30 days, status includes DCLN declined, with merchant name and MCC, no rule reason), `/{id}/token/statushistory`, and spend control search with `consumedThreshold`. Integrators: `GET /cards/{cardId}/transactions` (30 days, needs issuer support). No export of rule decisions with reasons found. | S24 l.277-298, 3179, 3248; S25 | S24: "It only returns transactions performed within the last 30 days" (wrapped across lines 288-289 in raw) |
| D13 multi-rail policy | ND | Agent Pay is card-only in the docs read. Agent Pay for Machines (June 2026) claims spending limits with "multi-rail settlement across cards, accounts and stablecoins". Press release only. | S30 l.78-82 | S30: "Organizations can set authorization rules and spending limits that are programmatically enforced, ensuring transactions stay within defined parameters." (PDF text, ligatures restored) |

Verifiable Intent, for reference [S27]: constraint types `mandate.checkout.allowed_merchants`,
`mandate.checkout.line_items`, `mandate.payment.allowed_payees`, `mandate.payment.amount_range`, `mandate.payment.budget`
(cumulative, with the network required to track spend), `mandate.payment.recurrence`, `mandate.payment.agent_recurrence`,
`mandate.payment.reference` (spec/constraints.md l.224-829). It defines no revocation: "VI v0.1 does not define a
credential-layer revocation protocol." (spec/security-model.md l.319). Lifetimes are recommended, not enforced by the spec
(L2 autonomous 24h to 30d, L3 about 5 minutes). Status line: "Draft (v0.1). Maintained by Mastercard" (README.md l.7).

### Test case

- (a) Named counterparties only: yes on the token, via `ALLOW_LST_MID`, but only the issuer can set it, and the token
  is per agent, so the list applies to every task that agent runs unless the issuer rewrites it per task.
- (b) Per-task budget: yes as `ABSOLUTE_SPEND_LIMIT`, but then no per-transaction or per-day cap can sit on the same
  token.
- (c) Ends when the task ends: not verifiable. The absolute limit's expiry ends the rule; behaviour after it is not
  documented. Manual suspend or delete is the reliable end.
- (d) One-step revocation a third party can verify: one-step suspend or delete exists (issuer or token requestor);
  not verifiable by a payee or auditor.
- (e) Credential per task: not documented (token per agent; one-time DTVC and single-use rule per transaction).
- Full test case: **no**. Missing: principal-direct control (all through the issuer, optional for issuers), a token per
  task, a task-end expiry on the token, combining a budget with a per-transaction cap, third-party-verifiable
  revocation, and a task identifier the merchant can see (Verifiable Intent is a draft).

### Sources (item 2)

- [S20] https://developer.mastercard.com/mastercard-checkout-solutions/documentation/use-cases/agent-pay/, rendered text capture 2026-10-08, raw/developer.mastercard.com/rendered-mcs-agent-pay.txt
- [S21] https://developer.mastercard.com/mastercard-checkout-solutions/documentation/llms-full.txt, fetched 2026-10-08, raw/developer.mastercard.com/mcs-llms-full.txt
- [S22] https://developer.mastercard.com/mdes-customer-service/documentation/release-history/release-notes-july2026/index.md, fetched 2026-10-08, raw/developer.mastercard.com/mdes-cs-release-history_release-notes-july2026.md
- [S23] https://developer.mastercard.com/mdes-customer-service/documentation/use-cases/tokenspendcontrol-use-case/index.md, fetched 2026-10-08, raw/developer.mastercard.com/mdes-cs-use-cases_tokenspendcontrol-use-case.md
- [S24] https://static.developer.mastercard.com/content/mdes-customer-service/swagger/mdes-customer-service.yaml (v4.0.1), fetched 2026-10-08, raw/static.developer.mastercard.com/mdes-customer-service.yaml
- [S25] https://static.developer.mastercard.com/content/mastercard-checkout-solutions/swagger/card_v1.yaml, fetched 2026-10-08, raw/static.developer.mastercard.com/mcs-card_v1.yaml (deleteCard l.825; getTransactionHistory l.981)
- [S26] https://developer.mastercard.com/merchant-cloud/documentation/tutorials-and-guides/ai-revolution/14/index.md, fetched 2026-10-08, raw/developer.mastercard.com/rails-for-agentic-commerce.md
- [S27] agent-intent/verifiable-intent@356c296 README.md, spec/constraints.md, spec/security-model.md
- [S28] https://newsroom.mastercard.com/news/press/2025/april/mastercard-unveils-agent-pay-pioneering-agentic-payments-technology-to-power-commerce-in-the-age-of-ai, fetched 2026-10-08, raw/newsroom.mastercard.com/pr-2025-04-agent-pay.html. Press release only: "Consumers will have complete control over what the agent is allowed to purchase on their behalf"
- [S29] https://s25.q4cdn.com/479285134/files/doc_news/Mastercard-Unveils-New-Tools-and-Collaborations-to-Power-Smarter-Safer-Agentic-Commerce-2025.pdf, fetched 2026-10-08, raw/s25.q4cdn.com/mc-agentic-tools-2025.pdf (Agent Toolkit, Insight Tokens)
- [S30] https://s25.q4cdn.com/479285134/files/doc_news/Mastercard-Launches-Agent-Pay-for-Machines-to-Unlock-Super-Fast-Always-On-Payments-2026.pdf (10 June 2026), fetched 2026-10-08, raw/s25.q4cdn.com/mc-ap4m-2026.pdf
- [S31] https://s25.q4cdn.com/479285134/files/doc_news/Mastercard-Advances-Agentic-Commerce-With-New-Trust-and-Intelligence-Services-2026.pdf (30 Sept 2026), fetched 2026-10-08, raw/s25.q4cdn.com/mc-trust-intel-2026.pdf
- [S32] https://developer.mastercard.com/platform/documentation/agent-toolkit/index.md, fetched 2026-10-08, raw/developer.mastercard.com/agent-toolkit.md (the Agent Toolkit MCP server serves documentation only; it does not make payments)
- [S33] https://blog.cloudflare.com/secure-agentic-commerce/, fetched 2026-10-08, raw/blog.cloudflare.com/secure-agentic-commerce.html (both TAP and Agent Pay use Web Bot Auth with a `tag` for browse versus pay and a network-hosted key directory)
- [S34] https://developer.mastercard.com/llms.txt, fetched 2026-10-08, raw/developer.mastercard.com/llms.txt (no Agent Pay service listed; MDES Customer Service listed)
- GitHub org listing for Mastercard (no Agent Pay repo; developers-agent-toolkit is documentation tooling): raw/api.github.com/orgs-Mastercard-repos.json

### Blocked or unverifiable (item 2)

- blocked: https://www.mastercard.com/news/press/2025/april/... and
  https://www.mastercard.com/global/en/business/artificial-intelligence/mastercard-agent-pay.html (Access Denied to
  curl); newsroom.mastercard.com and the investor PDFs were used instead.
- not public: https://developer.mastercard.com/mastercard-agent-pay/documentation/* (search engines index pages such as
  use-cases/card-enrollment and testing; every `index.md` returns 404 and the HTML is an app shell). The intent
  creation, authentication and checkout APIs for Agent Pay were not found in any public spec.
- not fetched: Mastercard Connect bulletins (for example GLB 13388.1 on Digital Commerce Solution Indicators,
  trc-techresource Token Authentication Framework guide), member-only.
- The authorization data elements that carry the agentic identifiers (DE numbers) are not public.

---

## 3. American Express Agentic Commerce Experiences (ACE) Developer Kit

- Vendor: American Express.
- Status: limited access. API guide and specifications are released only after a request form and a confidentiality
  agreement [S40]. American Express's own page says three of five specifications were available on 14 April 2026 and
  two were still in development [S41]. The portal page is "Last Updated: April 10, 2026" [S40]. Agent Purchase
  Protection is worded as a future commitment [S41].
- Versions read: developer portal overview (rendered capture) [S40]; company page [S41]; engineering blog post of 22
  April 2026 [S42]. No API reference, OpenAPI file, SDK or GitHub repository is public; the American Express GitHub
  organisation has no ACE repository [S43], and the blog says SDKs, an MCP server and reference implementations will
  come "in the future" [S42].

### Control model (vendor descriptions only, not verified against any API)

By American Express's description, a Card Member enrolls a card with a registered agent (issuer-led authentication,
required passkey). The agent submits a structured purchase intent ("budget limits, item specifications, and merchant
preferences"), the Card Member approves it with a passkey, and American Express then issues a payment credential
"scoped for limited use" against that intent [S40]. Enforcement is described as happening at credential issuance
(validating that the intent is valid and constraints are satisfied) and at execution [S42]. American Express acts as
issuer, network and acquirer for its proprietary cards, so issuer and network enforcement are the same party (press
reports; not checked against an API). Card Members are to manage agents, intents and spend controls in the American
Express app or participating issuer apps [S40]. None of this can be checked: the specifications are under NDA.

### Dimensions

| Dim | Verdict | What exactly is supported | Source | Quote (confirmed unless marked) |
|---|---|---|---|---|
| D1 per-transaction cap | ND | Marketing describes "budget limits" in the intent and "spending limits" enforced at execution; no field or rule type is public. | S40; S42 | S42: "Delegation often involves enforced boundaries, including spending limits, merchant restrictions, frequency controls, and conditional execution." (line-wrapped in raw) |
| D2 per-period cap | ND | "frequency controls" named in the blog only. | S42 | see D1 |
| D3 total budget | ND | "budget limits" in intent, marketing only. | S40 | S40: "Agents will be able to share a structured summary of the Card Member's purchase intent, including controls such as budget limits, item specifications, and merchant preferences." |
| D4 counterparty allowlist | ND | "merchant preferences" / "merchant restrictions", marketing only. | S40; S42 | see D3 |
| D5 per-counterparty cap | ND | Not mentioned. | none | none |
| D6 asset/network/MCC limits | ND | Not mentioned. Proprietary US-issued cards only at launch (secondary press reports, unconfirmed). | none | none |
| D7 expiry/time window | ND | "Short-lived authorization artifacts" and checks that "the intent is still valid", marketing only. | S42 | S42: "Intent is first captured and stored as a structured contract." |
| D8 per-task credential | ND | Credential issued per verified intent and "scoped for limited use", marketing only. | S40 | S40: "Payment credentials are scoped for limited use, enforcing the Card Member's intent and preferences." |
| D9 revocation | ND | **Who:** Card Member, in future tense. **How:** "view, manage, or revoke intents" in the American Express app or issuer apps. **How fast:** not stated. **Third-party verifiable:** not stated. | S40 | S40: "Card Members will be able to view, manage, or revoke intents, set granular spend controls, and clearly see their intent linked to the corresponding transaction." |
| D10 human step-up | ND | Issuer may re-involve the Card Member before credential issuance; human-in-the-loop and autonomous modes described. Marketing only. | S40 | S40: "Issuers can perform a risk assessment before issuing the payment credentials, with the option to bring the Card Member back into the flow for final confirmation." |
| D11 task/intent binding visible to counterparty | ND | Merchants are told to rely on "cryptographically-signed and auditable evidence of a delegated purchase intent"; Cart Context shares basket data for disputes; Agent Registration plans Web Bot Auth. Specs for Agent Registration and Cart Context were still under development. | S40; S41 | S41: "Account Enablement, Intent Intelligence, and Payment Credentials specifications are available as of 4/14/2026. Agent Registration and Cart Context specifications are still under development." |
| D12 audit export | ND | Dashboards for Card Members are promised; no export API is public. | S40 | none |
| D13 multi-rail policy | ND | Card only. | none | none |

### Test case

- (a) to (e): none can be verified from public sources. Vendor wording claims budget limits, merchant preferences,
  scoped per-intent credentials and revocable intents, which would cover (a), (b), (d, principal side only) and (e)
  if true; nothing is said about third-party verification of revocation.
- Full test case: **unknown (ND)**. Missing from public view: every field, rule type and endpoint.

### Sources (item 3)

- [S40] https://developer.americanexpress.com/products/nextgen-agentic-payments/overview, rendered text capture 2026-10-08 (tabs opened, no form submitted), raw/developer.americanexpress.com/rendered-ace-overview.txt
- [S41] https://www.americanexpress.com/en-us/company/agentic-commerce/, fetched 2026-10-08, raw/www.americanexpress.com/agentic-commerce.html
- [S42] https://www.americanexpress.io/building-trust-in-ai-powered-transactions-with-amex-agentic-commerce-experiences/ (22 April 2026), fetched 2026-10-08, raw/www.americanexpress.io/ace-blog-2026-04-22.html (vendor engineering blog, not an API reference)
- [S43] GitHub org listing for americanexpress, fetched 2026-10-08, raw/api.github.com/orgs-americanexpress-repos.json (88 repositories, none for ACE or agentic payments)
- Press release (14 April 2026) quoted via S41's own wording; S41 also says: "In the future, if a Card Member authorizes a registered AI agent to make a purchase, and that agent sends American Express the customer’s authenticated purchase intent, American Express will protect eligible customers from charges related to AI agent error."

### Blocked or unverifiable (item 3)

- gated: ACE API Guide and Specifications (request form plus confidentiality agreement on S40). Not requested, per the
  read-only rule.
- blocked: https://www.nasdaq.com/press-release/american-express-debuts-agentic-commerce-experiences-acetm-developer-kit-and
  (curl error 92) and https://financialit.net/news/infrastructure/american-express-debuts-agentic-commerce-experiences-acetm-developer-kit-and
  (157-byte block page, saved as raw/financialit.net/amex-ace-pr-2026-04-14.html). The Business Wire original was not tried
  after the Visa Business Wire page returned Access Denied.
- unconfirmed (secondary press only): US-issued proprietary cards only at launch; launch partners.

---

## Most surprising gaps

1. **The strongest card-side policy found is issuer-only.** Mastercard's Token Spend Controls (11 rule types,
   network-enforced, production since 5 August 2026) can be written only through the issuer's MDES Customer Service
   API, and issuer support is optional [S22 l.190]. An agent platform or a company principal has no public API to
   set them; the first sentence of the use-case page says "token requestors" define the rules, which contradicts the
   API it documents [S23 l.4 versus S24 l.434].
2. **Budget and per-transaction cap are mutually exclusive on a Mastercard token.** `ABSOLUTE_SPEND_LIMIT` "cannot
   coexist with other LIMIT type" [S24 l.3936], and its expiry ends the rule, with no statement of what the token does
   afterwards.
3. **Mastercard's own docs disagree on what TRANSACTION_SPEND_LIMIT means** (per transaction in S23 l.12, "Cumulative
   transaction spend limit" in S24 l.3941).
4. **Visa's enforcement claims live only on a product page.** The API reference defines `declineThreshold`,
   `effectiveUntilTime` and a merchant "preference" string, but says nothing about who declines what; the "VisaNet
   controls" sentence sits beside a development-and-deployment disclaimer [S1]. There is no cumulative per-instruction
   budget and no GET for instructions [S3].
5. **Revocation is never third-party verifiable at any network.** Token and instruction status is visible only to the
   issuer or token requestor; a merchant or auditor sees a decline. Visa's cancel can itself require cardholder
   re-authentication [S3 l.210614].
6. **Merchants receive agent identity, not task identity.** TAP and Agent Pay carry an agent key id, a browse/pay tag
   and a session nonce [S7, S33]; no instruction or mandate id is in the defined fields. Mastercard calls
   agent-to-merchant intent exchange "future facing" [S26]. Verifiable Intent would add it, but is a draft with no
   revocation protocol [S27].
7. **Visa's published key directory does not match its spec.** The TAP spec names https://mcp.visa.com/.well-known/jwks
   as the agent key directory; on 8 October 2026 it held a single RSA key and no Ed25519 agent keys [S12].
8. **Undocumented `PCT_AGENT` rule category** in Visa Transaction Controls [S9].
9. **One VIC instruction API, three paths** (`/vacp/v1`, `/acp/v1`, `/icc/v1`) across Visa sample code, the Cybersource
   guide and the Cybersource spec [S5, S4, S3].
10. **American Express publishes nothing checkable**: specifications only under NDA [S40].

## Products the teardown may be missing

- Mastercard Agent Pay for Machines (AP4M), June 2026: claims programmatic spending limits with settlement across cards,
  bank accounts and stablecoins, and cites Verifiable Intent; it would be the only card-network D13 candidate. Press
  release only: https://s25.q4cdn.com/479285134/files/doc_news/Mastercard-Launches-Agent-Pay-for-Machines-to-Unlock-Super-Fast-Always-On-Payments-2026.pdf
- Verifiable Intent (Mastercard with Google, draft v0.1): the most precise public constraint vocabulary from a card
  network (payee allowlist, amount range, cumulative budget); worth a row of its own if the mandate group does not
  cover it: https://github.com/agent-intent/verifiable-intent
- Visa Transaction Controls: the issuer product that actually holds per-token period limits, counts and category blocks
  on Visa; not agent-specific but it is where Visa-side enforcement exists in a public API:
  https://developer.visa.com/capabilities/vctc
- Mastercard Virtual Card Tokens (MVCT): the path Agent Pay integrators must use for web guest checkout, and one of the
  two programs whose issuers can set token spend controls:
  https://developer.mastercard.com/mastercard-checkout-solutions/documentation/use-cases/virtual-card-tokens/index.md
