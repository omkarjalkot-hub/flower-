"""Small display helpers."""


def money(value) -> str:
    """Format a number as Indian rupees, e.g. 1299 -> ₹1,299."""
    try:
        value = float(value)
    except (TypeError, ValueError):
        return "₹0"
    if value == int(value):
        return f"₹{int(value):,}"
    return f"₹{value:,.2f}"


def fmt_time(ts) -> str:
    """Show a stored UTC timestamp in Indian Standard Time, e.g. 21 Oct 2026, 5:02 PM."""
    from datetime import datetime, timedelta
    try:
        dt = datetime.strptime(str(ts)[:19], "%Y-%m-%d %H:%M:%S") + timedelta(hours=5, minutes=30)
    except ValueError:
        return str(ts or "")
    return dt.strftime("%d %b %Y, %I:%M %p").lstrip("0")
