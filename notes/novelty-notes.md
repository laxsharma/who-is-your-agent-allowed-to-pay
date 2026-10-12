# Novelty sweep: "accounts, not wallets" and task-scoped spending authority for agents

Group: novelty. Read and fetched 8 October 2026 (all fetch dates below are 2026-10-08 UTC unless stated).
Saved copies: `raw/<host>/...`, listed in [SOURCES.md](../SOURCES.md). Pages were read through plain-text
extractions, which were deleted afterwards because they are reproducible from the saved files. Every quote
below was re-checked against the saved file by script (70 of 70 found; the file also holds a few locator strings that are paraphrased, not quoted, in these notes). A few rows
cite raw copies saved by other groups (cards-networks, cards-stripe-corporate, coinbase-aws,
wallets); the path is given each time.

Thesis under test: agents need ACCOUNTS (the principal's money, operated by the agent under the
principal's rules, scoped to a task) rather than wallets the agent holds or bearer tokens; and spending
authority should be scoped to a TASK: pay only the counterparties this task names, up to this task's
budget, until this task ends, revocable in one verifiable step.

Codes used in the table.
Thesis parts: A accounts, not wallets (argued as such); P principal's money operated under the
principal's rules; T authority scoped to a task (or session, purpose, mandate); K a credential minted
per task, narrower than the agent's main key; R revocation a third party can verify; X one policy across
more than one rail. Y = stated, p = partly, - = not stated.
Test case: a named counterparties only; b per-task budget; c ends when the task ends; d one-step
revocation a third party can verify; e credential per task.

## 1. The two required checks

### 1.1 arXiv 2609.27452, "Issuer-Sovereign Agentic Payments"
- The id exists and resolves to that exact title. arXiv API and abstract page: v1, submitted
  Wed 23 Sep 2026 07:18 UTC, primary cs.CR (also cs.AI, cs.SE), only one version. Authors on arXiv:
  Dishant Sharma, Rajneesh Kaushal, Ashu Kanaujia; the PDF lists all three with thalesgroup.com
  addresses. Read in full: 6-page PDF, `../raw/arxiv.org/pdf-2609.27452v1.pdf` (the arXiv HTML
  rendering is not available for this paper; the saved `html-2609.27452v1.html` is the "no HTML" page).
- What it does: moves agent spending enforcement into the card issuer's 3-D Secure Access Control
  Server. At consent (cardholder present, biometric step-up, non-payment authentication) a constraint
  component records a rule (cap, allowed merchants, time window) and returns only a reference; no
  credential exists yet. At execution the merchant's agent cites the reference, and the issuer checks
  merchant, amount and window, then generates the CAVV or AAV only if the rule passes. The rule can cover
  several payments; it may also be committed as a signed object for disputes.
- What it does NOT cover, against the thesis and test case: no revocation mechanism at all (the word does
  not appear); no task identifier or task-end binding, only a time window; card rails only, so no
  cross-rail policy; the merchant sees only an ordinary authenticated card payment (the paper lists
  this as an advantage: nothing on the wire reveals the agent arrangement), so no third party can verify
  the rule or its revocation; no account-versus-wallet framing; no evaluation, prototype or security
  analysis. It is a method note, closest to the test case on (a) and (b) for cards only.

### 1.2 South et al., "Authenticated Delegation and Authorized AI Agents", arXiv 2501.09674
- Version read: v1 (16 Jan 2025), which is the only and therefore latest version (abstract page
  submission history lists only [v1]; arXiv API returns 2501.09674v1). 23-page PDF,
  `../raw/arxiv.org/pdf-2501.09674v1.pdf`. Authors: Tobin South, Samuele Marro, Thomas Hardjono,
  Robert Mahari, Cedric Deslandes Whitney, Dazza Greenwood, Alan Chan, Alex Pentland.
- What it does: extends OAuth 2.0 and OpenID Connect with an agent ID token and a user-signed
  delegation token that references the user's ID token and the agent's token, carries scope limits, a
  summarized goal, validity conditions such as expiry or revocation endpoints, and optional audit URLs.
  It distinguishes task scoping (which actions or workflows) from resource scoping (which resources),
  and proposes translating natural-language permissions into structured access control. Payments appear
  as a motivating example (an agent should buy only on specific booking services with explicit spending
  limits) and in Appendix C (a web-browsing scenario whose delegation credential scope lists spending
  limits and validity duration as example constraints).
- What it does NOT cover: no payment design. No budget accounting across payments, no counterparty
  binding in payment terms, no account or wallet model, no rails. Revocation is a field in the token
  (revocation endpoints) with no mechanism or third-party verification beyond the relying service.
  Task scoping is defined, but the paper treats structured resource scoping as the precise, auditable
  base and task scoping as more flexible but harder to encode.

## 2. Closest prior work

| # | Title | Author or vendor | Date | Link | What it argues or ships | Thesis parts (A P T K R X) | Test case (a b c d e) | What it misses |
|---|---|---|---|---|---|---|---|---|
| 1 | Issuer-Sovereign Agentic Payments (arXiv 2609.27452v1) | Kaushal, D. Sharma, Kanaujia (Thales) | 23 Sep 2026 | https://arxiv.org/abs/2609.27452 | Issuer ACS records a cap, merchant set and window at consent; generates CAVV/AAV only for an allowed merchant | A - P Y T p K p R - X - | a Y b Y c p d - e p | Revocation, task end, any rail but card, third-party view, evaluation |
| 2 | Authenticated Delegation and Authorized AI Agents (arXiv 2501.09674v1) | South, Marro, Hardjono, Mahari, Whitney, Greenwood, Chan, Pentland | 16 Jan 2025 | https://arxiv.org/abs/2501.09674 | OAuth/OIDC agent ID token plus user-signed delegation token with scope, expiry, revocation endpoints; task vs resource scoping; spending limits as an example | A - P p T Y K Y R p X - | a p b p c p d p e Y | Payments, budget accounting, counterparties, accounts, rails |
| 3 | Kite whitepaper "From Human-Centric to Agent-Native" and "Kite Passport: A Technical Deep Dive" | Kite AI | Undated web pages (a mainnet launch on 30 Apr 2026 appears only in search results, not saved) | https://www.gokite.ai/kite-whitepaper ; https://docs.avax.network/blog/kite-passport-technical-deep-dive | User owns one smart-contract account; agents operate it through task-scoped, random, expiring session keys limited to named providers, amounts and time windows; one-transaction revoke of all delegations; revocation certificates | A Y P Y T Y K Y R Y X p | a Y b Y c Y d Y e Y | Only on Kite's chain and services that check its passport; stablecoins only (cards and banks via ramps); self-published, undated, claims unverified |
| 4 | Moving money with agents (Lead Bank blog) plus Lead API docs, Account Number Controls | Lead Bank (Reses, Vyas quoted) | 29 Sep 2026 | https://www.lead.bank/blog/moving-money-with-agents ; https://docs.lead.bank/products/account-number/controls.md | One account number per agent task or session on the principal entity's bank account; per-rail controls (ACH, wire, international wire, instant, internal) for direction and counterparty allowlist; cancel or deactivate when the task ends | A Y P Y T Y K Y R p X p | a Y b p c p d p e Y | No amount cap or expiry field on account-number controls (daily and monthly limits are set at program setup); revocation is bank-internal; one control object per rail, no cards or stablecoins in the same object; examples are marked illustrative only |
| 5 | Who Banks the Agents? plus Agentic Banking (Beta) | Anchorage Digital (Zev Shimko, Viktor Stanchev) | 3 Aug 2026 | https://www.anchorage.com/research/who-banks-the-agents | The most explicit "accounts, not wallets" argument found: a wallet cannot carry KYC, compliance, recourse or treasury; an allowance is a sub-account with rules enforced at a regulated custodian | A Y P Y T - K - R p X p | a Y b p c - d p e - | Per agent, not per task; no per-task credential; beta, select teams |
| 6 | Banking as a service for AI agents | Rabea Bader (Quidkey) | 14 Apr 2026 | https://rabea.sh/posts/banking-as-a-service-for-ai-agents | Principal owns funds; each agent gets an isolated "wallet" defined as a virtual bank account with its own policy; single-use cards per purchase under the same policy; counterparty verify endpoint | A p P Y T p K p R p X p | a Y b p c p d p e p | Per agent, not per task; design paper and marketing; calls the account a wallet |
| 7 | Your AI Agent Doesn't Need a Wallet - It Needs a Treasury | Axon Finance (DEV) | 18 Mar 2026 | https://dev.to/axonfi/your-ai-agent-doesnt-need-a-wallet-it-needs-a-treasury-1dg3 | Agents sign payment intents against an owner's vault; per-transaction cap on-chain, periodic caps in a relayer, destination whitelist, pause | A Y P Y T - K p R p X - | a Y b p c - d p e - | No task scope or expiry; periodic limits off-chain; one chain per vault |
| 8 | When AI Agents Get Wallets, Who Stays in Control? (X article) | imToken | 24 Aug 2026 (decoded from the post id) | https://x.com/imTokenOfficial/article/2091818880230707301 | Each agent gets a policy-bound agent account with a TEE session key, allowlists, per-transaction and daily limits, validity; user revokes and recovers funds | A Y P Y T - K p R p X - | a p b p c p d p e p | Per agent; design concept, no spec |
| 9 | AI Agents Need Permissioned Funding Sources. Not Company Bank Accounts. | PYMNTS | 10 Sep 2026 | https://www.pymnts.com/news/artificial-intelligence/2026/ai-agents-need-permissioned-funding-sources-not-company-bank-accounts/ | Agents need permission to spend, not money; treasury stays central; cards, stablecoins and bank rails are execution options chosen by one control layer | A p P Y T - K - R - X Y | argument only | No mechanism; its title rejects separate bank accounts per agent, which matches the thesis in substance while using "account" in the opposite sense |
| 10 | Agentic Mobile Protocol (AMP) spec; "Account for Agent" | Ant International (Alipay+) | Repo ant-intl/AMP @a4fe50c, 23 Sep 2026; PYMNTS report 18 Sep 2026 | https://github.com/ant-intl/AMP | Mandate states task objective, budgetAmount, merchantNameList, MCC list, validity, wallet account to debit; states activated, revoked, expired, finished (task done or budget exhausted); Alipay+ returns latest status to participants | A p P Y T Y K p R p X - | a Y b Y c Y d p e p | One network (Alipay+ wallets); status visible to protocol participants, not publicly; Payment Token per transaction, not a task key |
| 11 | Technical deep dive: AgentCore Payments | AWS (Vangara, Ansari, Shriyan) | 26 May 2026 | https://aws.amazon.com/blogs/machine-learning/technical-deep-dive-agentcore-payments-and-innovation-in-agentic-commerce/ | Payment session with maxSpendAmount and expiry, passed to the agent when its task begins; agent cannot extend it; atomic budget reservation | A - P Y T Y K p R - X p | a - b Y c Y d - e p | No payee allowlist or revocation in the post; embedded wallets; status unclear (the post calls the service generally available in one paragraph and describes preview capabilities in the next) |
| 12 | Virtual Cards for AI Agents; Ramp Agent Cards | Ramp | 28 Apr 2026 | https://ramp.com/blog/virtual-cards-for-ai-agents | A scoped, revocable virtual card per agent task with limits, merchant restrictions and expiry; single-use network tokens | A - P Y T Y K Y R p X - | a Y b Y c Y d p e Y | Card only; revocation is issuer-side; Agent Cards "early access" |
| 13 | Agent Payments Protocol (AP2), open Payment Mandate | Google-originated spec, repo google-agentic-commerce/AP2 @e1ea56d | 29 Apr 2026 (commit date) | https://github.com/google-agentic-commerce/AP2 | Signed mandate constraints: allowed payees, allowed instrument, amount range, budget, execution date, recurrence | A - P Y T p K p R - X p | a Y b Y c p d - e p | No revocation in the spec documents (only a sample credentials-provider tool revokes tokens); mandate is not an account or a payment key |
| 14 | Visa Intelligent Commerce launch press release | Visa | 30 Apr 2025 | https://usa.visa.com/about-visa/newsroom/press-releases.releaseId.21361.html | Agent-specific tokenized credentials; consumer sets spending limits and conditions | A - P Y T - K p R ND X - | a p b p c ND d ND e p | No task scope; details are in the cards-networks group's notes |
| 15 | Issuing for agents (docs) and Shared Payment Token revoke API | Stripe | Docs read 8 Oct 2026 | https://docs.stripe.com/issuing/agents.md | Single-use Issuing cards, SPTs and agentic network tokens from one Issuing card, with spend controls; SPTs have a revoke endpoint | A - P Y T p K Y R p X p | a p b p c p d p e Y | No task object; card-funded only; revocation is issuer-side. Details in the cards-stripe-corporate notes |
| 16 | Spend Permissions | Coinbase (Coinbase Wallet, formerly Base Account) | Docs read 8 Oct 2026 | https://docs.cdp.coinbase.com/coinbase-wallet/improve-ux/spend-permissions.md | User's smart account grants a spender an allowance per period between start and end; revocable on-chain | A p P Y T - K Y R Y X - | a - b p c Y d Y e Y | Not agent- or task-specific; no payee list; one token per permission |
| 17 | ERC-7715 Request Permissions from Wallets; ERC-7710 Smart Contract Delegation | L. Isailovic, D. Rein, D. Finlay, D. Chiang and others (7715); R. McPeck, D. Finlay, R. Dawson, D. Chiang (7710) | Created 20 and 24 May 2024 (Draft) | https://eips.ethereum.org/EIPS/eip-7715 | Wallet grants scoped execution permissions to a session account; delegation with caveats | A p P Y T p K Y R p X - | a p b p c p d p e Y | Pre-dates the agent framing; generic dapp sessions; EVM only |
| 18 | draft-chen-oauth-rar-agent-extensions-01, Policy, Lifecycle, and Intent Extensions for OAuth RAR | M. Chen, L. Su (China Mobile) | 22 Apr 2026 | https://datatracker.ietf.org/doc/draft-chen-oauth-rar-agent-extensions/ | intent_request with constraints such as max_budget; lifecycle_binding ties the grant to a task_id and revokes it when the task reaches a terminal state; RS must check introspection or a revocation feed | A - P p T Y K p R p X - | a - b Y c Y d p e p | Generic OAuth, no payee field or payment semantics; individual draft, expires 24 Oct 2026 |
| 19 | draft-mcgraw-httpapi-agent-budget-04, The Delegation HTTP Authentication Scheme | J. McGraw (TaskHawk) | 10 Sep 2026 | https://datatracker.ietf.org/doc/draft-mcgraw-httpapi-agent-budget/ | Signed Budget-Attestation: total and remaining budget, currency, permitted rails or actions, expiry, one verifier or merchant binding, optional request binding | A - P p T p K Y R - X p | a p b Y c p d - e Y | No task id; one merchant binding, not a set; only key revocation; "does not define payment semantics" |
| 20 | draft-niyikiza-oauth-attenuating-agent-tokens-01, Attenuating Authorization Tokens | N. A. Niyikiza (Tenuo) | 15 Jun 2026 | https://datatracker.ietf.org/doc/draft-niyikiza-oauth-attenuating-agent-tokens/ | Task-scoped delegation tokens for tool calls with argument constraints, offline attenuation | A - P - T Y K Y R - X - | a p b p c p d - e Y | Not payments; revocation explicitly out of scope (short lifetimes instead) |
| 21 | draft-yossif-agent-mandate-problem-00, Verifiable Human Mandates for Autonomous Agent Actions | M. K. Yossif (Yuthent) | 22 Jul 2026 | https://datatracker.ietf.org/doc/draft-yossif-agent-mandate-problem/ | Problem statement: a mandate names permitted counterparties, value ceilings, validity window; credits AP2 for the payment case | A - P Y T p K - R - X - | problem only | Defines no mechanism by design |
| 22 | Agent-to-Agent Finance (arXiv 2607.00245v2) | Hui Gong | v1 30 Jun 2026 | https://arxiv.org/abs/2607.00245 | Book chapter: agent wallets need delegated authority (caps, time limits, counterparty allowlists, emergency revocation, approval thresholds), hard limits close to the wallet | A - P p T - K - R p X - | survey only | Keeps the wallet framing; no task scope |
| 23 | Beyond OAuth: Task-Scoped Authorization for AI Agents via Natural Language Slices (arXiv 2603.17170v2) | R. K. Sharma, L. Jiang, S. Chen, Z. Lin | v1 17 Mar 2026 | https://arxiv.org/abs/2603.17170 | Task-scoped implicit authorization over operations with operands (for example "transfer $100 to Bob") | T Y only | a p b p c p d - e - | Web-service calls, not payment rails or accounts |
| 24 | Who Grants the Agent Power? Task-Centric Access Control (arXiv 2510.26212v1) | Y. Cai et al. | 30 Oct 2025 | https://arxiv.org/abs/2510.26212 | Minimal temporary policies per user task, revoked on completion (mobile agents) | T Y, R p | not payments | Not money |
| 25 | Identity Management for Agentic AI (OpenID Foundation whitepaper, arXiv 2510.25819v1) | OpenID Foundation (lead editor Tobin South) | Oct 2025 (arXiv v1 29 Oct 2025) | https://arxiv.org/abs/2510.25819 | Names revocation across delegated, offline-attenuated agent tokens as largely unsolved | R (states the gap) | n/a | Identity, not payments |
| 26 | Natural (home page) | Natural | Read 8 Oct 2026 | https://www.natural.co/ | Markets FDIC-insured accounts that agents hold, with IDs tied to a legal identity | A p P p | ND | Docs not read; press pages blocked; "accounts agents can hold" is agent-held, not the thesis's sense |

### Quotes and evidence per row (each at most two sentences, each confirmed against the raw copy)

1. Abstract: "Later, when the agent pays a specific merchant, the bank checks the merchant against the
   approved rule and generates the card authentication value only if the merchant is allowed." Body:
   "The component records the rule, which holds the spending cap, the set of allowed merchants, and the
   time window." [N1] `../raw/arxiv.org/abs-2609.27452.html`, `../raw/arxiv.org/pdf-2609.27452v1.pdf`
2. "Instead, an AI agent should be authenticated and authorized to make a purchase on specific booking
   services, where credit cards are stored securely, and where explicit spending limits can be enforced."
   "The delegation token should specify validity conditions, such as expiration time or revocation
   endpoints, and be digitally signed by the user to prevent forgeries and ensure that the user knowingly
   granted the AI agent the listed privileges." [N2] `../raw/arxiv.org/pdf-2501.09674v1.pdf`
3. Whitepaper, two sentences from separate passages: "In Kite's model, the user owns a single on-chain
   AA account holding shared funds in stablecoins." and "Instead, each operation receives a one-time,
   task-scoped session key with surgical precision permissions." Paraphrased locators, each confirmed in
   the same saved file: agents operate the shared account via session
   keys only within their limits; an example session key allows at most 10 dollars to three named data
   providers within a five-minute window; a Fine-Grained Task Authorization paragraph says permissions are
   scoped per task rather than per agent; sessions expire at `validUntil` or are revoked on-chain with
   `removeSessionKeyPermission()`; the user can revoke all delegations in one transaction. The Avalanche
   Builder Hub deep dive says the same about per-task session keys (paraphrase; sentence confirmed in
   [N4]). [N3] `../raw/www.gokite.ai/kite-whitepaper.html`; [N4]
   `../raw/docs.avax.network/kite-passport-technical-deep-dive.html`
4. Blog, quoting the CTO: "Each task gets its own account number; controls are defined by rail and
   enforced on every payment; and access can be revoked when the mandate ends." Step 2: "Create one
   account number per agent task or session." Paraphrased, confirmed in the same file: the blog's table
   puts daily and monthly limits at program setup, and a note calls the examples illustrative only. API
   docs summary line: "Block or allow transactions at the account number level." The controls table has
   no amount or expiry field (a whole-word grep for limit, limits, amount, cap, expir, expires and
   expiration returns nothing). [N5] `../raw/www.lead.bank/moving-money-with-agents.html`;
   [N6] `../raw/docs.lead.bank/account-number-controls.md`
5. "An agent can hold a wallet, but it cannot open an account, pass identity checks, carry a compliance
   obligation, offer recourse when it errs, or run treasury." "It is a sub-account with rules attached, and
   the interesting engineering problem is where the rules get enforced." (The sentence before the second
   quote calls an allowance a banking primitive; the paper also says the account should settle across fiat
   and stablecoin rails. Product page heading confirmed: "Agentic Banking Beta".) [N7]
   `../raw/www.anchorage.com/who-banks-the-agents.html`; [N8] `../raw/www.anchorage.com/agentic-banking.html`
