from rest_framework_nested import routers
from django.urls import path
from .views import LikeDislikeView, LocationViewSet, ReviewViewSet

router = routers.SimpleRouter()
router.register(r"locations", LocationViewSet, basename="location")


locations_router = routers.NestedSimpleRouter(router, r"locations", lookup="location")
locations_router.register(r"reviews", ReviewViewSet, basename="location-reviews")

urlpatterns = [
    path(
        "reviews/<int:review_pk>/like_dislike/",
        LikeDislikeView.as_view(),
        name="like_dislike",
    ),
]

urlpatterns += router.urls
urlpatterns += locations_router.urls
