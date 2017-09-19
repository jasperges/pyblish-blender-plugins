"""Validate the rig(s)."""

import pyblish.api


# TODO: make sure the file is saved before publish


class ValidateRigContents(pyblish.api.InstancePlugin):
    """Ensure rig has the appropriate contents"""
    # TODO!

    order = pyblish.api.ValidatorOrder
    families = ['Rig']

    def process(self, instance):
        self.log.warning("Not validating anything at the moment... :/")
