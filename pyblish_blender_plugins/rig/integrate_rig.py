"""Integrate the rig(s)."""

# TODO: properly get version number for public file

import pathlib
import shutil
import re


import pyblish.api


class IntegrateRig(pyblish.api.InstancePlugin):
    """Copy files to an appropiate location where others may reach it"""

    order = pyblish.api.IntegratorOrder
    families = ['Rig']
    optional = True
    # active = False

    def process(self, instance):
        assert instance.data('tempFile'), 'Can\'t find rig on disk, aborting...'

        self.log.info('Computing output directory...')
        context = instance.context
        dirname = pathlib.Path(context.data('currentFile')).parent
        root = dirname / 'public'

        if not root.is_dir():
            root.mkdir()

        version = 'v{:02d}'.format(len(list(root.glob("*.blend"))) + 1)

        src = instance.data('tempFile')
        current_file = pathlib.Path(context.data('currentFile'))
        dst_filename = version.join(re.split(r'v\d+', current_file.name))
        dst = root / dst_filename

        self.log.info('Copying %s to %s...' % (src, dst))

        shutil.copy2(src, str(dst))
        self.log.info('Copied successfully!')
