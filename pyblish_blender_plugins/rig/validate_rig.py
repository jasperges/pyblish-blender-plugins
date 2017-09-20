"""Validate the rig(s)."""

# TODO:
#     - check if several armatures are not in the same group?
#     - check if an armature is parented

import pyblish.api
from mathutils import Matrix


class IsGrouped(pyblish.api.InstancePlugin):
    """Ensure the rig is in a group"""

    version = (0, 0, 1)
    order = pyblish.api.ValidatorOrder
    label = "Is Grouped"
    families = ["Rig"]
    optional = True

    def process(self, instance):
        armature = instance.data('armature')
        if not armature.users_group:
            raise ValueError("Armature '%s' is not grouped" % armature.name)
        if len(armature.users_group) > 1:
            raise ValueError("Armature '%s' should be in exactly 1 group" % armature.name)


class ChildrenInGroup(pyblish.api.InstancePlugin):
    """Ensure the children are in the same group as the armature"""

    version = (0, 0, 1)
    order = pyblish.api.ValidatorOrder + 0.1
    label = "Children Grouped"
    families = ["Rig"]
    optional = True
    # TODO: add action to group children

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
    # TODO: add action to remove widgets from the offending group

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
    label = "Not Animated"
    families = ["Rig"]
    optional = True
    # TODO: add action to remove animation

    def process(self, instance):
        armature = instance.data('armature')
        if armature.animation_data and armature.animation_data.action:
            raise ValueError("%s should not be animated" % armature.name)


class NoTransforms(pyblish.api.InstancePlugin):
    """Ensure the armature and bones have reset transformations"""

    version = (0, 0, 1)
    order = pyblish.api.ValidatorOrder + 0.4
    label = "No Transforms"
    families = ["Rig"]
    optional = True
    # TODO: add action to reset all transforms

    def process(self, instance):
        armature = instance.data('armature')
        identity_matrix = Matrix.Identity(4)
        if armature.matrix_world != identity_matrix:
            raise ValueError("%s has non-zero transforms" % armature.name)
        for pose_bone in armature.pose.bones:
            if pose_bone.matrix_basis != identity_matrix:
                raise ValueError("%s should be in rest position (no posed bones)" % armature.name)
