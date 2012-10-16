#    Copyright (C) 2006 Jeremy S. Sanders
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

"""Operations for simple_plugin file import"""

import veusz.qtall as qt4
from veusz.document import datasets
from veusz.document.operations import OperationDataImportBase
from veusz.document import simpleread
from veusz import utils

from veusz import plugins

from veusz.formats.simple_plugins import linked
from veusz.formats.simple_plugins import reader



def _(text, disambiguation=None, context="Operations"):
    """Translate text."""
    return unicode(
        qt4.QCoreApplication.translate(context, text, disambiguation))

class OperationDataImportPlugin(OperationDataImportBase):
    """Import data using a plugin."""

    descr = _('import using plugin')

    def doImport(self, document):
        """Do import."""

        pluginnames = [p.name for p in plugins.importpluginregistry]
        plugin = plugins.importpluginregistry[
            pluginnames.index(self.params.plugin)]

        # if the plugin is a class, make an instance
        # the old API is for the plugin to be instances
        if isinstance(plugin, type):
            plugin = plugin()

        # strip out parameters for plugin itself
        p = self.params

        # stick back together the plugin parameter object
        plugparams = plugins.ImportPluginParams(
            p.filename, p.encoding, p.pluginpars)
        results = plugin.doImport(plugparams)

        # make link for file
        LF = None
        if p.linked:
            LF = linked.LinkedFilePlugin(p)

        customs = []

        # convert results to real datasets
        names = []
        for d in results:
            if isinstance(d, plugins.Dataset1D):
                ds = datasets.Dataset(data=d.data, serr=d.serr, perr=d.perr,
                                      nerr=d.nerr)
            elif isinstance(d, plugins.Dataset2D):
                ds = datasets.Dataset2D(data=d.data, xrange=d.rangex,
                                        yrange=d.rangey)
            elif isinstance(d, plugins.DatasetText):
                ds = datasets.DatasetText(data=d.data)
            elif isinstance(d, plugins.DatasetDateTime):
                ds = datasets.DatasetDateTime(data=d.data)
            elif isinstance(d, plugins.Constant):
                customs.append(['constant', d.name, d.val])
                continue
            elif isinstance(d, plugins.Function):
                customs.append(['function', d.name, d.val])
                continue
            else:
                raise RuntimeError("Invalid data set in plugin results")

            # set any linking
            if linked:
                ds.linked = LF

            # construct name
            name = p.prefix + d.name + p.suffix

            # actually make dataset
            document.setData(name, ds)

            names.append(name)

        # add constants, functions to doc, if any
        self.addCustoms(document, customs)

        self.outdatasets = names
        self.outcustoms = list(customs)

