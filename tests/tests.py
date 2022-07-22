# -*- coding: utf-8 -*-

import unittest
from unittest import mock
from datetime import timedelta, date, datetime
from supplypipe.utils import str2list, list2str
from supplypipe.utils import calculate_download_days
from supplypipe.utils import setup_ohlc

class TestUtils(unittest.TestCase):

    def test_str2list(self):
        self.assertEqual(str2list("GENE"), ["GENE"])

    def test_list2str(self):
        self.assertEqual(list2str(["a","b","c","d"]), "abcd")

    def test_calculate_download_days(self):
        start_date = (date.today() - timedelta(days=729)).strftime('%Y-%m-%d')        
        end_date = (date.today() + timedelta(days=1)).strftime('%Y-%m-%d')
        self.assertEqual(calculate_download_days(), (start_date, end_date))

    def test_setup_ohlc(self):
        d = {
            'Open':'first', 'High':'max', 'Low':'min','Close': 'last',
            'Volume': 'sum'
        }
        self.assertDictEqual(setup_ohlc(), d)

if __name__ == '__main__':
    unittest.main()