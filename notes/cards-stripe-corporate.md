# Group: cards-stripe-corporate

Read on 8 Oct 2026 (all fetches 2026-10-08 UTC, listed in [SOURCES.md](../SOURCES.md)).
Verdict codes and dimensions are those of MATRIX.md. Source ids resolve in each
item's source list; S-numbers are unique across this file. Every quote below was checked verbatim
(whitespace-normalized) against the saved copy by a quote-checking script. Cells without quotation marks are my
paraphrase of the raw copy or the field names read from the spec.

---

## 1. Stripe Issuing used for agents ("Issuing for agents")

- Vendor: Stripe. Status: the core Issuing pages read carry no preview label, and the spending and
  lifecycle fields are in the GA spec; card currencies are `usd` (US), `eur` (EU) and `gbp` (UK); access
  needs an application in the Dashboard [S4][S5][S8]. Merchant ID spending controls: private preview [S1].
  PaymentMethod from an Issuing card (the SPT path): private preview, API version `2026-04-22.preview`
  [S12]. Webhook-triggered fraud challenges and Autopilot: public preview [S2].
- Spec read: stripe/openapi@52ca110 (commit of 2026-10-08), GA spec `2026-09-30.endive`, beta SDK spec
  `2026-09-30.preview`, private preview SDK spec `2026-10-07.preview` [S8][S9][S10].

