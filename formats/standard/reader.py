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

from veusz.document import datasets

import veusz.utils as utils

# a regular expression for splitting descriptor into tokens
descrtokens_split_re = re.compile(r'''
(
 `[^`]*`       |  # quoted name
 [ ,]          |  # comma or space
 \([a-z]+?\)   |  # data type
 \+- | \+ | -  |  # error bars
 \[.*?\]          # indices
)
''', re.VERBOSE)

range_re = re.compile(r'''^
 \[
 (-?[0-9]+)? 
 :
 (-?[0-9]+)? 
 \]
$''', re.VERBOSE)


# this is a regular expression to match properly quoted strings
# hopefully a matching expression can be passed to eval
string_re = re.compile(r'''
^
u?"" |            # match empty double-quoted string
u?".*?[^\\]" |    # match double-quoted string, ignoring escaped quotes
u?'' |            # match empty single-quoted string
u?'.*?[^\\]'      # match single-quoted string, ignoring escaped quotes
$
''', re.VERBOSE)

# a line starting with text
text_start_re = re.compile(r'^[A-Za-z]')

# convert data type strings in descriptor to internal datatype
datatype_name_convert = {
    'float': 'float',
    'numeric': 'float',
    'number': 'float',
    'text': 'string',
    'string': 'string',
    'date': 'date',
    'time': 'date'
    }

def guessDataType(val):
    """Try to work out data type from sample value (val)

    Return values are one of
    float, string, or date
    """

    # if the dataset type is specified
    # check for identifiers in dataset name
    # guess the type:
    # obvious float
    try:
        float(val)
        return 'float'
    except ValueError:
        pass

    # do all libcs check for these?
    if val.lower() in ('inf', '+inf', '-inf', 'nan'):
        return 'float'

    # obvious string
    if string_re.match(val):
        return 'string'

    # date
    if utils.isDateTime(val):
        return 'date'

    # assume string otherwise
    return 'string'

def interpretDescriptor(descr):
    """Get a descriptor and create a set of descriptor objects."""

    parts = []

    split = descrtokens_split_re.split(descr.strip())
    tokens = [x for x in split if x != '']
    # make sure that last dataset is added
    tokens += ['DUMMY']

    name = datatype = idxrange = None
    columns = []
    for tokenindex, token in enumerate(tokens):
        # skip spaces
        if token == ' ':
            if tokenindex > 0 and tokens[tokenindex - 1] == ',':
                columns.append(',')
            continue

        # ignore column
        if token == ',':
            if tokenindex == 0 or (tokens[tokenindex - 1] == ',' or
                                    tokens[tokenindex - 1] == ' '):
                columns.append(',')
            continue

        # does token match datatype name?
        if (token[0] == '(' and token[-1] == ')' and
             token[1:-1] in datatype_name_convert):
            datatype = datatype_name_convert[token[1:-1]]
            continue

        # match error bars
        if token in ('+', '-', '+-'):
            columns.append(token)
            continue

        # does token match a range?
        m = range_re.match(token)
        if m:
            if m.group(1):
                startindex = int(m.group(1))
            else:
                startindex = 1
            if m.group(2):
                stopindex = int(m.group(2))
            else:
                stopindex = 999999999
            idxrange = (startindex, stopindex)
            continue

        # quoted dataset name, so remove quotes
        if token[0] == '`' and token[-1] == '`':
            token = token[1:-1]

        # add previous entry
        if name is not None:
            parts.append(DescriptorPart(name, datatype, columns, idxrange))
            name = datatype = idxrange = None
            columns = []

        columns.append('D')
        name = token

    return parts

class DescriptorError(ValueError):
    """Used to indicate an error with the descriptor."""
    pass

