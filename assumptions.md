# Data assumptions

These are the decisions I made about the Olist data, and the reasons. The full output is in [docs/data_profile.md](docs/data_profile.md).

## What's in the data

- The orders span 2016-09-04 to 2018-10-17. The year 2016 is sparse, and September and October 2018 are partial, so a comparison that includes those periods can mislead. The agent says so when a query touches them.
- There are 99,441 orders. 775 of them have no item rows, so item revenue doesn't cover every order.
- Item prices total BRL 13,591,643.70, while payments total BRL 16,008,872.12. They measure different things (payments include freight and installment effects), so the two aren't expected to match.

## How I defined the metrics

- **Revenue** is the sum of item `price`. Freight is excluded, and answers say so.
- **Orders** are counted as distinct `order_id`.
- **Customers** are counted as distinct `customer_unique_id`. There are 96,096 of those behind 99,441 `customer_id` values, because `customer_id` is issued per order.
- **Order status** is never filtered unless the user asks. "Delivered" means `order_status = 'delivered'`.
- **Dates** use the purchase timestamp unless the question names another event, such as delivery.
- **"Latest" and "last quarter"** are measured from the newest purchase date in the database.

## Quirks I handle

- **Join fan-out.** Items and payments are both one-to-many from orders. Joining both to an order multiplies rows and inflates sums. The prompt tells the model to aggregate each child table separately before combining them.
- **Missing category translations.** 13 product categories have no English name. The agent uses a `LEFT JOIN` to the translation table and falls back to the Portuguese name, so those products stay in the results.
- **Duplicate review IDs.** `order_reviews.review_id` isn't unique, so I don't treat it as a row key. Multi-item orders also repeat the same review across items, which can distort category averages. This is the one known failure in the evaluation.

## What I left out

- The geolocation file (about a million rows). Customers and sellers already carry city and state, which is all the questions need.
- The text of the Portuguese review comments. Only the numeric score is used.
- Product dimension and photo columns, and zip-code prefixes, are hidden from the prompt to keep it short. They remain in the database.