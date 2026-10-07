"""Spelling suggestion core built on a BK tree.

A BK tree keeps words in a shape that makes near neighbours of a query
cheap to find: each node holds one word and at most one child per edit
distance to that word, so a search only walks into the children whose edge
can still reach the query inside the budget.

The kernel is pure in-memory string arithmetic.  It is deterministic -- the
same words, added in any order, answer the same query the same way -- and
uses no clock, no entropy source and no I/O.
"""

MAX_WORD_LENGTH = 16
DEFAULT_MAX_DISTANCE = 2


class SpellError(Exception):
    """Raised when the suggestion kernel cannot carry out the request."""


def _check_word(word):
    """Words are plain strings of at most MAX_WORD_LENGTH characters.

    The empty string is a word like any other: it is stored, measured and
    suggested like any other, and its distance to a word is that word's
    length.
    """
    if not isinstance(word, str):
        raise TypeError("word must be a str")
    if len(word) > MAX_WORD_LENGTH:
        raise ValueError("word must be at most %d characters" % (MAX_WORD_LENGTH,))
    return word


def _check_budget(max_distance):
    """Budgets are plain ints of zero or more."""
    if isinstance(max_distance, bool) or not isinstance(max_distance, int):
        raise TypeError("max_distance must be an int")
    if max_distance < 0:
        raise ValueError("max_distance must not be negative")
    return max_distance


def _length_gap(a, b, budget):
    """True when no budget of edits can bridge the lengths of a and b.

    Two words whose lengths differ by more than the budget can never lie
    within the budget of each other, whatever their letters are.
    """
    return abs(len(a) - len(b)) > budget


def edit_distance(a, b, max_distance=None):
    """Levenshtein distance between a and b.

    Without max_distance the exact distance comes back.  With a budget the
    exact value is not needed: any distance above the budget is reported as
    max_distance + 1.
    """
    a = _check_word(a)
    b = _check_word(b)
    if max_distance is not None:
        budget = _check_budget(max_distance)
        if _length_gap(a, b, budget):
            return budget + 1
    row = list(range(len(b) + 1))
    for i in range(1, len(a) + 1):
        new_row = [i] + [0] * len(b)
        for j in range(1, len(b) + 1):
            cost = 0 if a[i - 1] == b[j - 1] else 1
            new_row[j] = min(row[j] + 1, new_row[j - 1] + 1, row[j - 1] + cost)
        row = new_row
    return row[len(b)]


def _suggestion_key(query, candidate, distance):
    """How one suggestion ranks: nearest first, then the query's length, a..z.

    A word of the query's own length ranks before the rest of the words at
    the same distance: it is the shape a plain typo takes.
    """
    return (distance, len(candidate) != len(query), candidate)


def _should_descend(distance, edge, budget):
    """True when the subtree hung at edge may still hold a word in budget.

    A word at edge edits from a node that sits distance edits from the query
    is at least abs(distance - edge) and at most distance + edge edits away
    from the query, so when the edge leaves the window that runs from
    distance - budget to distance + budget the whole subtree is out of
    reach and can be skipped without looking inside.
    """
    return distance - budget <= edge <= distance + budget


class _Node:
    """One node of the tree: a word and one child per distance to it."""

    __slots__ = ("word", "children")

    def __init__(self, word):
        self.word = word
        self.children = {}


class BKTree:
    """A Burkhard-Keller tree over words.

    Adding a word walks down from the root following the edge named by the
    distance to every node it passes, and hangs the word under the first
    node that has no child at that distance.  Searching walks the same
    edges, but only into the children whose edge can still reach the query
    inside the budget.
    """

    def __init__(self):
        self._root = None
        self._size = 0

    def __len__(self):
        """How many words are stored."""
        return self._size

    def __contains__(self, word):
        """Whether word is stored."""
        return self.contains(word)

    def words(self):
        """Every stored word, in ascending order."""
        found = []
        walk = [] if self._root is None else [self._root]
        while walk:
            node = walk.pop()
            found.append(node.word)
            walk.extend(node.children.values())
        found.sort()
        return found

    def contains(self, word):
        """Whether word is stored."""
        word = _check_word(word)
        node = self._root
        while node is not None:
            distance = edit_distance(word, node.word)
            if distance == 0:
                return True
            node = node.children.get(distance)
        return False

    def add(self, word):
        """Store word; True when it was not stored before."""
        word = _check_word(word)
        if self._root is None:
            self._root = _Node(word)
            self._size = 1
            return True
        node = self._root
        while True:
            distance = edit_distance(word, node.word)
            if distance == 0:
                return False
            child = node.children.get(distance)
            if child is None:
                node.children[distance] = _Node(word)
                self._size += 1
                return True
            node = child

    def search(self, word, max_distance=DEFAULT_MAX_DISTANCE):
        """Every stored word within max_distance edits of word.

        The list comes out nearest first; words of the query's own length
        rank before the rest at the same distance, and words that tie on
        both come out in alphabetical order.
        """
        word = _check_word(word)
        budget = _check_budget(max_distance)
        hits = []
        walk = [] if self._root is None else [self._root]
        while walk:
            node = walk.pop()
            distance = edit_distance(word, node.word)
            if distance <= budget:
                hits.append((distance, node.word))
            for edge, child in node.children.items():
                if _should_descend(distance, edge, budget):
                    walk.append(child)
        hits.sort(key=lambda hit: _suggestion_key(word, hit[1], hit[0]))
        return [hit_word for _, hit_word in hits]


def suggest(words, query, max_distance=DEFAULT_MAX_DISTANCE):
    """The suggestions for query over a vocabulary.

    Words whose length is too far from the query's can never lie within the
    budget, so they are left out before the tree is even built.
    """
    query = _check_word(query)
    budget = _check_budget(max_distance)
    tree = BKTree()
    for entry in words:
        entry = _check_word(entry)
        if not _length_gap(query, entry, budget):
            tree.add(entry)
    return tree.search(query, budget)