6. "The principal is the company or legal entity that owns the funds and defines the rules." On the
   per-agent isolated wallet: "Think of it as a virtual bank account with its own account details and the
   ability to send and receive money." (Verify endpoint `GET /v1/agents/{id}/verify` confirmed.) [N9]
   `../raw/rabea.sh/banking-as-a-service-for-ai-agents.html`
7. "The mental shift: agents don't need wallets. They need permission to request payments from a vault
   they don't control." [N10] `../raw/dev.to/axonfi-treasury.html`
8. "The agent therefore does not receive an unrestricted wallet. It receives an execution account enclosed
   by policy guardrails." [N11] `../raw/x.com/imtoken-article.html`
9. "AI agents may not need money; they need permission to spend it." Highlight: "The real control layer
   determines identity, limits, counterparties, purpose and which rail gets used at the moment of
   payment." [N12] `../raw/www.pymnts.com/permissioned-funding-sources.html`
10. AMP spec, lifecycle table, state `finished`: "The task associated with the Mandate has been completed,
    the authorization budget has been exhausted, or closure conditions defined by Alipay+ rules have been
    met." "Alipay+, as the Mandate status maintainer, **MUST** record the creation, authorization,
    activation, revocation, expiration, and closure of each Mandate, and return the latest status when
    participants reference or invoke the Mandate." (Field rows budgetAmount and merchantNameList
    confirmed.) PYMNTS on Account for Agent (paraphrasing Ant's release): "Users authorize a single task
    and keep the account itself." [N13] `../raw/ant-intl-AMP/docs/Intent Trust Domain.md`; [N14]
    `../raw/www.pymnts.com/agents-getting-own-bank-accounts.html`
11. "This session is the agent's financial boundary; it defines exactly how much can be spent and for how
    long. The session ID and instrument ID are passed to the agent when its task begins." [N15]
    `../raw/aws.amazon.com/agentcore-payments-deep-dive.html`
12. "Instead of giving an agent your corporate card number, you issue a scoped, revokable virtual card
    configured for that agent's specific task." (Status line confirmed: Ramp Agent Cards are "now in early access".) [N16] `../raw/ramp.com/virtual-cards-for-ai-agents.html`
13. Payment Mandate constraint list: "**Allowed Payee:** Constrains the payee to one of a set of possible
    Merchants." and "**Budget:** Provides a total amount limit." [N17] `../raw/AP2/docs/ap2/payment_mandate.md`
    (clone by another group, AP2@e1ea56d)
14. "Allows consumers to easily set spending limits and conditions, providing clear guidelines for agent
    transactions." [N18] `../raw/usa.visa.com/pr-21361-vic.html` (saved by cards-networks)
15. "Before your agent makes a purchase, you can decide what it can spend, where, and how much." Revoke
    API title: "Revokes a SharedPaymentIssuedToken". [N19] `../raw/docs.stripe.com/issuing-agents.md`,
    `../raw/docs.stripe.com/api-spt-issued-token-revoke.md` (saved by cards-stripe-corporate)
16. "Spend Permissions let you designate a trusted `spender` that can move assets out of a user's Coinbase
    Wallet on their behalf." [N20] `../raw/docs.cdp.coinbase.com/cw-spend-permissions.md` (saved by
    coinbase-aws)
