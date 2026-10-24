class ICGFError(Exception):
    code = 40

    def __init__(self, message, **context):
        super().__init__(message)
        self.context = context


class SelectionRequired(ICGFError):
    code = 21


class DependencyUnavailable(ICGFError):
    code = 30


class IntegrityError(ICGFError):
    code = 40


class RenderBlocked(IntegrityError):
    """An editable proposal cannot yet be rendered without a known violation."""


class ImageDeferred(IntegrityError):
    """A format/frame case is intentionally preserved for explicit deferral."""


class UnsafeFilesystem(ICGFError):
    code = 41


class RecoverableFailure(ICGFError):
    code = 50


class Cancelled(ICGFError):
    code = 20
