"""Extract the valid rig(s)."""

# TODO: copy all settings from scene (or at least important ones)

import subprocess
import pathlib


import pyblish.api
import bpy


class ExtractRig(pyblish.api.InstancePlugin):
    """Serialise valid rig"""

    order = pyblish.api.ExtractorOrder
    families = ['Rig']
    hosts = ['blender']
    optional = True
    # active = False

    def process(self, instance):
        context = instance.context
        dirname = pathlib.Path(context.data('currentFile')).parent
        name, family = instance.data('name'), instance.data('family')

        temp_dir = pathlib.Path(bpy.app.tempdir)
        temp_file = temp_dir / '.'.join((name, "blend"))

        if not bpy.data.is_saved or bpy.data.is_dirty:
            self.log.info("Saving file %s..." % context.data('currentFile'))
            bpy.ops.wm.save_as_mainfile(filepath=context.data('currentFile'))

        # Create temp library file
        groups = set()
        layers = dict()
        visible_layers = list(bpy.context.scene.layers)
        scene_name = bpy.context.scene.name
        for obj in instance:
            groups.update({*obj.users_group})
            layers[obj.name] = list(obj.layers)
        bpy.data.libraries.write(str(temp_file), groups)
        self.log.info("Writing temp library file %s" % temp_file)

        # Change library file into a 'normal' file
        python_file = temp_dir / ".".join((name, "py"))
        python_expression = [
            "import bpy",
            "layers = {0}".format(layers),
            "bpy.data.scenes[0].name = \"{0}\"".format(scene_name),
            "for obj in bpy.data.objects:",
            "    bpy.data.scenes['{0}'].objects.link(obj)".format(scene_name),
            "    obj.layers = layers[obj.name]",
            "bpy.data.scenes['{0}'].layers = {1}".format(scene_name, visible_layers),
            "bpy.ops.wm.save_mainfile(filepath=\"{0}\")".format(str(temp_file)),
        ]
        with open(str(python_file), "w") as script_file:
            script_file.write("\n".join(python_expression))
        cmd = [bpy.app.binary_path, "-b", str(temp_file), "--python", str(python_file)]

        self.log.info("Exporting %s to %s" % (instance, temp_file))
        subprocess.run(cmd, check=True)

        instance.set_data('tempFile', str(temp_file))
