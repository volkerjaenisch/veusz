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

class ImportParamsCSV(ImportParamsBase):
    """CSV import parameters.

    additional parameters:
     readrows: readdata in rows
     delimiter: CSV delimiter
     textdelimiter: delimiter for text
     headerignore: number of lines to ignore after headers
     rowsignore: number of lines to ignore at top fo file
     blanksaredata: treat blank entries as nans
     numericlocale: name of local for numbers
     dateformat: date format string
     headermode: 'multi', '1st' or 'none'
    """

    defaults = {
        'readrows': False,
        'delimiter': ',',
        'textdelimiter': '"',
        'headerignore': 0,
        'rowsignore': 0,
        'blanksaredata': False,
        'numericlocale': 'en_US',
        'dateformat': 'YYYY-MM-DD|T|hh:mm:ss',
        'headermode': 'multi',
        }
    defaults.update(ImportParamsBase.defaults)

    def __init__(self, **argsv):
        ImportParamsBase.__init__(self, **argsv)
        if self.headermode not in ('multi', '1st', 'none'):
            raise ValueError, "Invalid headermode"

