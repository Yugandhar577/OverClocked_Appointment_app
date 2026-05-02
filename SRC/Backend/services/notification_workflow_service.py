from string import Template


class MissingTemplateValueError(ValueError):
    pass


def render_template(template: str, values: dict[str, object]) -> str:
    try:
        return Template(template).substitute({key: "" if value is None else str(value) for key, value in values.items()})
    except KeyError as exc:
        raise MissingTemplateValueError(str(exc)) from exc


def channel_payload(channel: str, *, recipient: str, subject: str | None, body: str) -> dict[str, str | None]:
    if channel not in {"email", "sms", "whatsapp"}:
        raise ValueError("unsupported notification channel")
    return {"channel": channel, "recipient": recipient, "subject": subject, "body": body}
