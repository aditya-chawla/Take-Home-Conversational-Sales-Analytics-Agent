# Design

## Architecture

```text
Rich REPL -> LangGraph (rewrite -> route -> clarify/refuse OR generate -> validate -> execute -> summarize)
                       | per-thread structured state + last three Q/A turns
                       + SQLite read-only database <- CSV build/profile pipeline
Local ChatOllama (qwen3:8b, temperature 0, thinking disabled)     sqlglot guard
```

The graph is explicit: routing, SQL generation, validation, execution, repair, and summarization are separate nodes with bounded transitions. This avoids relying on free-form tool selection by an 8B model. LangGraph provides the state machine and a `MemorySaver` checkpointer; a session thread retains prior turns and structured query context. The rewriter resolves follow-ups into standalone questions before routing and generation.

## Data decisions

The builder excludes geolocation (customer and seller tables already include city/state), retains review scores while ignoring comment text in prompts, writes timestamps as ISO strings, and indexes common joins and dates. `price` alone defines revenue; freight is excluded. Orders mean distinct order IDs, customers mean distinct `customer_unique_id`, and no order-status filter is applied unless requested. The latest-period anchor is the maximum purchase timestamp in the actual database. Dataset quirks and assumptions belong in `assumptions.md` and the generated data profile.

The deliberate simplification is local CSV-to-SQLite rather than a remote warehouse. SQLite is opened with URI `mode=ro`; `sqlglot` validates a single read-only query against an explicit table allowlist, and missing limits are injected.

## Guardrails and conversation behavior

Routing must choose answer, clarify, or refuse. A sensible default is stated rather than asking a needless question; genuine competing interpretations trigger one concise clarifying question. Missing metrics/columns, unsupported periods, and off-topic questions are refused. At most two SQL repair attempts follow a validation/execution failure or empty result. The response displays the result table, query, row count, and assumptions. Narrative claims are constrained to returned rows and checked against result values.

The state stores the last query's SQL, metric, grouping, filters, and period, plus three recent Q/A pairs. Follow-ups reuse those constraints where relevant. `/reset` starts a new thread.

## Evaluation and limitations

`evals/questions.yaml` contains multi-turn, aggregation, ambiguity, refusal, and join-fan-out cases. The runner compares answerable query results against reference SQL with float tolerance and checks routing actions for clarify/refuse. The baseline and post-fix reports must be produced on the actual downloaded dataset and local model; no data or model is bundled, so this repository does not claim fabricated benchmark numbers.

Known limitations: natural-language routing and SQL remain model-dependent; SQLite does not provide row-level user permissions; customer identity and profit are not present; only queryable schema columns can be used. Next steps include a repeatable dataset checksum, richer adversarial SQL tests, and a manually audited held-out evaluation.

## AI tools and effort

Implementation assistance used an AI coding assistant; the resulting code was checked with local tests. Time spent was not independently tracked.
