# params for standard data import dialog

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

"""params for standard data import dialog."""

from veusz.document.importparams import ImportParamsBase

class ImportParams2D(ImportParamsBase):
    """2D import parameters.

    additional parameters:
     datastr: text to read from instead of file
     xrange: tuple with range of x data coordinates
     yrange: tuple with range of y data coordinates
     invertrows: invert rows when reading
     invertcols: invert columns when reading
     transpose: swap rows and columns
    """

    defaults = {
        'datasetnames': None,
        'datastr': None,
        'xrange': None,
        'yrange': None,
        'invertrows': False,
        'invertcols': False,
        'transpose': False,
        }
    defaults.update(ImportParamsBase.defaults)
