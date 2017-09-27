"""Extract the valid rig(s)."""


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
        objects = set()
        layers = dict()
        scene = bpy.context.scene
        scene_settings = {
            'name': scene.name,
            'layers': list(scene.layers),
            'frame_start': scene.frame_start,
            'frame_end': scene.frame_end,
            'frame_step': scene.frame_step,
        }
        render_settings = dict()
        render_settings['resolution_x'] = scene.render.resolution_x
        render_settings['resolution_y'] = scene.render.resolution_y
        render_settings['resolution_percentage'] = scene.render.resolution_percentage
        render_settings['frame_map_old'] = scene.render.frame_map_old
        render_settings['frame_map_new'] = scene.render.frame_map_new
        render_settings['fps'] = scene.render.fps
        render_settings['fps_base'] = scene.render.fps_base
        children = [c.name for c in instance.data('children')]

        for obj in instance:
            groups.update({*obj.users_group})
            objects.add(obj)
            layers[obj.name] = list(obj.layers)
        datablocks = groups.union(objects)
        bpy.data.libraries.write(str(temp_file), datablocks)
        self.log.info("Writing temp library file %s" % temp_file)

        # Change library file into a 'normal' file
        python_file = temp_dir / ".".join((name, "py"))
        python_expression = [
            "import bpy",
            "layers = {0}".format(layers),
            "scene_settings = {0}".format(scene_settings),
            "render_settings = {0}".format(render_settings),
            "children = {0}".format(children),
            "scene = bpy.data.scenes[0]",
            "for k, v in scene_settings.items():",
            "    setattr(scene, k, v)",
            "for k, v in render_settings.items():",
            "    setattr(scene.render, k, v)",
            "for obj in bpy.data.objects:",
            "    scene.objects.link(obj)",
            "    obj.layers = layers[obj.name]",
            "    if obj.name in children:",
            "        obj.hide_select = True",
            "bpy.ops.wm.save_mainfile(filepath=\"{0}\")".format(str(temp_file)),
        ]
        with open(str(python_file), "w") as script_file:
            script_file.write("\n".join(python_expression))
        cmd = [bpy.app.binary_path, "-b", str(temp_file), "--python", str(python_file)]

        self.log.info("Exporting %s to %s" % (instance, temp_file))
        subprocess.run(cmd, check=True)

        instance.set_data('tempFile', str(temp_file))
