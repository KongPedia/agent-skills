# Context map
- Ordering: [ordering glossary](docs/ordering-glossary.md), owns order fulfilment and cancellation.
- Billing: [billing glossary](docs/billing-glossary.md), owns captured money and refunds.
- checkout.py coordinates both contexts; neither context imports checkout or the other context.
- See CONTRACT.md for the existing public behavior and supported failure policy.
