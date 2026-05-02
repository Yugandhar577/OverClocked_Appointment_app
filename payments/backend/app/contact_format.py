"""Razorpay Standard Checkout expects `prefill.contact` in E.164 (+countrycode…)."""


def normalize_contact_e164(phone: str | None, default_country_code: str = "91") -> str:
    """
    Normalise a stored phone string to E.164. India-focused defaults for hackathon/demo data.
    See: https://razorpay.com/docs/payments/payment-gateway/web-integration/standard/integration-steps/
    """
    if not phone or not str(phone).strip():
        return f"+{default_country_code}9999999999"

    digits = "".join(c for c in str(phone) if c.isdigit())
    if not digits:
        return f"+{default_country_code}9999999999"

    if digits.startswith(default_country_code) and len(digits) >= 11:
        return f"+{digits}"

    if len(digits) == 10:
        return f"+{default_country_code}{digits}"

    if len(digits) > 10:
        tail = digits[-10:]
        return f"+{default_country_code}{tail}"

    return f"+{default_country_code}9999999999"
