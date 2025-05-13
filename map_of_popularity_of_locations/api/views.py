from rest_framework.viewsets import ModelViewSet
from rest_framework.permissions import IsAuthenticated
from django_filters.rest_framework import DjangoFilterBackend
from rest_framework.filters import SearchFilter
from api.models import Location
from .helpers import (
    get_export_csv_cache_key,
    get_likes_dislikes_cache_key,
    get_location_detail_cache_key,
    get_location_list_cache_key,
    get_reviews_cache_key,
    get_subscription_cache_key,
)
from .tasks import send_subcribe_email
from .filters import LocationFilter
from .serializers import LocationSerializer
from rest_framework.decorators import action
from rest_framework.response import Response
from django.http import HttpResponse
import pandas as pd
from rest_framework import status
from .models import LikeDislike, LocationSubscription, Review
from .serializers import ReviewSerializer
from rest_framework.views import APIView
import csv
import io
from django.core.mail import send_mail
from django.core.cache import cache


class LocationViewSet(ModelViewSet):
    queryset = Location.objects.all()
    serializer_class = LocationSerializer
    permission_classes = [IsAuthenticated]
    filter_backends = [DjangoFilterBackend, SearchFilter]
    filterset_class = LocationFilter
    search_fields = ["title", "description"]

    def get_queryset(self):
        search_param = self.request.GET.get("search", "")
        category_param = self.request.GET.get("category", "")
        cache_key = get_location_list_cache_key(search_param, category_param)

        cached_locations = cache.get(cache_key)
        if cached_locations:
            return cached_locations

        queryset = Location.objects.all()

        if search_param:
            queryset = queryset.filter(title__icontains=search_param)
        if category_param:
            queryset = queryset.filter(category=category_param)

        cache.set(cache_key, queryset, timeout=300)
        return queryset

    def perform_create(self, serializer):
        location = serializer.save()
        (
            cache.delete_pattern("locations:list:*")
            if hasattr(cache, "delete_pattern")
            else None
        )
        return location

    def perform_update(self, serializer):
        location = serializer.save()
        cache_key = get_location_detail_cache_key(location.id)
        cache.delete(cache_key)
        (
            cache.delete_pattern("locations:list:*")
            if hasattr(cache, "delete_pattern")
            else None
        )
        cache.delete(get_export_csv_cache_key())
        return location

    @action(detail=True, methods=["post"], url_path="subscribe")
    def subscribe(self, request, pk=None):
        user = request.user
        location_id = pk
        if not location_id:
            return Response({"detail": "Location ID is required."}, status=400)

        cache_key = get_subscription_cache_key(user.id, location_id)
        cached_subscription = cache.get(cache_key)

        if cached_subscription:
            return Response({"detail": "Already subscribed."}, status=400)

        try:
            location = Location.objects.get(id=location_id)
        except Location.DoesNotExist:
            return Response({"detail": "Location not found."}, status=404)

        if LocationSubscription.objects.filter(user=user, location=location).exists():
            return Response({"detail": "Already subscribed."}, status=400)

        LocationSubscription.objects.create(user=user, location=location)

        cache.set(cache_key, True, timeout=3600)

        send_subcribe_email.delay(user_email=user.email, location_title=location.title)

        return Response({"detail": "Subscribed successfully."}, status=201)

    @action(detail=True, methods=["post"], url_path="unsubscribe")
    def unsubscribe(self, request, pk=None):
        location = self.get_object()
        user = request.user
        subscription = LocationSubscription.objects.filter(
            user=user, location=location
        ).first()

        if not subscription:
            return Response(
                {"detail": "Not subscribed to this location."},
                status=status.HTTP_400_BAD_REQUEST,
            )

        subscription.delete()

        cache_key = get_subscription_cache_key(user.id, location.id)
        cache.delete(cache_key)

        return Response(
            {"detail": "Unsubscribed successfully."}, status=status.HTTP_200_OK
        )

    @action(detail=False, methods=["get"], url_path="export/json")
    def export_json(self, request):
        locations = self.get_queryset()
        serializer = self.get_serializer(locations, many=True)
        return Response(serializer.data)

    @action(detail=False, methods=["get"], url_path="export/csv")
    def export_csv(self, request):
        cache_key = get_export_csv_cache_key()
        cached_export = cache.get(cache_key)

        if cached_export:
            return cached_export

        locations = self.get_queryset()

        output = io.StringIO()
        writer = csv.writer(output)
        writer.writerow(
            [
                "Title",
                "Description",
                "Address",
                "Category",
                "Average Rating",
                "Created At",
                "Updated At",
            ]
        )

        for location in locations:
            writer.writerow(
                [
                    location.title,
                    location.description,
                    location.address,
                    location.category,
                    location.average_rating,
                    location.created_at,
                    location.updated_at,
                ]
            )

        response = Response(output.getvalue(), content_type="text/csv")
        response["Content-Disposition"] = "attachment; filename=locations.csv"
        cache.set(cache_key, response, timeout=600)
        return response

    def perform_destroy(self, instance):
        location_id = instance.id
        cache_key = get_location_detail_cache_key(location_id)
        cache.delete(cache_key)
        (
            cache.delete_pattern(f"reviews:location:{location_id}*")
            if hasattr(cache, "delete_pattern")
            else None
        )
        (
            cache.delete_pattern("locations:list:*")
            if hasattr(cache, "delete_pattern")
            else None
        )
        cache.delete(get_export_csv_cache_key())
        instance.delete()


