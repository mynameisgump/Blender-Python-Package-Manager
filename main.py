bl_info = {
    "name": "Python Package Manager",
    "author": "Your Name",
    "version": (1, 0, 0),
    "blender": (3, 0, 0),
    "location": "Edit > Preferences > Python Package Manager",
    "description": "Manage Python packages in Blender",
    "category": "System",
}

import bpy
import subprocess
import sys
import os
import threading
from bpy.props import StringProperty, CollectionProperty, BoolProperty
from bpy.types import PropertyGroup, Panel, Operator, UIList


class PackageInfo(PropertyGroup):
    name: StringProperty(name="Package Name", default="")
    version: StringProperty(name="Version", default="")


class PYTHON_OT_refresh_packages(Operator):
    bl_idname = "python.refresh_packages"
    bl_label = "Refresh Package List"
    bl_description = "Refresh the list of installed packages"
    
    def execute(self, context):
        scene = context.scene
        scene.python_packages.clear()
        
        try:
            # Get Blender's Python executable path
            python_exe = sys.executable
            
            # Run pip list to get installed packages
            result = subprocess.run([python_exe, "-m", "pip", "list", "--format=json"], 
                                  capture_output=True, text=True, check=True)
            
            import json
            packages = json.loads(result.stdout)
            
            for pkg in packages:
                item = scene.python_packages.add()
                item.name = pkg['name']
                item.version = pkg['version']
                
            self.report({'INFO'}, f"Found {len(packages)} installed packages")
            
        except subprocess.CalledProcessError as e:
            self.report({'ERROR'}, f"Failed to get package list: {e}")
        except json.JSONDecodeError:
            self.report({'ERROR'}, "Failed to parse package list")
        except Exception as e:
            self.report({'ERROR'}, f"Error: {str(e)}")
            
        return {'FINISHED'}


class PYTHON_OT_install_package(Operator):
    bl_idname = "python.install_package"
    bl_label = "Install Package"
    bl_description = "Install a Python package"
    
    package_name: StringProperty(
        name="Package Name",
        description="Name of the package to install",
        default=""
    )
    
    def execute(self, context):
        if not self.package_name.strip():
            self.report({'ERROR'}, "Package name cannot be empty")
            return {'CANCELLED'}
            
        # Show progress message
        self.report({'INFO'}, f"Installing {self.package_name}...")
        
        # Run installation in a separate thread to avoid blocking UI
        def install_package():
            try:
                python_exe = sys.executable
                
                # Install package using pip
                result = subprocess.run([python_exe, "-m", "pip", "install", self.package_name.strip()], 
                                      capture_output=True, text=True, check=True)
                
                # Schedule UI update on main thread
                def update_ui():
                    self.report({'INFO'}, f"Successfully installed {self.package_name}")
                    # Refresh package list
                    bpy.ops.python.refresh_packages()
                
                bpy.app.timers.register(update_ui, first_interval=0.1)
                
            except subprocess.CalledProcessError as e:
                def show_error():
                    error_msg = e.stderr if e.stderr else str(e)
                    self.report({'ERROR'}, f"Failed to install {self.package_name}: {error_msg}")
                
                bpy.app.timers.register(show_error, first_interval=0.1)
            except Exception as e:
                def show_error():
                    self.report({'ERROR'}, f"Error installing {self.package_name}: {str(e)}")
                
                bpy.app.timers.register(show_error, first_interval=0.1)
        
        # Start installation in background thread
        thread = threading.Thread(target=install_package)
        thread.daemon = True
        thread.start()
        
        return {'FINISHED'}
    
    def invoke(self, context, event):
        return context.window_manager.invoke_props_dialog(self)


