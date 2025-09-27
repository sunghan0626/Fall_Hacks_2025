# Minimal session auth with signed cookies (itsdangerous).
# TODO (A):
# - COOKIE_NAME = "fitcoin_session"
# - sign_session(user_id) -> token
# - verify_session(token) -> user_id or None
# - SECRET_KEY from env with fallback "dev-secret"
