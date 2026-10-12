# Group notes: startups-mandates (read 8 October 2026)

Items: (1) Skyfire and KYAPay, (2) Payman, (3) Nekuda, (4) AP2, plus two extra blocks picked by usage:
(5) the x402 protocol and its reference client's spend controls, (6) Nevermined delegations.

How to read this file
- All fetches ran on 8 October 2026 between 22:00 and 22:31 UTC; each file is listed with its sha256 in
  [SOURCES.md](../SOURCES.md). Clones carry `git-commit:<hash>` in the sha column.
- Paths below are saved-copy paths (`raw/...`). For saved HTML pages, a plain-text copy (`.txt` beside the
  `.html`) was made only to grep quotes; line numbers cited for those pages
  refer to the `.txt` copy.
- Every quote below was confirmed by grep against the saved raw copy. Markdown emphasis markers were removed
  from quotes and nothing else was changed. No source is quoted for more than two sentences in total.
- Escrow, evaluators and work verification are out of scope. Where a product has them, that is noted once.
- No page contained text addressed to the reader as an agent, apart from routine documentation-index
  headers ("Fetch the complete documentation index at ...") on the Nevermined pages, which were ignored.

---

## 1. Skyfire (product) with KYAPay tokens (spec)

**Vendor:** Skyfire Systems Inc. **Status:** Skyfire API in production with a sandbox (docs, API base
`https://api.skyfire.xyz`); organization features need a signed agreement [SK17]. KYAPay token format is an
individual Internet-Draft, `draft-skyfire-oauth-kyapay-token-02`, posted 2 October 2026, group "none",
not adopted [SK15]; the companion `draft-skyfire-oauth-using-kyapay-tokens-01` is posted the same day
[SK15]. The GitHub working copy is already at -03 (unposted) [SK16]. **Docs version:** pages carry
`updatedAt` from 10 July to 8 October 2026. **Read:** 8 October 2026.

**Control model.** A user (person or organization member) owns one buyer agent account; the agent has a
Skyfire-managed wallet and one or more API keys [SK8]. Whoever holds the API key mints tokens through
`POST /api/v1/tokens`: `kya` (identity only), `pay` (payment) or `kya-pay` (both) [SK2]. A `pay` token is a
signed JWT bound to one seller agent account (`aud`) and one seller service (`ssi`), with a `tokenAmount`
that caps the total a seller may charge on it, and an expiry of 10 seconds to 24 hours [SK1][SK2]. Skyfire's
server places a hold on the wallet at mint time, enforces the cap on each charge, and settles from the
buyer's wallet to the seller's [SK1][SK9]. Card-funded tokens carry a single-transaction network agentic
credential and need the cardholder's passkey approval of the exact amount [SK6][SK13]. The seller verifies
the JWT locally against Skyfire's JWKS [SK8]. There is no principal-side policy object: no setting caps what
an API key may mint, other than the wallet balance [SK2][SK18]. Skyfire's own MCP server exposes a
`create-pay-token` tool whose `amount` the calling agent chooses, authenticated with the buyer agent API key
[SK10].

| Dim | Verdict | What exactly is supported | Sources | Quote (confirmed unless marked) |
|---|---|---|---|---|
| D1 per-transaction cap | C | A charge can never exceed the token's remaining amount, so a per-purchase cap means minting one token per purchase. No per-charge cap on the key or wallet. | SK1, SK2 | "The token amount is the maximum a seller can charge." [SK1] |
| D2 per-period cap | ND | No daily, weekly or monthly limit documented for a wallet, agent or API key. | SK8, SK18 | none |
| D3 total budget | N | `tokenAmount` is a lifetime cap on the token, held against the wallet at mint. The wallet balance is the only cap across tokens. | SK2, SK1, SK9 | "Determines the maximum amount the seller can charge." [SK2] |
| D4 counterparty allowlist | N (per token) | A pay token names exactly one seller agent (`aud`) and service (`ssi`). No allowlist can be set on the API key; it can mint for any onboarded seller service. | SK2, SK7, SK13 | none |
| D5 per-counterparty cap | C | One token per seller, each with its own amount. | SK2 | none |
| D6 asset/network/MCC | ND | Token records settlement type (`coin` is USDC in a Skyfire-custodied wallet; `card` is a Visa or Mastercard agentic credential); no principal setting restricts assets, chains or merchant categories. | SK13, SK19, SK6 | none |
| D7 expiry | N | `expiresAt` 10 s to 24 h (default 24 h for onboarded sellers). A token validated before expiry stays chargeable for 24 h after it. | SK1, SK2 | none |
| D8 per-task credential | N | The pay token is a per-task, single-seller, amount- and time-limited credential, separate from the API key. Works only if the principal mints it and keeps the API key from the agent. The draft allows an optional `cnf` key binding; the Skyfire claim list does not show `cnf`. | SK2, SK7, SK16 | none |
| D9 revocation | X (issued tokens) | WHO: an organization admin can deactivate an agent API key; a cardholder can lock or remove a card. HOW: API or dashboard. HOW FAST: key deactivation "typically immediate" with a cache window; already-issued pay tokens are not voided and stay chargeable until expiry plus 24 h. THIRD PARTY: introspection only answers a caller that is a party to the token; neither KYAPay draft defines revocation. No revoke-token endpoint is listed in the API index. | SK1, SK3, SK4, SK6, SK14, SK18 | "Deactivating an account does not void tokens that were already issued." [SK1] "This specification does not define a revocation mechanism." [SK14] |
| D10 human approval | C | Only by using card-funded tokens: the cardholder authorizes the exact amount of each purchase with a passkey. No threshold rule; coin-funded tokens have no approval step. | SK6, SK12 | "They authorize the exact amount shown, using their passkey." [SK6] |
| D11 task binding | N | `buyerTag` is carried to the seller as the `btg` claim (the draft calls it `itg`), with `jti` and `ssi`; confirmed by decoding the example token in SK2. | SK2, SK7, SK13 | none |
| D12 audit export | N (transactions) | Dashboard Tokens and Charges tabs; `GET /api/v1/tokens/{tokenId}/charges`; list tokens per agent. No record of refused mints or policy decisions. | SK5, SK9, SK11 | none |
| D13 multi-rail policy | ND | The same token format carries `coin` or `card` settlement, but there is no policy object, so nothing spans rails. | SK13 | none |

