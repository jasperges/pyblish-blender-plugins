"""Validate the rig(s)."""

# TODO:
#     - check if several armatures are not in the same group?

import pyblish.api
import bpy
from mathutils import Matrix


class ParentObjects(bpy.types.Operator):
    """Parent objects to another object"""

    bl_description = "Parent objects"
    bl_idname = "pyblish.objects_parent_set"
    bl_label = "Parent"
    bl_options = {'REGISTER', 'UNDO', 'INTERNAL'}

    parent = bpy.props.StringProperty(
        name="Parent",
        description="The object to parent the other objects under",
        default="",
    )
    objects = bpy.props.StringProperty(
        name="Objects",
        description="A semi-colon separated list of objects (e.g.: 'Suzanne;Cube.001')",
        default="",
    )
    keep_transform = bpy.props.BoolProperty(
        name="Keep transforms",
        description="Keep the visual transformations of the object",
        default=True,
    )

    def execute(self, context):
        parent = bpy.data.objects[self.parent]
        for obj_name in self.objects.split(';'):
            obj = bpy.data.objects[obj_name]
            if self.keep_transform:
                matrix_world = obj.matrix_world.copy()
            obj.parent = parent
            if self.keep_transform:
                obj.matrix_world = matrix_world
        return {'FINISHED'}


class UnparentObjects(bpy.types.Operator):
    """Unparent objects"""

    bl_description = "Unparent objects"
    bl_idname = "pyblish.object_parent_clear"
    bl_label = "Unparent"
    bl_options = {'REGISTER', 'UNDO', 'INTERNAL'}

    objects = bpy.props.StringProperty(
        name="Objects",
        description="A semi-colon separated list of objects (e.g.: 'Suzanne;Cube.001')",
        default="",
    )
    keep_transform = bpy.props.BoolProperty(
        name="Keep transforms",
        description="Keep the visual transformations of the object",
        default=True,
    )

    def execute(self, context):
        for obj_name in self.objects.split(";"):
            obj = bpy.data.objects[obj_name]
            if self.keep_transform:
                matrix_world = obj.matrix_world.copy()
            obj.parent = None
            if self.keep_transform:
                obj.matrix_world = matrix_world
        return {'FINISHED'}


class AddObjectsToGroup(bpy.types.Operator):
    """Add the selected objects to the specified group"""

    bl_description = "Add selected objects to a group"
    bl_idname = "pyblish.group_objects_add"
    bl_label = "Add to Group"
    bl_options = {'REGISTER', 'UNDO', 'INTERNAL'}

    group = bpy.props.StringProperty(
        name="Group",
        description="The name of the group to add the objects to",
        default="",
    )
    objects = bpy.props.StringProperty(
        name="Objects",
        description="A semi-colon separated list of objects to add to a group (e.g.: 'Suzanne;Cube.001')",
        default="",
    )

    def execute(self, context):
        group = bpy.data.groups[self.group]
        for obj in self.objects.split(';'):
            group.objects.link(bpy.data.objects[obj])
        return {'FINISHED'}


class RemoveObjectsFromGroup(bpy.types.Operator):
    """Remove objects from a group"""

    bl_description = "Remove objects from a group"
    bl_idname = "pyblish.group_objects_remove"
    bl_label = "Remove from Group"
    bl_options = {'REGISTER', 'UNDO', 'INTERNAL'}

    group = bpy.props.StringProperty(
        name="Group",
        description="The name of the group to remove the objects from",
        default="",
    )
    objects = bpy.props.StringProperty(
        name="Objects",
        description="A semi-colon separated list of objects to remove from a group (e.g.: 'Suzanne;Cube.001')",
        default="",
    )

    def execute(self, context):
        group = bpy.data.groups[self.group]
        for obj in self.objects.split(';'):
            group.objects.unlink(bpy.data.objects[obj])
        return {'FINISHED'}


class AnimationClear(bpy.types.Operator):
    """Remove animation from objects"""

    bl_description = "Remove animation from objects"
    bl_idname = "pyblish.animation_data_clear"
    bl_label = "Remove animation"
    bl_options = {'REGISTER', 'UNDO', 'INTERNAL'}

    objects = bpy.props.StringProperty(
        name="Objects",
        description="A semi-colon separated list of objects (e.g.: 'Suzanne;Cube.001')",
        default="",
    )

    def execute(self, context):
        for obj_name in self.objects.split(";"):
            obj = bpy.data.objects[obj_name]
            if obj.animation_data:
                obj.animation_data_clear()
        return {'FINISHED'}


