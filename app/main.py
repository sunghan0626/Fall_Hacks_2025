# FastAPI app entrypoint.
# TODO (All):
# - Wire up Jinja2 templates and StaticFiles mount.
# - Startup: call init_db().
# - Routes:
#   - GET "/" -> landing (shows open offers)
#   - Auth: GET/POST "/login", "/signup", "/logout"
#   - Offers: list/new/join ("/offers", "/offers/new", "/offers/{id}/join")
#   - Session: QR page + confirm ("/session/{sid}", "/session/{sid}/qr.png", POST "/session/{sid}/confirm")
#   - Wallet: GET "/wallet"
#   - Profile: GET/POST "/profile"
#   - Community: GET "/posts", GET/POST "/posts/new", GET "/posts/{pid}", POST "/posts/{pid}/comment"
#   - DEX: GET "/dex", POST "/dex/new"
#
# Owners:
# - Auth & Profile -> A
# - Community/Search -> B
# - Check-in/Geo -> C
# - Wallet/DEX -> D
