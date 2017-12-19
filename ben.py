#!/usr/bin/env python3
# encoding: utf-8

from collections import Iterable as _Iterable
from inspect import signature as _signature
import itertools as _itertools
import functools as _functools
import operator as _operator
import re as _re
import string as _string
import sys as _sys


def status_line(*args):
	print(*args, file=sys.stderr, end='\b'*len('\n'.join(map(str, args))))


def do_until(x, func, condition):
	while True:
		x = func(x)
		if condition(x):
			break
	return x


def curry(func):
	@_functools.wraps(func)
	def curry_1(*args):
		if len(args) >= len(_signature(func).parameters):
			return func(*args)
		else:
			def curry_2(*other_args):
				return curry(func)(*args, *other_args)
			return curry_2
	return curry_1


def primes():
    """ Generate an infinite sequence of prime numbers."""
	# Sieve of Eratosthenes
	# Code by David Eppstein, UC Irvine, 28 Feb 2002
	# http://code.activestate.com/recipes/117119/

    # Maps composites to primes witnessing their compositeness.
    # This is memory efficient, as the sieve is not "run forward"
    # indefinitely, but only as long as required by the current
    # number being tested.
    D = {}

    # The running integer that's checked for primeness
    q = 2

    while True:
        if q not in D:
            # q is a new prime.
            # Yield it and mark its first multiple that isn't
            # already marked in previous iterations
            yield q
            D[q * q] = [q]
        else:
            # q is composite. D[q] is the list of primes that
            # divide it. Since we've reached q, we no longer
            # need it in the map, but we'll mark the next
            # multiples of its witnesses to prepare for larger
            # numbers
            for p in D[q]:
                D.setdefault(p + q, []).append(p)
            del D[q]

        q += 1

class Vector(tuple):
	def __new__(cls, *args):
		# if they try to construct it like old-style tuple
		# e.g. Vector([1, 2]), it should still work
		if len(args) == 1 and isinstance(args[0], _Iterable):
			return cls.__new__(cls, *args[0])
		# allow construction via Vector(1, 2)
		# instead of tuple
		return super().__new__(cls, args)

	def __oper(self, other, operator):
		if isinstance(other, _Iterable):
			new = list(other)
			for i, value in enumerate(self):
				try:
					new[i] = operator(new[i], value)
				except IndexError:
					raise ValueError('operands must have the same dimensions')
			return tuple(new)
		else:
			raise TypeError('operand must be iterable')

	def __add__(self, other):
		return self.__oper(other, _operator.add)

	def __sub__(self, other):
		return self.__oper(other, _operator.sub)

	def __mul__(self, other):
		return self.__oper(other, _operator.mul)

	__rmul__ = __mul__

	def __truediv__(self, other):
		return self.__oper(other, _operator.truediv)


def _b_file(t: _Iterable, offset=1):
	for n, term in enumerate(t, offset):
		if n in (0, 1):
			print(n)
		yield '{} {}\n'.format(n, term)


def write_b_file(t: _Iterable, filename='b_file.txt', offset=1):
	"""write an iterable t to filename as a b-file suitable for OEIS,
	starting at the given offset"""

	with open(filename, 'w') as b_file:
		for line in _b_file(t, offset):
			b_file.write(line)


def flatten(l):
	for el in l:
		if isinstance(el, _Iterable) and not isinstance(el, (str, bytes)):
			yield from flatten(el)
		else:
			yield el


def input_iter():
	while True:
		try:
			yield input()
		except EOFError:
			return


class CircularList(list):
	def __getitem__(self, x):
		if isinstance(x, slice):
			return CircularList(self[x] for x in self._rangeify(x))
		return super().__getitem__(self._wrap(x))

	def _wrap(self, x):
		return x % len(self)

	def _rangeify(self, slice):
		start, stop, step = slice.start, slice.stop, slice.step
		if start is None:
			start = 0
		if stop is None:
			stop = len(self)
		if step is None:
			step = 1
		return range(start, stop, step)

	def insert(self, pos, x):
		super().insert(self._wrap(pos), x)


def first_index(predicate, seq):
	for i, el in enumerate(seq):
		if predicate(el):
			return i
	raise ValueError
	# alternatively:
	# return next(i for i, c in enumerate(seq) if predicate(seq))


def first_whitespace(string):
	try:
		return first_index(str.isspace, string)
	except ValueError as ex:
		raise ValueError('no whitespace found') from ex