17. ERC-7715 abstract use case: "Executing transactions for users with a wallet connection that is scoped
    with permissions." [N21] `../raw/ERCs/ERCS/erc-7715.md` (clone by another group, ERCs@ee5363b)
18. "The authorization grant's validity should ideally be coupled to the task's actual lifecycle." "Upon
    notification of a terminal state, the AS MUST immediately revoke the grant and all associated tokens."
    [N22] `../raw/www.ietf.org/draft-chen-oauth-rar-agent-extensions-01.txt`
19. "The initial authority profile is the Budget profile, which uses a CBOR/COSE Budget-Attestation
    envelope to prove bounded authority to spend, consume metered service units, or commit bounded
    resources." CDDL line confirmed: `13 => tstr, ; verifier or merchant binding`. [N23]
    `../raw/www.ietf.org/draft-mcgraw-httpapi-agent-budget-04.txt`
20. "This document defines Attenuating Authorization Tokens (AATs), a signed credential format for
    task-scoped delegation in AI agent systems." Section 8.9 says revocation of individual AATs "is outside
    the scope of this specification". [N24] `../raw/www.ietf.org/draft-niyikiza-oauth-attenuating-agent-tokens-01.txt`
21. "A mandate bounds the actions the Agent may execute on the Principal's behalf" (the same sentence
    goes on to name permitted operations, permitted counterparties, value ceilings and a validity window
    as examples). [N25]
    `../raw/www.ietf.org/draft-yossif-agent-mandate-problem-00.txt`
