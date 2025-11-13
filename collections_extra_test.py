from collections_extra import LimitedSizeOrderedSet, LimitedSizeOrderedDict
import unittest


class Test_LimitedSizeOrderedSet(unittest.TestCase):
    def test_basic_functionality(self):
        set = LimitedSizeOrderedSet(max_size=100)
        self.assertEqual(len(set), 0)
        self.assertFalse("foo" in set)

        set.add("foo")
        self.assertTrue("foo" in set)
        self.assertEqual(len(set), 1)

        set.add("bar")
        self.assertTrue("foo" in set)
        self.assertTrue("bar" in set)
        self.assertEqual(len(set), 2)

        set.add("bar")
        self.assertTrue("foo" in set)
        self.assertTrue("bar" in set)
        self.assertEqual(len(set), 2)

        set.clear()
        self.assertEqual(len(set), 0)

    def test_hit_max_size(self):
        # When we hit the max size the oldest elements in the set should be removed
        set = LimitedSizeOrderedSet(max_size=5)

        set.add(1)
        set.add(2)
        set.add(3)
        set.add(4)
        set.add(5)
        self.assertTrue(1 in set)
        self.assertTrue(2 in set)
        self.assertTrue(3 in set)
        self.assertTrue(4 in set)
        self.assertTrue(5 in set)

        self.assertFalse(6 in set)
        set.add(6)
        self.assertFalse(1 in set)
        self.assertTrue(2 in set)
        self.assertTrue(3 in set)
        self.assertTrue(4 in set)
        self.assertTrue(5 in set)
        self.assertTrue(6 in set)

    def test_reinsert_updates_map_location(self):
        # When we call add with an element that is already in the set it should
        # update the location of that element in the order so it is pushed to
        # the front of the order.
        
        set = LimitedSizeOrderedSet(max_size=3)

        set.add(1)
        set.add(2)
        set.add(3)
        self.assertTrue(1 in set)
        self.assertTrue(2 in set)
        self.assertTrue(3 in set)

        # add 1 again to push it to the front of the order
        set.add(1)
        self.assertTrue(1 in set)
        self.assertTrue(2 in set)
        self.assertTrue(3 in set)

        # now if we add 4 it should result in 2 being removed instead of 1
        self.assertFalse(4 in set)
        set.add(4)
        self.assertTrue(1 in set)
        self.assertFalse(2 in set)
        self.assertTrue(3 in set)
        self.assertTrue(4 in set)

class Test_LimitedSizeOrderedDict(unittest.TestCase):
    def test_basic_functionality(self):
        limitedDict = LimitedSizeOrderedDict(max_size=100)
        self.assertEqual(len(limitedDict), 0)
        self.assertFalse("foo" in limitedDict)

        limitedDict["foo"] = "foo"
        self.assertTrue("foo" in limitedDict)
        self.assertEqual(limitedDict["foo"], "foo")
        self.assertEqual(len(limitedDict), 1)

        limitedDict["bar"] = "bar"
        self.assertTrue("bar" in limitedDict)
        self.assertEqual(limitedDict["bar"], "bar")
        self.assertEqual(len(limitedDict), 2)

        limitedDict["bar"] = "bar"
        self.assertTrue("bar" in limitedDict)
        self.assertEqual(limitedDict["bar"], "bar")
        self.assertEqual(len(limitedDict), 2)

        limitedDict.clear()
        self.assertEqual(len(limitedDict), 0)

    def test_hit_max_size(self):
        # When we hit the max size the oldest elements in the set should be removed
        limitedDict = LimitedSizeOrderedDict(max_size=5)

        limitedDict[1] = "1"
        limitedDict[2] = "2"
        limitedDict[3] = "3"
        limitedDict[4] = "4"
        limitedDict[5] = "5"
        self.assertTrue(1 in limitedDict)
        self.assertTrue(2 in limitedDict)
        self.assertTrue(3 in limitedDict)
        self.assertTrue(4 in limitedDict)
        self.assertTrue(5 in limitedDict)
        self.assertEqual(limitedDict[1], "1")
        self.assertEqual(limitedDict[2], "2")
        self.assertEqual(limitedDict[3], "3")
        self.assertEqual(limitedDict[4], "4")
        self.assertEqual(limitedDict[5], "5")

        self.assertFalse(6 in limitedDict)
        limitedDict[6] = "6"
        self.assertFalse(1 in limitedDict)
        self.assertTrue(2 in limitedDict)
        self.assertTrue(3 in limitedDict)
        self.assertTrue(4 in limitedDict)
        self.assertTrue(5 in limitedDict)
        self.assertTrue(6 in limitedDict)
        self.assertEqual(limitedDict[2], "2")
        self.assertEqual(limitedDict[3], "3")
        self.assertEqual(limitedDict[4], "4")
        self.assertEqual(limitedDict[5], "5")
        self.assertEqual(limitedDict[6], "6")


    def test_reinsert_updates_map_location(self):
        # When we call insert with an element that is already in the set it
        # should update the location of that element in the order so it is
        # pushed to the front of the order.
        
        limitedDict = LimitedSizeOrderedDict(max_size=3)

        limitedDict[1] = "1"
        limitedDict[2] = "2"
        limitedDict[3] = "3"
        self.assertTrue(1 in limitedDict)
        self.assertTrue(2 in limitedDict)
        self.assertTrue(3 in limitedDict)
        self.assertEqual(limitedDict[1], "1")
        self.assertEqual(limitedDict[2], "2")
        self.assertEqual(limitedDict[3], "3")

        # add 1 again to push it to the front of the order
        limitedDict[1] = "new_1"
        self.assertTrue(1 in limitedDict)
        self.assertTrue(2 in limitedDict)
        self.assertTrue(3 in limitedDict)
        self.assertEqual(limitedDict[1], "new_1")
        self.assertEqual(limitedDict[2], "2")
        self.assertEqual(limitedDict[3], "3")

        # now if we add 4 it should result in 2 being removed instead of 1
        self.assertFalse(4 in limitedDict)
        limitedDict[4] = "4"
        self.assertTrue(1 in limitedDict)
        self.assertFalse(2 in limitedDict)
        self.assertTrue(3 in limitedDict)
        self.assertTrue(4 in limitedDict)
        self.assertEqual(limitedDict[1], "new_1")
        self.assertEqual(limitedDict[3], "3")
        self.assertEqual(limitedDict[4], "4")


if __name__ == '__main__':       
    unittest.main()