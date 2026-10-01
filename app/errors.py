"""The ten frozen error codes. E_RATE_LIMIT added with team-lead approval."""

ERRORS = {
    "E_EMPTY_URL": (400, "Please enter a website URL."),
    "E_INVALID_URL": (400, "Please enter a complete website URL."),
    "E_UNSUPPORTED_SCHEME": (400, "Only http and https addresses can be analysed."),
    "E_URL_TOO_LONG": (400, "That URL is too long to analyse."),
    "E_MODEL_UNAVAILABLE": (503, "Analysis is unavailable right now. Please try again later."),
    "E_FEATURE_FAILURE": (500, "This URL could not be analysed."),
    "E_PREDICTION_INVALID": (500, "This URL could not be analysed."),
    "E_EXPLANATION_FAILURE": (500, "The analysis completed but could not be explained."),
    "E_INTERNAL": (500, "Something went wrong. Please try again."),
    "E_RATE_LIMIT": (429, "Too many requests. Please wait a minute and try again."),
}

FIELD_ERRORS = {"E_EMPTY_URL", "E_INVALID_URL", "E_UNSUPPORTED_SCHEME", "E_URL_TOO_LONG"}


class AppError(Exception):
    def __init__(self, code):
        if code not in ERRORS:
            code = "E_INTERNAL"
        self.code = code
        self.status, self.message = ERRORS[code]
        self.field = "url" if code in FIELD_ERRORS else None
        super().__init__(code)

    def to_dict(self):
        return {"error": {"code": self.code, "message": self.message, "field": self.field}}
