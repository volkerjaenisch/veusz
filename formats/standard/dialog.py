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

"""Dialog box for standard import."""

import os.path

from veusz.dialogs.importtab import ImportTab
import veusz.qtall as qt4
from veusz.dialogs.veuszdialog import VeuszDialog
from veusz import utils

from veusz.formats.standard import params
from veusz.formats.standard import operations
from veusz.formats.standard import reader

class ImportTabStandard(ImportTab):
    """Standard import format tab."""

    resource = 'dialog.ui'

    def loadUi(self):
        """Load widget and setup controls."""
        #TODO: Find better solution for importing the resource file
        qt4.loadUi(os.path.join(utils.veuszDirectory, 'formats', 'standard',
                                self.resource), self)
        self.uiloaded = True

        self.connect(self.helpbutton, qt4.SIGNAL('clicked()'),
                      self.slotHelp)
        self.blockcheckbox.default = False
        self.ignoretextcheckbox.default = True

    def reset(self):
        """Reset controls."""
        self.blockcheckbox.setChecked(False)
        self.ignoretextcheckbox.setChecked(True)
        self.descriptoredit.setEditText("")

    def slotHelp(self):
        """Asked for help."""
        # TODO: Migrate this dialog into the CSV plugin
        d = VeuszDialog(self.dialog.mainwindow, 'importhelp.ui')
        self.dialog.mainwindow.showDialog(d)

    def doPreview(self, filename, encoding):
        """Standard preview - show start of text."""

        try:
            ifile = utils.openEncoding(filename, encoding)
            text = ifile.read(4096) + '\n'
            if len(ifile.read(1)) != 0:
                # if there is remaining data add ...
                text += '...\n'

            self.previewedit.setPlainText(text)
            return True
        except (UnicodeError, EnvironmentError):
            self.previewedit.setPlainText('')
            return False

    def doImport(self, doc, filename, linked, encoding, prefix, suffix, tags):
        """Standard Veusz importing."""

        # convert controls to values
        descriptor = unicode(self.descriptoredit.text())
        useblocks = self.blockcheckbox.isChecked()
        ignoretext = self.ignoretextcheckbox.isChecked()

        parameters = params.ImportParamsSimple(
            descriptor=descriptor,
            filename=filename,
            useblocks=useblocks,
            linked=linked,
            prefix=prefix, suffix=suffix,
            tags=tags,
            ignoretext=ignoretext,
            encoding=encoding,
            )

        try:
            # construct operation. this checks the descriptor.
            op = operations.OperationDataImport(parameters)

        except reader.DescriptorError:
            qt4.QMessageBox.warning(self, _("Veusz"),
                                    _("Cannot interpret descriptor"))
            return

        # actually import the data
        doc.applyOperation(op)

        # tell the user what happened
        # failures in conversion
        lines = []
        for var, count in op.outinvalids.iteritems():
            if count != 0:
                lines.append(_('%i conversions failed for dataset "%s"') %
                             (count, var))
        if len(lines) != 0:
            lines.append('')

        lines += self.dialog.retnDatasetInfo(op.outdatasets, linked, filename)

        self.previewedit.setPlainText('\n'.join(lines))

    def isFiletypeSupported(self, ftype):
        """Is the filetype supported by this tab?"""
        return ftype in ('.dat', '.txt')
