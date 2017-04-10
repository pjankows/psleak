#!/usr/bin/env python3
import unittest

from psleak import ProcessSnapshot, ProcessDelta, ProcessDeltaException
import psleak


class TestProcessDelta(unittest.TestCase):
    def setUp(self):
        self.p1 = ProcessSnapshot(1, 'test1', '/opt/bin/test1 arg1 arg2', 1024)
        self.p2 = ProcessSnapshot(1, 'test1', '/opt/bin/test1 arg1 arg2', 2048)
        self.p3 = ProcessSnapshot(2, 'test1', '/opt/bin/test1 arg1 arg2', 2048)
        self.p4 = ProcessSnapshot(1, 'test2', '/opt/bin/test2', 2048)

    def test_delta_sub_negative(self):
        d = self.p1 - self.p2
        self.assertEquals(d.delta, -1024)

    def test_delta_sub_positive(self):
        d = self.p2 - self.p1
        self.assertEquals(d.delta, 1024)

    def test_delta_percent_decrease(self):
        d = self.p1 - self.p2
        self.assertAlmostEquals(d.percent, -50)

    def test_delta_percent_increase(self):
        d = self.p2 - self.p1
        self.assertAlmostEquals(d.percent, 100)

    def test_sub_different_name(self):
        with self.assertRaises(psleak.ProcessDeltaException):
            self.p1 - self.p4

    def test_sub_different_pid(self):
        with self.assertRaises(psleak.ProcessDeltaException):
            self.p1 - self.p3


if __name__ == '__main__':
    unittest.main()
