import re

import common
from common import BaseMapping, DELETE_ME_TOKEN


class include_boost(BaseMapping):
    tokenFrom = '#include\s+[<"]boost/test/unit_test.hpp[>"]'

    def check(self, line):
        return re.search("^(.*)%s$" % self.tokenFrom, line)

    def convert(self, match):
        return '%s#include <gtest/gtest.h>\n%s#include "GTestUtil.hpp"\n' % (
            match.group(1), match.group(1)
        )

    def process(self, lines, lineIdx):
        line = lines[lineIdx]
        match = self.check(line)
        if match is not None:
            lines[lineIdx] = self.convert(match)
            return lineIdx
        return False


class BOOST_AUTO_TEST_SUITE(common.BOOST_AUTO_TEST_SUITE):
    def convert(self, match):
        return DELETE_ME_TOKEN


class BOOST_AUTO_TEST_SUITE_END(BaseMapping):
    tokenFrom = "BOOST_AUTO_TEST_SUITE_END"

    def convert(self, match):
        return DELETE_ME_TOKEN


class BOOST_AUTO_TEST_CASE(BaseMapping):
    tokenFrom = "BOOST_AUTO_TEST_CASE"
    tokenTo = "TEST"

    def __init__(self, suiteName):
        self.suiteName = suiteName

    def check(self, line):
        match = super(BOOST_AUTO_TEST_CASE, self).check(line)
        self.tabs = match.group(1)
        return match

    def convert(self, match):
        return "%s%s(%s, %s)%s\n" % (
            match.group(1), self.tokenTo, self.suiteName, match.group(2), match.group(3)
        )


class BOOST_FIXTURE_TEST_CASE(BaseMapping):
    tokenFrom = "BOOST_FIXTURE_TEST_CASE"
    tokenTo = "TEST_F"

    def __init__(self, suiteName):
        self.suiteName = suiteName
        self.prevFixtureName = None
        self.tabs = None

    def check(self, line):
        match = super(BOOST_FIXTURE_TEST_CASE, self).check(line)
        if match is not None:
            self.tabs = match.group(1)
        return match

    def convert(self, match):
        args = match.group(2).split(",")
        self.prevFixtureName = args[1].strip()
        self.newFixtureName = self.suiteName + self.prevFixtureName
        testName = args[0]

        return "%s%s(%s, %s)%s\n" % (
            match.group(1), self.tokenTo, self.newFixtureName, testName, match.group(3)
        )


class BOOST_CHECK(BaseMapping):
    tokenFrom = "BOOST_CHECK"
    tokenTo = "EXPECT_TRUE"


class BOOST_CHECK_EQUAL(BaseMapping):
    tokenFrom = "BOOST_CHECK_EQUAL"
    tokenTo = "EXPECT_EQ"


class BOOST_REQUIRE_EQUAL(BaseMapping):
    tokenFrom = "BOOST_REQUIRE_EQUAL"
    tokenTo = "ASSERT_EQ"


class BOOST_CHECK_CLOSE(BaseMapping):
    tokenFrom = "BOOST_CHECK_CLOSE"
    tokenTo = "EXPECT_NEAR"


class BOOST_CHECK_CLOSE_FRACTION(BaseMapping):
    tokenFrom = "BOOST_CHECK_CLOSE_FRACTION"
    tokenTo = "EXPECT_NEAR"


class BOOST_CHECK_LE(BaseMapping):
    tokenFrom = "BOOST_CHECK_LE"
    tokenTo = "EXPECT_LE"


class BOOST_CHECK_NE(BaseMapping):
    tokenFrom = "BOOST_CHECK_NE"
    tokenTo = "EXPECT_NE"


class BOOST_CHECK_MESSAGE(BaseMapping):
    tokenFrom = "BOOST_CHECK_MESSAGE"
    tokenTo = "EXPECT_TRUE"

    def convert(self, match):
        args = match.group(2)
        pred, message = self._parseArgs(args)

        return '%s%s(%s) << %s;\n' % (
            match.group(1), self.tokenTo, pred, message
        )


# class BOOST_TEST_MESSAGE(BaseMapping):
#     tokenFrom = "BOOST_TEST_MESSAGE"
#     tokenTo = "RecordProperty"
#     messageNum = 0
#
#     def convert(self, match):
#         BOOST_TEST_MESSAGE.messageNum += 1
#         return '%s%s("message%s", %s)%s\n'% (
#             match.group(1), self.tokenTo, self.messageNum, match.group(2), match.group(3)
#         )


class BOOST_TEST_MESSAGE(BaseMapping):
    tokenFrom = "BOOST_TEST_MESSAGE"
    tokenTo = "TEST_COUT"

    def convert(self, match):
        return "%s%s << %s%s\n" % (
            match.group(1), self.tokenTo, match.group(2), match.group(3)
        )


class BOOST_CHECK_SMALL(BaseMapping):
    tokenFrom = "BOOST_CHECK_SMALL"
    tokenTo = "EXPECT_NEAR"
    messageNum = 0

    def convert(self, match):
        return "%s%s(0, %s)%s\n" % (
            match.group(1), self.tokenTo, match.group(2), match.group(3)
        )


class BOOST_CHECK_PREDICATE(BaseMapping):
    tokenFrom = "BOOST_CHECK_PREDICATE"
    tokenTo = "EXPECT_PRED1"


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


def convert(lines, newFileName):

    for lineIdx, line in enumerate(lines):
        include_boost().process(lines, lineIdx)

    suite = None
    case = None
    lineIdx = -1

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
                print("Fixture case in %s:%s\n  %s => %s" % (
                    newFileName, lineIdx, newCase.prevFixtureName, newCase.newFixtureName
                ))

        if lastLineIdx is not None:
            case = newCase
            case.tabs = case.tabs.replace(suite.tabs, "", 1)
            lines[lineIdx] = lines[lineIdx].replace(case.tabs, "", 1)
            lineIdx = lastLineIdx
            continue

        if case is None:
            lines[lineIdx] = lines[lineIdx].replace(suite.tabs, "", 1)
            continue

        lines[lineIdx] = lines[lineIdx].replace(case.tabs, "", 1)

        for mappingCls in MAPPINGS:
            lastLineIdx = mappingCls().process(lines, lineIdx)
            if lastLineIdx is not None:
                lineIdx = lastLineIdx
                break