22. "Agent wallets need delegated authority rather than absolute control." [N26] `../raw/arxiv.org/pdf-2607.00245v2.pdf`
23. Abstract: OAuth "grants permissions over operators (e.g., TRANSFER), not operations (operator plus
    operands, e.g., transfer $100 to Bob)." [N27] `../raw/export.arxiv.org/search-task-scoped.xml`
24. Abstract: "Instead of granting broad, persistent permissions, AgentSentry dynamically generates and
    enforces minimal, temporary policies aligned with the user's specific task (e.g., register for an
    app), revoking them upon completion." [N27]
25. "A critical, and largely unsolved, problem in these architectures is revocation." [N28] `../raw/arxiv.org/pdf-2510.25819v1.pdf`
26. Home page: "accounts agents can hold, receive, & send funds from." and "All IDs tie back to a
    verifiable legal identity". Marketing only. [N29] `../raw/www.natural.co/home.html`

Also read, relevant but not tabled: draft-kroehl-agentic-trust-aae-02 (Agent Authorization Envelope:
MANDATE, CONSTRAINTS, VALIDITY blocks, amount ranges, a revocation_check URI template the relying party
must query), draft-wang-jep-action-mandate-profile-02 (bounded, terminable mandate descriptor with
amount limits), draft-chen-oauth-agent-revocation-00 (batch and cascade revocation for agent tokens),
draft-watts-oauth-agent-revocation-closure-00 (credential invalidation alone does not close every path
to a consequential action), draft-klrc-aiagent-auth-03 and draft-ietf-oauth-transaction-tokens-08
(generic agent and workload authorization context, no spending fields),
draft-hamr-oauth-agent-delegation-02, draft-mishra-oauth-agent-grants-02 and draft-agentir-aepp-02.
All saved under `../raw/www.ietf.org/`. None adds a payment-specific element the table lacks; AAE's
revocation_check is a second example of a relying-party-checkable revocation status.

