# trainlib test suite
# (c) James Aylett 2010

import unittest
import os.path

import trainlib

class TestLinesFileParsing(unittest.TestCase):
	def __init__(self, *kwargs, **args):
		thisdir = os.path.realpath(os.path.dirname(__file__))
		self.lines = trainlib.parse_lines(os.path.join(thisdir, 'data', 'test_parsing.json'))
		super(TestLinesFileParsing, self).__init__(*kwargs, **args)

	def check_simple_station_set(self, stations):
		self.assertEqual(len(stations), 3)
		s1 = stations[0]; s2 = stations[1]; s3 = stations[2]
		self.assertEqual(s1.name, 'Station 1')
		self.assertEqual(s1.type, 'station')
		self.assertEqual(len(s1.next), 1)
		self.assertEqual(s1.next[0], s2)
		self.assertEqual(len(s1.previous), 0)
		self.assertEqual(s2.name, 'Station 2')
		self.assertEqual(s2.type, 'station')
		self.assertEqual(len(s2.next), 1)
		self.assertEqual(s2.next[0], s3)
		self.assertEqual(len(s2.previous), 1)
		self.assertEqual(s2.previous[0], s1)
		self.assertEqual(s3.name, 'Depot 1')
		self.assertEqual(s3.type, 'depot')
		self.assertEqual(len(s3.next), 0)
		self.assertEqual(len(s3.previous), 1)
		self.assertEqual(s3.previous[0], s2)
	
	def test_basic(self):
		l = self.lines[0] # line 1 is fully explicit
		self.assertEqual(l.name, 'Test line 1')
		self.check_simple_station_set(l.stations)

	def test_defaults(self):
		l = self.lines[1] # line 2 uses defaults
		self.assertEqual(l.name, 'Test line 2')
		self.check_simple_station_set(l.stations)

	def test_compact(self):
		l = self.lines[2] # line 3 uses the compact syntax
		self.assertEqual(l.name, 'Test line 3')
		self.check_simple_station_set(l.stations)
		
	def test_next_regression(self):
		l = self.lines[3] # line data specific to this test
		self.assertEqual(len(l.stations), 2)
		s1 = l.stations[0]; s2 = l.stations[1]
		self.assertEqual(len(s1.next), 1)
		self.assertEqual(len(s2.next), 0)
		self.assertEqual(s1.next[0], s2)

	def test_termini_resolution(self):
		l = self.lines[4] # line data specific to this test
		self.assertEqual(len(l.stations), 4)
		s1 = l.stations[0]; s2 = l.stations[1]; s3 = l.stations[2]; s4 = l.stations[3]
		self.assertEqual(len(s1.next), 1)
		self.assertEqual(len(s2.next), 1)
		self.assertEqual(len(s3.next), 1)
		self.assertEqual(len(s4.next), 0)
		self.assertEqual(s1.next[0], s3)
		self.assertEqual(s2.next[0], s3)
		self.assertEqual(s3.next[0], s4)
		
		self.assertEqual(len(s1.previous), 0)
		self.assertEqual(len(s2.previous), 0)
		self.assertEqual(len(s3.previous), 2)
		self.assertEqual(len(s4.previous), 1)
		self.assertEqual(s4.previous[0], s3)
		self.assertTrue(s1 in s3.previous)
		self.assertTrue(s2 in s3.previous)
		self.assertFalse(s3 in s3.previous)

		self.assertEqual(len(l.termini), 3)
		self.assertTrue(s1 in l.termini)
		self.assertTrue(s2 in l.termini)
		self.assertTrue(s4 in l.termini)

	def test_links_resolution(self):
		l = self.lines[5] # line data specific to this test
		self.assertEqual(len(l.stations), 4)
		s1 = l.stations[0]; s2 = l.stations[1]; s3 = l.stations[2]; s4 = l.stations[3]; 
		self.assertEqual(len(s1.all_next), 3)
		self.assertEqual(len(s2.all_next), 1)
		self.assertEqual(len(s3.all_next), 1)
		self.assertEqual(len(s4.all_next), 0)
		self.assertEqual(len(s1.all_previous), 0)
		self.assertEqual(len(s2.all_previous), 1)
		self.assertEqual(len(s3.all_previous), 1)
		self.assertEqual(len(s4.all_previous), 3)