class TransformsClear(bpy.types.Operator):
    """Clear all transformations of objects"""

    bl_description = "Clear all transformations of objects"
    bl_idname = "pyblish.transforms_clear"
    bl_label = "Clear transforms"
    bl_options = {'REGISTER', 'UNDO', 'INTERNAL'}

    objects = bpy.props.StringProperty(
        name="Objects",
        description="A semi-colon separated list of objects (e.g.: 'Suzanne;Cube.001')",
        default="",
    )

    def execute(self, context):
        for obj_name in self.objects.split(";"):
            identity_matrix = Matrix.Identity(4)
            obj = bpy.data.objects[obj_name]
            obj.matrix_basis = identity_matrix
            if obj.type == 'ARMATURE':
                for pose_bone in obj.pose.bones:
                    pose_bone.matrix_basis = identity_matrix
        return {'FINISHED'}


class UnparentRig(pyblish.api.Action):
    """Unparent the armature"""

    label = "Unparent Rig"
    on = "failed"
    # icon = "times"

    def process(self, context, plugin):
        for result in context.data['results']:
            if result['error'] and plugin == result['plugin']:
                instance = result['instance']
                armature = instance.data('armature')
                if armature.parent:
                    bpy.ops.pyblish.object_parent_clear(True, objects=armature.name)
                    self.log.info("Unparented armature %s" % armature.name)


class SelectInvalidNodes(pyblish.api.Action):
    label = "Select Broken Objects"
    on = "failed"
    # icon = "hand-o-up"

    def process(self, context, plugin):
        nodes = []
        for result in context.data["results"]:
            if result['error'] and plugin == result['plugin']:
                instance = result['instance']
                broken = instance.data.get('broken')
                self.log.info(broken)
                if broken:
                    bpy.ops.object.select_all(action='DESELECT')
                    broken.select = True
                    bpy.context.scene.objects.active = broken


class ParentModifierChildren(pyblish.api.Action):
    """Parent modifier children to the armature"""

    label = "Parent Modifier Children"
    on = "failed"
    # icon = "users"

    def process(self, context, plugin):
        for result in context.data['results']:
            if result['error'] and plugin == result['plugin']:
                instance = result['instance']
                armature = instance.data('armature')
                objects = {c for c in bpy.data.objects if c.find_armature() == armature}
                objects = {c.name for c in objects if c.parent != armature}
                bpy.ops.pyblish.objects_parent_set(True, parent=armature.name, objects=";".join(objects))
                self.log.info("%s are now parented under %s" % (", ".join(objects), armature.name))


class GroupChildren(pyblish.api.Action):
    """Put the children in the same group as the armature"""

    label = "Put Children in Armature Group"
    on = "failed"
    # icon = "users"

    def process(self, context, plugin):
        for result in context.data['results']:
            if result['error'] and plugin == result['plugin']:
                instance = result['instance']
                armature = instance.data('armature')
                if not armature.users_group:
                    return
                group = armature.users_group[0]
                objects = {c.name for c in instance.data('children') if c not in group.objects.values()}
                bpy.ops.pyblish.group_objects_add(True, group=group.name, objects=";".join(objects))
                if len(objects) == 1:
                    word = "is"
                else:
                    word = "are"
                self.log.info("%s %s now in group %s" % (", ".join(objects), word, group.name))


class UngroupWidgets(pyblish.api.Action):
    """Remove the widgets from the armature group"""

    label = "Remove Widgets from Armature Group"
    on = "failed"
    # icon = "times"

    def process(self, context, plugin):
        for result in context.data['results']:
            if result['error'] and plugin == result['plugin']:
                instance = result['instance']
                armature = instance.data('armature')
                if not armature.users_group:
                    return
                group = armature.users_group[0]
                objects = {w.name for w in instance.data('widgets') if w in group.objects.values()}
                bpy.ops.pyblish.group_objects_remove(True, group=group.name, objects=";".join(objects))
                if len(objects) == 1:
                    word = "is"
                else:
                    word = "are"
                self.log.info("%s %s removed from group %s" % (", ".join(objects), word, group.name))


class RemoveAnimation(pyblish.api.Action):
    """Remove all animation from objects"""

    label = "Remove Animation"
    on = "failed"
    # icon = "times"

    def process(self, context, plugin):
        for result in context.data['results']:
            if result['error'] and plugin == result['plugin']:
                instance = result['instance']
                objects = {o.name for o in instance if o.animation_data and o.animation_data.action}
                bpy.ops.pyblish.animation_data_clear(True, objects=";".join(objects))
                self.log.info("Removed animation data from %s" % ", ".join(objects))


class ResetTransforms(pyblish.api.Action):
    """Reset all rig transforms"""

    label = "Reset Rig Transforms"
    on = "failed"
    # icon = "times"

    def process(self, context, plugin):
        for result in context.data['results']:
            if result['error'] and plugin == result['plugin']:
                instance = result['instance']
                armature = instance.data('armature')
                identity_matrix = Matrix.Identity(4)
                objects = set()
                if armature.matrix_world != identity_matrix:
                    objects.add(armature.name)
                for pose_bone in armature.pose.bones:
                    if pose_bone.matrix_basis != identity_matrix:
                        objects.add(armature.name)
                if objects:
                    bpy.ops.pyblish.transforms_clear(True, objects=";".join(objects))
                    self.log.info("Transformations of %s are reset" % armature.name)


