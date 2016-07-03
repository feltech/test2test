import re

import common
from common import BaseMapping, DELETE_ME_TOKEN, SimpleMapping


class include_boost(SimpleMapping):
	tokenFrom = '#include\s+[<"]boost/test/unit_test.hpp[>"]'
	tokenTo = '#include "catch.hpp"'


# class BOOST_AUTO_TEST_SUITE(common.BOOST_AUTO_TEST_SUITE):
# 	def convert(self, match):
# 		return DELETE_ME_TOKEN
#
#
# class BOOST_AUTO_TEST_SUITE_END(BaseMapping):
# 	tokenFrom = "BOOST_AUTO_TEST_SUITE_END"
#
# 	def convert(self, match):
# 		return DELETE_ME_TOKEN
#
#
# class BOOST_AUTO_TEST_CASE(BaseMapping):
# 	tokenFrom = "BOOST_AUTO_TEST_CASE"
# 	tokenTo = "TEST_CASE"
#
# 	def __init__(self, suiteName):
# 		self.suiteName = suiteName
#
# 	def check(self, line):
# 		match = super(BOOST_AUTO_TEST_CASE, self).check(line)
# 		self.tabs = match.group(1)
# 		return match
#
# 	def convert(self, match):
# 		return '%s%s("%s", "[%s]")%s\n' % (
# 			match.group(1), self.tokenTo, match.group(2), self.suiteName, match.group(3)
# 		)
#
#
# class BOOST_FIXTURE_TEST_CASE(BaseMapping):
# 	tokenFrom = "BOOST_FIXTURE_TEST_CASE"
# 	tokenTo = "TEST_CASE_METHOD"
#
# 	def __init__(self, suiteName):
# 		self.suiteName = suiteName
# 		self.tabs = None
#
# 	def check(self, line):
# 		match = super(BOOST_FIXTURE_TEST_CASE, self).check(line)
# 		if match is not None:
# 			self.tabs = match.group(1)
# 		return match
#
# 	def convert(self, match):
# 		args = match.group(2).split(",")
#
# 		return '%s%s(%s, "%s", "[%s][create]")%s\n' % (
# 			match.group(1), self.tokenTo, args[1].lstrip(" "), args[0], self.suiteName,
# 			match.group(3)
# 		)


class BOOST_AUTO_TEST_SUITE(common.BOOST_AUTO_TEST_SUITE):
	tokenTo = "SCENARIO"
	def convert(self, match):
		return '%s%s("%s")\n%s{%s\n' % (
			match.group(1), self.tokenTo, match.group(2), match.group(1), match.group(3)
		)


class BOOST_AUTO_TEST_SUITE_END(BaseMapping):
	tokenFrom = "BOOST_AUTO_TEST_SUITE_END"

	def convert(self, match):
		return "%s}\n" % match.group(1)


class BOOST_AUTO_TEST_CASE(BaseMapping):
	tokenFrom = "BOOST_AUTO_TEST_CASE"
	tokenTo = "WHEN"

	def __init__(self, suiteName):
		self.suiteName = suiteName

	def check(self, line):
		match = super(BOOST_AUTO_TEST_CASE, self).check(line)
		self.tabs = match.group(1)
		return match

	def convert(self, match):
		return '%s%s("%s")%s\n' % (
			match.group(1), self.tokenTo, match.group(2), match.group(3)
		)