class TestLineClosing(unittest.TestCase):
	def __init__(self, *kwargs, **args):
		thisdir = os.path.realpath(os.path.dirname(__file__))
		self.lines = trainlib.parse_lines(os.path.join(thisdir, 'data', 'test_closing.json'))
		super(TestLineClosing, self).__init__(*kwargs, **args)
		
	def setUp(self):
		self.close_station = trainlib.Station.close_station
		self.closed_stations = []
		test = self
		def c(self):
			if self.status!='closed':
				test.closed_stations.append(self)
				test.close_station(self)
		trainlib.Station.close_station = c
	
	def tearDown(self):
		trainlib.Station.close_staiton = self.close_station

	def test_closing_0_1(self):
		l = self.lines[0]
		l.close_line("s1", "t2")
		self.assertTrue(l.stations[1] in self.closed_stations)
		self.assertTrue(l.stations[3] in self.closed_stations)
		self.assertEqual(len(self.closed_stations), 2)

	def test_closing_0_2(self):
		l = self.lines[0]
		l.close_line("s2", "t2")
		self.assertTrue(l.stations[2] in self.closed_stations)
		self.assertTrue(l.stations[3] in self.closed_stations)
		self.assertEqual(len(self.closed_stations), 2)

	def test_closing_0_3(self):
		l = self.lines[0]
		l.close_line("t1", "s2")
		self.assertTrue(l.stations[0] in self.closed_stations)
		self.assertTrue(l.stations[2] in self.closed_stations)
		self.assertEqual(len(self.closed_stations), 2)

	def test_closing_0_4(self):
		l = self.lines[0]
		l.close_line("t1", "t2")
		self.assertTrue(l.stations[0] in self.closed_stations)
		self.assertTrue(l.stations[1] in self.closed_stations)
		self.assertTrue(l.stations[2] in self.closed_stations)
		self.assertTrue(l.stations[3] in self.closed_stations)
		self.assertEqual(len(self.closed_stations), 4)

	def test_closing_1_1(self):
		l = self.lines[1]
		l.close_line("s1", "s3")
		self.assertTrue(l.stations[1] in self.closed_stations)
		self.assertTrue(l.stations[3] in self.closed_stations)
		self.assertEqual(len(self.closed_stations), 2)

	def test_closing_0_1_reverse(self):
		l = self.lines[0]
		l.close_line("t2", "s1")
		self.assertTrue(l.stations[1] in self.closed_stations)
		self.assertTrue(l.stations[3] in self.closed_stations)
		self.assertEqual(len(self.closed_stations), 2)

	def test_closing_0_2_reverse(self):
		l = self.lines[0]
		l.close_line("t2", "s2")
		self.assertTrue(l.stations[2] in self.closed_stations)
		self.assertTrue(l.stations[3] in self.closed_stations)
		self.assertEqual(len(self.closed_stations), 2)

	def test_closing_0_3_reverse(self):
		l = self.lines[0]
		l.close_line("s2", "t1")
		self.assertTrue(l.stations[0] in self.closed_stations)
		self.assertTrue(l.stations[2] in self.closed_stations)
		self.assertEqual(len(self.closed_stations), 2)

	def test_closing_0_4_reverse(self):
		l = self.lines[0]
		l.close_line("t2", "t1")
		self.assertTrue(l.stations[0] in self.closed_stations)
		self.assertTrue(l.stations[1] in self.closed_stations)
		self.assertTrue(l.stations[2] in self.closed_stations)
		self.assertTrue(l.stations[3] in self.closed_stations)
		self.assertEqual(len(self.closed_stations), 4)

	def test_closing_1_1(self):
		l = self.lines[1]
		l.close_line("s1", "s3")
		self.assertTrue(l.stations[1] in self.closed_stations)
		self.assertTrue(l.stations[3] in self.closed_stations)
		self.assertEqual(len(self.closed_stations), 2)

	def test_closing_1_2(self):
		l = self.lines[1]
		l.close_line("s2", "s3")
		self.assertTrue(l.stations[2] in self.closed_stations)
		self.assertTrue(l.stations[3] in self.closed_stations)
		self.assertEqual(len(self.closed_stations), 2)

	def test_closing_1_3(self):
		l = self.lines[1]
		l.close_line("t1", "s2")
		self.assertTrue(l.stations[0] in self.closed_stations)
		self.assertTrue(l.stations[2] in self.closed_stations)
		self.assertEqual(len(self.closed_stations), 2)

	def test_closing_1_4(self):
		l = self.lines[1]
		l.close_line("t1", "s3")
		self.assertTrue(l.stations[0] in self.closed_stations)
		self.assertTrue(l.stations[1] in self.closed_stations)
		self.assertTrue(l.stations[2] in self.closed_stations)
		self.assertTrue(l.stations[3] in self.closed_stations)
		self.assertEqual(len(self.closed_stations), 4)

	def test_closing_1_5(self):
		l = self.lines[1]
		l.close_line("s1", "t3")
		self.assertTrue(l.stations[1] in self.closed_stations)
		self.assertTrue(l.stations[3] in self.closed_stations)
		self.assertTrue(l.stations[5] in self.closed_stations)
		self.assertTrue(l.stations[6] in self.closed_stations)
		self.assertEqual(len(self.closed_stations), 4)
		
	def test_closing_1_6(self):
		l = self.lines[1]
		l.close_line("t1", "t3", "s2") # closing "via" test
		self.assertTrue(l.stations[0] in self.closed_stations)
		self.assertTrue(l.stations[2] in self.closed_stations)
		self.assertTrue(l.stations[3] in self.closed_stations)
		self.assertTrue(l.stations[5] in self.closed_stations)
		self.assertTrue(l.stations[6] in self.closed_stations)
		self.assertEqual(len(self.closed_stations), 5)
		
	def test_closing_all_1(self):
		l = self.lines[0]
		l.close_entire_line()
		self.assertTrue(l.stations[0] in self.closed_stations)
		self.assertTrue(l.stations[1] in self.closed_stations)
		self.assertTrue(l.stations[2] in self.closed_stations)
		self.assertTrue(l.stations[3] in self.closed_stations)
		self.assertEqual(len(self.closed_stations), 4)
		
	def test_closing_all_2(self):
		l = self.lines[1]
		l.close_entire_line()
		self.assertTrue(l.stations[0] in self.closed_stations)
		self.assertTrue(l.stations[1] in self.closed_stations)
		self.assertTrue(l.stations[2] in self.closed_stations)
		self.assertTrue(l.stations[3] in self.closed_stations)
		self.assertTrue(l.stations[4] in self.closed_stations)
		self.assertTrue(l.stations[5] in self.closed_stations)
		self.assertTrue(l.stations[6] in self.closed_stations)
		self.assertEqual(len(self.closed_stations), 7)
		
	def test_closing_x_1(self):
		l = self.lines[1]
		self.assertRaises(NotImplementedError, l.close_line, "s1", None)
		
	def test_closing_x_2(self):
		l = self.lines[1]
		self.assertRaises(NotImplementedError, l.close_line, None, "s1")

