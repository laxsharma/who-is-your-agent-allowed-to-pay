# notes/

Working notes for each group of products, one file per group. Each cell carries a verdict, the evidence,
and a source id resolved in that file's source list. MATRIX.md is assembled from these files.

Verdict codes
- N    native: the product enforces it through a documented built-in field, rule type, parameter or setting.
- C    by configuration: enforced by the product, but only by composing several built-in controls, or by a
       setting that lives outside the agent's credential and cannot be scoped to it.
- CODE only by writing code: the product offers a hook (custom contract, custom caveat enforcer, webhook,
       authorization callback) and the principal must write and run the logic.
- X    not possible: the documentation, spec or code shows the design excludes it.
- ND   not documented, or could not verify from public sources.

Citations name the saved copy of each page (`raw/<host>/...`) or repository (`raw/<project>/...`). The copies are
not published; [SOURCES.md](../SOURCES.md) lists each one's URL, fetch time UTC and sha256 or commit.
