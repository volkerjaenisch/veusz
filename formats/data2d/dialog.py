# standard data import dialog

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

"""Dialog box for 2d import."""

import csv
import os.path
import re

from veusz.dialogs.importtab import ImportTab
import veusz.qtall as qt4
from veusz import utils

from veusz.formats.data2d import params
from veusz.formats.data2d import operations
from veusz.formats.data2d import reader

def _(text, disambiguation=None, context="ImportDialog"):
    """Translate text."""
    return unicode(
        qt4.QCoreApplication.translate(context, text, disambiguation))

class ImportTab2D(ImportTab):
    """Tab for importing from a 2D data file."""

    resource = 'dialog.ui'

    def loadUi(self):
        """Load user interface and set up validators."""
        #TODO: Find better solution for importing the resource file
        qt4.loadUi(os.path.join(utils.veuszDirectory, 'formats', 'data2d',
                                self.resource), self)
        self.uiloaded = True

        # set up some validators for 2d edits
        dval = qt4.QDoubleValidator(self)
        for i in (self.twod_xminedit, self.twod_xmaxedit,
                  self.twod_yminedit, self.twod_ymaxedit):
            i.setValidator(dval)

    def reset(self):
        """Reset controls."""
        for combo in (self.twod_xminedit, self.twod_xmaxedit,
                      self.twod_yminedit, self.twod_ymaxedit,
                      self.twod_datasetsedit):
            combo.setEditText("")
        for check in (self.twod_invertrowscheck, self.twod_invertcolscheck,
                      self.twod_transposecheck):
            check.setChecked(False)

    def doPreview(self, filename, encoding):
        """Preview 2d dataset files."""

        try:
            ifile = utils.openEncoding(filename, encoding)
            text = ifile.read(4096) + '\n'
            if len(ifile.read(1)) != 0:
                # if there is remaining data add ...
                text += '...\n'
            self.twod_previewedit.setPlainText(text)
            return True

        except (UnicodeError, EnvironmentError):
            self.twod_previewedit.setPlainText('')
            return False

    def doImport(self, doc, filename, linked, encoding, prefix, suffix, tags):
        """Import from 2D file."""

        # this really needs improvement...

        # get datasets and split into a list
        datasets = unicode(self.twod_datasetsedit.text())
        datasets = re.split('[, ]+', datasets)

        # strip out blank items
        datasets = [d for d in datasets if d != '']

        # an obvious error...
        if len(datasets) == 0:
            self.twod_previewedit.setPlainText(_('At least one dataset needs to '
                                                 'be specified'))
            return

        # convert range parameters
        ranges = []
        for e in (self.twod_xminedit, self.twod_xmaxedit,
                  self.twod_yminedit, self.twod_ymaxedit):
            f = unicode(e.text())
            r = None
            try:
                r = float(f)
            except ValueError:
                pass
            ranges.append(r)

        # propagate settings from dialog to reader
        rangex = None
        rangey = None
        if ranges[0] is not None and ranges[1] is not None:
            rangex = (ranges[0], ranges[1])
        if ranges[2] is not None and ranges[3] is not None:
            rangey = (ranges[2], ranges[3])

        invertrows = self.twod_invertrowscheck.isChecked()
        invertcols = self.twod_invertcolscheck.isChecked()
        transpose = self.twod_transposecheck.isChecked()

        # loop over datasets and read...
        parameters = params.ImportParams2D(
            datasetnames=datasets,
            filename=filename,
            xrange=rangex, yrange=rangey,
            invertrows=invertrows,
            invertcols=invertcols,
            transpose=transpose,
            prefix=prefix, suffix=suffix,
            tags=tags,
            linked=linked,
            encoding=encoding
            )

        try:
            op = operations.OperationDataImport2D(parameters)
            doc.applyOperation(op)

            output = [_('Successfully read datasets:')]
            for ds in op.outdatasets:
                output.append(' %s' % doc.data[ds].description(
                        showlinked=False))

            output = '\n'.join(output)
        except reader.Read2DError, e:
            output = _('Error importing datasets:\n %s') % str(e)

        # show status in preview box
        self.twod_previewedit.setPlainText(output)
