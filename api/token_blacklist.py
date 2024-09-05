from .models import BlacklistedToken

def add_to_blacklist(token):
    BlacklistedToken.objects.create(token=token)

def is_token_revoked(token):
    return BlacklistedToken.objects.filter(token=token).exists()