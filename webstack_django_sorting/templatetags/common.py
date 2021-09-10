"""
Common to Django tags (sorting_tags) and Jinja2 globals (jinja2_globals)
"""
from operator import attrgetter

from .settings import SORT_DIRECTIONS


def render_sort_anchor(request, field_name, title, default_sort=None):
    get_params = request.GET.copy()
    sort_by = get_params.get("sort", None)
    # This if statement is part of the default_sort_field kludge add by JMR.
    # Sets the sortby variable to the field specified in the `default_sort_field` context variable
    # but only if this is the primary page, without `sort` or `dir` GET parameters.
    if sort_by == None and default_sort:
        sort_by = default_sort.replace('-','')

    if sort_by == field_name:
        # This if is part of the default_sort_field kludge add by JMR. The else is the original code.
        # Sets the sortdir variable based on presence/absence of hyphen in the `default_sort_field` context variable
        # but only if this is the primary page, without `sort` or `dir` GET parameters.
        if get_params.get('dir') == None and default_sort:
            if default_sort[0] == '-':
                current_direction = SORT_DIRECTIONS['desc']
            else:
                current_direction = SORT_DIRECTIONS['asc']
            icon = current_direction["icon"]
            next_direction_code = current_direction["next"]
        else:
            # Render anchor link to next direction
            current_direction = SORT_DIRECTIONS[get_params.get("dir", "")]
            icon = current_direction["icon"]
            next_direction_code = current_direction["next"]
    else:
        icon = ""
        next_direction_code = "asc"

    # Not usual dict (can't update to replace)
    get_params["sort"] = field_name
    get_params["dir"] = next_direction_code
    url_append = "?" + get_params.urlencode() if get_params else ""
    return f'<a href="{request.path}{url_append}" title="{title}" class="sort-column">{title}{icon}</a>'


def get_order_by_from_request(request):
    """
    Retrieve field used for sorting a queryset

    :param request: HTTP request
    :return: the sorted field name, prefixed with "-" if ordering is descending
    """
    sort_direction = request.GET.get("dir")
    field_name = (request.GET.get("sort") or "") if sort_direction else ""
    sort_sign = "-" if sort_direction == "desc" else ""
    return f"{sort_sign}{field_name}"


def need_python_sorting(queryset, order_by):
    if order_by.find("__") >= 0:
        # Python can't sort order_by with '__'
        return False

    # Python sorting if not a DB field
    field = order_by[1:] if order_by[0] == "-" else order_by
    field_names = [f.name for f in queryset.model._meta.get_fields()]
    return field not in field_names


def sort_queryset(queryset, order_by):
    """order_by is an Django ORM order_by argument"""
    if not order_by:
        return queryset

    if need_python_sorting(queryset, order_by):
        # Fallback on pure Python sorting (much slower on large data)

        # The field name can be prefixed by the minus sign and we need to
        # extract this information if we want to sort on simple object
        # attributes (non-model fields)
        if order_by[0] == "-":
            if len(order_by) == 1:
                # Prefix without field name
                raise ValueError

            reverse = True
            name = order_by[1:]
        else:
            reverse = False
            name = order_by
        if hasattr(queryset[0], name):
            return sorted(queryset, key=attrgetter(name), reverse=reverse)
        else:
            raise AttributeError
    else:
        return queryset.order_by(order_by)