**Control model.** The principal is the Stripe account that runs Issuing. It sets `spending_controls`
on a Card or on a Cardholder (a cardholder's limits apply across all of its cards), and
`lifecycle_controls` on a virtual card. Stripe, as issuer processor, evaluates these controls at
authorization time, before it sends the optional synchronous `issuing_authorization.request` webhook,
in which the principal's own code approves or declines within 2 seconds [S1][S2]. The card network
carries the authorization; the merchant sees only an approval or a decline. The "Issuing for agents"
page is a use-case guide over the same Issuing APIs, not a separate product surface: it recommends one
virtual card per agent or per task, plus webhook logic for anything the built-in controls lack [S4].

| Dim | Verdict | What exactly is supported | Source | Quote (confirmed) |
|---|---|---|---|---|
| D1 | N | `spending_limits[].interval = per_authorization` with `amount` in minor units. Stripe also applies a default 10,000 USD per-authorization ceiling that only support can remove. | S1, S8 (spec3.json:26416, enum at 26734) | |
| D2 | N | `interval` values `daily`, `weekly`, `monthly`, `yearly`; date intervals start at midnight UTC (calendar periods, not rolling). Aggregation can lag up to 30 s, and tips or fees posted later can push spend over a limit. Default 500 USD per day if no limit is set. | S1, S8 | "Spending aggregation is done on a best-effort basis." [S1] |
| D3 | N | `interval = all_time` (lifetime of the card, carried across replacement cards). Also `lifecycle_controls.cancel_after.payment_count` cancels the card after N payments. | S1, S3, S8 (spec3.json:26207) | "You can use lifecycle controls to automatically cancel a virtual card after a specified number of payments." [S3] |
| D4 | CODE (GA); private preview for IDs | GA `spending_controls` has no merchant-identifier field (only categories, countries, card presence). Merchant ID controls are private preview; the field names `allowed_merchant_network_ids` / `blocked_merchant_network_ids` appear only inside `x-stripeMostCommon` hint lists of the create-card and create-cardholder request bodies in the beta and private-preview SDK specs, with no property definition. In GA the principal must check `merchant_data.network_id` or name in the real-time webhook (the agents page stores an `allowed_merchant` value in card metadata for that check). | S1, S2, S4, S8, S9 (spec3.beta.sdk.json:181752, 184846), S10 (219805) | "Merchant ID spending controls is in private preview." [S1] |
| D5 | CODE | A spending limit can carry `categories` (a per-category cap), but there is no per-merchant cap. A different limit per payee needs webhook logic, or one card per payee. | S1, S2 | |
| D6 | N | `allowed_categories` / `blocked_categories` (295 Stripe category values mapped from MCCs), `allowed_merchant_countries` / `blocked_merchant_countries`, `allowed_card_presences` / `blocked_card_presences`. Currency is fixed per card. `allowed_merchant_currencies` is named only in preview hint lists. | S1, S5, S8 (spec3.json:25481), S9 | |
| D7 | C | Custom card expiry by `exp_month` / `exp_year` only (month granularity). No valid-from and no hours-of-day field. Ending at task end needs an explicit `status=canceled` call or `payment_count`; time-of-day rules need webhook code. | S3, S6, S8 | "The expiration date must be at least 1 month and less than 5 years in the future." [S6] |
| D8 | N | One virtual card per task, with its own controls and metadata, is the documented pattern. Caveat: minting needs an API key with Issuing write permission, and restricted-key permissions are per resource type, so the key that mints a per-task card can also loosen any card's controls. | S4, S11 | "Issue virtual cards scoped to a single task or session." [S4]; "When you create a RAK in the Stripe Dashboard, you select which Stripe resources the key can access and the permissions for each resource: **Read**, **Write**, or **None**." [S11] |
| D9 | N (revoke); third party ND | Who: the Stripe account (Dashboard, or any key with Issuing card write). How: set card `status` to `inactive` (reversible) or `canceled` (permanent), or set the cardholder inactive; or rely on `payment_count` auto-cancel. How fast: applies to later authorizations; no latency is documented, and force posts still settle after cancellation (lifecycle doc, scenario 5). Third-party verifiable: no documented way; the merchant only sees a decline. | S3, S5 | |
| D10 | CODE | No built-in amount threshold for human approval. The real-time webhook can decline and alert a human, but Stripe falls back to the timeout setting after 2 seconds, so a synchronous human decision is not practical. Declining with `send_fraud_challenges: ["sms"]` (public preview) lets the cardholder confirm by SMS and the merchant retry. | S2, S7 | |
| D11 | ND | Card `metadata` stays in the issuer's account and appears in the issuer's own webhooks; no documented field carries an issuer-set task identifier to the merchant. (The SPT path in item 2 adds `shared_metadata`.) | S4, S5 | |
| D12 | N | Authorizations API records approved and declined attempts with `request_history.reason` (for example `spending_controls`, `webhook_declined`, `webhook_timeout`); Transactions API for settled spend; webhooks for each event. | S2, S4, S8 (spec3.json:25217) | |
| D13 | ND | Controls govern card authorizations only. They also bind SPT payments funded by the card (MPP, UCP), because those still run as card authorizations. The private-preview `crypto_wallet` parameter attaches a card to a Bridge wallet (funding, not a cross-rail policy). | S10, S12 | |

**Test case.**
(a) Named counterparties only: not in GA without code (webhook), or private preview merchant ID controls.
(b) Per-task budget: yes, `all_time` limit on a per-task card (subject to the 30 s aggregation lag and late tips or fees).
(c) Ends when the task ends: partly; `payment_count` or an explicit cancel; calendar expiry is month-granular.
(d) One-step revocation a third party can verify: one step yes (`status=canceled`); third-party verification no.
(e) Credential per task: yes, a virtual card per task.
Full test case: **no**. Missing in GA: a merchant allowlist by identifier, revocation that a payee or
auditor can check, a time window shorter than a month, and a task identifier the merchant can see.

**Sources (item 1)**
- [S1] https://docs.stripe.com/issuing/controls/spending-controls.md, 2026-10-08, raw/docs.stripe.com/issuing-spending-controls.md
- [S2] https://docs.stripe.com/issuing/controls/real-time-authorizations.md, 2026-10-08, raw/docs.stripe.com/issuing-real-time-authorizations.md
- [S3] https://docs.stripe.com/issuing/controls/lifecycle-controls.md, 2026-10-08, raw/docs.stripe.com/issuing-lifecycle-controls.md
- [S4] https://docs.stripe.com/issuing/agents.md, 2026-10-08, raw/docs.stripe.com/issuing-agents.md
- [S5] https://docs.stripe.com/api/issuing/cards/object.md and https://docs.stripe.com/api/issuing/cards/create.md, 2026-10-08, raw/docs.stripe.com/api-issuing-cards-object.md, raw/docs.stripe.com/api-issuing-cards-create.md
- [S6] https://docs.stripe.com/issuing/cards/virtual/issue-cards.md?testing-method=with-code, 2026-10-08, raw/docs.stripe.com/issuing-issue-virtual-cards.md
- [S7] https://docs.stripe.com/issuing/controls/fraud-challenges.md, 2026-10-08, raw/docs.stripe.com/issuing-fraud-challenges.md
- [S8] stripe/openapi@52ca110 openapi/spec3.json: issuing_authorization_request :25217, issuing_card_authorization_controls :25481, issuing_card_lifecycle_conditions :26207, issuing_card_spending_limit :26416; no /v1/shared_payment paths in the GA file
- [S9] stripe/openapi@52ca110 openapi/spec3.beta.sdk.json: x-stripeMostCommon hint lists :181752 (/v1/issuing/cardholders) and :184845 to :184852 (/v1/issuing/cards); /v1/shared_payment/issued_tokens :280790
- [S10] stripe/openapi@52ca110 openapi/spec3.private_preview.sdk.json: /v1/issuing/cards hint list :219805 and `crypto_wallet` create parameter; /v1/shared_payment/issued_tokens :332965 (recurring_param_api_params :333111, usage_limits_param :333149); shared_payment_tokens_usage_limits_recurring :114279
- [S11] https://docs.stripe.com/keys/restricted-api-keys.md, 2026-10-08, raw/docs.stripe.com/restricted-api-keys.md
- [S12] https://docs.stripe.com/issuing/agents/programmatic-checkout.md, 2026-10-08, raw/docs.stripe.com/issuing-agents-programmatic-checkout.md

---

## 2. Stripe Shared Payment Tokens (SPT) and the Agentic Commerce Protocol (ACP)

Two objects are treated separately: 2a is Stripe's SPT API, 2b is the ACP delegate-payment spec that
SPT implements on Stripe.

### 2a. Stripe Shared Payment Tokens

- Vendor: Stripe. Status: preview. Agent-side issuance is private preview with a waitlist [S18]. The API
  appears only in the beta and private-preview SDK specs, not in GA spec3.json [S8][S9][S10]. Docs use
  `Stripe-Version: 2026-09-30.preview` and preview terms of service [S13]. Available to agents,
  customers and sellers in the US, Canada and listed European countries [S13].

**Control model.** The agent business (or a principal paying with its own Issuing card) mints a
`SharedPaymentIssuedToken` (`spt_...`) from a PaymentMethod in its own Stripe account. The token is
bound to one seller's Stripe profile (`seller_details.network_business_profile`, required) and carries
`usage_limits` (`currency` and `max_amount` required, `expires_at`). The seller sees a view-only
`SharedPaymentGrantedToken` and charges it through a PaymentIntent. Stripe enforces the limits when the
seller confirms the PaymentIntent. Who mints: the agent's Stripe account, with a key holding
`shared_payment_token_write`. Who enforces: Stripe. Single use: no, usable until cumulative captures
reach `max_amount`, expiry, or revocation. Revocation: one POST by the issuing account, with events to
both sides [S12][S13][S14][S15][S17]. When the SPT is funded by an Issuing card, both the SPT limits
and the card's controls and webhook apply [S12].

| Dim | Verdict | What exactly is supported | Source | Quote (confirmed) |
|---|---|---|---|---|
| D1 | C | No separate per-payment field; `max_amount` caps the cumulative captured amount, so it also bounds any single payment. A distinct per-payment cap needs an Issuing card underneath (`per_authorization`). | S12, S15 | |
| D2 | N (private preview only) | `usage_limits.recurring.interval` (`hour`, `day`, `week`, `month`, `year`) with `interval_count`, plus an older `recurring_interval` (`month`, `week`, `year`), exist only in the private-preview spec; the beta spec has `currency`, `expires_at`, `max_amount` only. | S9 (:280894), S10 (:333111, :114279) | |
| D3 | N | `usage_limits.max_amount` (required) counts cumulative captured payments; `usage_details.amount_captured` shows use. | S12, S15, S16 | "An SPT remains usable until it expires, you revoke it, or cumulative captured payments reach `usage_limits[max_amount]`." [S12] |
| D4 | N | `seller_details.network_business_profile` is required: exactly one seller profile per token, with an optional `external_id` for a sub-merchant. Only sellers on Stripe with a Stripe profile can be named. | S10, S13, S15 | |
| D5 | C | One token per seller, each with its own `max_amount`; a different cap per payee means one token per payee. | S15 | |
| D6 | N (currency) | `usage_limits.currency` is required. No category or country fields (moot with one seller). Supported funding methods: cards, Link, Apple Pay, Google Pay, Klarna, Affirm (limited). | S13, S15 | |
| D7 | N | `usage_limits.expires_at` (Unix seconds). No valid-from. | S15 | |
| D8 | N | A token per purchase, narrower than the account's API key; the docs recommend a restricted key with `shared_payment_token_write` to mint it. | S12, S15 | |
| D9 | N; payee-verifiable | Who: the issuing (agent) account. How: `POST /v1/shared_payment/issued_tokens/{id}/revoke`. How fast: not documented; the docs say only that the seller can no longer create a payment, and say nothing about payments already created. Third-party verifiable: the seller (payee) receives `shared_payment.granted_token.deactivated` and can `GET` the granted token, whose `deactivated_reason` is `revoked`, `consumed`, `expired` or `resolved`. Visible only to the two parties through Stripe, not to an independent auditor. | S13, S14, S16, S17 | "Revoke the SPT at any time to prevent the seller from using it to create a payment." [S13]; "You can’t create a payment with a revoked SPT." [S14] |
| D10 | CODE | No approval field on the token. The `requires_action` state is 3D Secure or redirect, triggered by issuer, seller or Stripe rules, not by a principal threshold. A human step needs the agent platform's own flow, or the Issuing webhook when card-funded. (Stripe's Link wallet adds per-request approval; see the extra block.) | S12, S13 | |
| D11 | N | `shared_metadata` on create is visible to the seller by default, so a task or intent id can travel with the token. | S15 | "The values here are visible by default with the party that you share this SharedPaymentIssuedToken with." [S15] |
| D12 | C | Token objects carry `usage_details`, `deactivated_at`, `deactivated_reason`; webhooks `used`, `deactivated`, `requires_action`, `active`. No documented record of refused payment attempts on the token. | S13, S16 | |
| D13 | X | Each token wraps exactly one `payment_method` (a single required string). The same limit shape applies to every method type, but one token never spans two. | S10, S15 | |