**Test case.** (a) Named counterparties only: per token yes (one seller each), but nothing stops a holder
of the API key from minting tokens for other sellers. (b) Per-task budget: yes for a single seller
(`tokenAmount`); a multi-seller task needs several tokens and the sum is not capped except by wallet
balance. (c) Ends when the task ends: partly; maximum 24 h, plus a 24 h charge window after expiry, and no
early termination. (d) One-step revocation a third party can verify: no. (e) Credential per task: yes, the
pay token. **Full test case: no.** Missing: revoking an issued token, a multi-payee budget, any limit on
the API key, and third-party revocation status.

Notes
- Claim names differ between the product and the draft: Skyfire documents `btg`, `ssi`, `sdm` [SK7]; the
  posted -02 uses `itg`, `tsi`, `tdm` [SK13]. The example response token in [SK2], decoded locally, carries
  `btg` equal to the example request's `buyerTag`, and `amount` and `value` where the draft has `amt` and
  `val` (the example dates from July 2025, so it may predate the draft names).
- The buyer guide says the key holder can "create and authorize payments", so the key, not the token, is
  the real authority [SK5].

Sources
- [SK1] https://docs.skyfire.xyz/docs/payments-settlement.md, 2026-10-08, raw/docs.skyfire.xyz/docs-payments-settlement.md (lines 13, 17, 29, 40, 42)
- [SK2] https://docs.skyfire.xyz/reference/create-token.md, 2026-10-08, raw/docs.skyfire.xyz/reference-create-token.md (lines 18 to 31, `tokenAmount`, `expiresAt`, `buyerTag`)
- [SK3] https://docs.skyfire.xyz/reference/deactivate-agent-api-key.md, 2026-10-08, raw/docs.skyfire.xyz/reference-deactivate-agent-api-key.md (line 21)
- [SK4] https://docs.skyfire.xyz/reference/introspect-token.md, 2026-10-08, raw/docs.skyfire.xyz/reference-introspect-token.md (lines 111, 141: "caller not a party to the token")
- [SK5] https://docs.skyfire.xyz/docs/buyer-guide.md, 2026-10-08, raw/docs.skyfire.xyz/docs-buyer-guide.md (lines 48, 59, 107)
- [SK6] https://docs.skyfire.xyz/docs/building-an-agentic-checkout.md, 2026-10-08, raw/docs.skyfire.xyz/docs-building-an-agentic-checkout.md (lines 33, 39, 52)
- [SK7] https://docs.skyfire.xyz/docs/common-token-claims.md, 2026-10-08, raw/docs.skyfire.xyz/docs-common-token-claims.md (lines 26 to 35)
- [SK8] https://docs.skyfire.xyz/docs/platform-structure.md, 2026-10-08, raw/docs.skyfire.xyz/docs-platform-structure.md
- [SK9] https://docs.skyfire.xyz/docs/agent-provider.md, 2026-10-08, raw/docs.skyfire.xyz/docs-agent-provider.md (lines 196 to 223, hold, charge, release; list tokens)
- [SK10] https://docs.skyfire.xyz/docs/using-the-skyfire-mcp-server.md, 2026-10-08, raw/docs.skyfire.xyz/docs-using-the-skyfire-mcp-server.md (lines 252 to 267)
- [SK11] https://docs.skyfire.xyz/reference/get-token-charges.md, 2026-10-08, raw/docs.skyfire.xyz/reference-get-token-charges.md (line 40)
- [SK12] https://docs.skyfire.xyz/docs/payment-cards.md, 2026-10-08, raw/docs.skyfire.xyz/docs-payment-cards.md (line 42)
- [SK13] https://www.ietf.org/archive/id/draft-skyfire-oauth-kyapay-token-02.txt, 2026-10-08, raw/www.ietf.org/draft-skyfire-oauth-kyapay-token-02.txt (lines 454, 484, 487, 761 to 812). Quote used: "Such a credential is provisioned for a single transaction and is scoped to one initiator, one target, and one amount." (lines 804 to 806)
- [SK14] https://www.ietf.org/archive/id/draft-skyfire-oauth-using-kyapay-tokens-01.txt, 2026-10-08, raw/www.ietf.org/draft-skyfire-oauth-using-kyapay-tokens-01.txt (Section 8.7, lines 1441 to 1447)
- [SK15] https://datatracker.ietf.org/doc/draft-skyfire-oauth-kyapay-token/doc.json and .../draft-skyfire-oauth-using-kyapay-tokens/doc.json and .../draft-skyfire-kyapayprofile/doc.json (the profile draft is "Replaced"), 2026-10-08, raw/datatracker.ietf.org/
- [SK16] skyfire-xyz/draft-skyfire-oauth-kyapay-token@7cecb10 draft-skyfire-oauth-kyapay-token.md (cnf at the common-claims section; Document History -03); also skyfire-xyz/kyapay@35da6da README.md (v1.0 "aimed to be released soon"), skyfire-xyz/draft-skyfire-oauth-using-kyapay-tokens@d82c2f0
- [SK17] https://docs.skyfire.xyz/docs/organization-guide.md, 2026-10-08, raw/docs.skyfire.xyz/docs-organization-guide.md (line 13). Quote: "Onboarding as an organization requires an agreement."
- [SK18] https://docs.skyfire.xyz/llms.txt, 2026-10-08, raw/docs.skyfire.xyz/llms.txt (full API index; no revoke or cancel token endpoint, no limit settings)
- [SK19] https://docs.skyfire.xyz/docs/wallet-funding.md, 2026-10-08, raw/docs.skyfire.xyz/docs-wallet-funding.md (USDC on Base funding; note this July page also says card details are not delivered to merchants, while the September and October card pages describe card-funded tokens)

Blocked or unverifiable: none blocked. The API index lists no token revocation endpoint; absence was checked
only against `llms.txt` and the pages listed above.

---

## 2. Payman (Payman AI, Inc.)

**Status: developer platform no longer documented online.** `docs.paymanai.com` returns HTTP 526 (an origin
TLS error page) on 8 October 2026 [PM11]; the homepage now markets "agentic banking" for banks and credit
unions [PM12]. The developer docs were read from Internet Archive snapshots dated 12 October 2025 to 12
January 2026 [PM1 to PM10]; those docs say the platform was invite-only [PM4]. The public SDK on npm,
`@paymanai/payman-ts` 1.0.16 (18 September 2025), exposes only natural-language `ask()` calls and no policy
types [PM13]. Treat this block as the last documented state, not a current product. **Read:** 8 October 2026.

