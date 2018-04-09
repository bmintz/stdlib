#!/usr/bin/env python3
# encoding: utf-8

from collections import Iterable as _Iterable
from dis import dis as _dis
import functools as _functools
from inspect import signature as _signature
from io import StringIO as _StringIO
import itertools as _itertools
import operator as _operator
from pprint import PrettyPrinter
import pyperclip as _clipboard
import random as _random
import re as _re
import string as _string
import time as _time
import sys as _sys


def dis(x):
	"""dis.dis, but returns a string instead of printing"""
	with _StringIO() as out:
		_dis(x, file=out)
		return out.getvalue()


def shuffled(t):
	"""return a shuffled copy of list t"""
	t = t[:]
	_random.shuffle(t)
	return t


class AutoRepr(type):
	"""a metaclass that can be used if you cba to write a __repr__ func"""

	def __new__(cls, name, bases, attrs):
		newcls = super().__new__(cls, name, bases, attrs)

		# woah! i had no idea @wraps could be used like this
		@_functools.wraps(newcls.__repr__)
		def custom_repr(self):
			dct = self.__dict__ or ''
			return '{}.{}({})'.format(self.__class__.__module__, name, dct)

		newcls.__repr__ = custom_repr
		return newcls


class AttributeBox:
	"""an empty class, suitable for making objects with mutable attributes

	For example, this is not possible to do with `x = object()`:
	>>> x = AttributeBox()
	>>> x.foo = lambda self, bar: print(bar)
	>>> x.foo('baz')
	baz
	"""
	pass


def copy_result(func):
	"""a decorator that copies the result of func to the clipboard
	if copy=False, don't copy
	if no args are given, use clipboard.paste() insetead"""
	@_functools.wraps(func)
	def wrapped(*args, **kwargs):
		copy = kwargs.pop('copy', True)

		if not args:
			args = [_clipboard.paste()]
		result = func(*args, **kwargs)

		if copy:
			_clipboard.copy(str(result))
			# return

		return result
	return wrapped


@copy_result
def mock(text):
	def uplower(text):
		return _random.choice((str.upper, str.lower))(text)
	return ''.join(map(uplower, text))


@copy_result
def escape_mentions(text):
	"""Escapes @mentions in text. Useful for Discord"""
	return text.replace('@', '@\N{zero width non-joiner}')


@copy_result
def strip_colors(text):
	"""removes irc color codes from text"""
	# credit to @smerity on SO: https://stackoverflow.com/a/970723
	return _re.sub(r'\x03(?:\d{1,2}(?:,\d{1,2})?)?', '', text, _re.UNICODE)


@copy_result
def spaced_out(text):
	"""n e e d   i   s a y   m o r e ?"""
	return ' '.join(text)


@copy_result
def aesthetic(text):
	"""ｍａｋｅｓ　ｔｅｘｔ　ｆａｎｃｙ"""
	translations = {i: chr(i + 0xFEE0) for i in range(0x21, 0x7f)}
	# ideographic space != 0x20 + 0xFEE0
	translations[' '] = '\N{ideographic space}'
	return text.translate(translations)


@copy_result
def regional(text):
	"""converts text to regional indicators"""
	_regionals = {
		i + ord('a'): i + ord('\N{regional indicator symbol letter a}')
		for i in range(26)}
	flags = text.translate(regionals)
	# prevent FR -> French Flag emoji
	return '\N{zero width non-joiner}'.join(flags)


class Singleton(type):
	"""A singleton metaclass. Use it like `class Foo(metaclass=Singleton):`"""

	_instances = {}
	def __call__(cls, *args, **kwargs):
		if cls not in cls._instances:
			cls._instances[cls] = super().__call__(*args, **kwargs)
		return cls._instances[cls]


