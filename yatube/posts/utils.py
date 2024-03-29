from django.core.paginator import Paginator


def paginator(request, post_list):
    count_page_objects = 10
    paginator = Paginator(post_list, count_page_objects)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)
    return page_obj
