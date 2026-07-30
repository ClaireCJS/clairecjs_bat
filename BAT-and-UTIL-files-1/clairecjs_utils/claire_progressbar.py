"""Claire's reusable, rainbow-cycling progress bars.

Summary
-------
This module wraps :mod:`tqdm` so Claire's Python tools can share one consistent
progress-bar implementation. Its bars:

* cycle smoothly through a bright HSV rainbow by default;
* can use ordinary ``tqdm`` coloring by passing ``rainbow=False``;
* insert a readable space between numbers and units;
* accept a caller-supplied ``tqdm`` ``bar_format`` for task-specific wording;
* resize to the terminal width;
* disappear when the operation finishes; and
* degrade gracefully when ``tqdm`` is unavailable or progress is disabled.

This library intentionally does not decide whether an operation is slow enough
to need a bar. Timing, throughput calibration, and display thresholds belong in
the calling script because they describe that script's workload.

The module deliberately does not import ``clairecjs_utils.claire_console``.
That package initializer has additional optional dependencies, while a cosmetic
progress bar should never prevent the underlying job from running.

Typical inclusion and loop
--------------------------
Copy this pattern into a Python script::

    from clairecjs_utils.claire_progressbar import progress_bar

    files = list(folder.rglob("*"))
    show_progress = len(files) > 500  # The calling script owns this decision.

    with progress_bar(
        total=len(files),
        description="Processing files",
        unit="file",
        enabled=show_progress,
        bar_format=(
            "{desc}: {n:,.0f} files processed"
            " | {elapsed} elapsed | {rate_fmt}"
        ),
    ) as progress:
        for path in files:
            process(path)
            if progress is not None:
                progress.update(1)

To force an ordinary, non-rainbow ``tqdm`` bar, add ``rainbow=False``. To
suppress progress entirely, add ``enabled=False``. The caller is responsible
for calculating ``show_progress`` using whatever timing or workload rules make
sense for that project.
"""

from __future__ import annotations

import colorsys
from contextlib import contextmanager
from typing import Any, Iterator

try:
    from tqdm import tqdm
except ImportError:  # A missing cosmetic dependency must not stop the work.
    tqdm = None


def rainbow_hex(position: float) -> str:
    """Convert a cycle position into a bright RGB hex color.

    Args:
        position: Location around the HSV color wheel.  ``0.0`` is red,
            approximately ``1/3`` is green, and approximately ``2/3`` is blue.
            Values outside ``0.0`` through ``1.0`` wrap automatically, so
            ``1.25`` produces the same color as ``0.25``.

    Returns:
        A lowercase ``#rrggbb`` string suitable for ``tqdm``'s ``colour``
        property.
    """
    red, green, blue = colorsys.hsv_to_rgb(position % 1.0, 1.0, 1.0)
    return f"#{round(red * 255):02x}{round(green * 255):02x}{round(blue * 255):02x}"


def spaced_unit(unit: str) -> str:
    """Return a unit label with exactly one leading display space.

    ``tqdm`` normally joins its formatted rate directly to the unit, producing
    output such as ``11481.53file/s``. This helper converts ``"file"`` (or an
    already padded ``" file"``) to ``" file"`` so counts and rates remain
    readable. An empty unit remains empty.

    Args:
        unit: Singular or plural unit label supplied by the caller.

    Returns:
        The stripped label with one leading space, or ``""`` when no label was
        supplied.
    """
    stripped = unit.strip()
    return f" {stripped}" if stripped else ""


if tqdm is not None:
    class RainbowTqdm(tqdm):
        """A ``tqdm`` subclass whose completed portion traverses the rainbow.

        The class accepts the same constructor arguments as ``tqdm``.  Callers
        normally do not instantiate it directly; :func:`progress_bar`
        chooses it whenever rainbow output is enabled.
        """

        def display(self, *args: Any, **kwargs: Any) -> bool | None:
            """Refresh the bar after selecting its color for current progress.

            ``tqdm`` calls this method for initial display and subsequent
            refreshes.  The current completed fraction (``n / total``) becomes
            a position on the HSV wheel, producing one full rainbow traversal
            over the operation.  Unknown or zero totals safely use ``1``.

            Args:
                *args: Positional display arguments forwarded unchanged to
                    ``tqdm.display``.
                **kwargs: Keyword display arguments forwarded unchanged to
                    ``tqdm.display``.

            Returns:
                Whatever the installed ``tqdm.display`` implementation returns.
            """
            total = self.total or 1
            self.colour = rainbow_hex(self.n / total)
            return super().display(*args, **kwargs)
else:
    # Keep the public name importable when tqdm is not installed.  The context
    # manager below will yield None rather than attempting to instantiate it.
    RainbowTqdm = None


@contextmanager
def progress_bar(
    *,
    total: int | None,
    description: str,
    unit: str = "file",
    enabled: bool = True,
    rainbow: bool = True,
    mininterval: float = 0.05,
    maxinterval: float = 0.5,
    miniters: int = 1,
    bar_format: str | None = None,
) -> Iterator[Any | None]:
    """Create, yield, and reliably close a progress bar.

    Args:
        total: Total update count displayed by ``tqdm``. Pass ``None`` while
            enumerating an unknown number of items; callers may assign a known
            total later and refresh the bar.
        description: Text shown to the left of the bar.
        unit: Singular unit label used by ``tqdm``; defaults to ``"file"``.
        enabled: Caller-controlled switch. ``False`` suppresses the bar. The
            calling script—not this library—must decide whether its operation
            is slow or large enough to warrant progress display.
        rainbow: Use :class:`RainbowTqdm` when ``True`` (the default); use an
            ordinary ``tqdm`` bar when ``False``.
        mininterval: Minimum seconds between visual refreshes. The responsive
            default is ``0.05``.
        maxinterval: Maximum seconds allowed between refresh recalculations;
            defaults to ``0.5``.
        miniters: Minimum updates between refresh opportunities. The default of
            ``1`` prevents dynamic throttling from making jobs look stalled.
        bar_format: Optional custom ``tqdm`` format string. Use this when the
            caller needs task-specific labels such as ``"files found"`` or
            comma-formatted counters. ``None`` keeps ``tqdm``'s normal layout.

    Yields:
        A ``tqdm``-compatible object when enabled and available; otherwise
        ``None``. Callers must guard updates with ``if progress is not None`` as
        shown in the module example.

    Notes:
        The bar uses dynamic terminal width and ``leave=False``.  It is closed
        in a ``finally`` block, including when the caller's loop raises an
        exception.  Failure to import ``tqdm`` is treated as cosmetic and
        results in ``None`` rather than an application error.
    """
    should_show = enabled and tqdm is not None
    bar = (
        (RainbowTqdm if rainbow else tqdm)(
            total=total,
            desc=description,
            unit=spaced_unit(unit),
            bar_format=bar_format,
            dynamic_ncols=True,
            leave=False,
            mininterval=mininterval,
            maxinterval=maxinterval,
            miniters=miniters,
        )
        if should_show
        else None
    )
    try:
        yield bar
    finally:
        if bar is not None:
            bar.close()
