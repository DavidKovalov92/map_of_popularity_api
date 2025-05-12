from rest_framework import serializers
from .models import Category, Location
from .models import Review

class ReviewSerializer(serializers.ModelSerializer):
    user = serializers.HiddenField(default=serializers.CurrentUserDefault())
    email = serializers.EmailField(source="user.email", read_only=True)
    likes_count = serializers.SerializerMethodField()
    dislikes_count = serializers.SerializerMethodField()

    class Meta:
        model = Review
        fields = ('id', 'email', 'user', 'rating', 'comment', 'created_at', 'updated_at', 'likes_count', 'dislikes_count')
        read_only_fields = ('id', 'created_at', 'updated_at', 'email', 'likes_count', 'dislikes_count')

    def validate_rating(self, value):
        if value < 0 or value > 10:
            raise serializers.ValidationError("Rating must be between 0 and 10.")
        return value

    def validate_review(self, value):
        if not value.strip():
            raise serializers.ValidationError("Comment cannot be empty.")
        return value

    def get_likes_count(self, obj):
        return obj.likes_dislikes.filter(is_like=True).count()

    def get_dislikes_count(self, obj):
        return obj.likes_dislikes.filter(is_like=False).count()

class LocationSerializer(serializers.ModelSerializer):
    reviews = ReviewSerializer(many=True, read_only=True)
    category = serializers.ChoiceField(choices=Category.choices(), default=Category.OTHER.name)

    class Meta:
        model = Location
        fields = (
            'id',
            'title',
            'description',
            'address',
            'category',
            'created_at',
            'updated_at',
            'average_rating',
            'reviews',
        )
        read_only_fields = ('id', 'created_at', 'updated_at', 'average_rating', 'reviews')

    def validate_title(self, value):
        if not value.strip():
            raise serializers.ValidationError("Title cannot be empty.")
        if len(value) > 255:
            raise serializers.ValidationError("Title cannot exceed 255 characters.")
        return value

    def validate_description(self, value):
        if not value.strip():
            raise serializers.ValidationError("Description cannot be empty.")
        return value

    def validate_address(self, value):
        if not value.strip():
            raise serializers.ValidationError("Address cannot be empty.")
        if len(value) > 255:
            raise serializers.ValidationError("Address cannot exceed 255 characters.")
        return value

    def validate_average_rating(self, value):
        if value < 0 or value > 10:
            raise serializers.ValidationError("Average rating must be between 0 and 10.")
        return value
    
    def validate_category(self, value):
        valid_categories = [category.name for category in Category]
        if value not in valid_categories:
            raise serializers.ValidationError(f"Category must be one of: {', '.join(valid_categories)}.")
        return value





    
    
