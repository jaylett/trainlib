# trainlib
# (c) James Aylett 2010

import json

UNNAMED_STATION = 'Unnamed station'

class Line:
	def __init__(self, name, stations, termini = None):
		self.name = name
		self.stations = stations
		if termini==None:
			self.termini = []
		else:
			self.termini = termini
		for s in self.stations:
			s._update_links()
	
	def resolve_station(self, name):
		for s in self.stations:
			if s.name == unicode(name):
				return s
		return None
	
	def _close_line(self, from_station, target):
		from_station.close_station()
		if from_station==target:
			return
		for s in from_station.next:
			if target==s or target in s.all_next:
				self._close_line(s, target)
	
	def close_entire_line(self):
		for s in self.stations:
			s.close_station()
	
	def close_line(self, from_station, to_station, via_station=None):
		if via_station!=None:
			self.close_line(from_station, via_station)
			self.close_line(to_station, via_station)
			return
		if type(from_station) is unicode or type(from_station) is str:
			from_station = self.resolve_station(from_station)
		if type(to_station) is unicode or type(to_station) is str:
			to_station = self.resolve_station(to_station)
		if from_station==None or to_station==None:
			if from_station==None and to_station==None:
				self.close_entire_line()
			else:
				raise NotImplementedError("Cannot perform a line closure open-ended only at one end")
		if to_station not in from_station.all_next:
			f = from_station
			from_station = to_station
			to_station = f
		
		# so we always go from from_station towards to_station using the next relation
		self._close_line(from_station, to_station)
		
	def __str__(self):
		return unicode(self).encode('utf-8')
		
	def __unicode__(self):
		return self.name

class Station:
	def __init__(self, name, type, next=None, previous=None):
		self.name = name
		self.type = type
		if next==None:
			self.next = []
		else:
			self.next = next
		if previous==None:
			self.previous = []
		else:
			self.previous = previous
		self.status = 'open'
		self.all_next = []
		self.all_previous = []
		
	def close_station(self):
		self.status = 'closed'
		
	def open_station(self):
		self.status = 'open'
		
	def __hash__(self):
		return hash(self.name) # not quite right, but it isn't really valid anyway
		
	def __cmp__(self, other):
		if hasattr(other, 'name'):
			return cmp(self.name, other.name)
		else:
			return 1
			
	def _update_links(self):
		# do next first
		s = [self,]
		self.all_next = []
		while len(s)>0:
			x = []
			for st in s[0].next:
				if st not in self.all_next:
					x.append(st)
					self.all_next.append(st)
			s.extend(x)
			s = s[1:]
		s = [self,]
		self.all_previous = []
		while len(s)>0:
			x = []
			for st in s[0].previous:
				if st not in self.all_previous:
					x.append(st)
					self.all_previous.append(st)
			s.extend(x)
			s = s[1:]
		
	def __str__(self):
		return unicode(self).encode('utf-8')
		
	def __unicode__(self):
		return self.name

class Parser:
	def parse_lines(self, file_or_filename):
		if type(file_or_filename) is unicode or type(file_or_filename) is str:
			return self.parse_lines_from_filename(file_or_filename)
		else:
			return self.parse_lines_from_file(file_or_filename)

	def parse_lines_from_filename(self, filename):
		f = open(filename, 'r')
		r = self.parse_lines_from_file(f)
		f.close()
		return r

	def ponder_type_from_name(self, name):
		if 'depot' in name.lower():
			return 'depot'
		elif 'siding' in name.lower():
			return 'siding'
		else:
			return 'station'

	def fixup_station_name(self, name):
		return unicode(name)

	def parse_lines_from_file(self, file):
		l = json.load(file)
		out = []
		for line in l:
			lname = line.get('name', 'Unnamed line')
			stations = {}
			termini = []
			# first pass: get stations
			slist = line.get('stations', [])
			for st in slist:
				idx = slist.index(st)
				if type(st) is unicode:
					st = { 'name': self.fixup_station_name(st) }
				else:
					st['name'] = self.fixup_station_name(st.get('name', UNNAMED_STATION))
				slist[idx] = st
				s = Station(
					st['name'],
					st.get('type', self.ponder_type_from_name(st.get('name', '')))
					)
				next = st.get('next')
				if stations.get(s.name, None)!=None:
					# FIXME
					print u"Warning: overwriting station with name %s in line %s" % (s.name, lname,)
				stations[s.name] = s
		
			# build up backward links as we process forward links -- each value is a list of station *objects* that are
			# linked next to the station *object* that is the key.
			prev_map = {}
		
			# second pass: chain stations together (forward)
			for idx in range(0, len(slist)):
				st = slist[idx]
				next = st.get('next', [])
				st = st['name']
			
				if next == None:
					# must be explicit about being a terminus (or be the last station in a line list)
					termini.append(stations[st])
					continue
			
				if type(next) is unicode:
					next = [next,]
			
				if len(next)==0:
					if idx < len(slist) - 1:
						next = [ slist[idx+1].get('name', UNNAMED_STATION), ]
					else:
						termini.append(stations[st])
			
				for nst in next:
					stations[st].next.append(stations[nst])
					if prev_map.has_key(stations[nst]):
						prev_map[stations[nst]].append(stations[st])
					else:
						prev_map[stations[nst]] = [ stations[st], ]
			# third pass: chain stations together (backwards)
			for s in slist:
				st = stations[s.get('name', UNNAMED_STATION)]
				if prev_map.has_key(st):
					st.previous = prev_map[st]
				else:
					st.previous = []
					termini.append(st)
			# and hook all stations into a line object
			# stations.values() won't be in a helpful order so put them back in the original order from the file
			sts = []
			for s in slist:
				st = stations[s.get('name', UNNAMED_STATION)]
				sts.append(st)
			out.append(Line(lname, sts, termini))
		return out

def parse_lines(file_or_filename):
	"""Convenience function for when you don't need a full parser object."""
	p = Parser()
	return p.parse_lines(file_or_filename)
