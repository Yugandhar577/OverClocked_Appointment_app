def normalize_contact_e164(phone: str | None, default_country_code: str = "91") -> str:
    if not phone or not str(phone).strip():
        return f"+{default_country_code}9999999999"

    digits = "".join(char for char in str(phone) if char.isdigit())
    if not digits:
        return f"+{default_country_code}9999999999"
    if digits.startswith(default_country_code) and len(digits) >= 11:
        return f"+{digits}"
    if len(digits) == 10:
        return f"+{default_country_code}{digits}"
    if len(digits) > 10:
        return f"+{default_country_code}{digits[-10:]}"
    return f"+{default_country_code}9999999999"