class DescriptorPart(object):
    """Represents part of a descriptor."""

    def __init__(self, name, datatype, columns, idxrange):
        """Construct DescriptorPart
        name is dataset name
        datatype is None or one of the possible options
        columns is a list of the columns '+', '-', '+-', ',' or 'D'
         for errors, ignoring a column or a data column
        idxrange is None or a tuple (minidx, maxidx)
        """
        self.name = name
        self.datatype = datatype
        self.columns = tuple(columns)

        self.errorcount = 0

        self.single = idxrange is None
        if self.single:
            self.startindex = self.stopindex = 1
        else:
            self.startindex, self.stopindex = idxrange

    def readFromStream(self, stream, thedatasets, block=None):
        """Read data from stream, and write to thedatasets."""

        # loop over column range
        for index in xrange(self.startindex, self.stopindex + 1):
            # name for variable
            if self.single:
                name = self.name
            else:
                name = '%s_%i' % (self.name, index)

            # if we're reading multiple blocks
            if block is not None:
                name += '_%i' % block

            # loop over columns until we run out, or we don't need any
            for col in self.columns:
                # get next column and return if we run out of data
                val = stream.nextColumn()
                if val is None:
                    return
                # append a suffix to specify whether error or value
                # \0 is used as the user cannot enter it
                fullname = '%s\0%s' % (name, col)

                # get dataset (or get new one)
                try:
                    dataset = thedatasets[fullname]
                except KeyError:
                    dataset = thedatasets[fullname] = []

                if not self.datatype:
                    # try to guess type of data
                    self.datatype = guessDataType(val)

                # convert according to datatype
                if self.datatype == 'float':
                    try:
                        # do conversion
                        dat = float(val)
                    except ValueError:
                        dat = N.nan
                        self.errorcount += 1

                elif self.datatype == 'string':
                    if string_re.match(val):
                        # possible security issue:
                        # regular expression checks this is safe
                        try:
                            dat = eval(val)
                        except:
                            dat = val
                    else:
                        dat = val

                elif self.datatype == 'date':
                    dat = utils.dateStringToDate(val)

                # add data into dataset
                dataset.append(dat)

    def setInDocument(self, thedatasets, document, block=None,
                      linkedfile=None,
                      prefix="", suffix="", tail=None):
        """Set the read-in data in the document."""

        # we didn't read any data
        if self.datatype is None:
            return []

        names = []
        for index in xrange(self.startindex, self.stopindex + 1):
            # name for variable
            if self.single:
                name = '%s' % (self.name,)
            else:
                name = '%s_%i' % (self.name, index)
            if block is not None:
                name += '_%i' % block

            # does the dataset exist?
            if name + '\0D' in thedatasets:
                vals = thedatasets[name + '\0D']
                pos = neg = sym = None

                # retrieve the data for this dataset
                if name + '\0+' in thedatasets: pos = thedatasets[name + '\0+']
                if name + '\0-' in thedatasets: neg = thedatasets[name + '\0-']
                if name + '\0+-' in thedatasets: sym = thedatasets[name + '\0+-']

                # make sure components are the same length
                minlength = 99999999999999
                for ds in vals, pos, neg, sym:
                    if ds is not None and len(ds) < minlength:
                        minlength = len(ds)
                for ds in vals, pos, neg, sym:
                    if ds is not None and len(ds) != minlength:
                        del ds[minlength:]

                # only remember last N values
                if tail is not None:
                    vals = vals[-tail:]
                    if sym is not None: sym = sym[-tail:]
                    if pos is not None: pos = pos[-tail:]
                    if neg is not None: neg = neg[-tail:]

                # create the dataset
                if self.datatype == 'float':
                    ds = datasets.Dataset(data=vals, serr=sym,
                                           nerr=neg, perr=pos,
                                           linked=linkedfile)
                elif self.datatype == 'date':
                    ds = datasets.DatasetDateTime(data=vals,
                                                   linked=linkedfile)
                elif self.datatype == 'string':
                    ds = datasets.DatasetText(data=vals,
                                               linked=linkedfile)
                else:
                    raise RuntimeError, "Invalid data type"

                finalname = prefix + name + suffix
                document.setData(finalname, ds)
                names.append(finalname)
            else:
                break

        return names

