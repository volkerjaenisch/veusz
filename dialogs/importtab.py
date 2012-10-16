import os.path
import re
import sys

import veusz.qtall as qt4
import veusz.document as document
import veusz.setting as setting
import veusz.utils as utils
import veusz.plugins as plugins
import exceptiondialog

class ImportTab(qt4.QWidget):
    """Tab for a particular import type."""

    resource = ''

    def __init__(self, importdialog, *args):
        """Initialise dialog. importdialog is the import dialog itself."""
        qt4.QWidget.__init__(self, *args)
        self.dialog = importdialog
        self.uiloaded = False

    def loadUi(self):
        """Load up UI file."""
        qt4.loadUi(os.path.join(utils.veuszDirectory, 'dialogs',
                                self.resource), self)
        self.uiloaded = True

    def reset(self):
        """Reset controls to initial conditions."""
        pass

    def doPreview(self, filename, encoding):
        """Update the preview window, returning whether import
        should be attempted."""
        pass

    def doImport(self, filename, linked, encoding, prefix, suffix, tags):
        """Do the import iteself."""
        pass

    def okToImport(self):
        """Secondary check (after preview) for enabling import button."""
        return True

    def isFiletypeSupported(self, ftype):
        """Is the filetype supported by this tab?"""
        return False

    def useFiletype(self, ftype):
        """If the tab can do something with the selected filetype,
        update itself."""
        pass



