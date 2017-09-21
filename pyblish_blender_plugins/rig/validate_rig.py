"""Validate the rig(s)."""

# TODO:
#     - check if several armatures are not in the same group?
#     - check if an armature is parented
#     - check if children or widgets have animation (add to NoAnimation)
#     - check if all 'armature modifier' children are also parented to the armature

import pyblish.api
import bpy
from mathutils import Matrix


class SelectInvalidNodes(pyblish.api.Action):
    label = "Select Broken Objects"
    on = "failed"
    icon = "hand-o-up"

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


class GroupChildren(pyblish.api.Action):
    """Put the children in the same group as the armature"""

    label = "Put Children in Armature Group"
    on = "failed"
    icon = "users"

    def process(self, context, plugin):
        for result in context.data['results']:
            if result['error'] and plugin == result['plugin']:
                instance = result['instance']
                armature = instance.data('armature')
                if not armature.users_group:
                    return
                group = armature.users_group[0]
                for child in instance.data('children'):
                    try:
                        group.objects.link(child)
                        self.log.info("%s is now in group %s" % (child.name, group.name))
                    except RuntimeError:
                        pass


class UngroupWidgets(pyblish.api.Action):
    """Remove the widgets from the armature group"""

    label = "Remove Widgets from Armature Group"
    on = "failed"
    icon = "times"

    def process(self, context, plugin):
        for result in context.data['results']:
            if result['error'] and plugin == result['plugin']:
                instance = result['instance']
                armature = instance.data('armature')
                if not armature.users_group:
                    return
                group = armature.users_group[0]
                for widget in instance.data('widgets'):
                    try:
                        group.objects.unlink(widget)
                        self.log.info("%s is removed from group %s" % (widget.name, group.name))
                    except RuntimeError:
                        pass


class RemoveAnimation(pyblish.api.Action):
    """Remove all animation from objects"""

    label = "Remove Animation"
    on = "failed"
    icon = "times"

    def process(self, context, plugin):
        for result in context.data['results']:
            if result['error'] and plugin == result['plugin']:
                instance = result['instance']
                for member in instance:
                    if member.animation_data:
                        member.animation_data_clear()
                        self.log.info("Removed animation data from %s" % member.name)


class ResetTransforms(pyblish.api.Action):
    """Reset all transforms"""

    label = "Reset Rig Transforms"
    on = "failed"
    icon = "times"

    def process(self, context, plugin):
        for result in context.data['results']:
            if result['error'] and plugin == result['plugin']:
                instance = result['instance']
                armature = instance.data('armature')
                identity_matrix = Matrix.Identity(4)
                if armature.matrix_world != identity_matrix:
                    armature.matrix_world = identity_matrix
                    self.log.info("Transformations of %s are reset" % armature.name)
                for pose_bone in armature.pose.bones:
                    if pose_bone.matrix_basis != identity_matrix:
                        pose_bone.matrix_basis = identity_matrix
                        self.log.info("Transformations of %s are reset" % pose_bone.name)


class IsGrouped(pyblish.api.InstancePlugin):
    """Ensure the rig is in a group"""

    version = (0, 0, 1)
    order = pyblish.api.ValidatorOrder
    label = "Is Grouped"
    families = ["Rig"]
    optional = True
    # actions = [SelectInvalidNodes]

    def process(self, instance):
        armature = instance.data('armature')
        if not armature.users_group:
            # instance.set_data('broken', armature)
            raise ValueError("Armature '%s' is not grouped" % armature.name)
        if len(armature.users_group) > 1:
            # instance.set_data('broken', armature)
            raise ValueError("Armature '%s' should be in exactly 1 group" % armature.name)


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