## 3. Where I searched and the queries I ran

Web search (general engine, US):
- "accounts, not wallets" AI agents (extended)
- "agentic account" payments AI agent (extended)
- AI agents need bank accounts not crypto wallets (extended)
- Kite AI three-layer identity user agent session keys spending
- Catena Labs agent accounts AI-native financial institution blog
- "task-scoped" spending AI agent payments credential (extended)
- "per-task budget" AI agent payment
- "spend mandate" agent
- "accounts for agents" payments (results were unrelated: real-estate and travel agents)
- "agent account" principal funds spending policy revocable AI agent bank (extended)
- a16z crypto AI agents payments "know your agent" accounts wallets essay
- a16z crypto "Know Your Agent" Catalini Hall paper agents unbanked 2026
- Kite AI whitepaper "session" "agent" "user" three-layer identity SPACE framework gokite
- Kite AI whitepaper released "From Human-Centric to Agent-Native" date
- Kite AI publishes whitepaper SPACE framework agent payments 2025
- Skyfire KYAPay "know your agent" payment token spending limits agents accounts
- Natural agentic payments startup "agents" bank accounts launch 2026
- Natural (natural.co) agent wallets "FDIC" accounts for AI agents Column docs
- Sapiom AI agents payments financial layer spend
- arxiv agentic payments delegated spending authority AI agents mandate budget counterparty 2026 (extended)
- Mastercard Agent Pay "agentic tokens" scoped to task merchant amount time consumer-set controls
- Stripe "shared payment token" agent scoped seller amount expiration revoke agentic commerce
- Coinbase "agentic wallets" spend limits session caps "not a wallet" blog February 2026
- Visa Intelligent Commerce "agent-specific" credential "spend controls" consumer sets limits per agent tokens blog 2026
- Anchorage Digital "Agentic Banking" launch AI agents accounts controls
- "sub-account" per task AI agent bank API spending authority revoke "account number" agents 2026 (extended)
- Ant International "Account for Agent" WorldFirst press release September 2026 "Agentic Mobile Protocol" authorize task
- OpenID Foundation "Identity Management for Agentic AI" whitepaper delegation scope revocation agents
- W3C community group AI agents payments delegation "Web Payments" agentic commerce 2026
- Paradigm research AI agents payments wallets "session keys" essay (nothing from Paradigm found)