class MyParser(trainlib.Parser):
	def fixup_station_name(self, name):
		m = {
			'1st': 'First Station',
			'2nd': 'Second Station'
		}
		if m.has_key(name):
			return m[name]
		else:
			return name
		
	def fixup_line_name(self, name):
		m = {
			'1st': 'First Line',
			'2nd': 'Second Line'
		}
		if m.has_key(name):
			return m[name]
		else:
			return name

class TestNameFixups(unittest.TestCase):
	def __init__(self, *kwargs, **args):
		thisdir = os.path.realpath(os.path.dirname(__file__))
		p = MyParser()
		self.lines = p.parse_lines(os.path.join(thisdir, 'data', 'test_naming.json'))
		super(TestNameFixups, self).__init__(*kwargs, **args)

	def test_name_fixup_0(self):
		l = self.lines[0]
		self.assertEqual(l.name, u"First Line")
		self.assertEqual(l.stations[0].name, u"First Station")
		self.assertEqual(l.stations[1].name, u"Second Station")
		self.assertEqual(l.stations[2].name, u"Third Station")
		self.assertEqual(len(l.stations), 3)

	def test_name_fixup_1(self):
		l = self.lines[1]
		self.assertEqual(l.name, u"Second Line")
		self.assertEqual(l.stations[0].name, u"First Station")
		self.assertEqual(l.stations[1].name, u"2ndd")
		self.assertEqual(l.stations[2].name, u"3rd")
		self.assertEqual(len(l.stations), 3)

	def test_name_fixup_2(self):
		l = self.lines[2]
		self.assertEqual(l.name, u"3rd")
		self.assertEqual(l.stations[0].name, u"First Station")
		self.assertEqual(l.stations[1].name, u"2ndd")
		self.assertEqual(l.stations[2].name, u"3rd")
		self.assertEqual(len(l.stations), 3)

if __name__ == "__main__":
	unittest.main()
