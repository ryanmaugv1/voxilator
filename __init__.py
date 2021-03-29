"""

    Voxilator Root Module

    Imports all voxilator sub-modules and also handles import reloads 
    if module source changes.

    Authored By Ryan Maugin

"""


# # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #
#
#   Blender Addon Info Object
#
# # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #


bl_info = {
    "name": "Voxilator",
    "description": "Enables hassle-free voxel art workflow for game development.",
    "author": "Ryan Maugin",
    "version": (0, 1),
    "blender": (2, 91, 2),
    "location": "Mesh",
    "wiki_url": "https://github.com/ryanmaugv1/blender_voxilator",
    "support": "COMMUNITY",
    "category": "Mesh",
}


# # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #
#
#   Blender Addon Info Object
#
# # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #


# Reloads modules if they exist in local symbols table.
if "bpy" in locals():
    import importlib
    if "mesh_optimisation" in locals():
        importlib.reload(mesh_optimisation)
# Imports module classes if module exists in local symbols table
else:
    from .mesh_optimisation import MeshOptimisationModule

import bpy


# Call all module register methods to register entire addon.
def register():
    modules = [MeshOptimisationModule]
    for mod in modules:
        mod.register()