# The task-account object

One object per task, signed by the principal, naming the agent's per-task key. Amounts are integers in minor
units of one asset, so no rail has to agree on decimal handling. This is the article's trip: the airline up to
$500, the hotel up to $600, $1,000 in all, from 1 pm until midnight (UTC in this example).

```json
{
  "type": "task-account/0.1",
  "task_id": "trip-austin",
  "principal": "ed25519:<base64url principal public key>",
  "agent_key": "ed25519:<base64url public key, issued for this task only>",
  "asset": "USD",
  "budget_minor": 100000,
  "counterparties": [
    {"id": "payee:airline", "cap_minor": 50000,
     "rails": {"card": "<merchant id>"}},
    {"id": "payee:hotel", "cap_minor": 60000,
     "rails": {"card": "<merchant id>", "evm:8453": "0x<payee address>"}}
  ],
  "not_before": "2026-10-21T13:00:00Z",
  "expires": "2026-10-22T00:00:00Z",
  "revocation": {"by": "principal", "list": "<where the revocation list is published>"},
  "signature": "<principal signature over the canonical form of everything above>"
}
```

The rules it carries, all enforced by [engine/](engine/):

- R1: pay only a listed `id`.
- R2: the sum paid to each `id` stays at or under its `cap_minor`.
- R3: the sum across all stays at or under `budget_minor`.
- R4: no payment outside [`not_before`, `expires`).
- R5: one principal-signed statement naming `task_id` and this object's digest ends it, and anyone holding the
  object can verify that statement.
- R6: only `agent_key` can sign requests, and its signature binds `task_id`.

Caps may sum to more than the budget, as the trip's do; the budget then binds first.

## Mapping onto MetaMask's Delegation Framework, v1.3.0

Read from the contracts at the v1.3.0 tag; not deployed or run.

| Field | Construct |
|---|---|
| `principal` | the DeleGator account P (root delegator) |
| `task_id` | root delegation D0 (P to a principal-held key T); its hash is the task's on-chain identity |
| `budget_minor` | `ERC20TransferAmountEnforcer(token, budget)` on D0 |
| `not_before`, `expires` | `TimestampEnforcer(not_before, expires)` on D0 |
| `counterparties[i]` | one leaf Di (T to the agent key) with `AllowedCalldataEnforcer(4, pad32(address))` |
| `cap_minor` | `ERC20TransferAmountEnforcer(token, cap)` on Di |
| `agent_key` | Di's delegate, an EOA, plus `RedeemerEnforcer([agent])` |
| `revocation` | `disableDelegation(D0)` by P; status is `disabledDelegations(hash(D0))` |
| `asset` | the token address in both amount enforcers |

Seams: `enableDelegation` can undo the revocation, so R5 holds only while nobody calls it; time is the block
timestamp, and the window's start is exclusive on chain where the object's is inclusive; the key is secp256k1,
not Ed25519; a payee has to be handed both [Di, D0] to check anything.

## Mapping onto a card-network agent token

Read from Visa Intelligent Commerce's public material and its public API specification (published through
Cybersource), 8 October 2026.

| Field | Construct | Status |
|---|---|---|
| `agent_key` | the agent-specific payment token | documented |
| `counterparties[i]` + `cap_minor` | one purchase instruction per purchase; in the public API spec its merchant is an optional preference ("User merchant preference.") and its amount a per-transaction maximum | a merchant list the cardholder sets on the token, or a running cap per merchant: could not verify |
| `budget_minor` | a budget across purchases on the agent token | could not verify (issuer-set transaction controls have period limits, but nothing public ties them to agent tokens) |
| `expires` | an expiry on each instruction | documented for the pilot |
| `revocation` | cancelling an instruction or the token | no merchant-side status check found; the merchant learns the state only from the authorization result |
| `task_id` | none found; the instruction is the nearest unit | could not verify |

The difference that matters: on chain the payee can read revocation and spend state itself; on the card rail it
learns them only through an authorization decision.