class SimpleRead(object):
    '''Class to read in datasets from a stream.

    The descriptor specifies the format of data to read from the stream
    Read the docstring for this module for information

    tail attribute if set says to only use last tail data points when setting
    '''

    def __init__(self, descriptor):
        # convert descriptor to part objects
        descriptor = descriptor.strip()
        self._parseDescriptor(descriptor)

        # construct data names automatically
        self.autodescr = (descriptor == '')

        # get read for reading data
        self.clearState()

    def clearState(self):
        """Start reading from scratch."""
        self.datasets = {}
        self.blocks = None
        self.tail = None

    def _parseDescriptor(self, descriptor):
        """Take a descriptor, and parse it into its individual parts."""
        self.parts = interpretDescriptor(descriptor)

    def readData(self, stream, useblocks=False, ignoretext=False):
        """Read in the data from the stream.

        If useblocks is True, data are read as separate blocks.
        Dataset names are appending with an underscore and a block
        number if set.
        """

        self.ignoretext = ignoretext
        if useblocks:
            self._readDataBlocked(stream, ignoretext)
        else:
            self._readDataUnblocked(stream, ignoretext)

    def _readDataUnblocked(self, stream, ignoretext):
        """Read in that data from the stream."""

        allparts = list(self.parts)

        # loop over lines
        while stream.newLine():
            if stream.remainingline[:1] == ['descriptor']:
                # a change descriptor statement
                descriptor = ' '.join(stream.remainingline[1:])
                self._parseDescriptor(descriptor)
                allparts += self.parts
                self.autodescr = False
            elif (self.ignoretext and len(stream.remainingline) > 0 and
                   text_start_re.match(stream.remainingline[0]) and
                   len(self.parts) > 0 and
                   self.parts[0].datatype != 'string' and
                   stream.remainingline[0] not in ('inf', 'nan')):
                # ignore the line if it is text and ignore text is on
                # and first column is not text
                pass
            else:
                # normal text
                for p in self.parts:
                    p.readFromStream(stream, self.datasets)

                # automatically create parts if data are remaining
                if self.autodescr:
                    while len(stream.remainingline) > 0:
                        p = DescriptorPart(
                            str(len(self.parts) + 1), None, 'D', None)
                        p.readFromStream(stream, self.datasets)
                        self.parts.append(p)
                        allparts.append(p)

            stream.flushLine()

        self.parts = allparts
        self.blocks = None

    def _readDataBlocked(self, stream, ignoretext):
        """Read in the data, using blocks."""

        allparts = list(self.parts)

        blocks = {}
        block = 1
        while stream.newLine():
            line = stream.remainingline

            # if this is a blank line, separating data then advance to a new
            # block
            if len(line) == 0 or line[0].lower() == 'no':
                # blank lines separate blocks
                if block in blocks:
                    block += 1
            else:
                # read in data
                for p in self.parts:
                    p.readFromStream(stream, self.datasets, block=block)

                # automatically create parts if data are remaining
                if self.autodescr:
                    while len(stream.remainingline) > 0:
                        p = DescriptorPart(
                            str(len(self.parts) + 1), None, 'D', None)
                        p.readFromStream(stream, self.datasets, block=block)
                        self.parts.append(p)
                        allparts.append(p)

                blocks[block] = True

            # lose remaining data
            stream.flushLine()

        self.parts = allparts
        self.blocks = blocks.keys()

    def getInvalidConversions(self):
        """Return the number of invalid conversions after reading data.

        Returns a dict of dataset, number values."""

        out = {}
        for p in self.parts:
            out[p.name] = p.errorcount
        return out

    def getDatasetCounts(self):
        """Get a dict of the datasets read (main data part) and number
        of entries read."""
        out = {}
        for name, data in self.datasets.iteritems():
            if name[-2:] == '\0D':
                out[name[:-2]] = len(data)
        return out

    def setInDocument(self, document, linkedfile=None,
                      prefix='', suffix=''):
        """Set the data in the document.

        Returns list of variable names read.
        """

        # iterate over blocks used
        if self.blocks is None:
            blocks = [None]
        else:
            blocks = self.blocks

        # if automatically making parts, use a prefix/suffix if not set
        if self.autodescr and prefix == '' and suffix == '':
            prefix = 'col'

        names = []
        for block in blocks:
            for part in self.parts:
                names += part.setInDocument(
                    self.datasets, document,
                    block=block,
                    linkedfile=linkedfile,
                    prefix=prefix, suffix=suffix,
                    tail=self.tail)

        return names