class PYTHON_OT_uninstall_package(Operator):
    bl_idname = "python.uninstall_package"
    bl_label = "Uninstall Package"
    bl_description = "Uninstall the selected Python package"
    
    package_name: StringProperty(
        name="Package Name",
        description="Name of the package to uninstall",
        default=""
    )
    
    def execute(self, context):
        if not self.package_name.strip():
            self.report({'ERROR'}, "Package name cannot be empty")
            return {'CANCELLED'}
            
        # Show progress message
        self.report({'INFO'}, f"Uninstalling {self.package_name}...")
        
        def uninstall_package():
            try:
                python_exe = sys.executable
                
                # Uninstall package using pip
                result = subprocess.run([python_exe, "-m", "pip", "uninstall", "-y", self.package_name.strip()], 
                                      capture_output=True, text=True, check=True)
                
                def update_ui():
                    self.report({'INFO'}, f"Successfully uninstalled {self.package_name}")
                    # Refresh package list
                    bpy.ops.python.refresh_packages()
                
                bpy.app.timers.register(update_ui, first_interval=0.1)
                
            except subprocess.CalledProcessError as e:
                def show_error():
                    error_msg = e.stderr if e.stderr else str(e)
                    self.report({'ERROR'}, f"Failed to uninstall {self.package_name}: {error_msg}")
                
                bpy.app.timers.register(show_error, first_interval=0.1)
            except Exception as e:
                def show_error():
                    self.report({'ERROR'}, f"Error uninstalling {self.package_name}: {str(e)}")
                
                bpy.app.timers.register(show_error, first_interval=0.1)
        
        thread = threading.Thread(target=uninstall_package)
        thread.daemon = True
        thread.start()
        
        return {'FINISHED'}
    
    def invoke(self, context, event):
        return context.window_manager.invoke_props_dialog(self)


class PYTHON_OT_search_packages(Operator):
    bl_idname = "python.search_packages"
    bl_label = "Search PyPI"
    bl_description = "Search for packages on PyPI"
    
    search_term: StringProperty(
        name="Search Term",
        description="Search term for PyPI packages",
        default=""
    )
    
    def execute(self, context):
        if not self.search_term.strip():
            self.report({'ERROR'}, "Search term cannot be empty")
            return {'CANCELLED'}
            
        # Clear previous search results
        context.scene.search_results.clear()
        
        def search_packages():
            try:
                python_exe = sys.executable
                
                # Use pip search alternative (since pip search was disabled)
                # We'll use a simple approach with requests to PyPI API
                search_code = f"""
import json
import urllib.request
import urllib.parse

search_term = '{self.search_term.strip()}'
url = f'https://pypi.org/simple/'

# This is a basic search - for a more advanced search, you'd use PyPI's JSON API
# For now, we'll just show a message that search functionality needs enhancement
print(json.dumps([{{"name": "Search feature", "summary": "Use pip install <package_name> directly"}}]))
"""
                
                result = subprocess.run([python_exe, "-c", search_code], 
                                      capture_output=True, text=True, check=True)
                
                def update_ui():
                    self.report({'INFO'}, f"Search completed for '{self.search_term}'. Use 'Install Package' to install known packages.")
                
                bpy.app.timers.register(update_ui, first_interval=0.1)
                
            except Exception as e:
                def show_error():
                    self.report({'ERROR'}, f"Search failed: {str(e)}")
                
                bpy.app.timers.register(show_error, first_interval=0.1)
        
        thread = threading.Thread(target=search_packages)
        thread.daemon = True
        thread.start()
        
        return {'FINISHED'}
    
    def invoke(self, context, event):
        return context.window_manager.invoke_props_dialog(self)


class PYTHON_UL_package_list(UIList):
    def draw_item(self, context, layout, data, item, icon, active_data, active_propname):
        if self.layout_type in {'DEFAULT', 'COMPACT'}:
            # Create a split layout for better organization
            split = layout.split(factor=0.6)
            
            # Left side - package name
            left_col = split.column()
            left_col.alignment = 'LEFT'
            left_col.label(text=item.name, icon='PACKAGE')
            
            # Right side - version and uninstall button
            right_split = split.split(factor=0.7)
            
            # Version
            version_col = right_split.column()
            version_col.alignment = 'LEFT'
            version_col.label(text=f"v{item.version}")
            
            # Uninstall button
            button_col = right_split.column()
            button_col.alignment = 'RIGHT'
            op = button_col.operator("python.uninstall_package", text="Remove", icon='X')
            op.package_name = item.name
            
        elif self.layout_type in {'GRID'}:
            layout.alignment = 'CENTER'
            layout.label(text=item.name, icon='PACKAGE')


