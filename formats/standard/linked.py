# -*- coding: utf-8 -*-
#    Copyright (C) 2011 Jeremy S. Sanders
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
###############################################################################

"""linked text files"""

from veusz.document.linked import LinkedFileBase

class LinkedFile(LinkedFileBase):
    """Instead of reading data from a string, data can be read from
    a "linked file". This means the same document can be reloaded, and
    the data would be reread from the file.

    This class is used to store a link filename with the descriptor
    """

    def createOperation(self):
        """Return operation to recreate self."""
        import operations
        return operations.OperationDataImport

    def saveToFile(self, fileobj, relpath=None):
        """Save the link to the document file.
        If relpath is set, save links relative to path given
        """

        p = self.params
        params = [ repr(self._getSaveFilename(relpath)),
                   repr(p.descriptor),
                   "linked=True",
                   "ignoretext=" + repr(p.ignoretext) ]

        if p.encoding != "utf_8":
            params.append("encoding=" + repr(p.encoding))
        if p.useblocks:
            params.append("useblocks=True")
        if p.prefix:
            params.append("prefix=" + repr(p.prefix))
        if p.suffix:
            params.append("suffix=" + repr(p.suffix))

        fileobj.write("ImportFile(%s)\n" % (", ".join(params)))
