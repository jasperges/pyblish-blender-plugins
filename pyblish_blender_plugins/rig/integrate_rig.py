"""Integrate the rig(s)."""

# TODO: properly get version number for public file + connect to Stalker?

import pathlib
import shutil
import re


import pyblish.api


class IntegrateRig(pyblish.api.InstancePlugin):
    """Copy files to an appropiate location where others may reach it"""

    order = pyblish.api.IntegratorOrder
    families = ['Rig']
    optional = True

    def process(self, instance):
        assert instance.data('tempFile'), 'Can\'t find rig on disk, aborting...'

        self.log.info('Computing output directory...')
        context = instance.context
        dirname = pathlib.Path(context.data('currentFile')).parent
        root = dirname / 'public'

        if not root.is_dir():
            root.mkdir()

        current_file = pathlib.Path(context.data('currentFile'))
        pattern = re.compile(r"(?P<basename>.*)(?P<version>v\d+)$")
        match = re.match(pattern, current_file.stem)
        if not match:
            raise RuntimeError("Could not find a version number at the end of the file name")
        basename = match.group('basename')
        version_len = len(match.group('version')) - 1
        version = len(list(root.glob("{basename}*{suffix}".format(
            basename=basename, suffix=current_file.suffix)))) + 1
        version_string = "v{version:0{version_len}d}".format(
            version=version, version_len=version_len)

        src = instance.data('tempFile')
        dst_filename = "{basename}{version_string}{suffix}".format(
            basename=basename, version_string=version_string, suffix=current_file.suffix)
        dst = root / dst_filename

        self.log.info('Copying %s to %s...' % (src, dst))

        shutil.copy2(src, str(dst))
        self.log.info('Copied successfully!')