**Control model.** A Policy is assigned to an app, agent or wallet and holds four spend controls: an
approval threshold, a per-transaction maximum, a daily limit and a monthly limit [PM1]. A payment above the
threshold becomes a Request that the user approves or denies in the dashboard [PM2]. Money leaves only
toward a registered Payee (US bank account over ACH, a USDC address, or a test account) [PM3][PM6]. Apps
connected by OAuth get scopes, including separate `write_create_payee` and `write_send_payment`, and a
per-transaction limit [PM5]. All documented enforcement is in Payman's service; the docs do not say what the
bank, ACH or the chain enforce, and do not name a custodian.

| Dim | Verdict | What exactly is supported | Sources | Quote |
|---|---|---|---|---|
| D1 per-transaction cap | N | Policy "Per Transaction" maximum; OAuth app "Transaction Limits". | PM1, PM5 | none |
| D2 per-period cap | N | Policy "Daily Limit" and "Monthly Limit". | PM1 | none |
| D3 total budget | C | No lifetime cap field; only by funding a dedicated wallet and assigning it to the agent. | PM1, PM4 | none |
| D4 counterparty allowlist | C | Payments go only to existing payees; an app granted `write_send_payment` without `write_create_payee` cannot add payees. The payee list is account-wide and shared across wallets and agents, and `ask()` creates payees when allowed. | PM3, PM5, PM6, PM7 | "Payees must be added before any payment can be made using the SDK or dashboard." [PM3] |
| D5 per-counterparty cap | ND | Not documented. | PM1 | none |
| D6 asset/network/MCC | C | By choosing the wallet (USD over ACH, USDC, or test TSD) assigned to the agent; no chain or category rule. | PM4, PM3 | none |
| D7 expiry | ND | No validity window on policies, OAuth grants or credentials documented. | PM1, PM5 | none |
| D8 per-task credential | C | Separate app credentials and OAuth grants with scopes and a per-transaction limit; nothing per task. | PM5, PM8 | none |
| D9 revocation | ND | WHO: account owner. HOW: client secrets can be revoked and regenerated in the dashboard; OAuth access is described as revocable without a documented mechanism. HOW FAST: not documented. THIRD PARTY: not documented. | PM5, PM8 | "Lost your secret? Revoke and re-generate from the dashboard." [PM8] |
| D10 human approval | N | Threshold triggers a Request; the transaction pauses until approve or deny. Send-payment status includes `AWAITING_APPROVAL`. | PM1, PM2, PM6 | "Payman pauses the transaction until you approve or deny." [PM2] |
| D11 task binding | N (Payman-side) | `memo` and `metadata` on send-payment. Whether they reach the payee over ACH or on chain is not documented. | PM6 | "A note or memo to associate with this payment." [PM6] |
| D12 audit export | N (transactions) | Wallet transaction history with filter, sort and export; webhooks for payment events. Export of approve or deny decisions not documented. | PM4, PM10 | none |
| D13 multi-rail policy | ND | One policy can be applied to several wallets (USD and USDC), but whether limits aggregate across them is not documented. | PM1, PM4 | none |

**Test case.** (a) Named counterparties only: partly, through the payee registry plus withholding the
create-payee scope, not per task. (b) Per-task budget: no, only per-transaction and per-period limits.
(c) Ends when the task ends: no expiry. (d) Verifiable one-step revocation: no. (e) Credential per task: no.
**Full test case: no.** Missing: expiry, task budget, per-task payee scope, revocation semantics; and the
product's developer platform itself is no longer documented.

Sources
- [PM1] https://web.archive.org/web/20251118161108id_/https://docs.paymanai.com/dashboard-guide/policies, fetched 2026-10-08, raw/web.archive.org/paymanai-dashboard-guide-policies-20251118.html (.txt lines 78 to 81, 92, 98). Quote: "No policy = no access." (line 92)
- [PM2] https://web.archive.org/web/20251118161554id_/https://docs.paymanai.com/dashboard-guide/requests, raw/web.archive.org/paymanai-dashboard-guide-requests.html (.txt line 54)
- [PM3] https://web.archive.org/web/20260112170117id_/https://docs.paymanai.com/dashboard-guide/payees, raw/web.archive.org/paymanai-dashboard-guide-payees.html (.txt lines 53, 67)
- [PM4] https://web.archive.org/web/20251118170839id_/https://docs.paymanai.com/dashboard-guide/wallet, raw/web.archive.org/paymanai-dashboard-guide-wallet.html (.txt lines 59, 85). Quote: "(Payman is invite-only to ensure secure onboarding.)" (line 59)
- [PM5] https://web.archive.org/web/20251012054312id_/https://docs.paymanai.com/developer-guide/oauth-setup, raw/web.archive.org/paymanai-developer-guide-oauth-setup.html (.txt lines 52, 112, 121, 122)
- [PM6] https://web.archive.org/web/20251205181701id_/https://docs.paymanai.com/api-reference/endpoint/send-payment, raw/web.archive.org/paymanai-api-reference-endpoint-send-payment.html (.txt lines 97, 105, 124)
- [PM7] https://web.archive.org/web/20260112183536id_/https://docs.paymanai.com/getting-started/what-is-payman, raw/web.archive.org/paymanai-what-is-payman-20260112.html (.txt lines 68, 70: `ask()` creates a payee, then applies policies)
- [PM8] https://web.archive.org/web/20251205173924id_/https://docs.paymanai.com/developer-guide/generate-credentials, raw/web.archive.org/paymanai-developer-guide-generate-credentials.html (.txt line 60)
- [PM9] https://web.archive.org/web/20251118164730id_/https://docs.paymanai.com/resources/glossary, raw/web.archive.org/paymanai-resources-glossary.html
- [PM10] https://web.archive.org/web/20251012040433id_/https://docs.paymanai.com/developer-guide/webhooks, raw/web.archive.org/paymanai-developer-guide-webhooks.html
- [PM11] https://docs.paymanai.com/llms.txt, 2026-10-08, raw/docs.paymanai.com/llms.txt (body "error code: 526")
- [PM12] https://paymanai.com/ and https://paymanai.com/agentic-banking, 2026-10-08, raw/paymanai.com/
- [PM13] npm @paymanai/payman-ts 1.0.16 tarball, raw/npm/payman-ts-1.0.16/package/README.md

