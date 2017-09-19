"""Collect a rig in the open file."""

import pyblish.api
from stalker import db
from stalker import Task
import bpy


class CollectRig(pyblish.api.ContextPlugin):
    """Discover and collect available rigs into the context"""

    order = pyblish.api.CollectorOrder

    def process(self, context):
        try:
            task_id = bpy.context.scene.piecekeeper.stalker.task_id
        except AttributeError:
            self.log.error("Task ID could not be found in the scene")
            raise
        if task_id < 0:
            self.log.warning("The task ID is not set. Is this a valid production file?")
            return
        db.setup()
        task = Task.query.filter_by(id=task_id).first()
        if not task:
            self.log.warning("There is no task with ID %s" % task_id)
            return
        if not task.name.lower() == 'rig':
            self.log.info("This is not a rigging task, but %s" % task.name)
            return

        for obj in bpy.data.objects:
            if not obj.type == 'ARMATURE' or obj.name == 'metarig':
                continue

            for group in bpy.data.groups:
                members = group.objects.values()
                if obj in members:
                    widgets = [pb.custom_shape for pb in obj.pose.bones]
                    widgets.append(widgets[0].parent)
                    instance = context.create_instance(task.parent.name, family='Rig')
                    instance[:] = members + widgets
