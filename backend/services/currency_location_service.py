"""
Currency and Location Service.

Handles automatic currency detection, conversion rates,
and location-based pricing for the wellness platform.
"""

import os
import requests
from typing import Dict, Optional, Tuple
from datetime import datetime, timedelta
from dataclasses import dataclass
import json
from pathlib import Path
from functools import lru_cache


@dataclass
class CurrencyInfo:
    """Currency information."""
    code: str  # USD, INR, EUR, etc.
    symbol: str  # $, ₹, €, etc.
    name: str
    conversion_to_usd: float


@dataclass
class LocationInfo:
    """User location information."""
    country: str
    country_code: str  # US, IN, etc.
    region: str  # State/Province
    city: str
    timezone: str
    currency: CurrencyInfo
    latitude: Optional[float] = None
    longitude: Optional[float] = None


class CurrencyLocationService:
    """Service for handling currency and location."""

    # Currency data
    CURRENCIES = {
        "USD": CurrencyInfo("USD", "$", "US Dollar", 1.0),
        "INR": CurrencyInfo("INR", "₹", "Indian Rupee", 0.012),  # 1 INR = 0.012 USD
        "EUR": CurrencyInfo("EUR", "€", "Euro", 1.09),
        "GBP": CurrencyInfo("GBP", "£", "Pound Sterling", 1.27),
        "AUD": CurrencyInfo("AUD", "A$", "Australian Dollar", 0.66),
        "CAD": CurrencyInfo("CAD", "C$", "Canadian Dollar", 0.74),
    }

    # Country to currency mapping
    COUNTRY_CURRENCY = {
        "US": "USD",
        "IN": "INR",
        "GB": "GBP",
        "EU": "EUR",
        "AU": "AUD",
        "CA": "CAD",
        # Add more as needed
    }

    # Regional cost multipliers (relative to US baseline)
    COST_MULTIPLIERS = {
        "US": {
            "california": 1.3,
            "new_york": 1.35,
            "texas": 1.0,
            "florida": 1.05,
            "default": 1.1
        },
        "IN": {
            "mumbai": 0.35,
            "delhi": 0.33,
            "bangalore": 0.32,
            "chennai": 0.28,
            "pune": 0.30,
            "default": 0.25
        },
        # Add more countries/regions
    }

    def __init__(self, cache_dir: str = "data/cache"):
        """Initialize currency service."""
        self.cache_dir = Path(cache_dir)
        self.cache_dir.mkdir(parents=True, exist_ok=True)
        self.exchange_rates_cache = self.cache_dir / "exchange_rates.json"
        self.exchange_rates = self._load_exchange_rates()

    def _load_exchange_rates(self) -> Dict[str, float]:
        """Load cached exchange rates or fetch new ones."""
        # Check cache
        if self.exchange_rates_cache.exists():
            with open(self.exchange_rates_cache, 'r') as f:
                data = json.load(f)
                cache_time = datetime.fromisoformat(data['timestamp'])

                # Cache valid for 24 hours
                if datetime.now() - cache_time < timedelta(hours=24):
                    return data['rates']

        # Fetch new rates
        return self._fetch_exchange_rates()

    def _fetch_exchange_rates(self) -> Dict[str, float]:
        """Fetch live exchange rates from API."""
        try:
            # Using exchangerate-api.com (free tier)
            api_key = os.getenv("EXCHANGE_RATE_API_KEY", "demo")
            url = f"https://v6.exchangerate-api.com/v6/{api_key}/latest/USD"

            response = requests.get(url, timeout=5)

            if response.status_code == 200:
                data = response.json()
                rates = data.get('conversion_rates', {})

                # Cache the rates
                cache_data = {
                    'timestamp': datetime.now().isoformat(),
                    'rates': rates
                }
                with open(self.exchange_rates_cache, 'w') as f:
                    json.dump(cache_data, f)

                return rates
            else:
                # Fallback to hardcoded rates
                return self._get_fallback_rates()

        except Exception as e:
            print(f"Error fetching exchange rates: {e}")
            return self._get_fallback_rates()

    def _get_fallback_rates(self) -> Dict[str, float]:
        """Fallback exchange rates (updated periodically)."""
        return {
            "USD": 1.0,
            "INR": 83.12,
            "EUR": 0.92,
            "GBP": 0.79,
            "AUD": 1.52,
            "CAD": 1.36,
            "JPY": 149.50,
            "CNY": 7.24,
        }

    def detect_location_from_ip(self, ip_address: Optional[str] = None) -> LocationInfo:
        """
        Detect user location from IP address.

        Args:
            ip_address: IP address (None for automatic detection)

        Returns:
            LocationInfo object
        """
        try:
            # Using ipapi.co (free tier: 1000 requests/day)
            if ip_address:
                url = f"https://ipapi.co/{ip_address}/json/"
            else:
                url = "https://ipapi.co/json/"

            response = requests.get(url, timeout=5)

            if response.status_code == 200:
                data = response.json()

                country_code = data.get('country_code', 'US')
                currency_code = self.COUNTRY_CURRENCY.get(country_code, 'USD')

                return LocationInfo(
                    country=data.get('country_name', 'United States'),
                    country_code=country_code,
                    region=data.get('region', ''),
                    city=data.get('city', ''),
                    timezone=data.get('timezone', 'UTC'),
                    currency=self.CURRENCIES.get(currency_code, self.CURRENCIES['USD']),
                    latitude=data.get('latitude'),
                    longitude=data.get('longitude')
                )
            else:
                return self._get_default_location()

        except Exception as e:
            print(f"Error detecting location: {e}")
            return self._get_default_location()

    def _get_default_location(self) -> LocationInfo:
        """Default location (US)."""
        return LocationInfo(
            country="United States",
            country_code="US",
            region="California",
            city="San Francisco",
            timezone="America/Los_Angeles",
            currency=self.CURRENCIES['USD']
        )

    def convert_currency(
        self,
        amount: float,
        from_currency: str,
        to_currency: str
    ) -> float:
        """
        Convert amount between currencies.

        Args:
            amount: Amount to convert
            from_currency: Source currency code (USD, INR, etc.)
            to_currency: Target currency code

        Returns:
            Converted amount
        """
        if from_currency == to_currency:
            return amount

        # Convert to USD first if needed
        if from_currency != "USD":
            rate_from = self.exchange_rates.get(from_currency, 1.0)
            amount_usd = amount / rate_from
        else:
            amount_usd = amount

        # Convert from USD to target currency
        if to_currency != "USD":
            rate_to = self.exchange_rates.get(to_currency, 1.0)
            return amount_usd * rate_to
        else:
            return amount_usd

    def format_currency(
        self,
        amount: float,
        currency_code: str,
        show_symbol: bool = True
    ) -> str:
        """
        Format amount with currency symbol.

        Args:
            amount: Amount to format
            currency_code: Currency code
            show_symbol: Whether to show currency symbol

        Returns:
            Formatted string (e.g., "$50.00" or "₹4,150")
        """
        currency = self.CURRENCIES.get(currency_code, self.CURRENCIES['USD'])

        # Format based on currency
        if currency_code == "INR":
            # Indian numbering system (lakhs, crores)
            formatted = f"{amount:,.2f}"
            if show_symbol:
                return f"{currency.symbol}{formatted}"
            return formatted
        else:
            # Western numbering system
            formatted = f"{amount:,.2f}"
            if show_symbol:
                return f"{currency.symbol}{formatted}"
            return formatted

    def get_regional_cost_multiplier(
        self,
        country_code: str,
        region: Optional[str] = None
    ) -> float:
        """
        Get cost multiplier for region.

        This adjusts food costs based on local market prices.

        Args:
            country_code: Country code (US, IN, etc.)
            region: Region/state (optional)

        Returns:
            Cost multiplier (1.0 = US baseline)
        """
        country_multipliers = self.COST_MULTIPLIERS.get(
            country_code,
            {"default": 1.0}
        )

        if region:
            region_lower = region.lower().replace(" ", "_")
            return country_multipliers.get(region_lower, country_multipliers.get("default", 1.0))

        return country_multipliers.get("default", 1.0)

    def calculate_local_food_cost(
        self,
        base_cost_usd: float,
        location: LocationInfo
    ) -> Tuple[float, str]:
        """
        Calculate local food cost based on location.

        Args:
            base_cost_usd: Base cost in USD
            location: User location

        Returns:
            (local_cost, formatted_string)
        """
        # Apply regional multiplier
        multiplier = self.get_regional_cost_multiplier(
            location.country_code,
            location.region
        )
        adjusted_usd = base_cost_usd * multiplier

        # Convert to local currency
        local_amount = self.convert_currency(
            adjusted_usd,
            "USD",
            location.currency.code
        )

        # Format
        formatted = self.format_currency(
            local_amount,
            location.currency.code
        )

        return local_amount, formatted

    @lru_cache(maxsize=128)
    def get_timezone_info(self, timezone: str) -> Dict:
        """Get timezone information."""
        from datetime import datetime
        import pytz

        try:
            tz = pytz.timezone(timezone)
            now = datetime.now(tz)

            return {
                "timezone": timezone,
                "current_time": now.isoformat(),
                "utc_offset": now.strftime('%z'),
                "dst_active": bool(now.dst())
            }
        except Exception:
            return {
                "timezone": "UTC",
                "current_time": datetime.utcnow().isoformat(),
                "utc_offset": "+0000",
                "dst_active": False
            }