Blocked or unverifiable: docs.paymanai.com (HTTP 526, not a bot check). The live developer API and any
policy behavior after January 2026 could not be verified. Third-party review sites name a custodian bank
and a processor; not used, since no primary source confirms them.

---

## 3. Nekuda

**Status: payment product no longer documented.** `docs.nekuda.ai` now documents only the WebMCP Kit
[NK7] and the homepage lists only WebMCP products [NK8]. The payment SDKs are still published: PyPI
`nekuda` 0.2.10 (3 March 2026) [NK9], npm `@nekuda/nekuda-js` 0.2.14 and `@nekuda/wallet` 0.2.4
(9 December 2025) [NK4][NK5]. An archived January 2026 docs page labels the Payment Executor a "Developer
Preview" with a GA target of Q3 2025 [NK6]. The docs' "Policy Engine & Safety" page appears in that
archived navigation but no snapshot exists. Evidence below is SDK code and types only. **Read:** 8 October 2026.

**Control model.** The agent developer's backend, holding Nekuda's secret API key, creates a "mandate"
for a user id that describes one purchase: product, description, price, currency, merchant, merchant link,
conversation context, the human's messages, a confidence score and an optional payment method id [NK1]. It
then requests a short-lived reveal token for that mandate and exchanges it for card details: full card
number, expiry, cardholder name, CVV and billing details, or Visa credentials for Visa-tokenized cards
[NK2][NK3][NK4]. Nekuda's server decides whether to issue a reveal token; the SDK shows no step in which the
user approves the mandate, and no field that the card network or merchant receives. For stored cards
(`pm_type` "vgs"), whatever the mandate said, the revealed card can be charged by whoever holds it.

| Dim | Verdict | What exactly is supported | Sources | Quote |
|---|---|---|---|---|
| D1 per-transaction cap | ND | Mandate carries `price`; no documented check of the actual charge against it. | NK1, NK2 | none |
| D2 per-period cap | ND | Not in SDK types. | NK1, NK4 | none |
| D3 total budget | ND | Not in SDK types. | NK1, NK4 | none |
| D4 counterparty allowlist | ND | `merchant` and `merchant_link` are descriptive strings; enforcement not documented. | NK1 | none |
| D5 per-counterparty cap | ND | Not in SDK types. | NK1 | none |
| D6 asset/network/MCC | ND | Card only (stored card via a vault, or Visa token); no category rule. | NK3, NK4 | none |
| D7 expiry | ND | The reveal token has `expires_at`; the mandate has no expiry field and the revealed card is not time-bound by Nekuda. | NK1, NK3 | none |
| D8 per-task credential | ND | A per-mandate reveal token exists, but for stored cards what it yields is the full card number and CVV, which carry the card's whole authority. Scope of the Visa credentials is not documented. | NK2, NK3, NK4 | none |
| D9 revocation | ND | WHO, HOW, HOW FAST, THIRD PARTY: none documented in the SDKs. | NK2, NK4 | none |
| D10 human approval | ND | No approval call or status in the SDKs; `human_messages` only records conversation text. | NK1, NK2 | none |
| D11 task binding | ND | `mandate_id` and `request_id` stay on Nekuda's side; the archived executor page says reveals are tied to prior user intent, with no mechanism shown. | NK1, NK6 | "Mandate-bound Access : All reveals are tied to prior user intent" [NK6] |
| D12 audit export | ND | An archived navigation link names a card analytics endpoint; not read. | NK6 | none |
| D13 multi-rail policy | ND | Cards only. | NK3 | none |

**Test case.** None of (a) to (e) is verifiable from public sources. **Full test case: no.** What the
public SDK does show is the opposite of a scoped credential for stored cards: a reveal returns the PAN and
CVV to the agent's backend.

Sources
- [NK1] PyPI nekuda 0.2.10 wheel, raw/pypi.org/nekuda-0.2.10/nekuda/models.py lines 22 to 57 (`MandateData`)
- [NK2] same wheel, nekuda/client.py lines 223 to 332 (`request_card_reveal_token`, `reveal_card_details`, `create_mandate`; endpoints `/api/v2/wallet/request_card_reveal_token`, `/api/v2/wallet/reveal_card_details`, `/api/v2/mandate/create`)
- [NK3] same wheel, nekuda/response_models.py lines 17 to 47, 77 to 91 (`pm_type` "vgs or visa"), 152 to 178 (`RawCardDetailsResponse` with card number and CVV)
- [NK4] npm @nekuda/nekuda-js 0.2.14, raw/npm/nekuda-nekuda-js-0.2.14/package/dist/index.d.ts lines 1 to 110 (`VisaCredentials`, `CardDetailsResponse`)
- [NK5] npm @nekuda/wallet 0.2.4, raw/npm/nekuda-wallet-0.2.4/package/README.md (Settings tab is contact and shipping only)
- [NK6] https://web.archive.org/web/20260112033431id_/https://docs.nekuda.ai/payment-executor, raw/web.archive.org/nekuda-payment-executor-20260112.html (.txt lines 55, 56, 76, 103)
- [NK7] https://docs.nekuda.ai/llms.txt, 2026-10-08, raw/docs.nekuda.ai/llms.txt
- [NK8] https://nekuda.ai/, 2026-10-08, raw/nekuda.ai/home.html
- [NK9] https://pypi.org/pypi/nekuda/json, 2026-10-08, raw/pypi.org/nekuda.json

Blocked or unverifiable: the former payment docs (policy engine, payment flow, system overview) were not
archived (Wayback returned 404 for each). The live API was not exercised.

---

## 4. AP2, the Agent Payments Protocol

**Vendor / owner:** created by Google; core specification donated to the FIDO Alliance on 28 April 2026
[AP11][AP12]. **Status:** draft, version 0.2 [AP1]. Repo tag `v0.2.0` = b4587ac (release 28 April 2026);
`main` = e1ea56d (29 April 2026) differs from the tag only in CHANGELOG, CONTRIBUTING, README and a lock
file, so spec and schemas are identical [AP15]. The repo now takes contributions to samples and SDK only
[AP10]. FIDO's specifications pages list no AP2 document on 8 October 2026 [AP14]. **Read:** 8 October 2026.

