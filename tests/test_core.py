"""Behaviour tests for the spelling suggestion core."""

import unittest

from spell.core import BKTree
from spell.core import MAX_WORD_LENGTH
from spell.core import edit_distance
from spell.core import suggest


class TestEditDistance(unittest.TestCase):
    def test_01_distance_of_plain_and_empty_words(self):
        self.assertEqual(edit_distance("", ""), 0)
        self.assertEqual(edit_distance("", "cat"), 3)
        self.assertEqual(edit_distance("cat", ""), 3)
        self.assertEqual(edit_distance("cat", "cat"), 0)
        self.assertEqual(edit_distance("kitten", "sitting"), 3)
        self.assertEqual(edit_distance("flaw", "lawn"), 2)
        self.assertEqual(edit_distance("ab", "ba"), 2)
        self.assertEqual(edit_distance("book", "back"), 2)
        with self.assertRaises(TypeError):
            edit_distance("cat", 5)
        with self.assertRaises(TypeError):
            edit_distance(None, "cat")

    def test_02_distance_under_a_budget(self):
        self.assertEqual(edit_distance("cat", "cats", 1), 1)
        self.assertEqual(edit_distance("abc", "abcde", 2), 2)
        self.assertEqual(edit_distance("cat", "cat", 0), 0)
        self.assertEqual(edit_distance("abc", "xyz", 5), 3)
        self.assertEqual(edit_distance("abc", "xyz", 2), 3)
        self.assertEqual(edit_distance("cat", "dog", 2), 3)
        with self.assertRaises(TypeError):
            edit_distance("cat", "cats", "2")
        with self.assertRaises(ValueError):
            edit_distance("cat", "cats", -1)


class TestBKTree(unittest.TestCase):
    def test_03_empty_tree_and_rejected_input(self):
        tree = BKTree()
        self.assertEqual(len(tree), 0)
        self.assertEqual(tree.words(), [])
        self.assertEqual(tree.search("cat"), [])
        self.assertFalse(tree.contains("cat"))
        self.assertFalse(tree.contains(""))
        self.assertNotIn("cat", tree)
        with self.assertRaises(TypeError):
            tree.add(7)
        with self.assertRaises(TypeError):
            tree.contains(None)
        with self.assertRaises(TypeError):
            tree.search(["cat"])
        with self.assertRaises(TypeError):
            tree.search("cat", 1.5)
        with self.assertRaises(ValueError):
            tree.search("cat", -1)

    def test_04_added_words_are_found_and_listed_in_order(self):
        tree = BKTree()
        for word in ("dog", "cat", "cart", "cot", "dot"):
            self.assertTrue(tree.add(word))
        self.assertEqual(len(tree), 5)
        self.assertEqual(tree.words(), ["cart", "cat", "cot", "dog", "dot"])
        for word in tree.words():
            self.assertTrue(tree.contains(word))
            self.assertIn(word, tree)
        self.assertFalse(tree.contains("carts"))
        self.assertFalse(tree.contains("cab"))
        self.assertFalse(tree.contains("do"))

    def test_05_a_word_added_twice_is_stored_once(self):
        tree = BKTree()
        self.assertTrue(tree.add("cat"))
        self.assertFalse(tree.add("cat"))
        self.assertTrue(tree.add("cot"))
        self.assertFalse(tree.add("cot"))
        self.assertEqual(len(tree), 2)
        self.assertEqual(tree.words(), ["cat", "cot"])
        self.assertEqual(tree.search("cat", 1), ["cat", "cot"])
        self.assertEqual(tree.search("cot", 1), ["cot", "cat"])

    def test_06_suggestions_stay_inside_the_budget(self):
        tree = BKTree()
        for word in ("cot", "cup", "cat", "cut", "dog"):
            tree.add(word)
        found = tree.search("cat", 1)
        self.assertEqual(found, ["cat", "cot", "cut"])
        for word in found:
            self.assertLessEqual(edit_distance("cat", word), 1)
        self.assertNotIn("cup", found)
        self.assertNotIn("dog", found)

    def test_07_same_length_words_come_first(self):
        words = ("at", "bat", "cart", "cat", "coat", "cut")
        tree = BKTree()
        for word in words:
            tree.add(word)
        self.assertEqual(
            tree.search("cat", 1),
            ["cat", "bat", "cut", "at", "cart", "coat"],
        )
        self.assertEqual(tree.search("cat", 1), tree.search("cat", 1))
        shuffled = BKTree()
        for word in ("coat", "cut", "cart", "cat", "bat", "at"):
            shuffled.add(word)
        self.assertEqual(shuffled.search("cat", 1), tree.search("cat", 1))

    def test_08_every_reachable_branch_is_searched(self):
        tree = BKTree()
        for word in ("cat", "cut", "bat"):
            tree.add(word)
        self.assertEqual(tree.words(), ["bat", "cat", "cut"])
        self.assertEqual(tree.search("cat", 1), ["cat", "bat", "cut"])
        self.assertEqual(tree.search("cat", 2), ["cat", "bat", "cut"])
        self.assertEqual(tree.search("cut", 2), ["cut", "cat", "bat"])

    def test_09_the_empty_query_lists_the_shortest_words(self):
        tree = BKTree()
        for word in ("", "a", "ab", "abc", "b"):
            self.assertTrue(tree.add(word))
        self.assertEqual(len(tree), 5)
        self.assertEqual(tree.words(), ["", "a", "ab", "abc", "b"])
        self.assertTrue(tree.contains(""))
        self.assertIn("", tree)
        self.assertEqual(tree.search("", 0), [""])
        self.assertEqual(tree.search("", 1), ["", "a", "b"])
        self.assertEqual(tree.search("", 2), ["", "a", "b", "ab"])

    def test_10_vocabulary_filter_and_the_word_limit(self):
        words = ["at", "cat", "cart", "cats", "scat", "at"]
        found = suggest(words, "at", 2)
        self.assertEqual(found, ["at", "cat", "cart", "cats", "scat"])
        self.assertEqual(suggest(list(reversed(words)), "at", 2), found)
        longest = "z" * MAX_WORD_LENGTH
        tree = BKTree()
        self.assertTrue(tree.add(longest))
        self.assertEqual(tree.words(), [longest])
        self.assertEqual(edit_distance(longest, longest), 0)
        with self.assertRaises(ValueError):
            tree.add("z" * (MAX_WORD_LENGTH + 1))
        with self.assertRaises(ValueError):
            tree.search("z" * (MAX_WORD_LENGTH + 1), 1)
