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

"""This module contains routines for importing CSV data files
in an easy-to-use manner."""

import numpy as N

from veusz.document import datasets

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