**Current names (verified).** v0.2 defines two mandate types, each open or closed: Checkout Mandate
(`vct` `mandate.checkout.1`, open `mandate.checkout.open.1`) and Payment Mandate (`mandate.payment.1`, open
`mandate.payment.open.1`), plus a merchant-signed Checkout Receipt and a Payment Receipt [AP1][AP2][AP17].
The v0.1 vocabulary (Cart Mandate in section 4.1.1, Intent Mandate in 4.1.2) is gone [AP13]. v0.1's Intent
Mandate could state refundability [AP13]; v0.2 has no refund constraint (zero matches for "refund" in docs
and schemas).

**Credential format (verified).** Mandates are SD-JWTs (RFC 9901) chained per an individual draft,
"Delegate SD-JWT", with key-binding JWTs for closed mandates and the `cnf` claim (RFC 7800) for the agent
key [AP4]. In the User Credential model, delegation uses OpenID4VP `transaction_data` of type `delegate`
with `dc+sd-jwt` credentials, optionally over the Digital Credentials API; ISO mdoc is named as a possible
alternative [AP4]. There is no W3C Verifiable Credentials data model and no DID anywhere in docs or SDK
(zero matches for `did:` and for the VC context URLs) [AP1][AP4].

**Control model.** The shopping agent drafts mandate content; a Trusted Surface (which must be
non-agentic) shows it to the user and signs it, either as the holder of a user credential or with an agent
provider's key [AP1][AP4]. In human-not-present mode the user signs open mandates that carry constraints and
the agent's public key; the agent then signs closed mandates for a specific checkout [AP1]. The merchant
verifies the checkout mandate chain and its constraints; the credential provider and, if present, the
network verify the payment mandate chain and its constraints; the merchant payment processor must verify
that the payment credential is scoped to the checkout, for example by finding the closed payment mandate
inside it [AP1]. All enforcement is deterministic code at those verifiers. Stateful constraints (budget,
recurrence) need a spend ledger the spec does not assign to any role [AP2].

| Dim | Verdict | What exactly is supported | Sources | Quote |
|---|---|---|---|---|
| D1 per-transaction cap | N | `payment.amount_range` `max` (and optional `min`) with currency. Schema says integer minor units; the doc example uses `100.50`. | AP2, AP3 | "Maximum allowed amount in minor (cents) unit of currency." [AP3] |
| D2 per-period cap | C | `payment.agent_recurrence` (frequency ON_DEMAND to ANNUALLY, `max_occurrences`) combined with `amount_range` bounds count per period times a per-payment cap; no per-period amount field. The SDK evaluator at e1ea56d checks only `max_occurrences`, not frequency. | AP2, AP7 | none |
| D3 total budget | N | `payment.budget` `max` and currency, "to be used with" recurrence. Stateful: the verifier must track spend. Schema types `max` as a number with no unit; the SDK multiplies it by 100. The reference credential provider sample verifies without any usage context, and the sample's spend tracker is a local file written by the shopping agent. | AP2, AP3, AP7, AP8, AP9 | "Evaluating the budget requires tracking the total amount spent using this Payment Mandate." [AP2] |
| D4 counterparty allowlist | N | `payment.allowed_payees` and `checkout.allowed_merchants`, lists of merchant objects (`id`, `name`, `website`), selectively disclosable. SDK matches by `id`, else name plus website. | AP2, AP17, AP7 | "The `payee` property of the Payment Mandate MUST be present in the `allowed` array." [AP2] |
| D5 per-counterparty cap | C | Only by issuing one open mandate per payee, each with its own amount range or budget. | AP2 | none |
| D6 asset/network/MCC | N (instrument, currency) | `payment.allowed_payment_instruments` (instrument ids, free-form `type`), `payment.allowed_pisps`, ISO 4217 currency. No merchant-category, chain or token field. SKU limits via `checkout.line_items`. | AP2, AP17, AP18 | none |
| D7 expiry | N | `exp` on open mandates (optional in schema, RECOMMENDED as short as the task); `payment.execution_date` `not_before` / `not_after`. No hours-of-day rule. | AP1, AP2, AP3 | "It is RECOMMENDED to set the `exp` claim for these Mandates to the smallest value that will allow the Shopping Agent to complete the assigned task." [AP1] |
| D8 per-task credential | N | Each open mandate binds one agent key via `cnf` and its own constraints and expiry; closed mandates are signed per checkout with that key. | AP1, AP4 | none |
| D9 revocation | X | WHO: no role is given a revoke operation. HOW: none; management of delegated mandates at external Trusted Surfaces is declared out of scope; verifiers MAY reject overlapping mandates or invalidate payment tokens they issued. HOW FAST: a mandate lives until `exp` (or until single use is consumed). THIRD PARTY: no status claim or status list is defined (zero matches for revocation terms in docs). | AP5, AP6, AP1 | "In the case of external Trusted Surfaces it could make sense to allow for management of delegated Mandates but that is outside the scope of this specification." [AP5] |
| D10 human approval | C | Human-present mode has the user sign each closed mandate. A threshold is only by composition: cap the open mandate's `amount_range` and fall back to a human-present mandate when a verifier returns `unresolved_constraint`. | AP1, AP4 | none |
| D11 task binding | N | Closed Payment Mandate `transaction_id` is the hash of the merchant-signed checkout JWT; `payment.reference` ties the open payment mandate to the open checkout mandate; receipts reference the mandate hash. Seen by merchant (checkout) and by credential provider, network and processor (payment). No defined free-text task or purpose field, though extra claims are allowed. | AP1, AP2, AP4 | none |
| D12 audit export | N (receipts) | Every verifier must return a signed receipt on acceptance or rejection, with result, reference hash and error code; the four objects form dispute evidence. Retention and retrieval are out of scope. | AP4, AP1 | "Upon acceptance or rejection of the Mandate, the Verifier MUST return a signed Mandate Receipt." [AP4] |
| D13 multi-rail policy | N | One `allowed_payment_instruments` constraint can list instruments of different types (spec example: card and UPI). x402 appears only in samples. Amounts must be in an ISO 4217 currency, so a stablecoin payment is capped in fiat terms (the x402 sample converts USD cents to USDC units). | AP2, AP18, AP19 | none |

**The specific questions.** Constraints a human-not-present mandate can carry: amount range, budget,
recurrence, allowed payees or merchants, allowed instruments, allowed PISPs, execution window, line items
(SKUs and quantities), checkout reference, and `exp`; no refundability [AP2][AP17]. Verifiable by the
merchant: yes, for the checkout mandate. By the payment processor: the processor must verify the credential
is scoped to the checkout, and carrying the closed payment mandate inside the credential is given as one way,
not a requirement [AP1]. Credential format: SD-JWT with OpenID4VP, not W3C VCs. Revocation: none. One mandate
across card and crypto: the instrument list allows it, but no x402 instrument type is defined in the spec.