class ReviewViewSet(ModelViewSet):
    serializer_class = ReviewSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        location_id = self.kwargs.get("location_pk")
        user = self.request.user

        if location_id:
            cache_key = get_reviews_cache_key(location_id, user.id)
            cached_reviews = cache.get(cache_key)

            if cached_reviews:
                return cached_reviews

            queryset = Review.objects.filter(location_id=location_id)
        else:
            cache_key = f"reviews:user:{user.id}:subscribed"
            cached_reviews = cache.get(cache_key)

            if cached_reviews:
                return cached_reviews

            subscribed_locations = LocationSubscription.objects.filter(user=user)
            location_ids = [
                subscription.location.id for subscription in subscribed_locations
            ]
            queryset = Review.objects.filter(location_id__in=location_ids)

        cache.set(cache_key, queryset, timeout=60 * 15)
        return queryset

    def perform_create(self, serializer):
        location_id = self.kwargs["location_pk"]
        review = serializer.save(user=self.request.user, location_id=location_id)

        review.location.update_average_rating()

        (
            cache.delete_pattern(f"reviews:location:{location_id}*")
            if hasattr(cache, "delete_pattern")
            else None
        )

        cache.delete(get_location_detail_cache_key(location_id))

        (
            cache.delete_pattern("locations:list:*")
            if hasattr(cache, "delete_pattern")
            else None
        )

    def perform_update(self, serializer):
        review = serializer.save()
        location = review.location

        location.update_average_rating()

        (
            cache.delete_pattern(f"reviews:location:{location.id}*")
            if hasattr(cache, "delete_pattern")
            else None
        )

        cache.delete(get_location_detail_cache_key(location.id))

        (
            cache.delete_pattern("locations:list:*")
            if hasattr(cache, "delete_pattern")
            else None
        )

    def destroy(self, request, *args, **kwargs):
        instance = self.get_object()
        location = instance.location
        location_id = location.id

        self.perform_destroy(instance)

        location.update_average_rating()

        (
            cache.delete_pattern(f"reviews:location:{location_id}*")
            if hasattr(cache, "delete_pattern")
            else None
        )

        cache.delete(get_location_detail_cache_key(location_id))

        (
            cache.delete_pattern("locations:list:*")
            if hasattr(cache, "delete_pattern")
            else None
        )

        return Response({"detail": "Review deleted."}, status=status.HTTP_200_OK)


class LikeDislikeView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request, review_pk, *args, **kwargs):
        cache_key = get_likes_dislikes_cache_key(review_pk)
        cached_data = cache.get(cache_key)

        if cached_data:
            return Response(cached_data, status=status.HTTP_200_OK)

        try:
            review = Review.objects.get(pk=review_pk)
        except Review.DoesNotExist:
            return Response(
                {"detail": "Review not found."}, status=status.HTTP_404_NOT_FOUND
            )

        likes_count = review.likes_dislikes.filter(is_like=True).count()
        dislikes_count = review.likes_dislikes.filter(is_like=False).count()

        response_data = {"likes_count": likes_count, "dislikes_count": dislikes_count}

        cache.set(cache_key, response_data, timeout=300)

        return Response(response_data, status=status.HTTP_200_OK)

    def post(self, request, review_pk, *args, **kwargs):
        try:
            review = Review.objects.get(pk=review_pk)
        except Review.DoesNotExist:
            return Response(
                {"detail": "Review not found."}, status=status.HTTP_404_NOT_FOUND
            )

        is_like = request.data.get("is_like", None)
        if is_like is None:
            return Response(
                {"detail": "Please provide is_like (True or False)."},
                status=status.HTTP_400_BAD_REQUEST,
            )

        like_dislike, created = LikeDislike.objects.get_or_create(
            user=request.user, review=review
        )

        if created or like_dislike.is_like != is_like:
            like_dislike.is_like = is_like
            like_dislike.save()

            location_id = review.location.id
            (
                cache.delete_pattern(f"reviews:location:{location_id}*")
                if hasattr(cache, "delete_pattern")
                else None
            )

            cache.delete(get_likes_dislikes_cache_key(review_pk))

            return Response(
                {
                    "detail": f"{'Like' if is_like else 'Dislike'} {'added' if created else 'updated'} successfully."
                },
                status=status.HTTP_201_CREATED if created else status.HTTP_200_OK,
            )
        return Response({"detail": "No change made."}, status=status.HTTP_200_OK)

    def delete(self, request, review_pk, *args, **kwargs):
        try:
            like_dislike = LikeDislike.objects.get(
                user=request.user, review__id=review_pk
            )
            review = like_dislike.review
            location_id = review.location.id

            like_dislike.delete()

            (
                cache.delete_pattern(f"reviews:location:{location_id}*")
                if hasattr(cache, "delete_pattern")
                else None
            )

            cache.delete(get_likes_dislikes_cache_key(review_pk))

            return Response(
                {"detail": "Like/Dislike removed successfully."},
                status=status.HTTP_200_OK,
            )
        except LikeDislike.DoesNotExist:
            return Response(
                {"detail": "Like/Dislike not found."}, status=status.HTTP_404_NOT_FOUND
            )
