# data import dialog

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

"""Module for implementing dialog boxes for importing data in Veusz."""

import veusz.qtall as qt4

from veuszdialog import VeuszDialog

from veusz.formats.csv.dialog import ImportTabCSV
from veusz.formats.data2d.dialog import ImportTab2D
from veusz.formats.standard.dialog import ImportTabStandard
from veusz.formats.fits.dialog import ImportTabFITS

from importtab import *

def _(text, disambiguation=None, context="ImportDialog"):
    """Translate text."""
    return unicode(
        qt4.QCoreApplication.translate(context, text, disambiguation))


class ImportDialog(VeuszDialog):
    """Dialog box for importing data.
    See ImportTab classes above which actually do the work of importing
    """

    dirname = '.'

    def __init__(self, parent, document):

        VeuszDialog.__init__(self, parent, 'import.ui')
        self.document = document

        # whether file import looks likely to work
        self.filepreviewokay = False

        # tabs loaded currently in dialog
        self.tabs = {}
        for tabname, tabclass in (
            (_('&Standard'), ImportTabStandard),
            (_('CS&V'), ImportTabCSV),
            (_('FI&TS'), ImportTabFITS),
            (_('&2D'), ImportTab2D),
            (_('Plugins'), ImportTabPlugins),
            ):
            w = tabclass(self)
            self.methodtab.addTab(w, tabname)

        # add promoted plugins
        for p in plugins.importpluginregistry:
            if p.promote_tab is not None:
                w = ImportTabPlugins(self, promote=p.name)
                self.methodtab.addTab(w, p.promote_tab)

        self.connect(self.methodtab, qt4.SIGNAL('currentChanged(int)'),
                      self.slotUpdatePreview)

        self.connect(self.browsebutton, qt4.SIGNAL('clicked()'),
                     self.slotBrowseClicked)

        self.connect(self.filenameedit,
                      qt4.SIGNAL('editTextChanged(const QString&)'),
                      self.slotUpdatePreview)

        self.importbutton = self.buttonBox.addButton(_("&Import"),
                                                     qt4.QDialogButtonBox.ApplyRole)
        self.connect(self.importbutton, qt4.SIGNAL('clicked()'),
                      self.slotImport)

        self.connect(self.buttonBox.button(qt4.QDialogButtonBox.Reset),
                      qt4.SIGNAL('clicked()'), self.slotReset)

        self.connect(self.encodingcombo,
                      qt4.SIGNAL('currentIndexChanged(int)'),
                      self.slotUpdatePreview)

        # change to tab last used
        self.methodtab.setCurrentIndex(
            setting.settingdb.get('import_lasttab', 0))

        # add completion for filename if there is support in version of qt
        # (requires qt >= 4.3)
        if hasattr(qt4, 'QDirModel'):
            c = self.filenamecompleter = qt4.QCompleter(self)
            model = qt4.QDirModel(c)
            c.setModel(model)
            self.filenameedit.setCompleter(c)

        # defaults for prefix and suffix
        self.prefixcombo.default = self.suffixcombo.default = ['', '$FILENAME']

        # default state for check boxes
        self.linkcheckbox.default = True

        # further defaults
        self.encodingcombo.defaultlist = utils.encodings
        self.encodingcombo.defaultval = 'utf_8'

        # load icon for clipboard
        self.clipbutton.setIcon(utils.getIcon('kde-clipboard'))
        self.connect(qt4.QApplication.clipboard(), qt4.SIGNAL('dataChanged()'),
                     self.updateClipPreview)
        self.connect(
            self.clipbutton, qt4.SIGNAL("clicked()"), self.slotClipButtonClicked)
        self.updateClipPreview()

    def slotBrowseClicked(self):
        """Browse for a data file."""

        fd = qt4.QFileDialog(self, _('Browse data file'))
        fd.setFileMode(qt4.QFileDialog.ExistingFile)

        # use filename to guess a path if possible
        filename = unicode(self.filenameedit.text())
        if os.path.isdir(filename):
            ImportDialog.dirname = filename
        elif os.path.isdir(os.path.dirname(filename)):
            ImportDialog.dirname = os.path.dirname(filename)

        fd.setDirectory(ImportDialog.dirname)

        # update filename if changed
        if fd.exec_() == qt4.QDialog.Accepted:
            ImportDialog.dirname = fd.directory().absolutePath()
            self.filenameedit.replaceAndAddHistory(fd.selectedFiles()[0])
            self.guessImportTab()

    def guessImportTab(self):
        """Guess import tab based on filename."""
        filename = unicode(self.filenameedit.text())

        fname, ftype = os.path.splitext(filename)
        # strip off any gz, bz2 extensions to get real extension
        while ftype.lower() in ('gz', 'bz2'):
            fname, ftype = os.path.splitext(fname)
        ftype = ftype.lower()

        # examine from left to right
        # promoted plugins come after plugins
        idx = -1
        for i in xrange(self.methodtab.count()):
            w = self.methodtab.widget(i)
            if w.isFiletypeSupported(ftype):
                idx = i

        if idx >= 0:
            self.methodtab.setCurrentIndex(idx)
            self.methodtab.widget(idx).useFiletype(ftype)

    def slotUpdatePreview(self, *args):
        """Update preview window when filename or tab changed."""

        # save so we can restore later
        tab = self.methodtab.currentIndex()
        setting.settingdb['import_lasttab'] = tab
        filename = unicode(self.filenameedit.text())
        encoding = str(self.encodingcombo.currentText())
        importtab = self.methodtab.currentWidget()

        if encoding == '':
            return

        if isinstance(importtab, ImportTab):
            if not importtab.uiloaded:
                importtab.loadUi()
            self.filepreviewokay = importtab.doPreview(
                filename, encoding)

        # enable or disable import button
        self.enableDisableImport()

    def enableDisableImport(self, *args):
        """Disable or enable import button if allowed."""

        importtab = self.methodtab.currentWidget()
        enabled = self.filepreviewokay and importtab.okToImport()

        # actually enable or disable import button
        self.importbutton.setEnabled(enabled)

    def slotImport(self):
        """Do the importing"""

        filename = unicode(self.filenameedit.text())
        linked = self.linkcheckbox.isChecked()
        encoding = str(self.encodingcombo.currentText())
        if filename == '{clipboard}':
            linked = False
        else:
            # normalise filename
            filename = os.path.abspath(filename)

        # import according to tab selected
        importtab = self.methodtab.currentWidget()
        prefix, suffix = self.getPrefixSuffix(filename)
        tags = unicode(self.tagcombo.currentText()).split()

        try:
            qt4.QApplication.setOverrideCursor(qt4.QCursor(qt4.Qt.WaitCursor))
            self.document.suspendUpdates()
            importtab.doImport(self.document, filename, linked, encoding,
                               prefix, suffix, tags)
            qt4.QApplication.restoreOverrideCursor()
        except Exception:
            qt4.QApplication.restoreOverrideCursor()

            # show exception dialog
            d = exceptiondialog.ExceptionDialog(sys.exc_info(), self)
            d.exec_()
        self.document.enableUpdates()

    def retnDatasetInfo(self, dsnames, linked, filename):
        """Return a list of information for the dataset names given."""

        lines = [_('Imported data for datasets:')]
        dsnames.sort()
        for name in dsnames:
            ds = self.document.getData(name)
            # build up description
            lines.append(' %s' % ds.description(showlinked=False))

        # whether the data were linked
        if linked:
            lines.append('')
            lines.append(_('Datasets were linked to file "%s"') % filename)

        return lines

    def getPrefixSuffix(self, filename):
        """Get prefix and suffix values."""
        f = utils.cleanDatasetName(os.path.basename(filename))
        prefix = unicode(self.prefixcombo.lineEdit().text())
        prefix = prefix.replace('$FILENAME', f)
        suffix = unicode(self.suffixcombo.lineEdit().text())
        suffix = suffix.replace('$FILENAME', f)
        return prefix, suffix

    def slotReset(self):
        """Reset input fields."""

        self.filenameedit.setText("")
        self.encodingcombo.setCurrentIndex(
            self.encodingcombo.findText("utf_8"))
        self.linkcheckbox.setChecked(True)
        self.prefixcombo.setEditText("")
        self.suffixcombo.setEditText("")

        importtab = self.methodtab.currentWidget()
        importtab.reset()

    def slotClipButtonClicked(self):
        """Clicked clipboard button."""
        self.filenameedit.setText("{clipboard}")

    def updateClipPreview(self):
        """Clipboard contents changed, so update preview if showing clipboard."""

        filename = unicode(self.filenameedit.text())
        if filename == '{clipboard}':
            self.slotUpdatePreview()