class BOOST_FIXTURE_TEST_CASE(BaseMapping):
	tokenFrom = "BOOST_FIXTURE_TEST_CASE"
	tokenTo = "TEST_CASE_METHOD"

	def __init__(self, suiteName):
		self.suiteName = suiteName
		self.tabs = None
		self.startLineIdx = None
		self.lastLineIdx = None
		self.name = None

	def check(self, line):
		match = super(BOOST_FIXTURE_TEST_CASE, self).check(line)
		if match is not None:
			self.tabs = match.group(1)
		return match

	def convert(self, match):
		args = match.group(2).split(",")
		self.name = args[0].strip()
		self.fixtureName = args[1].strip()

		return '%s%s(%s, "%s: %s", "[%s]")%s\n' % (
			match.group(1), self.tokenTo, self.suiteName + self.fixtureName, self.suiteName,
			self.name, self.suiteName, match.group(3)
		)

	def process(self, lines, lineIdx):
		lastLineIdx = super(BOOST_FIXTURE_TEST_CASE, self).process(lines, lineIdx)
		if lastLineIdx is None:
			return None

		self.startLineIdx = lineIdx
		self.lastLineIdx = lastLineIdx
		line = lines[lastLineIdx]

		opens = line.count("{")
		closes = line.count("}")

		while (opens == 0 or opens != closes) and self.lastLineIdx < len(lines) - 1:
			self.lastLineIdx += 1
			nextLine = lines[self.lastLineIdx]
			line += nextLine
			opens += nextLine.count("{")
			closes += nextLine.count("}")

		return lastLineIdx

	def move(self, lines):
		newLines = "".join(lines[self.startLineIdx:self.lastLineIdx+1]).split("\n")
		line = "\n".join([
			line.replace(self.tabs, "", 1)
			for line in newLines
			if line != DELETE_ME_TOKEN[:-1]
		])

		lines[self.startLineIdx:self.lastLineIdx+1] = (
			[DELETE_ME_TOKEN] * (self.lastLineIdx - self.startLineIdx + 1)
		)

		lines.append("\n" + line + "\n")

		print('  Moved fixture test "%s" out of suite "%s"' % (self.name, self.suiteName))


class BOOST_CHECK(BaseMapping):
	tokenFrom = "BOOST_CHECK"
	tokenTo = "CHECK"


class BOOST_CHECK_EQUAL(BaseMapping):
	tokenFrom = "BOOST_CHECK_EQUAL"
	tokenTo = "CHECK"

	def convert(self, match):
		arg1, arg2 = self._parseArgs(match.group(2))

		return "%s%s(%s == %s)%s\n" % (
			match.group(1), self.tokenTo, arg1, arg2.lstrip(" "), match.group(3)
		)


class BOOST_REQUIRE_EQUAL(BaseMapping):
	tokenFrom = "BOOST_REQUIRE_EQUAL"
	tokenTo = "REQUIRE"

	def convert(self, match):
		arg1, arg2 = self._parseArgs(match.group(2))

		return "%s%s(%s == %s)%s\n" % (
			match.group(1), self.tokenTo, arg1, arg2.lstrip(" "), match.group(3)
		)


class BOOST_CHECK_CLOSE(BaseMapping):
	tokenFrom = "BOOST_CHECK_CLOSE"
	tokenTo = "CHECK"

	def convert(self, match):
		arg1, argRest = self._parseArgs(match.group(2))
		arg2, arg3 = self._parseArgs(argRest)

		return "%s%s(%s == Approx(%s).epsilon(%s))%s\n" % (
			match.group(1), self.tokenTo, arg1, arg2.strip(), arg3.strip(), match.group(3)
		)


class BOOST_CHECK_CLOSE_FRACTION(BOOST_CHECK_CLOSE):
	tokenFrom = "BOOST_CHECK_CLOSE_FRACTION"
	tokenTo = "CHECK"


class BOOST_CHECK_LE(BaseMapping):
	tokenFrom = "BOOST_CHECK_LE"
	tokenTo = "CHECK"

	def convert(self, match):
		arg1, arg2 = self._parseArgs(match.group(2))

		return "%s%s(%s <= %s)%s\n" % (
			match.group(1), self.tokenTo, arg1, arg2.lstrip(" "), match.group(3)
		)


class BOOST_CHECK_NE(BaseMapping):
	tokenFrom = "BOOST_CHECK_NE"
	tokenTo = "CHECK"

	def convert(self, match):
		arg1, arg2 = self._parseArgs(match.group(2))

		return "%s%s(%s != %s)%s\n" % (
			match.group(1), self.tokenTo, arg1, arg2.lstrip(" "), match.group(3)
		)