arXiv API (export.arxiv.org, abstract-field searches, 40 results each, saved as
`../raw/export.arxiv.org/search-*.xml`): agent AND payments (436 hits); "agentic commerce" (19);
agent AND spending AND delegat* (0); "session keys" AND agent* (1, irrelevant); "account abstraction" AND
agent* (2); capabilit* AND delegation AND "AI agent*" (0); mandate* AND agent* AND payment* (7);
wallet* AND "AI agent*" (8); "task-scoped" (63); budget AND agent* AND payment* (48). Plus id lookups
for 2609.27452 and 2501.09674. Titles scanned include 2604.03733 (SoK blockchain agent payments),
2604.15367 (SoK agentic commerce security), 2604.22602 (PASS provenanced subaccounts for agent wallets),
2609.14744 (runtime authorization for acquired resources), 2610.05840 (evaluating task-scoped
authorization), 2510.26702 (semantic task-to-scope matching), 2603.14011 (charter-governed fiscal
limits), 2511.15712, 2608.23858 and 2602.06345 (AP2 analyses). None states the account-versus-wallet
argument; the task-scoped ones are about tool or API authorization, not money.

IETF Datatracker API (`/api/v1/doc/document/?type=draft&name__contains=`): agent (314 drafts),
payment (14), delegat (106), mandate (3); title and abstract scanned for spend, budget, payment, wallet,
purchase, commerce, money, financial. Drafts fetched from `https://www.ietf.org/archive/id/`.

GitHub API: repository search "agentic mobile protocol" (1 hit, ant-intl/AMP, cloned at a4fe50c).
W3C and OpenID Foundation: via web search only (W3C AI Agent Protocol CG discussed AP2 and x402; no
W3C document on agent spending authority found; OpenID whitepaper read as arXiv 2510.25819v1).

Blocked or unverifiable:
- catena.com and catena.xyz (Catena Labs announcement): TLS certificate error in curl (rc=60) and in the
  fetch tool. Not read. Secondary reports say Catena offers agents "accounts, dollar balances" and a
  control plane with caps and pause; unverified, so not tabled.
- docs.skyfire.xyz/docs/agent-spending-limits: CloudFront 403 ("Request blocked"). The saved page also
  carries a line addressed to agents pointing at an llms.txt index; ignored. Secondary sources say the
  spending-limits feature is not publicly available; unverified.
- fintech.global (Natural funding news): CloudFront 403.
- web.archive.org CDX: "Internet Archive services are temporarily offline", so the Kite whitepaper's first
  publication date could not be established. Files deleted from raw and manifest.
- gleif.org "Agentic AI in Payments" PDF URL from search: returned a "Page not found" page; deleted.
  Secondary summary only (granular, time-bound, revocable mandates); not tabled.
- a16z crypto "Know Your Agent" paper: primary not located; secondary only. Not tabled.
- Mastercard Agent Pay: the developer page saved by the cards-networks group renders by script and
  yielded no checkable text here; see that group's notes. Not tabled.
- A KuCoin news-feed item (`../raw/www.kucoin.com/wallets-need-authority.html`) reposts a social post
  that asks the same questions rhetorically; no mechanism, not used.

