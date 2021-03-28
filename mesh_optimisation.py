"""

    Mesh Optimisation Module

    This module implements the mesh optimisation operators that can help
    reduce mesh complexity of imported voxel models for easier weight
    painting and better game performance.

    Authored By Ryan Maugin (@ryanmaugv1)

"""

import bpy
import bmesh


# # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #
#
#   Property Groups
#
# # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #


class AddonProperties(bpy.types.PropertyGroup):
    """Defines all custom addon property groups."""
    
    filter_strategy_options = [
        # ID, TEXT, DESCRIPTION, ICON
        ('filter_strategy.selected_faces', 'Selected', 'Filter/remove all selected faces'),
        ('filter_strategy.unselected_faces', 'Unselected', 'Filter/remove all unselected faces')
    ]
    
    filter_strats: bpy.props.EnumProperty(
        items = filter_strategy_options,
        description = 'Face filtering strategy to use when executing filter operator',
        default = 'filter_strategy.unselected_faces'
    )
    
    face_scale_factor: bpy.props.IntProperty(
        description = 'Merge/scale all faces that form `SCALE x SCALE` planes into one mesh',
        default = 2,
        min = 2
    )
    
    @classmethod
    def register_addon_props(cls):
        bpy.types.Scene.addon_props = bpy.props.PointerProperty(type=cls)
        
    @staticmethod
    def unregister_addon_props():
        del bpy.types.Scene.addon_props


# # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #
#
#   Operators
#
# # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #


class FaceFilterOperator(bpy.types.Operator):
    """Operator for filtering/removing faces from mesh using a specific strategy"""

    bl_idname = 'fpurger.face_filter'
    bl_label  = 'Filters/Removes Mesh Faces'

    def execute(self, context):
        print('Executing Face Filter Operation.')
        scene = context.scene
        filter_strategy = context.scene.addon_props.filter_strats
        removed_face_cnt = 0
        
        print('Selected Filter Strategy: %s' % filter_strategy)

        # Loop through all selected active objects in edit mode.
        selected_objs = context.selected_objects
        for obj in selected_objs:
            # Get mesh as bmesh.
            obj_data = obj.data
            obj_bmesh = bmesh.from_edit_mesh(obj_data)

            # Get faces to filter based on filter strategy
            faces_to_filter = []
            if filter_strategy == 'filter_strategy.unselected_faces':
                faces_to_filter = [face for face in obj_bmesh.faces if not face.select]
            if filter_strategy == 'filter_strategy.selected_faces':
                faces_to_filter = [face for face in obj_bmesh.faces if face.select]

            # Delete all faces within faces filter.
            bmesh.ops.delete(obj_bmesh, geom=faces_to_filter, context='FACES')
            removed_face_cnt += len(faces_to_filter)
            bmesh.update_edit_mesh(obj_data)

        print('Removed a total of %s faces from a collection of %s objects.'
              % (removed_face_cnt, len(selected_objs)))

        # Set selected objects as active.
        for obj in selected_objs:
            bpy.context.view_layer.objects.active = obj

        # Join the active selected objs to form one mesh after face filter.
        bpy.ops.object.mode_set(mode='OBJECT')
        bpy.ops.object.join()

        # Recalculate and set origin to center of mass for joined object.
        bpy.ops.object.origin_set(type='ORIGIN_CENTER_OF_MASS')

        # Merge vertex by distance of 0.0001m to get rid of duped verts and geom artefacts.
        bpy.ops.object.mode_set(mode='EDIT')
        bpy.ops.mesh.remove_doubles(threshold=0.0001)
        bpy.ops.object.mode_set(mode='OBJECT')

        print('Completed Face Filter Operation.')
        return {'FINISHED'}
    
    
class FaceScalingOperator(bpy.types.Operator):
    """Operator for scaling/merging mutiple faces from mesh into one to reduce geometry complexity"""

    bl_idname = 'fpurger.face_scaling'
    bl_label  = 'Scale/Merge Mesh Faces'

    def execute(self, context):
        print('Executing Face Scaling Operation.')
        return {'FINISHED'}


# # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #
#
#   Panels
#
# # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #


class VoxilatorPanel:
    """Define root panel configuration for addon."""

    bl_space_type  = 'VIEW_3D'
    bl_region_type = 'UI'
    bl_category    = 'Voxilator'

    @classmethod
    def poll(cls, context):
        """Returns true if there is a valid scene context else false."""
        return context.scene is not None


class MeshOptimisationPanel(VoxilatorPanel, bpy.types.Panel):
    """Panel for mesh optimisation related UI and operators."""

    bl_idname = 'VIEW3D_PT_MESHOPTIMISATION'
    bl_label  = 'Mesh Optimisation'

    def draw(self, context):
        layout, scene = self.layout, context.scene
        
        box = layout.box()
        box.label(text='Filter Strategy')
        box.prop(context.scene.addon_props, 'filter_strats', text='')
        box.operator(FaceFilterOperator.bl_idname, text='Filter')

        box = layout.box()        
        box.label(text='Face Scaling')
        box.prop(context.scene.addon_props, 'face_scale_factor', text='')
        box.operator(FaceScalingOperator.bl_idname, text='Scale')


# # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #
#
#   Class Management
#
# # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #


# List of classes to register (order matters)
CLASSES = [
    FaceFilterOperator,
    FaceScalingOperator,
    AddonProperties,
    MeshOptimisationPanel
]


def register():
    from bpy.utils import register_class
    for cls in CLASSES:
        register_class(cls)
    AddonProperties.register_addon_props()
    print('Class Register Procedure Completed.')


def unregister():
    from bpy.utils import unregister_class
    for cls in reversed(CLASSES):
        unregister_class(cls)
    AddonProperties.unregister_addon_props()
    print('Class Unregisteration Procedure Completed,')


if __name__ == '__main__':
    register()