class IsNotParented(pyblish.api.InstancePlugin):
    """Ensure the rig is not parented"""

    version = (0, 0, 1)
    order = pyblish.api.ValidatorOrder
    label = "Rig Not Parented"
    families = ["Rig"]
    optional = True
    actions = [UnparentRig]

    def process(self, instance):
        armature = instance.data('armature')
        if armature.parent:
            raise ValueError("Armature '%s' should not be parented" % armature.name)


class IsGrouped(pyblish.api.InstancePlugin):
    """Ensure the rig is in a group"""

    version = (0, 0, 1)
    order = pyblish.api.ValidatorOrder + 0.08
    label = "Rig Grouped"
    families = ["Rig"]
    optional = True

    def process(self, instance):
        armature = instance.data('armature')
        if not armature.users_group:
            # instance.set_data('broken', armature)
            raise ValueError("Armature '%s' is not grouped" % armature.name)
        if len(armature.users_group) > 1:
            # instance.set_data('broken', armature)
            raise ValueError("Armature '%s' should be in exactly 1 group" % armature.name)


class ChildrenParented(pyblish.api.InstancePlugin):
    """Ensure that all modifier children are also parented to the armature"""

    version = (0, 0, 1)
    order = pyblish.api.ValidatorOrder + 0.09
    label = "Parent Modifier Children"
    families = ["Rig"]
    optional = True
    actions = [ParentModifierChildren]

    def process(self, instance):
        armature = instance.data('armature')
        modifier_children = {c for c in bpy.data.objects if c.find_armature() == armature}
        for modifier_child in modifier_children:
            if modifier_child.parent != armature:
                raise ValueError("{0} should be parented to {1}".format(modifier_child.name, armature.name))


class ChildrenInGroup(pyblish.api.InstancePlugin):
    """Ensure the children are in the same group as the armature"""

    version = (0, 0, 1)
    order = pyblish.api.ValidatorOrder + 0.1
    label = "Children Grouped"
    families = ["Rig"]
    optional = True
    actions = [GroupChildren]

    def process(self, instance):
        armature = instance.data('armature')
        if not armature.users_group:
            return
        group = armature.users_group[0]
        for child in instance.data('children'):
            if not group in child.users_group:
                raise ValueError("%s should be in group %s" % (child.name, group.name))


class WidgetsNotGrouped(pyblish.api.InstancePlugin):
    """Ensure the bone widgets are not part of the same group as the armature"""

    version = (0, 0, 1)
    order = pyblish.api.ValidatorOrder + 0.2
    label = "Widgets not Grouped"
    families = ["Rig"]
    optional = True
    actions = [UngroupWidgets]

    def process(self, instance):
        armature = instance.data('armature')
        if not armature.users_group:
            return
        group = armature.users_group[0]
        for widget in instance.data('widgets'):
            if group in widget.users_group:
                raise ValueError("%s should not be in the same group (%s) as the armature" % (widget.name, group.name))


class NoAnimation(pyblish.api.InstancePlugin):
    """Ensure the armature and bones are not animated"""

    version = (0, 0, 1)
    order = pyblish.api.ValidatorOrder + 0.3
    label = "No Animation"
    families = ["Rig"]
    optional = True
    actions = [RemoveAnimation]

    def process(self, instance):
        for member in instance:
            if member.animation_data and member.animation_data.action:
                raise ValueError("%s should not be animated" % member.name)


class NoTransforms(pyblish.api.InstancePlugin):
    """Ensure the armature and bones have reset transformations"""

    version = (0, 0, 1)
    order = pyblish.api.ValidatorOrder + 0.4
    label = "No Transforms"
    families = ["Rig"]
    optional = True
    actions = [ResetTransforms]

    def process(self, instance):
        armature = instance.data('armature')
        identity_matrix = Matrix.Identity(4)
        if armature.matrix_world != identity_matrix:
            raise ValueError("%s has non-zero transforms" % armature.name)
        for pose_bone in armature.pose.bones:
            if pose_bone.matrix_basis != identity_matrix:
                raise ValueError("%s should be in rest position (no posed bones)" % armature.name)


bpy.utils.register_class(AddObjectsToGroup)
bpy.utils.register_class(ParentObjects)
bpy.utils.register_class(UnparentObjects)
bpy.utils.register_class(RemoveObjectsFromGroup)
bpy.utils.register_class(AnimationClear)
bpy.utils.register_class(TransformsClear)
