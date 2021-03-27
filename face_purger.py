"""

    Face Purger

    Blender plugin for optimising meshes by removing/purging hidden faces
    using various strategies and allowing control.

    Authored By Ryan Maugin (@ryanmaugv1)

"""

import bpy
import bmesh


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
        print('Executing Unselected Face Filter Operation.')

        # Loop through all selected active objects in edit mode.
        selected_objs = context.selected_objects
        for obj in selected_objs:
            # Get mesh as bmesh and get unselected_faces.
            obj_data = obj.data
            obj_bmesh = bmesh.from_edit_mesh(obj_data)
            unselected_faces = [face for face in obj_bmesh.faces if not face.select]

            # Delete all faces but those selected.
            bmesh.ops.delete(obj_bmesh, geom=unselected_faces, context='FACES')
            print('Number of unselected faces: %s' % len(unselected_faces))
            bmesh.update_edit_mesh(obj_data)

        # Set selected objects as active.
        for obj in selected_objs:
            bpy.context.view_layer.objects.active = obj

        # Join the active selected objs to form one mesh after face filter.
        bpy.ops.object.mode_set(mode='OBJECT')
        bpy.ops.object.join()

        # Recalculate and set origin to center of mass for joined object.
        bpy.ops.object.origin_set(type='ORIGIN_CENTER_OF_MASS')

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
