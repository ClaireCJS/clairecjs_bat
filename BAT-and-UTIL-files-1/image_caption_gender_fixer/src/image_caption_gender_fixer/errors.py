class ICGFError(Exception):
    code = 40


class SelectionRequired(ICGFError):
    code = 21


class DependencyUnavailable(ICGFError):
    code = 30


class IntegrityError(ICGFError):
    code = 40


class UnsafeFilesystem(ICGFError):
    code = 41


class RecoverableFailure(ICGFError):
    code = 50


class Cancelled(ICGFError):
    code = 20
