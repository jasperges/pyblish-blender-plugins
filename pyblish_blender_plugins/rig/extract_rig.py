"""Extract the valid rig(s)."""

import os
import tempfile
import shutil
from datetime import datetime


import pyblish.api
import bpy


class ExtractRig(pyblish.api.InstancePlugin):
    """Serialise valid rig"""

    order = pyblish.api.ExtractorOrder
    families = ['Rig']
    hosts = ['blender']

    def process(self, instance):
        context = instance.context
        dirname = os.path.dirname(context.data('currentFile'))
        name, family = instance.data('name'), instance.data('family')
        date = datetime.now().strftime('%Y%m%dT%H%M%SZ')

        temp_dir = tempfile.mkdtemp()
        temp_file = os.path.join(temp_dir, '.'.join((name, 'blend')))

        self.log.info('Exporting %s to %s' % (instance, temp_file))

        # TODO: find a way to (resursively) remove unwanted things.
        # del_objs = [obj.name for obj in bpy.data.objects if obj not in instance]
        # for obj in del_objs:
        #     bpy.data.objects.remove(bpy.data.objects[obj], do_unlink=True)

        bpy.ops.wm.save_as_mainfile(filepath=temp_file, copy=True)
        # bpy.ops.wm.open_mainfile(filepath=context.data('currentFile'))

        instance.set_data('tempFile', temp_file)
