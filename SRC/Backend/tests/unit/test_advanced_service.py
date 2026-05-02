from SRC.Backend.services.advanced_service import DEFAULT_THEME, feature_flags


def test_feature_flags_include_all_advanced_modules():
    flags = feature_flags()

    assert flags["ENABLE_WAITLIST"] is False
    assert flags["ENABLE_BOOKING_CART"] is False
    assert flags["ENABLE_VARIABLE_DURATION"] is False
    assert flags["ENABLE_RECURRING_BOOKINGS"] is False
    assert flags["ENABLE_NO_SHOW_PROTECTION"] is False
    assert flags["ENABLE_SMART_ASSIGNMENT"] is False
    assert flags["ENABLE_DYNAMIC_PRICING"] is False
    assert flags["ENABLE_NOTIFICATION_WORKFLOWS"] is False
    assert flags["ENABLE_ADMIN_MANUAL_BOOKING"] is False
    assert flags["ENABLE_APPOINTMENT_ANALYTICS"] is False
    assert flags["ENABLE_THEME_CUSTOMIZATION"] is False
    assert flags["ENABLE_ODOO_STYLE_UI"] is False


def test_default_theme_has_required_odoo_tokens():
    for key in [
        "primaryColor",
        "secondaryColor",
        "accentColor",
        "backgroundColor",
        "cardColor",
        "borderColor",
        "successColor",
        "warningColor",
        "errorColor",
        "sidebarColor",
        "headerColor",
        "buttonStyle",
        "roundedness",
        "mode",
    ]:
        assert DEFAULT_THEME[key]
