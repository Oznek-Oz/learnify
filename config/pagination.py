from rest_framework.pagination import PageNumberPagination


class StandardPagination(PageNumberPagination):
    """
    Pagination standard pour la plupart des listes.
    20 éléments par page, maximum 100.
    """
    page_size = 20
    page_size_query_param = 'page_size'
    max_page_size = 100


class LargePagination(PageNumberPagination):
    """
    Pagination pour les listes volumineuses (flashcards, quiz).
    50 éléments par page, maximum 200.
    """
    page_size = 50
    page_size_query_param = 'page_size'
    max_page_size = 200