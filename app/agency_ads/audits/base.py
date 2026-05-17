"""BaseCheck — what every check subclasses."""

from abc import ABC, abstractmethod

from agency_ads.audits.types import Category, CheckContext, CheckResult, Severity


class BaseCheck(ABC):
    """Subclass and set the class attributes, then implement `evaluate`.

    Example:

        class MyCheck(BaseCheck):
            check_id = "tracking.conversion_window_lt_90d"
            title = "Primary conversion window is at least 90 days"
            category = Category.TRACKING
            severity = Severity.CRITICAL
            weight = 1.0

            def evaluate(self, ctx: CheckContext) -> CheckResult:
                ...
    """

    check_id: str = ""
    title: str = ""
    category: Category
    severity: Severity = Severity.MEDIUM
    weight: float = 1.0

    @abstractmethod
    def evaluate(self, ctx: CheckContext) -> CheckResult: ...

    def __init_subclass__(cls, **kwargs: object) -> None:
        super().__init_subclass__(**kwargs)
        if not cls.__name__.startswith("_") and cls.check_id == "":
            raise TypeError(f"{cls.__name__} must set check_id")
        if not cls.__name__.startswith("_") and cls.title == "":
            raise TypeError(f"{cls.__name__} must set title")
