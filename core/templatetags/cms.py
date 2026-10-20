from django import template

from accounts.permissions import user_can

register = template.Library()


@register.filter(name="can")
def can(user, capability):
    return user_can(user, capability)


@register.simple_tag(takes_context=True)
def querystring(context, **kwargs):
    """Return the current query string with the provided values replaced."""
    request = context.get("request")
    if request is None:
        return ""
    params = request.GET.copy()
    for key, value in kwargs.items():
        if value is None or value == "":
            params.pop(key, None)
        else:
            params[key] = value
    return params.urlencode()