**Test case (2a).**
(a) Named counterparties only: yes for one seller per token; several named sellers need several tokens.
(b) Per-task budget: yes per token; one budget across several sellers needs an Issuing card with an
`all_time` limit underneath (composition, private preview).
(c) Ends when the task ends: yes, `expires_at`, or revoke.
(d) One-step revocation a third party can verify: one call; the payee can verify through Stripe; no auditor view.
(e) Credential per task: yes.
Full test case: **close, by composition, and only inside Stripe's network, in preview.** Missing: a single
token that names several payees, sellers outside Stripe, auditor-verifiable revocation, and GA status.

### 2b. ACP Delegate Payment API (allowance)

- Maintainers: OpenAI and Stripe; repo status `beta` [S21]. RFC status Draft, RFC version 2025-09-29
  [S20]. Latest released spec version 2026-04-17 (changelog/2026-04-17.md) [S19][S21]. Read at
  agentic-commerce-protocol@7fdd78d (last commit 2026-07-17); the `Allowance` schema in `spec/unreleased`
  is identical to 2026-04-17.

**Control model.** The agent platform (the protocol's client) sends the buyer's card credential (FPAN
or network token) with an `Allowance` to `POST /agentic_commerce/delegate_payment`, served by the
merchant's PSP or vault. The server mints a vault token (`vt_...`) that the merchant then charges on its
own PSP. Who mints: the PSP or vault provider that serves the endpoint (Stripe's response is an SPT in
the payment handlers RFC example [S22]). Who enforces: that server; the RFC's conformance checklist requires
it to enforce the allowance and its expiry [S20:396]. Who sets the limits: the agent platform, to
match the checkout session; the buyer has no field in the protocol. Single use: yes, `reason` must be
`one_time`. Revocation: not defined; the token dies at `expires_at`.

Allowance fields (all required): `reason` (enum `one_time`), `max_amount` (integer, minor units),
`currency` (ISO 4217 lowercase), `checkout_session_id`, `merchant_id` (max 256), `expires_at`
(RFC 3339) [S19:518 to 551]. No other members (`additionalProperties: false`).

| Dim | Verdict | What exactly is supported | Source | Quote (confirmed) |
|---|---|---|---|---|
| D1 | N | `max_amount` on a one-time token, so it is the per-transaction cap. | S19, S20 | "The returned token **MUST ONLY** be usable within the provided **Allowance** (reason, max_amount, currency, expiry)." [S20] |
| D2 | X | `reason` enum has only `one_time`; the RFC puts multi-use tokens out of scope. | S19:526, S20:17 | "Usage pattern for this allowance; currently only one_time is supported" [S19] |
| D3 | N | `max_amount` on a single-use token. | S19 | |
| D4 | N | `merchant_id` (required) names the one merchant allowed to use the token; `checkout_session_id` binds it to one checkout. | S19:537 | |
| D5 | C | One merchant per token, so per-payee caps mean one token per payee. | S19 | |
| D6 | N (currency) | `currency` required. Only one credential type, card; no MCC or network field. | S19:23 | "Exactly one credential type is currently supported: **card**." [S19] |
| D7 | N | `expires_at` required; the token MUST become invalid at or after it. No valid-from. | S20:65 | "The token **MUST** become invalid at or after `allowance.expires_at`." [S20] |
| D8 | N | One token per checkout session. | S19, S20 | |
| D9 | ND | Who, how, how fast, third-party: none defined. The RFC defines a single endpoint and no revoke operation; only expiry ends a token. | S20 | |
| D10 | ND | No approval step in the delegate payment API. A separate Draft RFC (delegate authentication, 2026-01-28) covers 3DS2 consumer authentication through a merchant-chosen provider, which is issuer authentication, not a principal threshold. | S20, S23 | |
| D11 | N | `checkout_session_id` ties the token to a checkout the merchant created; request `metadata` is echoed in the response. | S19, S20 | |
| D12 | ND | The RFC lists auditability as a goal but defines no audit record or export. | S20:14 | |
| D13 | X | Card only in the current spec. | S19:23 | |

**Test case (2b).** (a) One named merchant per token: yes. (b) Budget per checkout: yes. (c) Expiry:
yes. (d) Revocation: not defined. (e) Credential per checkout: yes. Full test case: **no**; it is a
single-purchase token with no revocation, no recurring use, and limits chosen by the agent platform.

**Sources (item 2)**
- [S12] (see item 1) programmatic checkout
- [S13] https://docs.stripe.com/agentic-commerce/concepts/shared-payment-tokens.md?agent-seller=agent, 2026-10-08, raw/docs.stripe.com/spt-concept-agent.md
- [S14] https://docs.stripe.com/agentic-commerce/concepts/shared-payment-tokens.md?agent-seller=seller, 2026-10-08, raw/docs.stripe.com/spt-concept-seller.md (Connect variant also saved: raw/docs.stripe.com/spt-concept-connect.md)
- [S15] https://docs.stripe.com/api/shared-payment/issued-token/create.md, 2026-10-08, raw/docs.stripe.com/api-spt-issued-token-create.md
- [S16] https://docs.stripe.com/api/shared-payment/issued-token/object.md, 2026-10-08, raw/docs.stripe.com/api-spt-issued-token-object.md (granted token: raw/docs.stripe.com/api-spt-granted-token.md)
- [S17] https://docs.stripe.com/api/shared-payment/issued-token/revoke.md, 2026-10-08, raw/docs.stripe.com/api-spt-issued-token-revoke.md
- [S18] https://docs.stripe.com/agentic-commerce.md, 2026-10-08, raw/docs.stripe.com/agentic-commerce-index.md ("This feature is in private preview." for the agent side)
- [S19] agentic-commerce-protocol@7fdd78d spec/2026-04-17/openapi/openapi.delegate_payment.yaml :1 to 30, :518 to 551
- [S20] agentic-commerce-protocol@7fdd78d rfcs/rfc.delegate_payment.md :3 to 17, :64 to 65, :121 to 128, :392 to 396
- [S21] agentic-commerce-protocol@7fdd78d README.md :10 ("is currently in `beta`"); changelog/2026-04-17.md
- [S22] agentic-commerce-protocol@7fdd78d rfcs/rfc.payment_handlers.md :81 to 89, :245 to 263
- [S23] agentic-commerce-protocol@7fdd78d rfcs/rfc.delegate_authentication.md :1 to 25
- [S8], [S9], [S10] (see item 1) for SPT schema lines

---

## 3. Stripe agent toolkit and Stripe MCP server

- Vendor: Stripe. Toolkit: open source, github.com/stripe/agent-toolkit@08d371a (commit of 2026-10-08).
  Remote MCP server at mcp.stripe.com; several MCP tools are marked public or private preview [S26].
  From 31 Oct 2026 the MCP server accepts only OAuth or agent-tagged keys [S26].

**Control model.** The toolkit adds no spend controls. Its TypeScript and Python packages connect to
the remote MCP server with the key they are given and expose whatever tools that key's permissions
allow [S24][S25]. Constraint lives in Stripe account objects: restricted API keys (per resource
None/Read/Write), the agent tag on a restricted key, approval rules (two-party approval) that apply to
agent-tagged keys, and a human confirmation step that the MCP server itself requires for certain
writes [S11][S26][S27][S28]. These constrain what an agent does to the principal's own Stripe account
(refunds, PaymentIntents, payouts), not what it buys elsewhere. The MCP's documented method list
includes Issuing only as list and retrieve methods, and no shared-payment method, so buying through
cards or SPTs is not done through this toolkit [S26]. The toolkit's "stripe-pay" skill (business-to-
business transfers by Stripe Profile handle) carries safety rules written as instructions to the agent,
not as enforcement [S29].

