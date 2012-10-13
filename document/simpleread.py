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

#####################################################################
# 2D data reading

class Read2DError(ValueError):
    pass

class SimpleRead2D(object):
    def __init__(self, name, params):
        """Read dataset with name given.
        params is a ImportParams2D object
        """
        self.name = name
        self.params = params.copy()

    ####################################################################
    # Follow functions are for setting parameters during reading of data

    def _paramXRange(self, cols):
        try:
            self.params.xrange = (float(cols[1]), float(cols[2]))
        except ValueError:
            raise Read2DError, "Could not interpret xrange"

    def _paramYRange(self, cols):
        try:
            self.params.yrange = (float(cols[1]), float(cols[2]))
        except ValueError:
            raise Read2DError, "Could not interpret yrange"

    def _paramInvertRows(self, cols):
        self.params.invertrows = True

    def _paramInvertCols(self, cols):
        self.params.invertcols = True

    def _paramTranspose(self, cols):
        self.params.transpose = True

    ####################################################################

    def readData(self, stream):
        """Read data from stream given

        stream consists of:
        optional:
         xrange A B   - set the range of x from A to B
         yrange A B   - set the range of y from A to B
         invertrows   - invert order of the rows
         invertcols   - invert order of the columns
         transpose    - swap rows and columns
        then:
         matrix of columns and rows, separated by line endings
         the rows are in reverse-y order (highest y first)
         blank line stops reading for further datasets
        """

        settings = {
            'xrange': self._paramXRange,
            'yrange': self._paramYRange,
            'invertrows': self._paramInvertRows,
            'invertcols': self._paramInvertCols,
            'transpose': self._paramTranspose
            }

        rows = []
        # loop over lines
        while stream.newLine():
            cols = stream.allColumns()

            if len(cols) > 0:
                # check to see whether parameter is set
                c = cols[0].lower()
                if c in settings:
                    settings[c](cols)
                    stream.flushLine()
                    continue
            else:
                # if there's data and we get to a blank line, finish
                if len(rows) != 0:
                    break

            # read columns
            line = []
            while True:
                v = stream.nextColumn()
                if v is None:
                    break
                try:
                    line.append(float(v))
                except ValueError:
                    raise Read2DError, "Could not interpret number '%s'" % v

            # add row to dataset
            if len(line) != 0:
                if self.params.invertcols:
                    line.reverse()
                rows.insert(0, line)

        # swap rows if requested
        if self.params.invertrows:
            rows.reverse()

        # dodgy formatting probably...
        if len(rows) == 0:
            raise Read2DError, "No data could be imported for dataset"

        # convert the data to a numpy
        try:
            self.data = N.array(rows)
        except ValueError:
            raise Read2DError, "Could not convert data to 2D matrix"

        # obvious check
        if len(self.data.shape) != 2:
            raise Read2DError, "Dataset was not 2D"

        # transpose matrix if requested
        if self.params.transpose:
            self.data = N.transpose(self.data).copy()

    def setInDocument(self, document, linkedfile=None):
        """Set the data in the document.

        Returns list containing name of dataset read
        """

        ds = datasets.Dataset2D(self.data, xrange=self.params.xrange,
                                yrange=self.params.yrange)
        ds.linked = linkedfile

        fullname = self.params.prefix + self.name + self.params.suffix
        document.setData(fullname, ds)

        return [fullname]
