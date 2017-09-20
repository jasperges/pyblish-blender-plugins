"""Collect a rig in the open file."""

import pyblish.api
from stalker import db
from stalker import Task
import bpy
import logging


def get_recurse_children(obj):
    """Recursively get all children of an object"""
    children = [obj]
    if obj.children:
        for child in obj.children:
            children.extend(get_recurse_children(child))
    return children


def get_children(obj):
    """Get all the children of an object"""
    children = set(get_recurse_children(obj))
    children.discard(obj)
    return children

def get_all_children(objects):
    """Get all the combined children of the objects"""
    all_children = []
    for obj in objects:
        children = get_recurse_children(obj)
        all_children.extend(children)
    return set(all_children)


class SaveFile(pyblish.api.Action):
    """Save the blend file"""

    def process(self, context, plugin):
        if not bpy.data.is_saved or bpy.data.is_dirty:
            bpy.ops.wm.save_mainfile()
        self.log.info("Saved file %s" % bpy.data.filepath)

class CollectRig(pyblish.api.ContextPlugin):
    """Discover and collect available rigs into the context"""

    order = pyblish.api.CollectorOrder
    label = "Collect rigs"
    actions = [SaveFile]

    def process(self, context):
        # First check if the file is saved
        if not bpy.data.is_saved or bpy.data.is_dirty:
            raise Warning("Please save the file before publishing")
        # try:
        #     task_id = bpy.context.scene.piecekeeper.stalker.task_id
        # except AttributeError:
        #     self.log.error("Task ID could not be found in the scene")
        #     raise
        # if task_id < 0:
        #     self.log.warning("The task ID is not set. Is this a valid production file?")
        #     return
        # db.setup()
        # task = Task.query.filter_by(id=task_id).first()
        # if not task:
        #     self.log.warning("There is no task with ID %s" % task_id)
        #     return
        # if not task.name.lower() == 'rig':
        #     self.log.info("This is not a rigging task, but %s" % task.name)
        #     return

        # for obj in bpy.data.objects:
        #     if not obj.type == 'ARMATURE' or obj.name == 'metarig':
        #         continue

        #     for group in bpy.data.groups:
        #         members = group.objects.values()
        #         if obj in members:
        #             widgets = [pb.custom_shape for pb in obj.pose.bones]
        #             widgets.append(widgets[0].parent)
        #             instance = context.create_instance(task.parent.name, family='Rig')
        #             instance[:] = members + widgets

        for obj in bpy.data.objects:
            if not obj.type == 'ARMATURE' or obj.name == 'metarig':
                continue

            modifier_children = {c for c in bpy.data.objects if c.find_armature() == obj}
            object_children = get_children(obj)
            children = modifier_children.union(object_children)
            all_children = get_all_children(children)
            widgets = {pb.custom_shape for pb in obj.pose.bones if pb.custom_shape is not None}
            members = {obj}.union(all_children).union(widgets)

            instance = context.create_instance(obj.name, family='Rig')
            instance[:] = list(members)
            instance.set_data('armature', obj)
            instance.set_data('children', all_children)
            instance.set_data('widgets', widgets)
