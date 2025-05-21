def get_location_list_cache_key(search_param="", category_param=""):
    return f"locations:list:{search_param}:{category_param}"


def get_location_detail_cache_key(location_id):
    return f"location:detail:{location_id}"


def get_reviews_cache_key(location_id, user_id=None):
    if user_id:
        return f"reviews:location:{location_id}:user:{user_id}"
    return f"reviews:location:{location_id}"


def get_subscription_cache_key(user_id, location_id):
    return f"subscription:{user_id}:{location_id}"


def get_export_csv_cache_key():
    return "locations:export:csv"


def get_likes_dislikes_cache_key(review_id):
    return f"review:{review_id}:likes_dislikes"
