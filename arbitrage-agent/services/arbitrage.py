from typing import Optional
from datetime import datetime

from config import get_settings
from models.price import PricePoint, Marketplace
from models.opportunity import Opportunity


class ArbitrageService:
    """Service for calculating arbitrage opportunities."""

    def __init__(self):
        self.settings = get_settings()
        self.min_margin = self.settings.min_margin_threshold
        self.amazon_fee_pct = self.settings.amazon_seller_fee_pct

    def calculate_opportunity(
        self,
        product_id: str,
        product_name: str,
        amazon_price: PricePoint,
        bestbuy_price: PricePoint
    ) -> Optional[Opportunity]:
        """
        Calculate arbitrage opportunity between Amazon and Best Buy.

        The strategy is to buy from the cheaper marketplace and sell on the more expensive one.
        We account for Amazon seller fees when selling on Amazon.

        Args:
            product_id: Product ID
            product_name: Product name for display
            amazon_price: Latest Amazon price point
            bestbuy_price: Latest Best Buy price point

        Returns:
            Opportunity if profitable, None otherwise
        """
        if not amazon_price or not bestbuy_price:
            return None

        amazon_total = amazon_price.total_cost
        bestbuy_total = bestbuy_price.total_cost

        # Determine buy/sell direction
        if amazon_total < bestbuy_total:
            # Buy on Amazon, sell on Best Buy (rare - Best Buy doesn't have marketplace)
            buy_price = amazon_price
            sell_price = bestbuy_price
            estimated_fees = 0
        else:
            # Buy on Best Buy, sell on Amazon (more common scenario)
            buy_price = bestbuy_price
            sell_price = amazon_price
            # Amazon seller fees (approximately 15% of sale price)
            estimated_fees = sell_price.price * (self.amazon_fee_pct / 100)

        # Calculate profits
        gross_profit = sell_price.price - buy_price.total_cost
        net_profit = gross_profit - estimated_fees

        # Avoid division by zero
        if buy_price.total_cost <= 0:
            return None

        margin_pct = (net_profit / buy_price.total_cost) * 100

        # Only return if above minimum margin threshold
        if margin_pct < self.min_margin:
            return None

        # Calculate risk score (0-10, lower is better)
        risk_score, risk_factors = self._calculate_risk(
            buy_price, sell_price, margin_pct
        )

        return Opportunity(
            product_id=product_id,
            product_name=product_name,
            buy_marketplace=buy_price.marketplace,
            buy_price=buy_price.price,
            buy_shipping=buy_price.shipping,
            buy_url=buy_price.url,
            sell_marketplace=sell_price.marketplace,
            sell_price=sell_price.price,
            sell_url=sell_price.url,
            gross_profit=round(gross_profit, 2),
            estimated_fees=round(estimated_fees, 2),
            net_profit=round(net_profit, 2),
            margin_pct=round(margin_pct, 2),
            risk_score=risk_score,
            risk_factors=risk_factors,
            stock_status=buy_price.stock,
            last_updated=datetime.utcnow()
        )

    def _calculate_risk(
        self,
        buy_price: PricePoint,
        sell_price: PricePoint,
        margin_pct: float
    ) -> tuple[float, list[str]]:
        """
        Calculate risk score and identify risk factors.

        Args:
            buy_price: Buy side price point
            sell_price: Sell side price point
            margin_pct: Calculated profit margin

        Returns:
            Tuple of (risk_score, risk_factors)
        """
        risk_score = 5.0  # Start at medium risk
        risk_factors = []

        # Stock availability risk
        buy_stock_lower = buy_price.stock.lower() if buy_price.stock else ""
        if "out of stock" in buy_stock_lower or "unavailable" in buy_stock_lower:
            risk_score += 3.0
            risk_factors.append("Buy source out of stock")
        elif "low" in buy_stock_lower or "only" in buy_stock_lower:
            risk_score += 1.5
            risk_factors.append("Low stock at buy source")

        # Third-party seller risk (Amazon)
        if buy_price.seller and buy_price.seller.lower() != "amazon.com":
            risk_score += 1.0
            risk_factors.append("Third-party seller")

        # Very high margin might indicate data error
        if margin_pct > 50:
            risk_score += 2.0
            risk_factors.append("Unusually high margin - verify prices")

        # Very low margin has less room for error
        if margin_pct < 10:
            risk_score += 1.0
            risk_factors.append("Thin margin - price sensitive")

        # Shipping cost risk
        if buy_price.shipping > 0:
            risk_score += 0.5
            risk_factors.append("Shipping costs reduce margin")

        # Cap risk score at 10
        risk_score = min(10.0, max(0.0, risk_score))

        return round(risk_score, 1), risk_factors

    def filter_opportunities(
        self,
        opportunities: list[Opportunity],
        min_margin: Optional[float] = None,
        max_risk: Optional[float] = None
    ) -> list[Opportunity]:
        """
        Filter opportunities by margin and risk thresholds.

        Args:
            opportunities: List of opportunities to filter
            min_margin: Minimum margin percentage (uses config default if None)
            max_risk: Maximum risk score (no limit if None)

        Returns:
            Filtered list of opportunities
        """
        if min_margin is None:
            min_margin = self.min_margin

        filtered = [
            opp for opp in opportunities
            if opp.margin_pct >= min_margin
        ]

        if max_risk is not None:
            filtered = [
                opp for opp in filtered
                if opp.risk_score <= max_risk
            ]

        # Sort by margin percentage (highest first)
        filtered.sort(key=lambda x: x.margin_pct, reverse=True)

        return filtered
