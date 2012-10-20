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

"""params for HDF5 data import dialog."""

from veusz.document.importparams import ImportParamsBase

class ImportParamsHDF5(ImportParamsBase):
    """FITS file import parameters.

    Additional parameters:
     dsname: name of dataset
     hdu: name/number of hdu
     datacol: name of column
     symerrcol: symmetric error column
     poserrcol: positive error column
     negerrcol: negative error column
    """

    defaults = {
        'dsname': None,
        'hdu': None,
        'datacol': None,
        'symerrcol': None,
        'poserrcol': None,
        'negerrcol': None,
        }
    defaults.update(ImportParamsBase.defaults)
