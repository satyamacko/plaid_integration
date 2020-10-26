from django.conf import settings
from django.core.paginator import Paginator
from rest_framework.pagination import PageNumberPagination
from rest_framework.utils.urls import replace_query_param, remove_query_param


class PaginationMixin(PageNumberPagination):
    page = None
    result_count = None

    def paginate(self, queryset, current_page_number):
        paginator = Paginator(queryset, 20)
        if current_page_number > paginator.num_pages:
            raise Exception(f"Invalid page, {paginator.num_pages} pages are there.")
        self.page = paginator.page(current_page_number)
        self.result_count = paginator.count

    def get_next_link(self):
        if not self.page.has_next():
            return None
        url = settings.SITE_URL + self.request.get_full_path()
        page_number = self.page.next_page_number()
        return replace_query_param(url, self.page_query_param, page_number)

    def get_previous_link(self):
        if not self.page.has_previous():
            return None
        url = settings.SITE_URL + self.request.get_full_path()
        page_number = self.page.previous_page_number()
        if page_number == 1:
            return remove_query_param(url, self.page_query_param)
        return replace_query_param(url, self.page_query_param, page_number)
