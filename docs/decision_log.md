# Decision log

Each entry is a problem I found by running the agent, the evidence, and the general fix I made. I fixed problems with prompt rules, the guard, or the evaluation harness, and never by adding an evaluation question to a prompt. Timings are from a CPU-only laptop.

## Speed

| Problem | Evidence | Fix | Result |
|---|---|---|---|
| One question took about 220 s. | Three model calls per question (route, SQL, summary). The first two each spent about 90 to 100 s reading a ~3,500-token prompt (prefill 88.4 s and 101.1 s); generation was only 6 to 8 s. | Merged routing and SQL into one `plan` call. Put the schema first and the question last so Ollama can reuse its cache. Hid unused columns and tables to shrink the prompt to about 1,800 tokens. Made the summary deterministic by default. | Warm single-turn questions take 10 to 20 s, with prefill of 1 to 3 s. The full evaluation went from 1,251 s to 759 s. |
| Questions that needed a repair took 280 to 390 s. | The repair prompt had different wording at the start, so it evicted the cache: repair prefill 74 to 88 s, then the next plan call 113 to 129 s. | Repair now reuses the `plan` prompt, with the error appended at the end. | Repair prefill dropped to 0.2 to 31 s. |
| Thinking mode would add minutes of hidden reasoning. | `ollama run qwen3:8b` printed a long reasoning trace for a two-word reply. | `reasoning=False`, set only for models that support it. | Generation takes 6 to 10 s per call. |

## Query quality

| Problem | Evidence | Fix | Result |
|---|---|---|---|
| Inner join to the category translation table dropped products with no English name. | `revenue_category` and `category_review_scores` failed in the baseline; the SQL used `JOIN` on the translation table. | Prompt rule and example: `LEFT JOIN` lookup tables and `COALESCE` to the original label. | `revenue_category` passes. |
| "Top 5 categories", then "break that down by state" applied `LIMIT 5` to category and state rows. | `categories_then_state` returned five rows. | Prompt rule and example: pick the top N in a CTE first, then break those down. | Still fails. The model now builds a CTE but joins it on a column it doesn't have; after two repairs the agent reports the SQLite error and the SQL instead of guessing. Left as a known limit. |
| "Compare with 2018" replaced 2017 instead of showing both. | `compare_with_2018` and `full_followup_chain` failed. | Prompt rule: show both periods side by side. | Both pass. |
| The agent added a status filter nobody asked for. | Seen once with `WHERE order_status = 'delivered'` on a malformed question. | Prompt rule: add only the filters the user asked for. | `yearly_revenue` passes with no filter. |
| Review scores are averaged per item row, not per order. | `category_review_scores` fails with the right joins; multi-item orders count several times. | None yet. The reference query averages per order first. | Known limitation. A small view that reduces reviews to one score per order is the likely fix. |

## Conversation behavior

| Problem | Evidence | Fix | Result |
|---|---|---|---|
| A shell command typed into the chat was answered as a revenue question. | The agent returned yearly revenue for the text of a PowerShell command. | Refuse input that isn't a question, and add `refuse_not_a_question` to the evaluation. | Passes. |
| The new refusal rule over-fired. | `add_delivered_filter` ("Only delivered orders.") and `refuse_profit` both returned `clarify`. | Short follow-up fragments are valid when there is prior context. A missing metric is a refuse, never a clarify. | Both pass in a rerun. |
| A failed attempt overwrote the saved query that follow-ups build on. | Found in code review. | The saved query is updated only after a query succeeds; unit test added. | Passes. |

## Evaluation harness

| Problem | Fix |
|---|---|
| Result comparison required identical column counts and names. | Compare column by column on values, so aliases and extra columns are fine. |
| Reference SQL used Portuguese category names while the agent returns English ones, and it ignored "top 5". | Rewrote the reference queries to match the question and the translation rule. |
| The runner checked required SQL terms before checking that rows came back, which hid real errors. | Check for rows first and report the agent's error. |
| Results were written only at the end, and an untagged run overwrote the baseline. | Save after every case, and default the tag to a timestamp. |

## Scores

| Run | Score | Held out | Time |
|---|---|---|---|
| Baseline | 17/22 | 4/5 | 1,251 s |
| Final Run | 19/23 | 5/5 | 759 s |

The held-out cases are not fully clean: I read the baseline failures before writing the later rules.