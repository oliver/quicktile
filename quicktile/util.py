"""Helper functions and classes"""

__author__ = "Stephan Sokolow (deitarion/SSokolow)"
__license__ = "GNU GPL 2.0 or later"

from itertools import chain, combinations
from UserDict import DictMixin

# Allow MyPy to work without depending on the `typing` package
# (And silence complaints from only using the imported types in comments)
MYPY = False
if MYPY:
    # pylint: disable=unused-import
    from typing import (Any, Callable, Dict, Iterable, Iterator, List,  # NOQA
                        Optional, Sequence, Tuple)
    from mypy_extensions import VarArg, KwArg  # NOQA

    # pylint: disable=C0103
    PercentRect = Tuple[float, float, float, float]
    Strut = Tuple[int, int, int, int, int, int, int, int, int, int, int, int]

    # FIXME: Replace */** with a dict so I can be strict here
    CommandCB = Callable[..., Any]
del MYPY

def clamp_idx(idx, stop, wrap=True):
    # type: (int, int, bool) -> int
    """Ensure a 0-based index is within a given range [0, stop).

    Uses the same half-open range convention as Python slices.

    @param wrap: If C{True}, wrap around rather than saturating.
    """
    if wrap:
        return idx % stop
    else:
        return max(min(idx, stop - 1), 0)

def powerset(iterable):  # type: (Iterable[Any]) -> Iterator[Sequence[Any]]
    """C{powerset([1,2,3])} --> C{() (1,) (2,) (3,) (1,2) (1,3) (2,3) (1,2,3)}

    @rtype: iterable
    """
    i = list(iterable)
    return chain.from_iterable(combinations(i, j) for j in range(len(i) + 1))

def fmt_table(rows,          # type: Any
              headers,       # type: Sequence
              group_by=None  # type: Optional[int]
              ):  # type: (...) -> str
    """Format a collection as a textual table.

    @param headers: Header labels for the columns
    @param group_by: Index of the column to group results by.
    @type rows: C{dict} or iterable of iterables
    @type headers: C{list(str)}
    @type group_by: C{int}

    @attention: This uses C{zip()} to combine things. The number of columns
        displayed will be defined by the narrowest of all rows.

    @rtype: C{str}
    """
    output = []  # type: List[str]

    if isinstance(rows, dict):
        rows = list(sorted(rows.items()))

    groups = {}  # type: Dict[str, List[str]]
    if group_by is not None:
        headers = list(headers)
        headers.pop(group_by)
        rows = [list(row) for row in rows]
        for row in rows:
            group = row.pop(group_by)
            groups.setdefault(group, []).append(row)
    else:
        groups[''] = rows

    # Identify how much space needs to be allocated for each column
    col_maxlens = []
    for pos, header in enumerate(headers):
        maxlen = max(len(x[pos]) for x in rows if len(x) > pos)
        col_maxlens.append(max(maxlen, len(header)))

    def fmt_row(row, pad=' ', indent=0, min_width=0):
        """Format a fmt_table row"""
        result = []
        for width, label in zip(col_maxlens, row):
            result.append('%s%s ' % (' ' * indent, label.ljust(width, pad)))

        _width = sum(len(x) for x in result)
        if _width < min_width:
            result[-1] = result[-1][:-1]
            result.append(pad * (min_width - _width + 1))

        result.append('\n')
        return result

    # Print the headers and divider
    group_width = max(len(x) for x in groups)
    output.extend(fmt_row(headers))
    output.extend(fmt_row([''] * len(headers), '-', min_width=group_width + 1))

    for group in sorted(groups):
        if group:
            output.append("\n%s\n" % group)
        for row in groups[group]:
            output.extend(fmt_row(row, indent=1))

    return ''.join(output)

class EnumSafeDict(DictMixin):
    """A dict-like object which avoids comparing objects of different types
    to avoid triggering spurious Glib "comparing different enum types"
    warnings.
    """

    def __init__(self, *args):
        self._contents = {}

        for in_dict in args:
            for key, val in in_dict.items():
                self[key] = val

    def __contains__(self, key):
        ktype = type(key)
        return ktype in self._contents and key in self._contents[ktype]

    def __delitem__(self, key):  # type: (Any) -> None
        if key in self:
            ktype = type(key)
            section = self._contents[ktype]
            del section[key]
            if not section:
                del self._contents[ktype]
        else:
            raise KeyError(key)

    def __getitem__(self, key):  # type: (Any) -> Any
        if key in self:
            return self._contents[type(key)][key]
        else:
            raise KeyError(key)

    def __iter__(self):
        for section in self._contents.values():
            for key in section.keys():
                yield key

    def __len__(self):
        return len(self._contents)

    def __repr__(self):
        return "%s(%s)" % (self.__class__.__name__,
            ', '.join(repr(x) for x in self._contents.values()))

    def __setitem__(self, key, value):  # type: (Any, Any) -> None
        ktype = type(key)
        self._contents.setdefault(ktype, {})[key] = value

    def iteritems(self):
        return [(key, self[key]) for key in self]

    def keys(self):  # type: () -> List[Any]
        """D.keys() -> list of D's keys"""
        return list(self)

class XInitError(Exception):
    """Raised when something outside our control causes the X11 connection to
       fail.
    """

    def __str__(self):
        return ("%s\n\t(The cause of this error lies outside of QuickTile)" %
                Exception.__str__(self))

# vim: set sw=4 sts=4 expandtab :
