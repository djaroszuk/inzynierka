from django import template


register = template.Library()


@register.simple_tag
def update_query(request, **kwargs):
    """
    Update query parameters while preserving the existing ones.
    Exclude any parameter by passing `None` as its value.
    """
    query = request.GET.copy()
    for key, value in kwargs.items():
        if value is None:
            query.pop(key, None)  # Remove the parameter if its value is None
        else:
            query[key] = value  # Update or add the parameter
    return query.urlencode()
