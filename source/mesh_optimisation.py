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

    scale_selected_faces: bpy.props.BoolProperty(
        name = 'Selected Faces Only',
        description = 'Scale/merge selected mesh faces rather than entire mesh faces',
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
        print('Executing Face Filter Operation.')
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
        print('Executing Face Scaling Operation.')
        scene = context.scene
        scale_factor = context.scene.addon_props.face_scale_factor
        scale_selected_faces_only = context.scene.addon_props.scale_selected_faces

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
            if not self._apply_face_scaling(bmesh_faces, scale_factor):
                self.report({'ERROR'}, 'Failed to perform face scaling optimisation on mesh.')

        print('Completed Face Scaling Operation.')
        return {'FINISHED'}


    def _apply_face_scaling(self, faces: [bmesh.types.BMFace], scale_factor: int) -> bool:
        """Applies face scaling optimisation on quad topology bmesh face sequence.

        Arguments:
            faces: List of bmesh faces we want to apply scale optimisation to.
            scale_factor: Defines `SCALExSCALE` face pattern we will be optimising.
        
        Returns:
            `True` if applying face scaling succeeded, else `False`.
        """
        # TODO(ryanmaugv1): Implement face scaling algorithm and test on voxel mesh.
        # Grouping:
        # 1) Create dict key first partition : {face.normal.x}{face.normal.y}
        #      a) Derived from "face.normal".
        #           - Might have to normalise normal vector if not done so already.
        # 2) Create dict key second partition: _{normalDirectionAxis}{PlaneConstForNormalDirAxis}
        #      a) Derived from "face.calc_center_bounds()" 
        #           - Check if returned vector is relative to local or global space.
        #           - If we need to do space transformation on vector we need to embed it in face obj.
        # 3) Check if key exists in "plane_groups" dictionary, else create a new entry with key. 
        # 4) Add face into correct position within correct plane_group matrix.
        #      a) If plane_group contain empty np.array simply just add it as only element.
        #      b) If plane_group is not empty.
        #           I) Get an available corner element.
        #           II) Calculate relative position for new face:
        #               Formula: CORNER_FACE_CENTER_VEC - NEW_FACE_CENTER_VEC
        #           III) Scale result vector by -1 if face.normal point BACK or DOWN relative to WORLD orientation.
        #           IV) Add extra dimensions if neeeded and/or place face obj in position.
        #               - Should be in corner if dimensions were expanded.
        #               - Should not be in corner if dimensions were not expanded.
        # 5) Create a stride filter matrix, derived from scale factor.
        # 6) Aopply stride filter to plane_groups.
        #       a) For each match merge faces into one.
        #           - Ensure UV's are kept intact (research more on how to do this).
        #               - Could be done by not remove edges between diff coloured quads.
        #               - Look into Cycles "Bake" texture on new optimised mesh.
        # 7) Finalise mesh, cleanup and done.
        return True


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
        box.prop(context.scene.addon_props, 'face_scale_factor', text='')
        box.prop(context.scene.addon_props, 'scale_selected_faces')
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