import secrets
import jwt
from .cache import QueryCacheSingleton
from api.models import CustomUser
from UserAuthModule.settings import SECRET_KEY


from django.contrib.auth.hashers import make_password


def hash_token(token_str: str) -> str:
    """
    Hash a token string using Django's password hashing system.
    """
    return make_password(token_str)


def get_transaction_id():
    return secrets.token_urlsafe(32)


def create_jwt(payload):
    return jwt.encode(payload, SECRET_KEY, algorithm="HS256")


def decode_jwt(token):
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=["HS256"])
        return payload
    except jwt.ExpiredSignatureError:
        raise Exception("Token has expired")
    except jwt.InvalidTokenError:
        raise Exception("Invalid token")


def blacklist_refresh(conn, token):
    # Blacklist refresh token
    refresh_ttl = conn.ttl(f"refresh_token:{token}")
    if refresh_ttl > 0:
        conn.set(f"blacklisted_token:{token}", "true", ex=refresh_ttl)
        conn.delete(f"refresh_token:{token}")


def blacklist_access(conn, token):
    # Blacklist access token
    access_ttl = conn.ttl(f"access_token:{token}")
    if access_ttl > 0:
        conn.set(f"blacklisted_token:{token}", "true", ex=access_ttl)
        conn.delete(f"access_token:{token}")


def get_user_by_email(email: str, cache_key_prefix: str = "user") -> CustomUser | None:
    """
    Fetch a user by email with per-request caching.

    Args:
        email: The email of the user to fetch.
        cache_key_prefix: Prefix to use for the cache key (default 'user').

    Returns:
        CustomUser instance or None if not found.
    """
    key = f"{cache_key_prefix}:{email}"

    def query_user():
        return CustomUser.objects.filter(email=email).first()

    return QueryCacheSingleton.get_or_set(key, query_user)


def get_user_by_id(user_id: int, cache_key_prefix: str = "user") -> CustomUser | None:
    """
    Fetch a user by primary key (ID) with per-request caching.

    Args:
        user_id: The ID of the user to fetch.
        cache_key_prefix: Prefix to use for the cache key (default 'user').

    Returns:
        CustomUser instance or None if not found.
    """
    key = f"{cache_key_prefix}:{user_id}"

    def query_user():
        return CustomUser.objects.filter(pk=user_id).first()

    return QueryCacheSingleton.get_or_set(key, query_user)
