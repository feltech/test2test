import re

DELETE_ME_TOKEN = "//>>>>>>>>>>>>>DELETE_ME_TOKEN\n"

class SimpleMapping(object):
	tokenFrom = None
	tokenTo = None

	def check(self, line):
		return re.search("^(.*)%s$" % self.tokenFrom, line)

	def convert(self, match):
		return '%s%s\n' % (self.tokenTo, match.group(1))

	def process(self, lines, lineIdx):
		line = lines[lineIdx]
		match = self.check(line)
		if match is not None:
			lines[lineIdx] = self.convert(match)
			return lineIdx
		return False


class BaseMapping(SimpleMapping):

	def check(self, line):
		return re.search(
			"(.*)%s[^_]*?\(([\s\S]*)\)(.*)" % self.tokenFrom, line, re.MULTILINE
		)

	def convert(self, match):
		return "%s%s(%s)%s\n" % (
			match.group(1), self.tokenTo, match.group(2), match.group(3)
		)

	def process(self, lines, lineIdx):
		lastLineIdx = lineIdx
		line = lines[lineIdx]
		if not self.tokenFrom in line:
			return None

		opens = line.count("(")
		closes = line.count(")")

		while (opens == 0 or opens != closes) and lastLineIdx < len(lines) - 1:
			lastLineIdx += 1
			nextLine = lines[lastLineIdx]
			line += nextLine
			opens += nextLine.count("(")
			closes += nextLine.count(")")

		match = self.check(line)
		if match is not None:
			lines[lineIdx] = self.convert(match)
			lines[lineIdx + 1:lastLineIdx + 1] = [DELETE_ME_TOKEN] * (lastLineIdx - lineIdx)
			return lastLineIdx
		return None

	def _parseArgs(self, param):
		args = param.split(",")

		for argIdx, _ in enumerate(args):
			argsBefore = ",".join(args[0:argIdx + 1])
			argsAfter = ",".join(args[argIdx + 1:len(args)])
			if (
				argsBefore.count('(') == argsBefore.count(')') and
				argsAfter.count('(') == argsAfter.count(')') and
				argsBefore.count('"') % 2 == 0 and argsAfter.count('"') % 2 == 0
			):
				return argsBefore, argsAfter


class BOOST_AUTO_TEST_SUITE(BaseMapping):
	tokenFrom = "BOOST_AUTO_TEST_SUITE"

	def __init__(self):
		self.tabs = None
		self.name = None

	def check(self, line):
		match = re.search("(.*)%s\s*\((?:test_)?(.*)\)(.*)" % self.tokenFrom, line, re.MULTILINE)
		if match is not None:
			self.tabs = match.group(1)
			self.name = match.group(2)
		return match
