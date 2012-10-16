#    Copyright (C) 2004 Jeremy S. Sanders
#    Email: Jeremy Sanders <jeremy@jeremysanders.net>
#
#    This program is free software; you can redistribute it and/or modify
#    it under the terms of the GNU General Public License as published by
#    the Free Software Foundation; either version 2 of the License, or
#    (at your option) any later version.
#
#    This program is distributed in the hope that it will be useful,
#    but WITHOUT ANY WARRANTY; without even the implied warranty of
#    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#    GNU General Public License for more details.
#
#    You should have received a copy of the GNU General Public License along
#    with this program; if not, write to the Free Software Foundation, Inc.,
#    51 Franklin Street, Fifth Floor, Boston, MA 02110-1301 USA.
##############################################################################

"""SimpleRead: a class for the reading of data formatted in a simple way

To read the data it takes a descriptor which takes the form of

varname<error specifiers><[repeater]>
where <> marks optional arguments, e.g.

x+- y+,- z+-[1:5]
x(text) y(date) z(number),+-

+- means symmetric error bars
+,- means asymmetric error bars
, is a separator
(text) or (date) specifies datatype

z+-[1:5] means read z_1+- z_2+- ... z_5+-

Indicices can be unspecified, [:], [1:], [:5]
The first 3 mean the same thing, the last means read from 1 to 5

Commas are now optional in 1.6, so descriptors can look like
x +- y + -
"""

import re
import cStringIO
import numpy as N

import datasets


class Stream(object):
    """This object reads through an input data source (override
    readLine) and interprets data from the source."""

    # this is a regular expression for finding data items in data stream
    # I'll try to explain this bit-by-bit (these are ORd, and matched in order)
    find_re = re.compile(r'''
    `.+?`[^ \t\n\r#!%;]* | # match dataset name quoted in back-ticks
                           # we also need to match following characters to catch
                           # corner cases in the descriptor
    u?"" |          # match empty double-quoted string
    u?".*?[^\\]" |  # match double-quoted string, ignoring escaped quotes
    u?'' |          # match empty single-quoted string
    u?'.*?[^\\]' |  # match single-quoted string, ignoring escaped quotes
    [#!%;](?=descriptor) | # match separately comment char before descriptor
    [#!%;].* |      # match comment to end of line
    [^ \t\n\r#!%;]+ # match normal space/tab separated items
    ''', re.VERBOSE)

    def __init__(self):
        """Initialise stream object."""
        self.remainingline = []

    def nextColumn(self):
        """Return value of next column of line."""
        try:
            return self.remainingline.pop(0)
        except IndexError:
            return None

    def allColumns(self):
        """Get all columns of current line (none are discarded)."""
        return self.remainingline

    def flushLine(self):
        """Forget the rest of the line."""
        self.remainingline = []

    def readLine(self):
        """Read the next line of the data source.
        StopIteration is raised if there is no more data."""
        pass

    def newLine(self):
        """Read in, and split the next line."""

        while True:
            # get next line from data source
            try:
                line = self.readLine()
            except StopIteration:
                # end of file
                return False

            # break up and append to buffer (removing comments)
            cmpts = self.find_re.findall(line)
            self.remainingline += [ x for x in cmpts if x[0] not in '#!%;']

            if self.remainingline and self.remainingline[-1] == '\\':
                # this is a continuation: drop this item and read next line
                self.remainingline.pop()
            else:
                return True

class FileStream(Stream):
    """A stream based on a python-style file (or iterable)."""

    def __init__(self, file):
        """File can be any iterator-like object."""
        Stream.__init__(self)
        self.file = file

    def readLine(self):
        """Read the next line of the data source.
        StopIteration is raised if there is no more data."""
        return self.file.next()

class StringStream(FileStream):
    '''For reading data from a string.'''

    def __init__(self, text):
        """A stream which reads in from a text string."""

        FileStream.__init__(self, cStringIO.StringIO(text))

