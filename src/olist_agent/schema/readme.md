# schema

`column_descriptions.yaml` is a hand-written data dictionary, because Kaggle doesn't publish one. It's the only place where meaning is attached to the tables and columns, and `prompts/__init__.py` reads it to build the schema section of the prompt.

## Structure

- `tables:` one entry per table, with a short `description` and a `columns` map from column name to a one-line explanation (what it holds, the unit, whether it is nullable, what it joins to).
- `global:` things that apply everywhere: the currency and timestamp format (`units`), and the key relationships between tables (`relationships`), such as orders to items by `order_id` and orders to customers by `customer_id`.

## Why it matters

The database knows column names and types but not their meaning. A model that sees `price` and `payment_value` needs to be told that one is an item price and the other a payment amount, and that the two differ. Clear descriptions here reduce wrong guesses more than any prompt wording does.