**Test case.** (a) Named counterparties only: yes (`allowed_payees`, `allowed_merchants`). (b) Per-task
budget: yes on paper (`budget` plus recurrence, or a single-use mandate with `amount_range`), but which
verifier keeps the running total is unassigned. (c) Ends when the task ends: yes by `exp` and
`execution_date`, not by an explicit end. (d) One-step revocation a third party can verify: no. (e)
Credential per task: yes, an open mandate bound to the agent key. **Full test case: no.** Missing:
revocation, and an owner for budget state.

Sources
- [AP1] google-agentic-commerce/AP2@e1ea56d docs/ap2/specification.md lines 1, 106 to 107, 138 to 143, 147 to 152, 170 to 190, 221 to 243, 319 to 342, 396 to 401
- [AP2] AP2@e1ea56d docs/ap2/payment_mandate.md lines 14 to 15, 33 to 45, 47 to 71, 85 to 87, 166 to 190, 192 to 217, 219 to 242, 244 to 266
- [AP3] AP2@e1ea56d code/sdk/schemas/ap2/open_payment_mandate.json lines 7 to 11, 50 to 52, 116 to 144, 245 to 269
- [AP4] AP2@e1ea56d docs/ap2/agent_authorization.md lines 94 to 121, 386 to 447, 496 to 535, 539 to 544
- [AP5] AP2@e1ea56d docs/ap2/implementation_considerations.md lines 129 to 139
- [AP6] AP2@e1ea56d docs/ap2/security_and_privacy_considerations.md lines 100 to 114. Quote: "Credential Provider, Networks or MPPs MAY reject multiple overlapping Mandates, or invalidate previously issued payment tokens." (lines 113 to 114)
- [AP7] AP2@e1ea56d code/sdk/python/ap2/sdk/constraints.py lines 37 to 42 (`MandateContext`), 45 (`merchant_matches`), 172 (`calculate_period_start`, defined and not called outside tests), 197 to 231 (recurrence checks `max_occurrences` only), 278 to 313 (budget, line 307 `int(self.constraint.max * 100)`), 489 to 541
- [AP8] AP2@e1ea56d code/samples/python/src/roles/credentials_provider_mcp/server.py lines 189 to 200 (`chain.verify` with no `mandate_context`)
- [AP9] AP2@e1ea56d code/samples/python/src/roles/shopping_agent_v2/shopping_agent/mandate_tools.py lines 565 to 580, 850 to 873 (usage file kept by the shopping agent)
- [AP10] AP2@e1ea56d CONTRIBUTING.md lines 3 to 7. Quote: "Contributions to this repo going forward are to the samples and sdk only."
- [AP11] https://fidoalliance.org/fido-alliance-to-develop-standards-for-trusted-ai-agent-interactions/, 2026-10-08, raw/fidoalliance.org/standards-trusted-ai-agent-interactions.html (.txt lines 27 to 41). Quote: "These contributions will be reviewed and further developed through the FIDO Alliance’s collaborative standards process within the Payments Technical Working Group." (line 41)
- [AP12] https://blog.google/products-and-platforms/platforms/google-pay/agent-payments-protocol-fido-alliance/, 2026-10-08, raw/blog.google/ap2-fido-alliance.html (datePublished 2026-04-28)
- [AP13] https://raw.githubusercontent.com/google-agentic-commerce/AP2/v0.1.0/docs/specification.md, 2026-10-08, raw/raw.githubusercontent.com/AP2-v0.1.0-specification.md (lines 278 to 335)
- [AP14] https://fidoalliance.org/specifications/ and .../specifications/download/, 2026-10-08, raw/fidoalliance.org/
- [AP15] https://api.github.com/repos/google-agentic-commerce/AP2/releases and .../compare/v0.2.0...main, 2026-10-08, raw/api.github.com/
- [AP17] AP2@e1ea56d docs/ap2/checkout_mandate.md (allowed merchants, line items) and code/sdk/schemas/ap2/open_checkout_mandate.json
- [AP18] AP2@e1ea56d code/sdk/schemas/ap2/types/amount.json and types/payment_instrument.json
- [AP19] AP2@e1ea56d code/samples/python/src/roles/x402_credentials_provider_mcp/server.py lines 130 to 170 (fallback payee address from environment when the mandate has none, line 154; cents to USDC, line 170; EIP-3009 nonce from the mandate hash, line 163)

Blocked or unverifiable: none blocked. No FIDO working draft of AP2 is public, so whether FIDO's version
will change these objects is unknown.

---

## 5. x402 (protocol) and its reference client's spend controls

**Why picked:** by far the most used agent payment protocol among candidates: npm `x402` 1,803,939 and
`@x402/core` 1,289,470 downloads from 8 September to 7 October 2026 [XP7]. **Owner:**
x402-foundation/x402 (6,689 GitHub stars on 8 October 2026, raw/api.github.com/x402-repo.json). **Status:** protocol spec v2 (history entry
v2.0, 2025-12-9) [XP2]; repo at 7f2b2f1 (7 October 2026); `@x402/core` 2.28.0 published 29 September 2026;
client `spendControls` added in 2.23.0 (published 18 August 2026) [XP4]. **Read:** 8 October 2026.

**Control model.** x402 moves one payment per request: the client signs a single authorization (for
`exact` on EVM, a time-bound EIP-3009 transfer; for `upto`, a Permit2 transfer bound to a recipient, a
maximum and a deadline, settled once) [XP1][XP6]. The protocol spec puts client-side budget management out
of scope [XP2]. The reference TypeScript client adds `spendControls`: a per-payment USD cap on recognized
stablecoins (default $1), an asset allowlist with optional per-asset caps, and network scoping through which
schemes are registered; plus `registerPolicy` filters and an `onBeforePaymentCreation` hook that can abort
[XP3]. All of these run in the payer's own process next to the signing key, so whoever controls that process
can turn them off (`spendControls: false`) [XP3]. On chain only the per-authorization amount, recipient and
time window are enforced.