| Dim | Verdict | What exactly is supported | Source | Quote (confirmed) |
|---|---|---|---|---|
| D1 | C | Approval rule with an amount condition on "Payment intent is created" or "Refund is created", actor condition "agent-tagged API keys", control Require approval or Block. Account setting, not on the key. | S28 | "**Amount condition**: Require approval for a refund only if the amount exceeds a threshold." [S28] |
| D2 | C (count only) | Rate limit condition: approval when the number of requests in a duration exceeds a threshold. No amount-per-period rule documented. | S28 | |
| D3 | ND | No lifetime amount budget on a key or session. | S11, S28 | |
| D4 | ND | No payee allowlist on keys, sessions or approval rules. | S11, S28 | |
| D5 | ND | None. | | |
| D6 | ND | None (keys scope API resources, not assets or categories). | S11 | |
| D7 | C | Keys can be expired from the Dashboard, with a delayed expiration of up to 7 days; OAuth sessions are revoked by hand. No valid-until at creation documented. | S11, S26 | |
| D8 | C | A separate restricted or agent-tagged key per agent, created in the Dashboard, with per-resource permissions; granularity is the resource type, never an object, amount or payee. The toolkit warns on `sk_` keys and accepts `sk_` or `rk_`. | S11, S25, S27 | "Tool permissions are controlled by your Restricted API Key (RAK)." [S24] |
| D9 | N (revoke); third party ND | Who: the user (own OAuth sessions) or an admin (others' sessions, all sessions), and key holders with Dashboard access (expire or rotate). How: Dashboard "Revoke access" or expire key. How fast: not documented. Third-party verifiable: no. | S11, S26 | |
| D10 | N | The MCP server requires a human to confirm certain `stripe_api_write` actions through a URL (approval expires in 24 h). Agent-tagged keys fall under approval rules with designated reviewers; Stripe ships default rules for refunds and subscription cancellation. | S26, S27, S28 | "To prevent agents from making mistakes, Stripe requires human confirmation before it takes certain `stripe_api_write` actions, such as refunds and outbound payments." [S26] |
| D11 | ND | None in the toolkit. Approval requests can carry a justification text (internal). | S28 | |
| D12 | N | Approval events (`v2.core.approval_request.created`, `approved`, `rejected`, `expired`, `succeeded`, `failed`) as events; Security history logs rule and request changes; Workbench logs API requests and MCP tool calls. Export format not verified. | S26, S28 | |
| D13 | ND | Not applicable; no cross-rail spend policy. | | |

**Test case.** (a) No. (b) No. (c) Key expiry only. (d) One-step revoke in the Dashboard; not
third-party verifiable. (e) A key per agent, created by hand, scoped by resource type. Full test case:
**no**. The toolkit relies on Issuing (item 1), SPT (item 2) and account settings for any spend limit;
by itself it only decides which API calls the agent can make, plus human confirmation for some writes.

Also from S26: "Beginning October 31, 2026, Stripe MCP no longer accepts full-access secret keys or
restricted API keys without the Agent tag."

**Sources (item 3)**
- [S24] stripe/agent-toolkit@08d371a tools/README.md :26, :46
- [S25] stripe/agent-toolkit@08d371a tools/typescript/src/shared/constants.ts :9 (`MCP_SERVER_URL = 'https://mcp.stripe.com'`); tools/typescript/src/shared/mcp-client.ts :87 to 95 (key prefix check and warning)
- [S26] https://docs.stripe.com/mcp.md, 2026-10-08, raw/docs.stripe.com/mcp.md
- [S27] https://docs.stripe.com/keys.md, 2026-10-08, raw/docs.stripe.com/keys.md (section "API keys for autonomous agents")
- [S28] https://docs.stripe.com/account/approvals.md, 2026-10-08, raw/docs.stripe.com/account-approvals.md
- [S29] stripe/agent-toolkit@08d371a skills/stripe-pay/SKILL.md :28 to 31 ("Don’t send money unless the user explicitly asks you to make the transfer." is a prompt rule, not enforcement); `stripe pay` CLI reference saved at raw/docs.stripe.com/cli-pay.html, not otherwise relied on
- [S11] (see item 1)

---

## 4. Ramp (Agentic Payments: Agent Cards, Stripe MPP, x402; Funds)

- Vendor: Ramp. Status: Developer API v1 (OpenAPI `info.version` v1). The Ramp MCP guide says the
  server is subject to change [S39]. The agents site routes beta access requests through a contact form
  [S34]. The default identity model (agent acts as the signed-in user) is described as available today;
  standalone agent identities are limited early access [S34]. Server-side card details (Vault API) need production approval [S33].

**Control model.** Every Ramp card draws against a Fund, a budget object with `spending_restrictions`
(amount and interval, per-transaction cap, allowed and blocked categories, MCCs and vendors, lock date)
[S30][S33]. An Agent Card is a one-time credential that the agent requests through the Ramp MCP or CLI
tool `ramp_get_agent_card_creds` against one fund it can access, passing `fund_id`, `merchant_name`,
`merchant_url`, `merchant_country_code`, `amount`, `currency_code` [S35]. Ramp, as card program
manager, enforces fund restrictions at authorization and records declines with a reason [S30]. By
default the agent acts with the connected user's OAuth session and can use any fund that user can
[S31][S34]. Stripe MPP purchases also draw on funds; x402 purchases draw on a separate USDC wallet that
fund controls may not cover [S31].

| Dim | Verdict | What exactly is supported | Source | Quote (confirmed) |
|---|---|---|---|---|
| D1 | N | `transaction_amount_limit` on fund restrictions (and on vault-card limits). | S30 (:27142, :33126) | |
| D2 | N | `interval` enum `DAILY`, `WEEKLY`, `MONTHLY`, `QUARTERLY`, `TERTIARY`, `YEARLY`, `ANNUAL`; fund dump shows `start_of_interval` and `next_interval_resets_at`. | S30 | |
| D3 | N, with overage | `interval = TOTAL`. But `allowed_overage_percent_override` (0 to 100) on vault-card creation, a business default overage, and `temporary_limit` / `is_temporary_increase` let spend exceed the stated limit by design. | S30 (:24667) | "Optional fund-level override for the allowed overage percent." [S30] |
| D4 | N (identifier space unclear) | Fund `allowed_vendor_ids` / `blocked_vendor_ids` (UUIDs); vault-card limits `allowed_vendors` / `blocked_vendors`, which the schema describes as a list of merchants. Ramp's own data guide says card Merchants and bill-pay Vendors are separate objects, so which identifier the allowlist takes is not stated. The Agent Card request names one merchant; that the one-time card is locked to that merchant at authorization is stated only on a marketing blog. | S30, S35, S36, S37 | "Merchant ↔ Vendor: no direct link in the API." [S37] |
| D5 | C | No per-merchant limit inside one fund; a different cap per payee means one fund per payee. | S30, S32 | |
| D6 | N | `allowed_category_codes` / `blocked_category_codes` (43 Ramp category codes), `blocked_mcc_codes`; limit currency via `currency_code`. The spend-controls guide also names allowed countries, but no country field exists in the fund schema (ND for countries). | S30, S32 | |
| D7 | N | `lock_date` (date-time) suspends a fund or locks a card automatically. The landing page (marketing) claims auto-expiry from seconds to quarters; not found in the API. | S30, S34 | "Date to automatically suspend the fund." [S30] |
| D8 | C | The principal can create a per-task fund (`funds:write`), and each Agent Card is a one-time credential. But the default agent identity is the user, which can draw on all of that user's funds; confining an agent to one fund needs a standalone agent identity (limited early access). | S31, S34, S35 | "Standalone agent identities are in limited early access." [S34] |
| D9 | N (revoke); third party ND | Who: admins or integrations with `funds:write`; admins also control which users may use MCP connectors; standalone agents can be paused, have credentials rotated, or be removed. How: `POST /developer/v1/funds/{fund_id}/suspension`, `DELETE /developer/v1/funds/{fund_id}` (terminate), card lock tools. How fast: not documented. Third-party verifiable: no. | S30 (:10650, :10376), S34, S39 | |
| D10 | C (not in API) | The developer guide says approvals can route agent purchases above a threshold to a human; no API field for that rule was found (approval policies are set in the Ramp app). The skills' "confirm with the customer" steps are prompt instructions. | S32, S35 | "Funds constrain what an agent can spend, per merchant and per amount. Approvals can route agent purchases above a threshold to a human." [S32] |
| D11 | ND | Memo, receipt and accounting fields are completed in Ramp after the purchase, and the credential request takes a rationale; nothing documented reaches the merchant. | S31, S35 | |
| D12 | N | Transactions API lists `DECLINED` transactions with `decline_details.reason` (for example `AUTHORIZER_CARD_LIMIT`, `AUTHORIZER_CARD_AUTO_LOCK_DATE`, `AUTHORIZER_BUSINESS_VENDOR_BLACKLIST`); audit logs API (`audit_logs:read`). | S30 (:13542, :33561, :3962) | |
| D13 | C (card side only) | One fund governs cards, reimbursements, bills and MPP purchases; the x402 USDC wallet is outside it. | S31, S32 | "x402 purchases draw from a separately funded x402 wallet, rather than a user's card or fund. Its wallet balance and x402-specific setup apply; do not assume that card or fund controls apply identically to this method." [S31] |

**Test case.** (a) Named counterparties: yes by fund vendor allowlist, with the identifier caveat.
(b) Per-task budget: yes (`TOTAL`), unless overage or temporary increases are set. (c) Ends when the
task ends: yes (`lock_date`, date-time). (d) One-step revocation a third party can verify: suspend or
terminate the fund in one call; not third-party verifiable. (e) Credential per task: one-time Agent Card
per purchase yes; an agent confined to a per-task fund only with a standalone identity (early access).
Full test case: **no**. Missing: verifiable revocation, per-agent confinement in GA, a stated identifier
for the merchant allowlist, and any control over the x402 wallet path.

Marketing-only claims (not used for verdicts, paraphrased): the landing page lists spend restrictions
per agent, per task and per merchant, a customizable human-in-the-loop policy, auto-expiring cards and
one key per agent [S34]; the blog says the one-time credentials are single-use tokens scoped at the
Visa network level and revocable instantly [S36].

**Sources (item 4)**
- [S30] https://docs.ramp.com/openapi/developer-api.json, 2026-10-08, raw/docs.ramp.com/openapi-developer-api.json: audit logs :3962, /funds :10153, /funds/{fund_id} :10376, suspension :10650, /transactions :13542, ApiCardVaultCreationRequestBody :24638 (overage :24667), ApiFundSpendingRestrictionsRequestBody :27142, ApiSpendingRestrictionsRequestBody :33126, ApiTransactionDeclineDetails :33561
- [S31] https://docs.ramp.com/llms-guides/agent-payments.txt, 2026-10-08, raw/docs.ramp.com/guide-agent-payments.txt
- [S32] https://docs.ramp.com/llms-guides/spend-controls.txt, 2026-10-08, raw/docs.ramp.com/guide-spend-controls.txt
- [S33] https://docs.ramp.com/llms-guides/cards-and-funds.txt, 2026-10-08, raw/docs.ramp.com/guide-cards-and-funds.txt ("Every Ramp card draws against a fund.")
- [S34] https://agents.ramp.com/llms-full.txt, 2026-10-08, raw/agents.ramp.com/llms-full.txt (landing :9 to 33, introduction :81 to 115, identity :384 to 507, payments :509 to 583)
- [S35] ramp-public/skills@68f016d skills/ramp-agentic-purchase/SKILL.md :36 to 60 (tool summary "Get a one-time payment token for a fund")
- [S36] https://ramp.com/blog/virtual-cards-for-ai-agents, 2026-10-08, raw/ramp.com/blog-virtual-cards-for-ai-agents.html (marketing)
- [S37] https://docs.ramp.com/llms-guides/data-relationships.txt, 2026-10-08, raw/docs.ramp.com/guide-data-relationships.txt
- [S38] https://docs.ramp.com/llms.txt, 2026-10-08, raw/docs.ramp.com/llms.txt (index of the guide files)
- [S39] https://docs.ramp.com/llms-guides/ramp-mcp.txt, 2026-10-08, raw/docs.ramp.com/guide-ramp-mcp.txt

---

## 5. Brex (Team API cards, Budgets API v2 Spend Limits, Brex MCP)

- Vendor: Brex. Status: Team API version 1.0 and Budgets API v2 carry no alpha or beta suffix; under
  the launch-stage guide's versioning rule that implies GA (my inference) [S40][S41][S50]. Spend Limits
  (v1) are deprecated in favour of v2 [S44]. Brex MCP is Beta and needs an opt-in [S43].
  No agent-specific card or payment product found in the developer docs or the changelog through
  October 2026 [S44]; a web search on 8 Oct found none on brex.com either.

**Control model.** A principal with an API token holding the `cards` scope creates a vendor card
(`limit_type = CARD`, virtual) with `spend_controls`, or a Spend Limit (Budgets v2) whose cards and
members draw on it [S40][S41]. Brex, as issuer, enforces at authorization and reports declines with a
reason [S42]. Through MCP an agent acts with the signed-in user's Brex permissions, but card
management is not available via MCP [S43]. An agent would hold card details minted by a human or an
API integration.

| Dim | Verdict | What exactly is supported | Source | Quote (confirmed) |
|---|---|---|---|---|
| D1 | C | Card `spend_controls` has no per-transaction field; a Spend Limit has `transaction_limit`. Per-transaction caps need a Spend Limit behind the card. | S40, S41 (:1349) | |
| D2 | N | Card `spend_duration` `MONTHLY`, `QUARTERLY`, `YEARLY`; Spend Limit `period_recurrence_type` `PER_WEEK`, `PER_MONTH`, `PER_QUARTER`, `PER_YEAR`. No daily period. | S40 (:2539), S41 (:2079) | |
| D3 | N, can be soft | `ONE_TIME` (the limit never refreshes) on cards and Spend Limits. Spend Limit `authorization_type` `HARD` or `SOFT`, and `limit_buffer_percentage` (0 to 100), so a limit can be configured not to decline. | S40, S41 (:735 to 786) | "Whether authorizations will decline based on available balance." [S41] |
| D4 | N (by name) | `allowed_merchant_details` / `blocked_merchant_details`, each item `{name}`, up to 50, mutually exclusive. Matching is by merchant name; no merchant ID field. | S40 (:2151, :2435) | "List of merchants where card transactions are allowed. Cannot be used together with blocked_merchant_details." [S40] |
| D5 | C | One vendor card per merchant, each with its own limit. | S40 | |
| D6 | C | `merchant_category_controls` (allowed or blocked, 48 Brex categories) exist on Spend Limit update and read, not on card create or Spend Limit create. No currency or country rules beyond the limit's currency. | S41 (:1639, :2458) | |
| D7 | N (day) | Card `lock_after_date` (date, UTC). Spend Limit `start_date` / `end_date` (date). | S40 (:2392), S41 (:1912 to 1940) | |
| D8 | N | A vendor card per task through the API (`cards` scope covers create and update, so the minting token can also change limits). Not possible through MCP. | S40, S43 | "Actions like approvals and card management are not yet available via MCP." [S43] |
| D9 | N (revoke); third party ND | Who: an API token with `cards` scope, or Dashboard admins; the card owner is notified. How: `POST /v2/cards/{id}/lock` (reversible) or `POST /v2/cards/{id}/terminate`; `POST /v2/spend_limits/{id}/archive`. How fast: not documented. Third-party verifiable: no. | S40 (:194, :308), S41 (:699) | |
| D10 | ND | Approval policies exist for limit increase requests (`limit_increase_setting`, `limit_approval_policy_id`), not for individual purchases above a threshold. No documented real-time authorization decision hook; an `EMBEDDED_CARD_AUTHORIZATION` webhook type is listed without a payload schema. | S41, S42 (:1221) | |
| D11 | ND | Card `metadata` (up to 50 keys) is private; nothing documented reaches the merchant. | S40 (:1692) | |
| D12 | N | `EXPENSE_PAYMENT_UPDATED` webhook with `payment_status` `DECLINED` and `payment_status_reason` (for example `EXCEEDED_CARD_LIMIT`, `BUDGET_MERCHANT_RESTRICTION`, `BUDGET_EXPIRED`); Transactions API for settled card spend. | S42 (:784 to 830, :987) | |
| D13 | C | A Spend Limit can be spent through cards, reimbursement or bill payment (implementation guide; not verified in the API beyond `spend_type`). No crypto rail. | S41, S45 | "Spend limits can be spent via employee cards, virtual limit cards, physical cards, virtual cards, reimbursement, or bill payment." [S45] |

**Test case.** (a) Named counterparties: yes by merchant name (up to 50) on a vendor card. (b) Per-task
budget: yes (`ONE_TIME`), unless a soft limit or buffer is set. (c) Ends when the task ends: yes, by
date (`lock_after_date`). (d) One-step revocation a third party can verify: terminate in one call; not
third-party verifiable. (e) Credential per task: yes, a vendor card, minted outside the agent (MCP cannot).
Full test case: **no**. Missing: verifiable revocation, merchant matching by ID, a per-transaction cap on
the card itself, and any agent-specific product.

**Sources (item 5)**
- [S40] https://developer.brex.com/_bundle/openapi/team_api.yaml, 2026-10-08, raw/developer.brex.com/team_api.yaml: /v2/cards :40, /v2/cards/{id} :128 (PUT, scope `cards`), lock :194, terminate :308, CreateCardRequest :1692, LimitType :2106, LockedMerchantDetails :2151, SpendControl :2392, SpendControlRequest :2435, SpendDuration :2539
- [S41] https://developer.brex.com/_bundle/openapi/budgets_api.yaml, 2026-10-08, raw/developer.brex.com/budgets_api.yaml: /v2/spend_limits :520, archive :699, AuthorizationSettings :735, AuthorizationType :778, CreateAuthorizationSettings :1086, CreateSpendLimitRequest :1349, MerchantCategoryControls :1639, SpendLimit :1855, SpendLimitPeriodRecurrenceType :2079, UpdateSpendLimitRequest :2379
- [S42] https://developer.brex.com/_bundle/openapi/webhooks_api.yaml, 2026-10-08, raw/developer.brex.com/webhooks_api.yaml: ExpensePaymentStatus and ExpensePaymentUpdated :784 to 830, PaymentStatusReason :987, WebhookEventType :1221
- [S43] https://developer.brex.com/docs/mcp.md, 2026-10-08, raw/developer.brex.com/mcp.md
- [S44] https://developer.brex.com/changelog.md, 2026-10-08, raw/developer.brex.com/changelog.md
- [S45] https://www.brex.com/implementation/essentials/4-issue-a-spend-limit, 2026-10-08, raw/brex.com/implementation-issue-a-spend-limit.html
- [S50] https://developer.brex.com/guides/api-launch-stages.md, 2026-10-08, raw/developer.brex.com/api-launch-stages.md (also saved: raw/developer.brex.com/team_api.md, budgets_api.md, transactions_api.yaml, roles_permissions_scopes.md, createcard.html, llms.txt)

---

## 6. PayPal (short block)

- PayPal Agent Toolkit, paypal/agent-toolkit@a3aa963 (last commit 2026-09-01). Its tools are
  merchant-side: invoices, orders (`create_order`, `pay_order`), refunds, disputes, shipment tracking,
  catalog, subscriptions, reporting [S46 README :5 to 60]. The only control is a boolean per product and
  action in `configuration.actions`, checked by `isToolAllowed` [S46 configuration.ts :11 to 35]. No
  amount, period, payee, expiry or approval controls in the toolkit: D1 to D13 all ND, except D8 at
  most C (whatever PayPal credential the integrator supplies).
- PayPal Agentic Commerce Services / "Agent Ready" (paypal.ai) is a merchant acceptance offer for
  orders that come from shopping agents; the page is marketing and documents no buyer-side spend limits
  [S47]. I found no public PayPal API for a principal to cap what an agent spends.
- Sources: [S46] paypal/agent-toolkit@a3aa963 README.md, typescript/src/shared/configuration.ts;
  [S47] https://paypal.ai/, 2026-10-08, raw/paypal.ai/index.html (marketing).

## Extra: Stripe Link Agent Wallet (short block, consumer product)

Found while reading Stripe's agentic commerce pages; it may belong to a consumer-wallet group. A
developer's agent, authorized by a consumer through OAuth (`payment_methods.agentic` scope), creates a
spend request with `amount` and `context` (at least 100 characters, shown to the customer), plus
merchant name and URL for virtual cards, optional line items, totals and `expires_at`. The customer
approves in the Link app or website (10 minutes to respond); Link then returns a one-time-use credential
(a virtual card number, an SPT, or a Link Pay Token). Approval is requested by default; unused requests
can be cancelled. Available to US and Canadian consumers [S48][S49]. Against the dimensions: D1 and D3 N
(amount per request), D4 N (merchant per request for card credentials; Link resolves the seller for SPT
and Pay Token), D7 N, D8 N (one credential per request), D10 N (customer approval per request), D9 cancel
of an unused request, third party ND. Quote: "Your agent creates a spend request, the customer approves
it, and Link returns a one-time-use payment credential for that purchase." [S49]
- [S48] https://docs.stripe.com/agentic-commerce/agents/link-agent-wallet.md, 2026-10-08, raw/docs.stripe.com/link-agent-wallet.md
- [S49] https://docs.stripe.com/agentic-commerce/agents/link-agent-wallet/use-link-wallet-pay-online.md, 2026-10-08, raw/docs.stripe.com/link-agent-wallet-pay-online.md (approval default :90, 10-minute window :170, cancel :407)

---

## Blocked or unverifiable sources

- Nothing was blocked by a bot check. docs.ramp.com renders as a JavaScript shell; I used Ramp's public
  plain-text copies (llms-guides/*.txt, openapi/developer-api.json) instead.
- Text addressed to AI agents, treated as data and not followed as instructions: docs.ramp.com/llms.txt
  opens with "Usage Instructions" and "Automation Recommendations" for agents [S38]; Ramp and Stripe
  skill files (S29, S35) are written as instructions to agents by design.
- Ramp Agent Card credential lifetime: a search-engine summary claimed the credential expires after the
  first authorization or 12 hours. The page it named (agents.ramp.com/docs/agent-cards/overview) now
  serves the Payments guide and contains no such text (raw/agents.ramp.com/agent-cards-overview.md).
  Unverified; not used.
- Ramp's `ramp_get_agent_card_creds` contract is known only from the skill file; the live MCP tool list
  is generated at runtime (agents.ramp.com "Agent Tools" page renders a component) and was not readable.
- Stripe Issuing merchant ID controls: field names visible only in preview SDK hint lists, with no
  definitions or docs page (a guessed docs URL returned 404). Semantics unverified.
- Revocation latency is undocumented for every product in this group.

## Most surprising gaps

1. **Revocation nobody else can check.** Every card product here revokes in one API call, but none lets
   the payee or an auditor verify it. Only Stripe SPT tells the payee (signed webhook plus a
   `deactivated_reason` on the granted token), and only inside Stripe.
2. **No GA merchant allowlist by identifier at Stripe Issuing.** The "Issuing for agents" guide's
   answer is a 2-second webhook; merchant ID controls are private preview and their field names show up
   only as hint lists in preview SDK specs. Brex allows by merchant name; Ramp by a "vendor" UUID whose
   identifier space its own docs leave unclear.
3. **The key that mints the per-task card can loosen every card.** Stripe restricted keys are scoped by
   resource type; Ramp `funds:write` and Brex `cards` cover both create and update. Per-task credentials
   exist, but the authority to set their limits is not separable from the authority to mint them.
4. **Limits are softer than they look.** Stripe aggregates spend best-effort with up to 30 s lag and
   lets late tips and fees exceed limits; Ramp has overage percentages and temporary increases; Brex has
   `SOFT` limits and a percentage buffer.
5. **ACP's allowance is set by the agent platform, is one-time only, and has no revocation.** The buyer
   has no field in the protocol; the PSP enforces whatever the platform sent.
6. **Ramp's default agent is the user.** Under the "available today" model an agent can draw on every
   fund the user can; per-agent identities are early access. Ramp's x402 wallet sits outside fund
   controls, by its own docs.
7. **Recurring SPT limits exist only in the private-preview spec**, and SPTs as a whole are not in
   Stripe's GA spec.

## Widely used products this teardown may be missing

- Mercury Agent Cards (virtual cards that agents fetch by API or CLI; humans set daily, weekly or monthly
  limits that the agent cannot change, according to a search summary of Mercury's support article; the
  article returned HTTP 403 to a plain fetch, so not read or verified here):
  https://support.mercury.com/hc/en-us/articles/51299754284948/
- Lithic (card issuing with programmable authorization rules, a common base for agent card startups;
  page exists, contents not reviewed): https://docs.lithic.com/docs/auth-rules
- Privacy.com virtual cards (merchant-locked and single-use cards, marketed for agents):
  https://www.privacy.com/blog/payment-solutions-ai-agents-2026-compared
- AWS AgentCore Payments (payment sessions with an optional spending limit; a third-party analysis says
  the service does not validate the recipient): https://hidekazu-konishi.com/entry/agentic_payments_on_aws.html