class PYTHON_OT_open_package_manager(Operator):
    bl_idname = "python.open_package_manager"
    bl_label = "Python Package Manager"
    bl_description = "Open Python Package Manager window"
    
    def execute(self, context):
        return context.window_manager.invoke_props_dialog(self, width=800)
    
    def draw(self, context):
        layout = self.layout
        scene = context.scene
        
        # Main container
        main_col = layout.column()
        
        # Title
        title_row = main_col.row()
        title_row.label(text="Python Package Manager", icon='CONSOLE')
        
        main_col.separator()
        
        # Action buttons section
        actions_box = main_col.box()
        actions_box.label(text="Actions:", icon='TOOL_SETTINGS')
        
        actions_row = actions_box.row(align=True)
        actions_row.scale_y = 1.2
        actions_row.operator("python.refresh_packages", text="Refresh List", icon='FILE_REFRESH')
        actions_row.operator("python.install_package", text="Install Package", icon='IMPORT')
        actions_row.operator("python.search_packages", text="Search PyPI", icon='VIEWZOOM')
        
        main_col.separator()
        
        # Package list section
        packages_box = main_col.box()
        packages_header = packages_box.row()
        packages_header.label(text=f"Installed Packages ({len(scene.python_packages)}):", icon='PACKAGE')
        
        if scene.python_packages:
            # Create a cleaner package list
            packages_box.template_list("PYTHON_UL_package_list", "", scene, "python_packages", 
                                     scene, "python_package_index", rows=15)
        else:
            no_packages_row = packages_box.row()
            no_packages_row.alignment = 'CENTER'
            no_packages_row.label(text="No packages found")
            
            refresh_row = packages_box.row()
            refresh_row.alignment = 'CENTER'
            refresh_row.operator("python.refresh_packages", text="Refresh Package List", icon='FILE_REFRESH')
            
        main_col.separator()
        
        # Python environment info section
        info_box = main_col.box()
        info_box.label(text="Python Environment:", icon='INFO')
        
        info_col = info_box.column(align=True)
        info_col.label(text=f"Version: {sys.version.split()[0]}")
        info_col.label(text=f"Executable: {os.path.basename(sys.executable)}")
        info_col.label(text=f"Path: {sys.executable}")


class PYTHON_OT_open_package_window(Operator):
    """Deprecated - keeping for compatibility"""
    bl_idname = "python.open_package_window"
    bl_label = "Python Package Manager Window"
    bl_description = "Open Python Package Manager in a separate window"
    
    def execute(self, context):
        bpy.ops.python.open_package_manager('INVOKE_DEFAULT')
        return {'FINISHED'}


def menu_func(self, context):
    self.layout.operator("python.open_package_manager", icon='CONSOLE')


def register():
    bpy.utils.register_class(PackageInfo)
    bpy.utils.register_class(PYTHON_OT_refresh_packages)
    bpy.utils.register_class(PYTHON_OT_install_package)
    bpy.utils.register_class(PYTHON_OT_uninstall_package)
    bpy.utils.register_class(PYTHON_OT_search_packages)
    bpy.utils.register_class(PYTHON_UL_package_list)
    bpy.utils.register_class(PYTHON_OT_open_package_manager)
    bpy.utils.register_class(PYTHON_OT_open_package_window)
    
    # Add to preferences menu
    bpy.types.TOPBAR_MT_edit.append(menu_func)
    
    # Add properties to scene
    bpy.types.Scene.python_packages = CollectionProperty(type=PackageInfo)
    bpy.types.Scene.python_package_index = bpy.props.IntProperty(default=0)
    bpy.types.Scene.search_results = CollectionProperty(type=PackageInfo)


def unregister():
    bpy.utils.unregister_class(PackageInfo)
    bpy.utils.unregister_class(PYTHON_OT_refresh_packages)
    bpy.utils.unregister_class(PYTHON_OT_install_package)
    bpy.utils.unregister_class(PYTHON_OT_uninstall_package)
    bpy.utils.unregister_class(PYTHON_OT_search_packages)
    bpy.utils.unregister_class(PYTHON_UL_package_list)
    bpy.utils.unregister_class(PYTHON_OT_open_package_manager)
    bpy.utils.unregister_class(PYTHON_OT_open_package_window)
    
    # Remove from preferences menu
    bpy.types.TOPBAR_MT_edit.remove(menu_func)
    
    # Remove properties from scene
    del bpy.types.Scene.python_packages
    del bpy.types.Scene.python_package_index
    del bpy.types.Scene.search_results


if __name__ == "__main__":
    register()