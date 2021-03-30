"""

    Voxilator Root Module

    Imports all voxilator sub-modules and also handles import reloads 
    if module source changes. This module enables this addon to be
    installed within Blender and improves development workflow by allowing
    script reloading in Blender (Blender Icon -> System -> Reload Scripts). 

    This file must remain at root of project to allow for addon
    installation as zip.

    Authored By Ryan Maugin (@ryanmaugv1)

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
    "wiki_url": "https://github.com/ryanmaugv1/voxilator",
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

    if "MeshOptimisationModule" in locals():
        from .source import mesh_optimisation
        importlib.reload(mesh_optimisation)

# Imports module classes if "bpy" module does not exist (infers first run).
else:
    from .source.mesh_optimisation import MeshOptimisationModule

import bpy

# List of all addon modules.
modules = [MeshOptimisationModule]

# Called by Blender and triggers addon's module registerations.
def register():
    for mod in modules:
        mod.register()

# Called by Blender and triggers addon's module unregisterations.
def unregister():
    for mod in reversed(modules):
        mod.unregister()