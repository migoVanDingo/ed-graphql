import strawberry

from app.graphql.dashboard.query import DashboardQuery
from app.graphql.dashboard.subscription import Subscription as DashboardSubscription

# from app.graphql.dashboard.scalars import BigInt   # if you ever scalar-override

# Example: another feature module
# from app.graphql.reports.query import ReportsQuery
# from app.graphql.reports.subscription import ReportsSubscription
# from app.graphql.reports.mutation import ReportsMutation


# ─────────────────────────────────────────
# Root Query
# ─────────────────────────────────────────


@strawberry.type
class Query(
    DashboardQuery,
    # ReportsQuery,
    # ... add more feature query mixins here
):
    """
    Root Query type, composed from feature-specific query mixins.
    """

    pass


# ─────────────────────────────────────────
# Root Mutation
# ─────────────────────────────────────────


@strawberry.type
class Mutation(
    # ReportsMutation,
    # OtherFeatureMutation,
):
    """
    Root Mutation type.

    For now, if you don't have dashboard mutations, you can leave Dashboard out.
    """

    pass


# ─────────────────────────────────────────
# Root Subscription
# ─────────────────────────────────────────


@strawberry.type
class Subscription(
    DashboardSubscription,
    # ReportsSubscription,
    # OtherFeatureSubscription,
):
    """
    Root Subscription type, composed from feature-specific subscriptions.
    """

    pass


schema = strawberry.Schema(
    query=Query,
    mutation=Mutation,
    subscription=Subscription,
    # If you needed scalar overrides, you'd add them here.
    # scalar_overrides={int: BigInt}  # Only if you decide to map this globally.
)