| Dim | Verdict | What exactly is supported | Sources | Quote |
|---|---|---|---|---|
| D1 per-transaction cap | N (client SDK) | `spendControls.maxAmountPerPayment` (default "$1"), per-asset atomic caps. Not enforced by any party other than the client. | XP3, XP4 | none |
| D2 per-period cap | CODE | Only in a policy or before-payment hook. | XP3 | none |
| D3 total budget | CODE | Only in a hook; spec says budget management is implementation-specific. | XP2, XP3 | none |
| D4 counterparty allowlist | CODE | `registerPolicy` can filter requirements by `payTo`. The signed recipient binding protects against a facilitator redirect, not against the agent choosing a payee. | XP3, XP1 | none |
| D5 per-counterparty cap | CODE | Hook. | XP3 | none |
| D6 asset/network/MCC | N (client SDK) | `allowedAssets` entries with network patterns; networks limited to registered schemes. | XP3, XP4 | "Network scoping is scheme registration, not a control here." [XP3] |
| D7 expiry | N (per authorization) | `validBefore` / `deadline` on each authorization, bounded by the server's `maxTimeoutSeconds`. There is no grant object to expire at task level. | XP1, XP2 | none |
| D8 per-task credential | ND | x402 defines none; any session key or delegated key comes from the wallet layer. | XP2 | none |
| D9 revocation | ND | WHO, HOW, HOW FAST, THIRD PARTY: not defined by x402; authorizations are single-use and short-lived. `upto` on EVM depends on a standing ERC-20 approval to Permit2, whose revocation is outside x402. | XP1, XP6 | "Each authorization MUST be settled at most once." [XP1] |
| D10 human approval | CODE | `onBeforePaymentCreation` can abort; the paywall package disables spend controls in favor of UI approval. | XP3, XP4 | none |
| D11 task binding | N | `payment-identifier` extension carries a client id (16 to 128 chars) to the resource server and facilitator; not written on chain. | XP5 | none |
| D12 audit export | CODE | No log of policy decisions; settled transfers are public on chain. | XP3 | none |
| D13 multi-rail policy | N (client SDK) | One client's spend controls apply across every registered network family (EVM, SVM and others). | XP3, XP4 | none |

**Test case.** (a) Named counterparties: code. (b) Per-task budget: code. (c) Ends with the task: no
grant exists. (d) Verifiable revocation: no. (e) Credential per task: not in x402. **Full test case: no.**
x402 is a per-payment rail; every principal-side control lives in the payer's own client.

Sources
- [XP1] x402-foundation/x402@7f2b2f1 specs/schemes/upto/scheme_upto.md lines 25, 30 to 45, 52 to 56, 69 to 72
- [XP2] x402@7f2b2f1 specs/x402-specification-v2.md lines 14 to 20 ("Client-side budget management" listed as out of scope), 662 to 668, 723 to 729
- [XP3] x402@7f2b2f1 typescript/packages/core/src/client/x402Client.ts lines 43 to 45, 146 to 190, 395 to 466
- [XP4] x402@7f2b2f1 typescript/packages/core/CHANGELOG.md, section 2.23.0 (line 34 onward); npm registry times for @x402/core
- [XP5] x402@7f2b2f1 specs/extensions/payment_identifier.md
- [XP6] x402@7f2b2f1 specs/schemes/upto/scheme_upto_evm.md lines 33 to 46, 150 to 153
- [XP7] https://api.npmjs.org/downloads/point/2026-09-08:2026-10-07/x402 and .../@x402/core, 2026-10-08, raw/api.npmjs.org/

Blocked or unverifiable: none. Python and Go clients also ship spend controls (files present), not read in detail.

---

## 6. Nevermined delegations

**Why picked:** second in usage among the remaining candidates (`@nevermined-io/payments` 2,747 npm
downloads from 8 September to 7 October 2026, against 237 for `@agentcommercekit/ack-pay` and 363 for
`gokite-aa-sdk`) [NV9], and its delegation object targets this test case directly. It also runs an x402
facilitator with credit burns; that settlement machinery is out of scope here. **Status:** docs list sandbox
and live environments; the x402 Delegation Extension spec is "Version: 0.1, Status: Draft, Last Updated:
February 2026" [NV2]; Groups and Budgets are paid-tier features [NV3]. **Read:** 8 October 2026.

**Control model.** A user enrolls a card (Stripe, Braintree or a Visa Agentic Token) or uses an ERC-4337
smart account, then creates a delegation: `spendingLimitCents` over its lifetime, `durationSecs`, optional
`maxTransactions`, currency, optional `planId` (the seller's plan) and optional `apiKeyId` [NV1]. The
delegation is a JWT signed by Nevermined's facilitator; Nevermined checks status, usage and expiry on every
verify and settle and resolves the payee from the plan, never from the client [NV1][NV2]. Each card has a
cumulative ceiling across its active delegations (default $10) [NV1]. Visa delegations need a passkey
ceremony bound to the limit, duration and merchant context [NV1]. The Router spends one delegation across
x402 and MPP services [NV7].

| Dim | Verdict | What exactly is supported | Sources | Quote |
|---|---|---|---|---|
| D1 per-transaction cap | C | No per-transaction field; only by `maxTransactions` 1, or the plan's price. | NV1 | "`spendingLimitCents` caps the cumulative amount charged over the delegation's lifetime, not per-transaction." [NV1] |
| D2 per-period cap | C | Group budgets over a period, set by an org admin per group, paid tiers only; not per delegation. | NV3 | "Groups, budgets, and shared payment methods are Premium and Enterprise features." [NV3] |
| D3 total budget | N | `spendingLimitCents`; also a per-card ceiling. | NV1 | none |
| D4 counterparty allowlist | N (one plan) | `planId` binds a delegation to one seller plan (required for Visa, optional otherwise); funds route to the plan owner. No multi-seller list documented. | NV1, NV2 | none |
| D5 per-counterparty cap | C | One delegation per plan. | NV1 | none |
| D6 asset/network/MCC | C | By choice of payment method (card PSP or ERC-4337 account) and currency; no category rule. | NV1, NV2 | none |
| D7 expiry | N | `durationSecs`; status becomes `Expired`. | NV1 | none |
| D8 per-task credential | N | Delegation optionally linked to one API key; callers pass an explicit `delegationId` (recommended "create-first"). | NV1, NV6, NV5 | none |
| D9 revocation | N | WHO: the user with their API credentials; also per agent binding. HOW: `DELETE /api/v1/delegation/{id}`, or revoke a connected-agent binding, which kills every credential minted from it; RFC 7009 token revoke. HOW FAST: immediate for verify; in-flight settlements whose PSP charge is confirmed may complete. THIRD PARTY: a seller learns it through the facilitator's verify result; no public status list. | NV1, NV2, NV4 | "Revocation is immediate: in-flight verify/settle calls against the delegation fail with `DELEGATION_INACTIVE`." [NV1] "One action kills every credential minted from that binding." [NV4] |
| D10 human approval | C | Human approval happens when the delegation is created (passkey for Visa; a hosted approval URL for the catalog MCP flow); no amount-threshold step-up. | NV1, NV8 | none |
| D11 task binding | N | The delegation JWT (`jti` = delegation id, `nvm.planId`) is carried in the x402 payment payload that the seller receives and forwards to the facilitator. | NV2 | none |
| D12 audit export | N | Per-delegation transaction history with status (`succeeded`, `failed`, `refunded`); bindings list keeps revoked entries. | NV1, NV4 | none |
| D13 multi-rail policy | N (Router) | One delegation covers x402 and MPP services through the Router; the same delegation config spans card PSPs and ERC-4337. | NV7, NV2 | "A single Delegation covers x402 and MPP alike." [NV7] |

**Test case.** (a) Named counterparties only: one plan per delegation, yes; several named sellers need
several delegations. (b) Per-task budget: yes (`spendingLimitCents`). (c) Ends when the task ends: yes by
`durationSecs`, or by revoking. (d) One-step revocation a third party can verify: one step yes; third-party
verification only by asking Nevermined's facilitator. (e) Credential per task: yes (delegation linked to an
API key). **Full test case: nearly.** Missing: a multi-payee list inside one delegation, and revocation
status a seller or auditor can check without trusting Nevermined.