## 4. Verdict

Is "accounts, not wallets" new as an argument? No. It has been made repeatedly in 2026, in both
banking and crypto vocabulary. The plainest statement is Anchorage Digital's "Who Banks the Agents?"
(3 Aug 2026): a wallet cannot carry identity, compliance, recourse or treasury, and an agent's allowance
should be a sub-account with rules enforced at the account by a regulated custodian. On the crypto side,
Axon (18 Mar 2026) says agents do not need wallets, only permission to draw on a vault they do not
control; imToken (24 Aug 2026) says the agent "does not receive an unrestricted wallet" but an
"execution account"; Kite's whitepaper describes one principal-owned smart account operated by agents
through session keys. PYMNTS (10 Sep 2026) makes the treasury version: agents need permission to spend,
not money of their own. Be careful with the word, though: the industry uses "account for agents" for two
opposite things. Natural, Anchorage's launch coverage and Ant's "Account for Agent" market accounts the
agent holds or is assigned, while Kite, Lead, Axon and PYMNTS mean the principal's money operated under
the principal's rules. The thesis means the second. Defining that cleanly is a contribution; the slogan
is not.

Is task-scoped spending authority new? No. It is stated outright, with budget, named payees and task-end
expiry, by at least four sources. Lead and Ant document it in a public API or an open spec; Kite
describes it in a whitepaper and reports a live chain:
- Kite's whitepaper: a "one-time, task-scoped session key" valid only for specific providers, exact
  amounts and narrow windows, useless once the task completes; permissions scoped per task rather than
  per agent; on-chain revocation.
- Lead Bank (29 Sep 2026, nine days ago): "Each task gets its own account number", counterparty
  allowlists per rail, cancel the number when the task is done. This is the thesis in bank form, from a
  regulated bank, with a public API for the controls.
- Ant International's AMP spec (repo 23 Sep 2026): a mandate holds the task objective, budget, merchant
  list and validity, and enters `finished` when the task completes; Alipay+ keeps and serves the status.
- draft-chen-oauth-rar-agent-extensions-01 (22 Apr 2026): authorization bound to a task_id, revoked when
  the task ends, with a max_budget constraint.
- Narrower versions: AWS AgentCore Payments sessions (budget and expiry handed over when the task starts),
  Ramp's per-task virtual cards, AP2's open Payment Mandate (payees, budget, dates), the McGraw
  Budget-Attestation draft. South et al. (Jan 2025) had already defined task scoping and put spending
  limits and revocation endpoints in a delegation token; task-scoped authorization for tools is its own
  research line (AATs, PAuth, AgentSentry).

Closest single prior work: the Kite whitepaper. It states almost the whole thesis: a principal-owned
account, agents operating it under the principal's rules, a credential minted per task, named providers,
amounts and time windows, expiry at task end, and revocation in one on-chain transaction that anyone can
check. What it lacks is the cross-rail part. Its enforcement lives on Kite's own chain and in services that
check its passport, and it is a self-published, undated vendor document whose strong claims are
unverified. Runner-up in fiat terms: Lead Bank's 29 Sep post plus API docs, whose controls lack a
per-task amount cap and an expiry field, and whose revocation is invisible to anyone outside the bank.
Runner-up as an open spec: Ant's AMP, which meets (a), (b) and (c) of the test case but only inside
Alipay+.

What the article can claim without overclaiming:
1. Not the idea. Credit Anchorage for "accounts, not wallets" in banking terms, Kite and Lead for
   task-scoped authority, AP2 and AMP for payee-and-budget mandates, and South et al. for task scoping
   in delegation tokens.
2. A rail-neutral statement of the test case, with the task (not the agent, card or key) as the unit
   that binds the account, the credential, the payee set, the budget, the expiry and the revocation, and
   a definition of "account" that excludes agent-held balances.
3. The measured comparison: which shipped products and specs can express each part natively, with
   evidence. This sweep already shows where the gaps are. Bank account-number controls carry payees per
   rail but no per-task amount or expiry field (Lead). AP2's spec documents define no revocation. AATs put
   revocation out of scope. In this sweep, revocation a third party can check appears only on-chain (Kite, Coinbase
   Spend Permissions, ERC-7710/7715 style delegations), in AMP's participant status lookup, in
   relying-party checks in drafts (Chen, AAE), and in Quidkey's verify endpoint.
4. The one part not found shipped anywhere in this sweep: a single task policy enforced across card, bank
   and stablecoin rails at once. It is argued (PYMNTS; Quidkey's design; Anchorage's beta, which it says
   settles over fiat and stablecoin rails; Catena per unverified secondary reports), but no documented credential or API
   in this sweep enforces one per-task budget and payee set across card plus bank plus on-chain. State it
   as "we did not find", not "does not exist", and check the other groups' notes before asserting it.

Timing note for the article: six of the closest items appeared in the last ten weeks (Anchorage 3 Aug,
imToken 24 Aug, PYMNTS 10 Sep, Ant 18 to 23 Sep, the issuer paper 23 Sep, Lead 29 Sep). A reader in this
field will have seen at least one of them, so the article should cite them up front.

## 5. Sources