pyfits = None
class ImportTabFITS(ImportTab):
    """Tab for importing from a FITS file."""

    resource = 'import_fits.ui'

    def loadUi(self):
        ImportTab.loadUi(self)
        # if different items are selected in fits tab
        self.connect(self.fitshdulist, qt4.SIGNAL('itemSelectionChanged()'),
                      self.slotFitsUpdateCombos)
        self.connect(self.fitsdatasetname,
                      qt4.SIGNAL('editTextChanged(const QString&)'),
                      self.dialog.enableDisableImport)
        self.connect(self.fitsdatacolumn,
                      qt4.SIGNAL('currentIndexChanged(int)'),
                      self.dialog.enableDisableImport)

    def reset(self):
        """Reset controls."""
        self.fitsdatasetname.setEditText("")
        for c in ('data', 'sym', 'pos', 'neg'):
            cntrl = getattr(self, 'fits%scolumn' % c)
            cntrl.setCurrentIndex(0)

    def doPreview(self, filename, encoding):
        """Set up controls for FITS file."""

        # load pyfits if available
        global pyfits
        if pyfits is None:
            try:
                import pyfits as PF
                pyfits = PF
            except ImportError:
                pyfits = None

        # if it isn't
        if pyfits is None:
            self.fitslabel.setText(
                _('FITS file support requires that PyFITS is installed.'
                  ' You can download it from'
                  ' http://www.stsci.edu/resources/software_hardware/pyfits'))
            return False

        # try to identify fits file
        try:
            ifile = open(filename, 'rU')
            line = ifile.readline()
            # is this a hack?
            if line.find('SIMPLE  =                    T') == -1:
                raise EnvironmentError
            ifile.close()
        except EnvironmentError:
            self.clearFITSView()
            return False

        self.updateFITSView(filename)
        return True

    def clearFITSView(self):
        """If invalid filename, clear fits preview."""
        self.fitshdulist.clear()
        for c in ('data', 'sym', 'pos', 'neg'):
            cntrl = getattr(self, 'fits%scolumn' % c)
            cntrl.clear()
            cntrl.setEnabled(False)

    def updateFITSView(self, filename):
        """Update the fits file details in the import dialog."""
        f = pyfits.open(str(filename), 'readonly')
        l = self.fitshdulist
        l.clear()

        # this is so we can lookup item attributes later
        self.fitsitemdata = []
        items = []
        for hdunum, hdu in enumerate(f):
            header = hdu.header
            hduitem = qt4.QTreeWidgetItem([str(hdunum), hdu.name])
            data = []
            try:
                # if this fails, show an image
                cols = hdu.get_coldefs()

                # it's a table
                data = ['table', cols]
                rows = header['NAXIS2']
                descr = _('Table (%i rows)') % rows

            except AttributeError:
                # this is an image
                naxis = header['NAXIS']
                if naxis == 1 or naxis == 2:
                    data = ['image']
                else:
                    data = ['invalidimage']
                dims = [ str(header['NAXIS%i' % (i + 1)])
                         for i in xrange(naxis) ]
                dims = '*'.join(dims)
                if dims:
                    dims = '(%s)' % dims
                descr = _('%iD image %s') % (naxis, dims)

            hduitem = qt4.QTreeWidgetItem([str(hdunum), hdu.name, descr])
            items.append(hduitem)
            self.fitsitemdata.append(data)

        if items:
            l.addTopLevelItems(items)
            l.setCurrentItem(items[0])

    def slotFitsUpdateCombos(self):
        """Update list of fits columns when new item is selected."""

        items = self.fitshdulist.selectedItems()
        if len(items) != 0:
            item = items[0]
            hdunum = int(str(item.text(0)))
        else:
            item = None
            hdunum = -1

        cols = ['N/A']
        enablecolumns = False
        if hdunum >= 0:
            data = self.fitsitemdata[hdunum]
            if data[0] == 'table':
                enablecolumns = True
                cols = ['None']
                cols += ['%s (%s)' %
                         (i.name, i.format) for i in data[1]]

        for c in ('data', 'sym', 'pos', 'neg'):
            cntrl = getattr(self, 'fits%scolumn' % c)
            cntrl.setEnabled(enablecolumns)
            cntrl.clear()
            cntrl.addItems(cols)

        self.dialog.enableDisableImport()

    def okToImport(self):
        """Check validity of Fits import."""

        items = self.fitshdulist.selectedItems()
        if len(items) != 0:
            item = items[0]
            hdunum = int(str(item.text(0)))

            # any name for the dataset?
            if not unicode(self.fitsdatasetname.text()):
                return False

            # if a table, need selected item
            data = self.fitsitemdata[hdunum]
            if data[0] != 'image' and self.fitsdatacolumn.currentIndex() == 0:
                return False

            return True
        return False

    def doImport(self, doc, filename, linked, encoding, prefix, suffix, tags):
        """Import fits file."""

        item = self.fitshdulist.selectedItems()[0]
        hdunum = int(str(item.text(0)))
        data = self.fitsitemdata[hdunum]

        name = prefix + unicode(self.fitsdatasetname.text()) + suffix

        if data[0] == 'table':
            # get list of appropriate columns
            cols = []

            # get data from controls
            for c in ('data', 'sym', 'pos', 'neg'):
                cntrl = getattr(self, 'fits%scolumn' % c)

                i = cntrl.currentIndex()
                if i == 0:
                    cols.append(None)
                else:
                    cols.append(data[1][i - 1].name)

        else:
            # item is an image, so no columns
            cols = [None] * 4

        # construct operation to import fits
        params = document.ImportParamsFITS(
            dsname=name,
            filename=filename,
            hdu=hdunum,
            datacol=cols[0],
            symerrcol=cols[1],
            poserrcol=cols[2],
            negerrcol=cols[3],
            tags=tags,
            linked=linked,
            )

        op = document.OperationDataImportFITS(params)

        # actually do the import
        doc.applyOperation(op)

        # inform user
        self.fitsimportstatus.setText(_("Imported dataset '%s'") % name)
        qt4.QTimer.singleShot(2000, self.fitsimportstatus.clear)

    def isFiletypeSupported(self, ftype):
        """Is the filetype supported by this tab?"""
        return ftype in ('.fit', '.fits')

