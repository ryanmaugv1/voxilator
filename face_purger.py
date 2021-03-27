"""

    Face Purger

    Blender plugin for optimising meshes by removing/purging hidden faces
    using various strategies and allowing control.

    Authored By Ryan Maugin (@ryanmaugv1)

"""

import bpy


# # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #
#
#   Operators
#
# # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #


class UnselectedFaceFilterOperator(bpy.types.Operator):
    """Operator for filtering/removing unselected faces from mesh."""

    bl_idname = 'fpurger.unselected_face_purger'
    bl_label  = 'Filters/Removes Unselected Faces'

    def execute(self, context):
        scene = context.scene
        return {'FINISHED'}


# # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #
#
#   Panels
#
# # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #


class FacePurgerPanel:
    """Define root panel configuration for plugin."""

    bl_space_type  = 'VIEW_3D'
    bl_region_type = 'UI'
    bl_category    = 'FPurger'

    @classmethod
    def poll(cls, context):
        """Returns true if there is a valid scene context else false."""
        return context.scene is not None