Sources
- [NV1] https://nevermined.ai/docs/products/payments/mandates.md, 2026-10-08, raw/nevermined.ai/docs-products-payments-mandates.md (lines 21 to 34, 160 to 177, 184, 199 to 216, 229 to 250)
- [NV2] https://nevermined.ai/docs/specs/x402-card-delegation.md, 2026-10-08, raw/nevermined.ai/docs-specs-x402-card-delegation.md (lines 23 to 25, 201 to 246, 543 to 575 for the seller forwarding the payload to the facilitator, 710 to 791, 795, 928 to 940). Quote: "In-flight settlements at the time of revocation MAY complete if the PSP PaymentIntent has already been confirmed" (line 932)
- [NV3] https://nevermined.ai/docs/solutions/organizations/groups-and-budgets.md, 2026-10-08, raw/nevermined.ai/docs-solutions-organizations-groups-and-budgets.md (lines 12, 31)
- [NV4] https://nevermined.ai/docs/integrate/authentication/connections.md, 2026-10-08, raw/nevermined.ai/docs-integrate-authentication-connections.md (lines 12, 45 to 60, 67)
- [NV5] https://nevermined.ai/docs/solutions/card-delegation.md, 2026-10-08, raw/nevermined.ai/docs-solutions-card-delegation.md (lines 52 to 66)
- [NV6] https://nevermined.ai/docs/products/payments/mandate-selection.md, 2026-10-08, raw/nevermined.ai/docs-products-payments-mandate-selection.md
- [NV7] https://nevermined.ai/docs/products/catalog/router/overview.md, 2026-10-08, raw/nevermined.ai/docs-products-catalog-router-overview.md (lines 11, 35, 43, 99)
- [NV8] https://nevermined.ai/docs/llms.txt and https://nevermined.ai/docs/products/payments/faq.md, 2026-10-08, raw/nevermined.ai/ (setup_delegation returns one approval URL, per the index description; FAQ line 140 on Visa passkey)
- [NV9] https://api.npmjs.org/downloads/point/2026-09-08:2026-10-07/ for @nevermined-io/payments, @agentcommercekit/ack-pay, gokite-aa-sdk, 2026-10-08, raw/api.npmjs.org/

Blocked or unverifiable: the Organizations API reference is "coming soon" per NV3, so per-group budget
fields could not be read. Not picked: Catena Labs ACK (ACK-Pay, ACK-ID) and Kite (passport, session keys),
both with far lower package downloads (NV9); not researched further.

---

## Most surprising gaps

1. **AP2 has no revocation at all.** The only end to an open mandate is `exp` or single use; managing
   delegated mandates is declared out of scope [AP5].
2. **AP2's budget has no owner.** The spec requires tracking cumulative spend but names no role to keep it;
   the reference credential provider verifies without usage context, and the sample's ledger is a file
   written by the shopping agent, the party the threat model treats as a possible attacker [AP2][AP8][AP9].
   The SDK also never checks recurrence frequency, and units differ between `amount_range` (integer minor
   units) and `budget` (unitless number multiplied by 100) [AP3][AP7].
3. **Skyfire pay tokens cannot be recalled.** Deactivating an account or key leaves issued tokens
   chargeable for up to 24 hours past expiry, and only the token's own parties can introspect it [SK1][SK4].
4. **Skyfire's real authority is the API key, which has no limits.** The key holder sets each token's
   amount, and Skyfire's own MCP tool lets the agent choose it [SK5][SK10].
5. **Two of four named startups no longer document their agent payment product.** Payman's docs host is
   down and the company now sells to banks; Nekuda's docs now cover WebMCP only [PM11][PM12][NK7][NK8].
6. **Nekuda's public SDK returns full card number and CVV** to the agent developer's backend after a
   mandate that the SDK never shows a user approving [NK1][NK3].
7. **x402 says budget management is out of scope**, and the reference client's caps run in the payer's own
   process, where they can be switched off [XP2][XP3].
8. **Only Nevermined comes close to the test case**, and even there revocation is visible only by asking
   Nevermined [NV1][NV2].

## Possibly missing from the teardown

- **Mastercard Verifiable Intent**, contributed to FIDO alongside AP2 as its companion intent record
  (https://fidoalliance.org/fido-alliance-to-develop-standards-for-trusted-ai-agent-interactions/, saved as
  AP11); worth a block if its open specification is public.
- **Nevermined Router and catalog MCP**, if the teardown wants one budget across x402 and MPP
  (https://nevermined.ai/docs/products/catalog/router/overview.md).
- **The MPP rail itself** (HTTP 402 with `WWW-Authenticate: Payment`), named by Nevermined's Router as a
  second agent payment protocol beside x402 (same URL, line 56); not checked here.
