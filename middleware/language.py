from starlette.requests import Request

class LanguageMiddleware:
    """Middleware to detect request language"""

    SUPPORTED_LANGS = ["en", "fr"]

    def __init__(self, app):
        self.app = app

    async def __call__(self, scope, receive, send):
        if scope["type"] == "http":
            request = Request(scope, receive=receive)
            lang = request.headers.get("accept-language", "en")
            lang = lang.split(",")[0].split("-")[0]

            if lang not in self.SUPPORTED_LANGS:
                lang = "en"

            scope.setdefault("state", {})
            scope["state"].lang = lang

        await self.app(scope, receive, send)