class BOOST_CHECK_MESSAGE(BaseMapping):
	tokenFrom = "BOOST_CHECK_MESSAGE"
	tokenTo = "CHECK"

	def convert(self, match):
		args = match.group(2)
		pred, message = self._parseArgs(args)

		return '%sINFO(%s);\n%s%s(%s)%s\n' % (
			match.group(1), message, match.group(1), self.tokenTo, pred, match.group(3)
		)


class BOOST_TEST_MESSAGE(BaseMapping):
	tokenFrom = "BOOST_TEST_MESSAGE"
	tokenTo = "INFO"


class BOOST_CHECK_SMALL(BaseMapping):
	tokenFrom = "BOOST_CHECK_SMALL"
	tokenTo = "CHECK"

	def convert(self, match):
		arg1, arg2 = self._parseArgs(match.group(2))

		return "%s%s(%s == Approx(0).epsilon(%s))%s\n" % (
			match.group(1), self.tokenTo, arg1, arg2.strip(), match.group(3)
		)


class BOOST_CHECK_PREDICATE(BaseMapping):
	tokenFrom = "BOOST_CHECK_PREDICATE"
	tokenTo = "CHECK"

	def convert(self, match):
		arg1, arg2 = self._parseArgs(match.group(2))

		return "%s%s(%s(%s))%s\n" % (
			match.group(1), self.tokenTo, arg1.lstrip(" "), arg2.lstrip(" "), match.group(3)
		)


MAPPINGS = [
	BOOST_CHECK,
	BOOST_AUTO_TEST_SUITE,
	BOOST_AUTO_TEST_SUITE_END,
	BOOST_CHECK_CLOSE,
	BOOST_CHECK_CLOSE_FRACTION,
	BOOST_CHECK_EQUAL,
	BOOST_CHECK_LE,
	BOOST_CHECK_MESSAGE,
	BOOST_CHECK_NE,
	BOOST_CHECK_PREDICATE,
	BOOST_CHECK_SMALL,
	BOOST_REQUIRE_EQUAL,
	BOOST_TEST_MESSAGE
]


def convert(lines):

	for lineIdx, line in enumerate(lines):
		include_boost().process(lines, lineIdx)

	suite = None
	case = None
	lineIdx = -1
	fixtureTests = []

	while lineIdx < len(lines) - 1:
		lineIdx += 1

		newSuite = BOOST_AUTO_TEST_SUITE()
		lastLineIdx = newSuite.process(lines, lineIdx)
		if lastLineIdx is not None:
			suite = newSuite
			continue

		if suite is None:
			continue

		lastLineIdx = BOOST_AUTO_TEST_SUITE_END().process(lines, lineIdx)
		if lastLineIdx is not None:
			suite = None
			lineIdx = lastLineIdx
			continue

		newCase = BOOST_AUTO_TEST_CASE(suite.name)
		lastLineIdx = newCase.process(lines, lineIdx)
		if lastLineIdx is None:
			newCase = BOOST_FIXTURE_TEST_CASE(suite.name)
			lastLineIdx = newCase.process(lines, lineIdx)
			if lastLineIdx is not None:
				fixtureTests.append(newCase)

		if lastLineIdx is not None:
			case = newCase
			case.tabs = case.tabs.replace(suite.tabs, "", 1)
			# lines[lineIdx] = lines[lineIdx].replace(case.tabs, "", 1)
			lineIdx = lastLineIdx
			continue

		# if case is None:
		# 	lines[lineIdx] = lines[lineIdx].replace(suite.tabs, "", 1)
		# 	continue

		for mappingCls in MAPPINGS:
			lastLineIdx = mappingCls().process(lines, lineIdx)
			if lastLineIdx is not None:
				# lines[lineIdx] = "\n".join(
				# 	[subline.replace(case.tabs, "", 1) for subline in lines[lineIdx].split("\n")]
				# )

				lineIdx = lastLineIdx
				break
		# else:
		# 	lines[lineIdx] = lines[lineIdx].replace(case.tabs, "", 1)

	for fixtureTest in fixtureTests:
		fixtureTest.move(lines)
