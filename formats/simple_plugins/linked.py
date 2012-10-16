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

"""linked simple_plugin files"""

from veusz.document.linked import LinkedFileBase

class LinkedFilePlugin(LinkedFileBase):
    """Represent a file linked using an import plugin."""

    def createOperation(self):
        """Return operation to recreate self."""
        import operations
        return operations.OperationDataImportPlugin

    def saveToFile(self, fileobj, relpath=None):
        """Save the link to the vsz document file."""

        p = self.params
        params = [repr(p.plugin),
                  repr(self._getSaveFilename(relpath)),
                  "linked=True"]
        if p.encoding != "utf_8":
            params.append("encoding=" + repr(p.encoding))
        if p.prefix:
            params.append("prefix=" + repr(p.prefix))
        if p.suffix:
            params.append("suffix=" + repr(p.suffix))
        for name, val in p.pluginpars.iteritems():
            params.append("%s=%s" % (name, repr(val)))

        fileobj.write("ImportFilePlugin(%s)\n" % (", ".join(params)))