All fetched 2026-10-08 UTC. Saved paths are relative to raw/.
- [N1] https://arxiv.org/abs/2609.27452 and https://arxiv.org/pdf/2609.27452v1 ; arxiv.org/abs-2609.27452.html, arxiv.org/pdf-2609.27452v1.pdf ; arXiv API record export.arxiv.org/api-ids-2609.27452-2501.09674.xml
- [N2] https://arxiv.org/abs/2501.09674 and https://arxiv.org/pdf/2501.09674v1 ; arxiv.org/abs-2501.09674.html, arxiv.org/pdf-2501.09674v1.pdf, arxiv.org/html-2501.09674v1.html
- [N3] https://www.gokite.ai/kite-whitepaper ; www.gokite.ai/kite-whitepaper.html
- [N4] https://docs.avax.network/blog/kite-passport-technical-deep-dive ; docs.avax.network/kite-passport-technical-deep-dive.html
- [N5] https://www.lead.bank/blog/moving-money-with-agents ; www.lead.bank/moving-money-with-agents.html
- [N6] https://docs.lead.bank/products/account-number/controls.md and .../overview.md and https://docs.lead.bank/llms.txt ; docs.lead.bank/
- [N7] https://www.anchorage.com/research/who-banks-the-agents ; www.anchorage.com/who-banks-the-agents.html
- [N8] https://www.anchorage.com/platform/agentic-banking ; www.anchorage.com/agentic-banking.html
- [N9] https://rabea.sh/posts/banking-as-a-service-for-ai-agents ; rabea.sh/banking-as-a-service-for-ai-agents.html
- [N10] https://dev.to/axonfi/your-ai-agent-doesnt-need-a-wallet-it-needs-a-treasury-1dg3 ; dev.to/axonfi-treasury.html
- [N11] https://x.com/imTokenOfficial/article/2091818880230707301 ; x.com/imtoken-article.html
- [N12] https://www.pymnts.com/news/artificial-intelligence/2026/ai-agents-need-permissioned-funding-sources-not-company-bank-accounts/ ; www.pymnts.com/permissioned-funding-sources.html (article text is behind a form in a browser but present in the saved HTML)
- [N13] https://github.com/ant-intl/AMP @a4fe50c (commit a4fe50c74a8071c0714d410fbc53106b57e25378, 23 Sep 2026) ; ant-intl-AMP/docs/Intent Trust Domain.md (lines 98 to 160 mandate content, 233 to 256 lifecycle)
- [N14] https://www.pymnts.com/news/artificial-intelligence/2026/ai-agents-are-getting-their-own-bank-accounts/ ; www.pymnts.com/agents-getting-own-bank-accounts.html
- [N15] https://aws.amazon.com/blogs/machine-learning/technical-deep-dive-agentcore-payments-and-innovation-in-agentic-commerce/ ; aws.amazon.com/agentcore-payments-deep-dive.html
- [N16] https://ramp.com/blog/virtual-cards-for-ai-agents ; ramp.com/virtual-cards-for-ai-agents.html (also ramp.com/ai-agent-spending-controls.html)
- [N17] https://github.com/google-agentic-commerce/AP2 @e1ea56d ; AP2/docs/ap2/payment_mandate.md lines 31 to 46 ; revocation only in AP2/code/samples/python/src/roles/credentials_provider_mcp/server.py:257
- [N18] https://usa.visa.com/about-visa/newsroom/press-releases.releaseId.21361.html ; usa.visa.com/pr-21361-vic.html (SOURCES.md)
- [N19] https://docs.stripe.com/issuing/agents.md and https://docs.stripe.com/api/shared-payment/issued-token/revoke.md ; docs.stripe.com/ (SOURCES.md)
- [N20] https://docs.cdp.coinbase.com/coinbase-wallet/improve-ux/spend-permissions.md ; docs.cdp.coinbase.com/cw-spend-permissions.md (SOURCES.md)
- [N21] https://github.com/ethereum/ERCs @ee5363b ; ERCs/ERCS/erc-7715.md, ERCs/ERCS/erc-7710.md
- [N22] https://www.ietf.org/archive/id/draft-chen-oauth-rar-agent-extensions-01.txt ; www.ietf.org/draft-chen-oauth-rar-agent-extensions-01.txt
- [N23] https://www.ietf.org/archive/id/draft-mcgraw-httpapi-agent-budget-04.txt ; www.ietf.org/draft-mcgraw-httpapi-agent-budget-04.txt (Budget-Claims CDDL in section 5.2)
- [N24] https://www.ietf.org/archive/id/draft-niyikiza-oauth-attenuating-agent-tokens-01.txt ; www.ietf.org/draft-niyikiza-oauth-attenuating-agent-tokens-01.txt (section 8.9)
- [N25] https://www.ietf.org/archive/id/draft-yossif-agent-mandate-problem-00.txt ; www.ietf.org/draft-yossif-agent-mandate-problem-00.txt
- [N26] https://arxiv.org/pdf/2607.00245v2 ; arxiv.org/pdf-2607.00245v2.pdf (section 4.4)
- [N27] arXiv API searches ; export.arxiv.org/search-*.xml (abstracts of 2603.17170v2, 2510.26212v1); PDF arxiv.org/pdf-2603.17170v2.pdf
- [N28] https://arxiv.org/pdf/2510.25819v1 ; arxiv.org/pdf-2510.25819v1.pdf
- [N29] https://www.natural.co/ ; www.natural.co/home.html
- Datatracker listings: datatracker.ietf.org/api-docs-name-{agent,payment,delegat,mandate}.json
- Other drafts read: www.ietf.org/draft-{kroehl-agentic-trust-aae-02, wang-jep-action-mandate-profile-02, klrc-aiagent-auth-03, chen-oauth-agent-revocation-00, watts-oauth-agent-revocation-closure-00, hamr-oauth-agent-delegation-02, mishra-oauth-agent-grants-02, agentir-aepp-02, ietf-oauth-transaction-tokens-08}.txt
