# SQLModel data models.
# TODO (A):
# - User(id, handle, password_hash, coins, created_at)
# - Profile(user_id unique, sports, timezones, regions, goals)
#
# TODO (B):
# - Post(author_id, title, body, tags, created_at)
# - Comment(post_id, author_id, body, created_at)
#
# TODO (C):
# - Offer(owner_id, title, when_text, where_text, is_open, lat?, lon?, created_at)
# - Session(offer_id, host_id, guest_id, started_at, confirmed_host, confirmed_guest, qr_nonce)
#
# TODO (D):
# - Tx(user_id, amount, kind['earn','spend','bonus'], note, created_at)
# - Order(user_id, side['buy','sell'], price, amount, created_at)
