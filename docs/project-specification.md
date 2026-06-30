# Project specification

## Proposed title

**Scalable Real-Time E-Commerce Product-Trend and Funnel-Abandonment Analytics Using an AWS Lambda Architecture**

## Problem

An e-commerce operator cannot act on historical reports alone. It needs to know which products are receiving exceptional attention now, whether interest becomes purchases, and whether the analytics system remains responsive during traffic spikes.

## Primary real-time question

**Which products have unusually high customer activity during the latest five-minute sliding window, and is the larger funnel drop-off currently view-to-cart or cart-to-purchase?**

## Users and decisions

| User | Information supplied | Possible decision |
|---|---|---|
| Marketing | Unusually trending products | Promote or feature a product |
| Inventory team | Sudden view/cart/purchase growth | Check or replenish stock |
| Product/UX team | Current funnel drop-off | Investigate product or payment experience |
| Platform operations | Throughput, latency and stream backlog | Scale processing capacity |

The project provides decision support; it does not automatically contact customers or change prices.

## Operational definitions

### Product activity

For product `p` during the latest five minutes:

```text
trend_score(p) = views(p) + 3 * carts(p) + 5 * purchases(p)
activity_lift(p) = current_trend_score(p) / historical_average_5m_trend_score(p)
```

The first prototype labels a product **unusually trending** when its activity lift is at least 2.0. The threshold will be sensitivity-tested before the report is finalised.

### Funnel drop-off

Within the current window:

```text
view_to_cart_dropoff = 1 - unique_cart_sessions / unique_view_sessions
cart_to_purchase_dropoff = 1 - unique_purchase_sessions / unique_cart_sessions
```

These are operational window indicators, not proof that a particular customer permanently abandoned a purchase. A separate cart signal is emitted when a session adds a product to its cart and has neither purchased nor removed that product after 15 replay-clock minutes.

### Active session

A session with at least one event inside the current five-minute window.

## Why Lambda architecture is justified

- A stream-only system can report recent counts but lacks an accurate, recomputable historical baseline.
- A batch-only system produces correct historical views but cannot identify a traffic spike while it is happening.
- The batch layer supplies complete averages and conversion context; the speed layer supplies low-latency recent activity; the serving layer combines them as activity lift and current funnel drop-off.

## Dataset

The selected source is the public REES46 multi-category e-commerce behaviour dataset. Its useful fields are:

| Source field | Use |
|---|---|
| `event_time` | Source event ordering and batch windows |
| `event_type` | View, cart, removal, or purchase |
| `product_id` | Product-level aggregation |
| `category_id`, `category_code`, `brand` | Optional dashboard grouping |
| `price` | Optional revenue aggregation |
| `user_id`, `user_session` | Distinct sessions and funnel transitions |

Historical timestamps are preserved as `source_event_time`. The producer assigns a new replay-clock `event_time`, allowing the speed layer and latency measurements to behave like a live system.

## Minimum outputs

1. Top five products by recent trend score.
2. Current activity lift against the batch baseline.
3. View-to-cart and cart-to-purchase drop-off.
4. Delayed cart-abandonment signals.
5. Ingestion throughput, end-to-end latency, Kinesis backlog, and batch duration.
6. Speedup and efficiency for different Spark worker counts.

## Success criteria

- Process at least three controlled ingestion rates without record loss.
- Produce an updated speed view no more than one minute after its window closes.
- Show that parallel Spark execution improves over a one-worker baseline for a sufficiently large input.
- Demonstrate EMR scaling or another approved auto-scaling policy under load.
- Explain bottlenecks and non-linear speedup rather than reporting graphs without analysis.

## Scope exclusions

- No claim of checkout-page abandonment because the dataset has no checkout-start event.
- No personal identification; source user/session identifiers are anonymised.
- No machine-learning recommender is required for the assessment.
- No automatic marketing intervention or customer messaging.