class ImportTabPlugins(ImportTab):
    """Tab for importing using a plugin."""

    resource = 'import_plugins.ui'

    def __init__(self, importdialog, promote=None):
        """Initialise dialog. importdialog is the import dialog itself.

        If promote is set to a name of a plugin, it is promoted to its own tab
        """
        ImportTab.__init__(self, importdialog)
        self.promote = promote
        self.plugininstance = None

    def loadUi(self):
        """Load the user interface."""
        ImportTab.loadUi(self)

        # fill plugin combo
        names = list(sorted([p.name for p in plugins.importpluginregistry]))
        self.pluginType.addItems(names)

        self.connect(self.pluginType, qt4.SIGNAL('currentIndexChanged(int)'),
                     self.pluginChanged)

        self.fields = []

        # load previous plugin
        idx = -1
        if self.promote is None:
            if 'import_plugin' in setting.settingdb:
                try:
                    idx = names.index(setting.settingdb['import_plugin'])
                except ValueError:
                    pass
        else:
            # set the correct entry for the plugin
            idx = names.index(self.promote)
            # then hide the widget so it can't be changed
            self.pluginchoicewidget.hide()

        if idx >= 0:
            self.pluginType.setCurrentIndex(idx)

        self.pluginChanged(-1)

    def getPluginFields(self):
        """Return a dict of the fields given."""
        results = {}
        plugin = self.getSelectedPlugin()
        for field, cntrls in zip(plugin.fields, self.fields):
            results[field.name] = field.getControlResults(cntrls)
        return results

    def getSelectedPlugin(self):
        """Get instance selected plugin or none."""
        selname = unicode(self.pluginType.currentText())
        names = [p.name for p in plugins.importpluginregistry]
        try:
            idx = names.index(selname)
        except ValueError:
            return None

        p = plugins.importpluginregistry[idx]
        if isinstance(p, type):
            # this is a class, rather than an object
            if not isinstance(self.plugininstance, p):
                # create new instance, if required
                self.plugininstance = p()
            return self.plugininstance
        else:
            # backward compatibility with old API
            return p

    def pluginChanged(self, index):
        """Update controls based on index."""
        plugin = self.getSelectedPlugin()
        if self.promote is None:
            setting.settingdb['import_plugin'] = plugin.name

        # delete old controls
        layout = self.pluginParams.layout()
        for line in self.fields:
            for cntrl in line:
                layout.removeWidget(cntrl)
                cntrl.deleteLater()
        del self.fields[:]

        # make new controls
        for row, field in enumerate(plugin.fields):
            cntrls = field.makeControl(None, None)
            layout.addWidget(cntrls[0], row, 0)
            layout.addWidget(cntrls[1], row, 1)
            self.fields.append(cntrls)

        # update label
        self.pluginDescr.setText("%s (%s)\n%s" %
                                 (plugin.name, plugin.author,
                                  plugin.description))

        self.dialog.slotUpdatePreview()

    def doPreview(self, filename, encoding):
        """Preview using plugin."""

        # check file exists
        if filename != '{clipboard}':
            try:
                f = open(filename, 'r')
                f.close()
            except EnvironmentError:
                self.pluginPreview.setPlainText('')
                return False

        # get the plugin selected
        plugin = self.getSelectedPlugin()
        if plugin is None:
            self.pluginPreview.setPlainText('')
            return False

        # ask the plugin for text
        params = plugins.ImportPluginParams(filename, encoding,
                                            self.getPluginFields())
        try:
            text, ok = plugin.getPreview(params)
        except plugins.ImportPluginException, ex:
            text = unicode(ex)
            ok = False
        self.pluginPreview.setPlainText(text)
        return bool(ok)

    def doImport(self, doc, filename, linked, encoding, prefix, suffix, tags):
        """Import using plugin."""

        fields = self.getPluginFields()
        plugin = unicode(self.pluginType.currentText())

        params = document.ImportParamsPlugin(
            plugin=plugin,
            filename=filename,
            linked=linked, encoding=encoding,
            prefix=prefix, suffix=suffix,
            tags=tags,
            **fields)

        op = document.OperationDataImportPlugin(params)
        try:
            doc.applyOperation(op)
        except plugins.ImportPluginException, ex:
            self.pluginPreview.setPlainText(unicode(ex))
            return

        out = [_('Imported data for datasets:')]
        for ds in op.outdatasets:
            out.append(doc.data[ds].description(showlinked=False))
        if op.outcustoms:
            out.append('')
            out.append(_('Set custom definitions:'))
            # format custom definitions
            out += ['%s %s=%s' % tuple(c) for c in op.outcustoms]

        self.pluginPreview.setPlainText('\n'.join(out))

    def isFiletypeSupported(self, ftype):
        """Is the filetype supported by this tab?"""

        if self.promote is None:
            # look through list of supported plugins to check filetypes
            inany = False
            for p in plugins.importpluginregistry:
                if ftype in p.file_extensions:
                    inany = True
            return inany
        else:
            # find plugin class and check filetype
            for p in plugins.importpluginregistry:
                if p.name == self.promote:
                    return ftype in p.file_extensions

    def useFiletype(self, ftype):
        """Select the plugin corresponding to the filetype."""

        if self.promote is None:
            plugin = None
            for p in plugins.importpluginregistry:
                if ftype in p.file_extensions:
                    plugin = p.name
            idx = self.pluginType.findText(plugin, qt4.Qt.MatchExactly)
            self.pluginType.setCurrentIndex(idx)
            self.pluginChanged(-1)