def fancy_text(text):
	"""makes text ｆａｎｃｙ"""

	# mad props to the Aristois hacked client
	# i dug through the obfuscated code to find this

	fancy = []

	for char in text:
		if ord(char) in range(33, 127):
			# U+FEE0 is the beginning of the fullwidth block
			fancy.append(chr(ord(char) + 0xFEE0))
		else:
			fancy.append(char)

	return ''.join(fancy)


def fancy_text(text):
	"""makes text ｆａｎｃｙ"""
	return text.translate(
		{i: chr(i + 0xFEE0) for i in range(0x21, 0x7f)}
	)


def convert_to_base(n, base, _acc=''):
	if not n:
		return int(_acc)
	else:
		# shoutout to compsci class
		# dunno why this works
		return ctb(n // base, base, str(n % base) + _acc)


def convert_to_base(n: int, base):
	converted = ''
	while n > 0:
		converted = str(n % base) + converted
		n //= base
	try:
		return int(converted)
	except ValueError:
		raise ValueError('positive ints only')


def thue_morse():
	for n in _itertools.count():
		yield bin(n).count('1') % 2


def memoize(f):
	"""
	Use functools.lru_cache instead
	Memoization decorator for functions taking one or more arguments.
	Does not work on functions that take unhashable arguments
	or that take keyword arguments.
	"""
	class MemoDict(dict):
		def __init__(self, f):
			self.f = f

		def __call__(self, *args):
			return self[args]

		def __missing__(self, args):
			self[args] = ret = self.f(*args)
			return ret

	return MemoDict(f)


memoize = _functools.lru_cache(maxsize=None)


def natural_keys(text):
	"""
	list.sort(key=natural_keys) sorts in human_order
	http://nedbatchelder.com/blog/200712/human_sorting.html
	"""

	atoi = lambda text: float(text) if text.isdigit() else text
	return [atoi(c) for c in _re.split('(\d+)', text.lower())]


def initials_in(initials, full_name):
	# TODO rewrite in linear time
	index = -1
	for initial in initials:
		# try progessively smaller substrings of full_name starting at 0
		index = full_name.find(initial, index+1)
		if index == -1:
			return False
	return True

# i thought this would be faster than the one above but it's not
# turns out the above one is faster cause it uses `str.find`
# which is implemented in C

#def initials_in(initials, full_name):
#	# lets us pop() in linear time
#	initials = list(initials)[::-1]
#
#	for char in full_name:
#		# short circuit if initials is empty
#		if initials and char == initials[0]:
#			initials = initials[1:]
#		if not initials:
#			break
#
#	return len(initials) == 0

def clap(text):
	return text.replace(' ', '\N{clapping hands sign}')


def rot(s, n=13):
	def _rot(char, n):
		if char not in _string.ascii_letters:
			return char
		alphabet = (_string.ascii_lowercase if char.islower() else _string.ascii_uppercase)

		pos = alphabet.index(char)
		return alphabet[(pos + n) % len(alphabet)]

	return ''.join(_rot(char, n) for char in s)


"""Return string + 1F300 (start of emoji block)"""
emoji_cipher = lambda string: ''.join(chr(ord(char) + 0x1F300) for char in string)

"""Return the inverse of emoji_cipher()"""
emoji_decipher = lambda string: ''.join(chr(ord(char) - 0x1F300) for char in string)


'''all the biomes needed to complete "Adventuring time"'''
needed_biomes = {
	'Beach',
	'Birch Forest',
	'Birch Forest Hills',
	'Cold Beach',
	'Cold Taiga',
	'Cold Taiga Hills',
	'Deep Ocean',
	'Desert',
	'DesertHills',
	'Extreme Hills',
	'Extreme Hills+',
	'Forest',
	'ForestHills',
	'FrozenRiver',
	'Ice Mountains',
	'Ice Plains',
	'Jungle',
	'JungleEdge',
	'JungleHills',
	'Mega Taiga',
	'Mega Taiga Hills',
	'Mesa',
	'Mesa Plateau',
	'Mesa Plateau F',
	'MushroomIsland',
	'MushroomIslandShore',
	'Ocean',
	'Plains',
	'River',
	'Roofed Forest',
	'Savanna',
	'Savanna Plateau',
	'Stone Beach',
	'Swampland',
	'Taiga',}


onions = {
	'archive.torproject.org': 'http://yjuwkcxlgo7f7o6s.onion/',
	'atlas.testnet.torproject.org': 'http://2d5quh2deowe4kpd.onion/',
	'atlas.torproject.org': 'http://52g5y5karruvc7bz.onion/',
	'aus1.torproject.org': 'http://x3nelbld33llasqv.onion/',
	'aus2.torproject.org': 'http://vijs2fmpd72nbqok.onion/',
	'bridges.torproject.org': 'http://z5tfsnikzulwicxs.onion/',
	'cloud.torproject.org': 'http://icxe4yp32mq6gm6n.onion/',
	'collector.testnet.torproject.org': 'http://vhbbidwvzwhahsrg.onion/',
	'collector.torproject.org': 'http://qigcb4g4xxbh5ho6.onion/',
	'collector2.torproject.org': 'http://kkvj4mhsttfcrksj.onion/',
	'compass.torproject.org': 'http://lwygejoa6fm26eef.onion/',
	'consensus-health.torproject.org': 'http://tgnv2pssfumdedyw.onion/',
	'crm.torproject.org': 'http://sgs4q3dzv74f723x.onion/',
	'deb.torproject.org': 'http://sdscoq7snqtznauu.onion/',
	'dist.torproject.org': 'http://rqef5a5mebgq46y5.onion/',
	'donate.torproject.org': 'http://bjk3o77eebkax2ud.onion/',
	'exonerator.torproject.org': 'http://zfu7x4fuagirknhb.onion/',
	'extra.torproject.org': 'http://klbl4glo2btuwyok.onion/',
	'fpcentral.tbb.torproject.org': 'http://ngp5wfw5z6ms3ynx.onion/',
	'gettor.torproject.org': 'http://tngjm3owsslo3wgo.onion/',
	'git.torproject.org': 'http://dccbbv6cooddgcrq.onion/',
	'gitweb.torproject.org': 'http://jqs44zhtxl2uo6gk.onion/',
	'health.testnet.torproject.org': 'http://fr6scuhdp5dqvy7d.onion/',
	'help.torproject.org': 'http://54nujbl4qohb5qdp.onion/',
	'jenkins.torproject.org': 'http://f7lqb5oicvsahone.onion/',
	'media.torproject.org': 'http://n46o4uxsej2icp5l.onion/',
	'metrics.torproject.org': 'http://rougmnvswfsmd4dq.onion/',
	'munin.torproject.org': 'http://hhr6fex2giwmolct.onion/',
	'nagios.torproject.org': 'http://kakxayzmcc3zeomu.onion/',
	'newsletter-master.torproject.org': 'http://wuxx5wlnezbkohsp.onion/',
	'newsletter.torproject.org': 'http://kzcx36ytbsm5iogs.onion/',
	'nyx.torproject.org': 'http://ebxqgaz3dwywcoxl.onion/',
	'onion.torproject.org': 'http://yz7lpwfhhzcdyc5y.onion/',
	'onionoo.torproject.org': 'http://tgel7v4rpcllsrk2.onion/',
	'onionperf.torproject.org': 'http://llhb3u5h3q66ha62.onion/',
	'ooni.torproject.org': 'http://fqnqc7zix2wblwex.onion/',
	'people.torproject.org': 'http://sbe5fi5cka5l3fqe.onion/',
	'rbm.torproject.org': 'http://yabd3wlpvybdnvzg.onion/',
	'research.torproject.org': 'http://wcgqzqyfi7a6iu62.onion/',
	'spec.torproject.org': 'http://s2bweojt5vg52e5i.onion/',
	'staging.crm.torproject.org': 'http://swnwd5bhvjk4dd5o.onion/',
	'staging.donate.torproject.org': 'http://cvtwbn7mgxki7gvc.onion/',
	'stem.torproject.org': 'http://vt5hknv6sblkgf22.onion/',
	'styleguide.torproject.org': 'http://buqlpzbbcyat2jiy.onion/',
	'survey.torproject.org': 'http://bogdyardcfurxcle.onion/',
	'tb-manual.torproject.org': 'http://dgvdmophvhunawds.onion/',
	'test-data.tbb.torproject.org': 'http://fylvgu5r6gcdadeo.onion/',
	'test.crm.torproject.org': 'http://abp7hndzgazze2wy.onion/',
	'test.donate.torproject.org': 'http://p73stlm5nhogxw4w.onion/',
	'testnet.torproject.org': 'http://bo7uextohjpuqvrh.onion/',
	'trac.torproject.org': 'http://ea5faa5po25cf7fb.onion/',
	'webstats.torproject.org': 'http://gbinixxw7gnsh5jr.onion/',
	'www-staging.torproject.org': 'http://krkzagd5yo4bvypt.onion/',
	'www.onion-router.net': 'http://hzmun3rnnxjhkyhg.onion/',
	'www.torproject.org': 'http://expyuzz4wqqyqhjn.onion/',}