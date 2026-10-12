# Who is your agent allowed to pay?

The matrix and the engine behind the article
[Who Is Your Agent Allowed to Pay?](https://laxsharma.com/writing/who-is-your-agent-allowed-to-pay/).

One errand, written as an instruction to the money: **pay only the people this task names, up to this task's
budget, until this task ends, and let me take it back in one step that anyone can check.** On 8 October 2026
that sentence was checked against 42 agent payment products and standards, using public documentation,
specifications and code only. Nothing was signed into or run, except the engine in this repository.

## What's here

| | |
|---|---|
| [MATRIX.md](MATRIX.md) | 42 rows by 13 dimensions, a verdict and its evidence for every cell, and the five-part test |
| [notes/](notes/) | the working notes for each group of products, with every source id and quote |
| [SOURCES.md](SOURCES.md) | every source the matrix cites: URL, fetch time, sha256 or commit |
| [TASK-ACCOUNT.md](TASK-ACCOUNT.md) | the sentence as one signed object, its six rules, and how it maps onto two rails |
| [engine/](engine/) | an offline reference engine for the object, its tests, and the article's afternoon replayed |

## The five parts, and how many of the 42 hold each

| Part | In full | Partly |
|---|---|---|
| (a) pay only the payees the task names | 16 | 11 |
| (b) a budget for the task | 17 | 10 |
| (c) authority that ends when the task ends, scored on an expiry set at the deadline | 20 | 3 |
| (d) revocation in one step that a payee or an auditor can verify | 10 | 5 |
| (e) a credential for this task, narrower than the agent's own key | 23 | 5 |

All ten that hold (d) in full are contracts on a public chain. Three hold all five parts, each on one chain:
MetaMask's Delegation Framework (by configuration), Rhinestone Smart Sessions (in beta) and Crossmint's wallet
signer scopes (confirmed in public code on Stellar; the EVM and Solana versions rest on the vendor's word).
Nothing in the 42 can hear that a task has finished, which is why (c) is scored on an expiry.

## Correct a row

Vendors move fast. If a product does better than its row says, open an issue with the
[correct a row](../../issues/new?template=correct-a-row.md) template and a link to where it is documented.
Corrections are made with a dated note in the row.

## Limits

Contract behaviour is read from code, not tested. "Not documented" means not found in the sources listed, not
proven absent. Pilot, beta and preview products are marked; cells that rest on a specification's text or on a
vendor's word alone are flagged; rows that could not be read are left blank. Every claim carries its fetch date
or commit.

## Licence

The code in [engine/](engine/) is under the [Apache License 2.0](LICENSE). The matrix, the notes, the sources list
and TASK-ACCOUNT.md are under [Creative Commons Attribution 4.0](LICENSE-CC-BY-4.0). Quotations from vendor
documentation remain their owners' and are quoted for review.

Laxmikant Sharma, [laxsharma.com](https://laxsharma.com)
