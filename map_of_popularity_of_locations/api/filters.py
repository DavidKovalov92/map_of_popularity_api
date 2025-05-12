import django_filters
from .models import Location

class LocationFilter(django_filters.FilterSet):
    min_rating = django_filters.NumberFilter(field_name="average_rating", lookup_expr='gte')
    max_rating = django_filters.NumberFilter(field_name="average_rating", lookup_expr='lte')
    category = django_filters.CharFilter(field_name="category")
    
    class Meta:
        model = Location
        fields = ['min_rating', 'max_rating', 'category']