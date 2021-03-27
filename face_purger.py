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


class UnselectedFaceFilterPanel(FacePurgerPanel, bpy.types.Panel):
    """Panel for select face filter related UI."""

    bl_idname = 'VIEW3D_PT_UNSELECTEDACEFILTER'
    bl_label  = 'Unselected Face Filter'

    def draw(self, context):
        layout, scene = self.layout, context.scene

        col = layout.column()
        col.operator(UnselectedFaceFilterOperator.bl_idname, 
                     text='Delete Unselected Faces', icon='FILTER')


# # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #
#
#   Class Management
#
# # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #


# List of classes to register (order matters)
CLASSES = [
    UnselectedFaceFilterOperator,
    UnselectedFaceFilterPanel
]


def register():
    from bpy.utils import register_class
    for cls in CLASSES:
        register_class(cls)
    print('Class Register Procedure Completed.')


def unregister():
    from bpy.utils import unregister_class
    for cls in reversed(CLASSES):
        unregister_class(cls)
    print('Class Unregisteration Procedure Completed,')


if __name__ == '__main__':
    register()