# Singleton instance
_currency_service = None

def get_currency_service() -> CurrencyLocationService:
    """Get singleton currency service."""
    global _currency_service
    if _currency_service is None:
        _currency_service = CurrencyLocationService()
    return _currency_service


# Example usage
if __name__ == "__main__":
    service = CurrencyLocationService()

    # Detect location
    print("=== Location Detection ===")
    location = service.detect_location_from_ip()
    print(f"Detected Location: {location.city}, {location.region}, {location.country}")
    print(f"Currency: {location.currency.symbol} ({location.currency.code})")
    print(f"Timezone: {location.timezone}")

    # Currency conversion
    print("\n=== Currency Conversion ===")
    amount_usd = 100
    amount_inr = service.convert_currency(amount_usd, "USD", "INR")
    print(f"${amount_usd} USD = {service.format_currency(amount_inr, 'INR')}")

    # Local food cost
    print("\n=== Local Food Cost ===")
    base_meal_cost = 12.50  # USD baseline
    local_cost, formatted = service.calculate_local_food_cost(base_meal_cost, location)
    print(f"Base cost: ${base_meal_cost}")
    print(f"Local cost: {formatted}")

    # Regional multiplier
    print("\n=== Regional Cost Multipliers ===")
    print(f"US - California: {service.get_regional_cost_multiplier('US', 'California')}")
    print(f"IN - Mumbai: {service.get_regional_cost_multiplier('IN', 'Mumbai')}")
    print(f"IN - Bangalore: {service.get_regional_cost_multiplier('IN', 'Bangalore')}")