def pipe(inp, *funcs):
	"""composes inp over func[::-1]

	>>> pipe(' foo ', (str.lstrip, str.rstrip, str.upper)
	'FOO'
	>>> str.upper(str.rstrip(str.lstrip(' foo ')))
	'FOO'
	"""
	for func in funcs:
		inp = func(inp)
	return inp


def timeit(func):
	@_functools.wraps(func)
	def timed(*args, **kwargs):
		start_time = _time.time()
		result = func(*args, **kwargs)
		log(func.__name__, 'ran in', _time.time() - start_time, 's')
		return result
	return timed

def none(iterable):
	"""a silly little alias for `not any(iterable)`"""
	return not any(iterable)


def log(*args, **kwargs):
	kwargs['file'] = _sys.stderr
	print(*args, **kwargs)


def do_until(x, func, condition):
	# lol this docstring just puts the code into English
	"""assign x to func(x) until condition(x) is true. return x"""
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
	"""flattens l. treats str, bytes as non-iterable.
	use more_itertools.flatten instead"""

	for el in l:
		if isinstance(el, _Iterable) and not isinstance(el, (str, bytes)):
			yield from flatten(el)
		else:
			yield el


def input_iter():
	"""yield successive lines of input until there is no more.
	useful for reading files from stdin.
	p.s. just iterate over sys.stdin, ya don't need this."""
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


@copy_result
def clap(text):
	"""just👏a👏fucking👏meme👏"""
	return '\N{clapping hands sign}'.join(text.split())


@copy_result
def animate(text):
	emoji = []
	format = ':anim_{}:'
	alnum = set(_string.ascii_lowercase+_string.digits)
	punctuation = {'!': 'bang', '?': 'ques', '&': 'amp'}
	for letter in text:
		letter = letter.lower()
		if letter in alnum:
			emoji.append(format.format(letter))
		elif letter in punctuation:
			emoji.append(format.format(punctuation[letter]))
		else:
			emoji.append(letter)
	return ''.join(emoji)


@copy_result
def rot(s, n=13):
	def rot(char):
		if char not in _string.ascii_letters:
			return char
		alphabet = (_string.ascii_lowercase if char.islower() else _string.ascii_uppercase)

		pos = alphabet.index(char)
		return alphabet[(pos + n) % len(alphabet)]

	return ''.join(map(rot, s))


@copy_result
def emoji_cipher(text):
	"""Return text + 1F300 (start of emoji block)"""
	return ''.join(chr(ord(char) + 0x1F300) for char in text)

@copy_result
def emoji_decipher(text):
	"""Return the inverse of emoji_cipher()"""
	return ''.join(chr(ord(char) - 0x1F300) for char in text)


def status_line(*args):
	log(*args, end='\b'*len('\n'.join(map(str, args))))


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
	'www.torproject.org': 'http://expyuzz4wqqyqhjn.onion/',

	'0xacab.org': 'vivmyccb3jdb7yij.onion',
	'account.riseup.net': 'j6uhdvbhz74oefxf.onion',
	'black.riseup.net': 'cwoiopiifrlzcuos.onion',
	'help.riseup.net': 'nzh3fv6jc6jskki3.onion',
	'imap.riseup.net': 'zsolxunfmbfuq7wf.onion',
	'lists.riseup.net': 'xpgylzydxykgdqyg.onion',
	'mail.riseup.net': 'zsolxunfmbfuq7wf.onion',
	'mx1.riseup.net': 'wy6zk3pmcwiyhiao.onion',
	'pad.riseup.net': '5jp7xtmox6jyoqd5.onion',
	'pop.riseup.net': 'zsolxunfmbfuq7wf.onion',
	'riseup.net': 'nzh3fv6jc6jskki3.onion',
	'share.riseup.net': '6zc6sejeho3fwrd4.onion',
	'smtp.riseup.net': 'zsolxunfmbfuq7wf.onion',
	'we.riseup.net': '7lvd7fa5yfbdqaii.onion',
	'xmpp.riseup.net': '4cjw6cwpeaeppfqz.onion'}
