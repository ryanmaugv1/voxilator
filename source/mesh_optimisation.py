"""

    Mesh Optimisation Module

    This module implements the mesh optimisation operators that can help
    reduce mesh complexity of imported voxel models for easier weight
    painting and better game performance.

    Authored By Ryan Maugin (@ryanmaugv1)

"""

import bpy
import bmesh
import mathutils
import numpy as np

from dataclasses import dataclass
from enum import Enum
from typing import Dict


# # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #
#
#   Utility Classes
#
# # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #


@dataclass
class Tuple2DCoord:
    def __init__(self, x, y=None):
        self.x = x
        self.y = y


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

    scale_window_shapes = [
        # ID, TEXT, DESCRIPTION, ICON
        ('scale_window_shapes.square', 'Square', 'Creates square shaped filter: [+]'),
        ('scale_window_shapes.h_rect', 'Horizontal Rectangle', 
            'Creates horizontal rectangle shaped filter: [|]'),
        ('scale_window_shapes.v_rect', 'Vertical Rectangle', 
            'Creates vertical rectangle shaped filter: [-]'),
    ]

    scale_window_shape: bpy.props.EnumProperty(
        items = scale_window_shapes,
        description = 'Determines the shape of the sliding window (also scaled by scale factor)',
        default = 'scale_window_shapes.square'
    )

    scale_selected_faces: bpy.props.BoolProperty(
        name = 'Selected Faces Only',
        description = 'Scale/merge selected mesh faces rather than entire mesh faces',
        default = False
    )

    preserve_uv: bpy.props.BoolProperty(
        name = 'Preserve UV',
        description = 'Preserve mesh UV when performing face scale (makes optimisation less effective)',
        default = False
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

    bl_idname = 'voxilator.face_filter'
    bl_label  = 'Filters/Removes Mesh Faces'


    def execute(self, context):
        print('=========================================================')
        print('Executing Face Filter Operation.')
        print('=========================================================')
        scene = context.scene
        filter_strategy = context.scene.addon_props.filter_strats
        removed_face_cnt = 0
        
        print('Selected Filter Strategy: %s' % filter_strategy)

        # Set mode to edit or else bmesh.from_edit_mesh() will fail.
        bpy.ops.object.mode_set(mode='EDIT')

        # Loop through all selected active objects in edit mode.
        selected_objs = context.selected_objects
        for obj in selected_objs:
            # Convert mesh to bmesh object.
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

            # Do some cleanup of the bmesh manually.
            obj_bmesh.select_flush_mode()
            obj_bmesh.free()

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

        print('Completed Face Filter Operation.')
        return {'FINISHED'}
    
    
class FaceScalingOperator(bpy.types.Operator):
    """Operator for scaling/merging mutiple faces from mesh into one to reduce geometry complexity"""

    bl_idname = 'voxilator.face_scaling'
    bl_label  = 'Scale/Merge Mesh Faces'


    def execute(self, context):
        print('=========================================================')
        print('     Executing Face Scaling Operation.')
        print('=========================================================')
        scene = context.scene
        scale_factor = context.scene.addon_props.face_scale_factor
        scale_selected_faces_only = context.scene.addon_props.scale_selected_faces
        scale_window_shape = context.scene.addon_props.scale_window_shape

        # Set mode to edit or else bmesh.from_edit_mesh() will fail.
        bpy.ops.object.mode_set(mode='EDIT')

        # Loop through each selected object and apply optimisation.
        selected_objs = context.selected_objects
        for obj in selected_objs:
            obj_data = obj.data
            obj_bmesh = bmesh.from_edit_mesh(obj_data)

            # Selected subset of faces if we only want to scale selected mesh faces.
            bmesh_faces = []
            if scale_selected_faces_only:
                bmesh_faces = [face for face in obj_bmesh.faces if face.select]
            else:
                bmesh_faces = obj_bmesh.faces

            # Ensure mesh has full-quad topology (no traingles).
            if not self._has_full_quad_topology(bmesh_faces):
                self.report(
                    {'ERROR'}, 'Optimisation can only be applied to mesh with full-quad topology.')
                return {'FINISHED'}
        
            # Applies optimisation and handles error/failure reporting back to user.
            self._apply_face_scaling(bmesh_faces, scale_factor, scale_window_shape)

        print('Completed Face Scaling Operation.')
        return {'FINISHED'}


    def _apply_face_scaling(
        self, faces: [bmesh.types.BMFace], scale_factor: int, scale_window_shape: str) -> bool:
        """Applies face scaling optimisation on quad topology bmesh face sequence.

        Arguments:
            faces: List of bmesh faces we want to apply scale optimisation to.
            scale_factor: Defines `SCALExSCALE` face pattern we will be optimising.
        
        Returns:
            `True` if applying face scaling succeeded, else `False`.
        """
        planar_groups = self._group_faces_by_plane(faces)
        print('Number of Planar Groups: %s' % len(planar_groups))
        print('PLANAR GROUP: \n%s' % planar_groups)
        
        # Derive sliding window shape.
        window_shape = self._derive_window_shape(scale_factor, scale_window_shape)
        if window_shape is None:
            return False
        print('WINDOW SHAPE: (x:%s, y:%s)' %(window_shape.x, window_shape.y))

        #       - First make sure planar group shape is greater than or equal to 2x2.
        #       a) For each match merge faces into one.
        #           - Ensure UV's are kept intact (research more on how to do this).
        #               - Could be done by not remove edges between diff coloured quads.
        #               - Look into Cycles "Bake" texture on new optimised mesh.
        
        # 7) Finalise mesh, cleanup and done.
        #       - Maybe add timer of how long task took to complete.
        return True


    def _group_faces_by_plane(self, faces: [bmesh.types.BMFace]) -> Dict[str, np.ndarray]:
        """Segments faces from mesh into 2-dimension planar groups.

        This method will take in a list of faces making up a mesh and segment
        the faces into planar groups. This means that faces with common normal
        direction and common position on normal axis will be grouped together
        in a numpy array forming a planar group.

        These generated planar groups map the position of each face relative to
        eachother.
        
        For example imagine a table-like mesh made up of the following faces:

        __________________
        [ ][ ]      [ ][ ]
        [ ][ ]      [ ][ ]

        The upward facing faces (denotes as "__") are on the same plane and will
        be placed within the same planar group. This planar group will 
        look something like this:

        [F, F, F, F, F, F, F]
        WHERE F = Face

        The forward facing faces (denoted as "[ ]") are on the same plane and will
        therefore be placed within the same planar group. This planar group will 
        look something like this:

        [F, F, 0, 0, 0, F, F]
        [F, F, 0, 0, 0, F, F]
        WHERE F = Face AND 0 = Padding Value (represent empty space).

        The above example illustrates what is meant by faces are positioned
        relative to eachother in planar groups.

        Arguments:
            faces: List of faces to group by plane.

        Returns:
            Dictionary, containing all mesh planar groups.
        """
        planar_groups = {}

        for face in faces:
            group_key = self._form_planar_group_key(face)

            # If planar group for face doesn't exists then init one with face.
            if not group_key in planar_groups:
                planar_groups[group_key] = [face]
                continue

            # Add all faces to respective plane group.
            planar_groups[group_key].append(face)

        for key, faces in planar_groups.items():
            # Get min and max x-axis and y-axis value to use for deriving shape of planar group.
            min_x_axis = min([self._convert_face_pos_vec_to_2d(face).x for face in faces])
            min_y_axis = min([self._convert_face_pos_vec_to_2d(face).y for face in faces])
            max_x_axis = max([self._convert_face_pos_vec_to_2d(face).x for face in faces])
            max_y_axis = max([self._convert_face_pos_vec_to_2d(face).y for face in faces])

            # Define new planar group matrix with shape that enncompasses entire plane area.
            planar_group_shape = (int((max_x_axis - min_x_axis) + 1), int((max_y_axis - min_y_axis) + 1))
            planar_group_ndarray = np.zeros((planar_group_shape[1], planar_group_shape[0]), dtype='object')
           
            # Add faces into new planar group matrix in a way which encodes they're world position.
            for face in faces:
                face_center_vec = self._convert_face_pos_vec_to_2d(face)
                col_index = int(face_center_vec.x - min_x_axis)
                row_index = int(face_center_vec.y - min_y_axis)
                planar_group_ndarray[row_index][col_index] = face
            planar_groups[key] = planar_group_ndarray

        return planar_groups


    def _convert_face_pos_vec_to_2d(self, face: bmesh.types.BMFace) -> Tuple2DCoord:
        """Convert 3D blender vector into a 2D tuple vector excluding the normal axis for given face.

        We flatten the 3D Blender vector into a 2D tuple vector as planar groups are not 3D tensors.
        This is done by excluding the normal axis of the face (axis which pokes through plane) and 
        keep the two axis's which go vertically and horizontally along the plane.
        
        Arguments:
            face: BMesh face to get normal axis and center position vector that is to be converted.

        Returns:
            Tuple2DCoord, with x and y axis of face on plane.
        """
        face_center_vec = face.calc_center_bounds()
        if face.normal.x in [-1, 1]:
            return Tuple2DCoord(round(face_center_vec.y, 1), round(face_center_vec.z, 1))
        if face.normal.y in [-1, 1]:
            return Tuple2DCoord(round(face_center_vec.x, 1), round(face_center_vec.z, 1))
        return Tuple2DCoord(round(face_center_vec.x, 1), round(face_center_vec.y, 1))

    
    def _form_planar_group_key(self, face: bmesh.types.BMFace) -> str:
        """Creates a dict key for planar group the given face belongs to.
        
        This method creates a key for the planar group dictionary, this key
        is derived from the given mesh center and normal vector.

        Keys are derived like so:

        FN = Face Normal
        FC = Face Center
        KEY = '{FN.x}.{FN.y}.{FN.z}_'
        if FN.x != 0: KEY += 'X{FC.x}'
        if FN.y != 0: KEY += 'Y{FC.y}'
        if FN.z != 0: KEY += 'Z{FC.z}'

        Note: For the sake of readability I have not included decimal obj
        conversion for floating-point precision correction.

        Which should look something like this:

        WHEN: 
            FN = [0, -1, 0], FC = [8.5, 12, 3]
        THEN:
            KEY = "0.-1.0_Y12"

        Arguments:
            face: Face to derive planar group dict key from.

        Returns:
            String, planar group dictionary key derived from face.
        """
        fn = face.normal
        fc = face.calc_center_bounds()
        key = '%s.%s.%s_' % (int(fn.x), int(fn.y), int(fn.z))
        if fn.x in [-1, 1]: key += 'X%s' % round(fc.x, 1)
        if fn.y in [-1, 1]: key += 'Y%s' % round(fc.y, 1)
        if fn.z in [-1, 1]: key += 'Z%s' % round(fc.z, 1)
        return key


    def _derive_window_shape(self, scale_factor: int, scale_window_shape: str) -> Tuple2DCoord:
        """Derive sliding window shape based on given scale factor and desired shape.
        
        Arguments:
            scale_factor: Integer used to scale window shape by.
            scale_window_shape: Shape of the window e..g square, vertical rectangle etc.

        Returns:
            Tuple2DCoord containing window shape, else `None` if derivation fails.
        """
        if scale_window_shape == 'scale_window_shapes.square':
            return Tuple2DCoord(scale_factor, scale_factor)
        if scale_window_shape == 'scale_window_shapes.h_rect':
            return Tuple2DCoord(0, scale_factor)
        if scale_window_shape == 'scale_window_shapes.v_rect':
            return Tuple2DCoord(scale_factor, 0)
        self.report(
            {'ERROR'}, 
            'Unsupported window shape %s cannot be used (report this to dev).' % scale_window_shape)
        return None


    def _has_full_quad_topology(self, faces: [bmesh.types.BMFace]) -> bool:
        """Check that all mesh faces have 4 vertices, ensuring full-quad topology."""
        for face in faces:
            if len(face.verts) != 4:
                return False
        return True


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
        box.prop(context.scene.addon_props, 'face_scale_factor', text='Scale Factor')
        box.prop(context.scene.addon_props, 'scale_window_shape', text='Window Shape')
        box.prop(context.scene.addon_props, 'scale_selected_faces')
        box.prop(context.scene.addon_props, 'preserve_uv')
        box.operator(FaceScalingOperator.bl_idname, text='Scale')


# # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #
#
#   Module Management
#
# # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #


class MeshOptimisationModule:
    """Mesh optimisation module wrapper."""

    # List of classes to register (order matters)
    CLASSES = [
        FaceFilterOperator,
        FaceScalingOperator,
        AddonProperties,
        MeshOptimisationPanel
    ]

    @staticmethod
    def register():
        from bpy.utils import register_class
        for cls in MeshOptimisationModule.CLASSES:
            register_class(cls)
        AddonProperties.register_addon_props()
        print('Mesh Optimisation Module Class Register Procedure Completed.')

    @staticmethod
    def unregister():
        from bpy.utils import unregister_class
        for cls in reversed(MeshOptimisationModule.CLASSES):
            unregister_class(cls)
        AddonProperties.unregister_addon_props()
        print('Mesh Optimisation Module Class Unregisteration Procedure Completed,')