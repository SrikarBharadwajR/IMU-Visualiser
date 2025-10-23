# pyvista_widget.py
# This module contains the PyVista widget for rendering the 3D cuboid.
# It replaces the old gl_widget.py

import vtk
import pyvista as pv
import numpy as np
from pyvistaqt import QtInteractor
from PyQt5.QtGui import QQuaternion
from PyQt5.QtWidgets import QFrame

# Ensure pyvista uses the Qt backend
pv.set_plot_theme("document")  # Use a neutral theme


class RotateOnlyInteractorStyle(vtk.vtkInteractorStyleTrackballCamera):
    """A custom interactor style that only allows camera rotation."""

    def __init__(self):
        super().__init__()
        # Set a high priority to intercept these events first
        priority = -1.0
        self.AddObserver("MiddleButtonPressEvent", self.no_op, priority)
        self.AddObserver("MiddleButtonReleaseEvent", self.no_op, priority)
        self.AddObserver("RightButtonPressEvent", self.no_op, priority)
        self.AddObserver("RightButtonReleaseEvent", self.no_op, priority)
        self.AddObserver("LeftButtonPressEvent", self.no_op, priority)
        self.AddObserver("LeftButtonPressEvent", self.no_op, priority)

        self.AddObserver("MouseWheelForwardEvent", self.no_op, priority)
        self.AddObserver("MouseWheelBackwardEvent", self.no_op, priority)

    def no_op(self, obj, event):
        """A no-op callback to intercept and 'do nothing' for an event."""
        pass


class PyVistaWidget(QtInteractor):
    """
    Widget for rendering the 3D cuboid using PyVista.
    Inherits from pyvistaqt.QtInteractor, which is a QFrame.
    """

    def __init__(self, parent=None):
        # We must initialize the QtInteractor with a QFrame as its parent
        # This is a quirk of how pyvistaqt is designed
        super_parent = QFrame(parent)
        super(PyVistaWidget, self).__init__(parent=super_parent)

        # The 'plotter' is self
        self.plotter = self

        # --- 1. Create Cuboid with Face Colors ---

        # Create cuboid geometry matching old dimensions
        # Old: w, d, h = 1.0, 0.6, 0.2
        # X-axis (width) = 2.0 (2*w)
        # Y-axis (height) = 0.4 (2*h)
        # Z-axis (depth) = 1.2 (2*d)
        self.cuboid_mesh = pv.Cube(
            center=(0, 0, 0), x_length=2.0, y_length=0.4, z_length=1.2
        )

        # Define the original face colors from gl_widget.py
        original_colors = [
            (0.8, 0.2, 0.8),  # 0: Magenta (Old Left, -X)
            (0.2, 0.8, 0.2),  # 1: Green (Old Front, +Z)
            (0.8, 0.8, 0.2),  # 2: Yellow (Old Top, +Y)
            (0.2, 0.2, 0.8),  # 3: Blue (Old Bottom, -Y)
            (0.2, 0.8, 0.8),  # 4: Cyan (Old Right, +X)
            (0.8, 0.2, 0.2),  # 5: Red (Old Back, -Z)
        ]

        # pv.Cube() cell order is: [0: -X, 1: +X, 2: -Y, 3: +Y, 4: -Z, 5: +Z]
        # We map the original colors to this new order
        pv_face_colors = np.array(
            [
                original_colors[4],  # -X face (Magenta)
                original_colors[5],  # +X face (Cyan)
                original_colors[2],  # -Y face (Blue)
                original_colors[3],  # +Y face (Yellow)
                original_colors[0],  # -Z face (Red)
                original_colors[1],  # +Z face (Green)
            ]
        )

        # Add the colors as cell data
        self.cuboid_mesh.cell_data["face_colors"] = pv_face_colors

        # Add actor for the cuboid, telling it to use the cell data for color
        self.cuboid_actor = self.plotter.add_mesh(
            self.cuboid_mesh,
            scalars="face_colors",
            rgb=True,  # Interpret scalars as RGB
            show_edges=True,
            edge_color="#FFFFFF",  # White edges for dark theme
            line_width=2,
        )

        # Make the cuboid 'unlit' (shadeless) by adjusting its material
        # This uses the full face color without directional shadows
        prop = self.cuboid_actor.GetProperty()
        prop.SetAmbient(0.9)  # Reflect 100% of ambient light (the face color)
        prop.SetDiffuse(0.0)  # Reflect 0% of directional light
        prop.SetSpecular(0.0)  # Reflect 0% of highlights

        # --- 2. Create and Add Rotating Axes (and 3D Labels) ---

        # Define axis lengths
        # Note the coordinate swap: IMU (Y=Up, Z=Fwd) -> VTK (Z=Up, Y=Fwd)
        x_axis_len = 1.25
        y_axis_len_imu = 0.75
        z_axis_len_imu = 0.5

        # Create lines in VTK coordinates
        x_axis = pv.Line((0, 0, 0), (x_axis_len, 0, 0))
        y_axis_vtk = pv.Line(
            (0, 0, 0), (0, z_axis_len_imu, 0)
        )  # VTK Y-axis uses IMU Z-length
        z_axis_vtk = pv.Line(
            (0, 0, 0), (0, 0, y_axis_len_imu)
        )  # VTK Z-axis uses IMU Y-length

        # Add axis actors with original colors
        # Red (X), Green (Y), Blue (Z)
        self.x_axis_actor = self.plotter.add_mesh(
            x_axis, color=(1.0, 0.4, 0.4), line_width=3
        )
        self.y_axis_actor = self.plotter.add_mesh(
            y_axis_vtk, color=(0.6, 0.6, 1.0), line_width=3
        )  # Blue for IMU Z
        self.z_axis_actor = self.plotter.add_mesh(
            z_axis_vtk, color=(0.6, 1.0, 0.6), line_width=3
        )  # Green for IMU Y

        # === NEW 3D LABELS ===
        # Create 3D Text geometry
        text_scale = 0.2
        text_x = (
            pv.Text3D("X", depth=0.1)
            .scale(text_scale, inplace=True)
            .translate((x_axis_len + 0.1, 0, 0), inplace=True)
        )
        text_y = (
            pv.Text3D("Y", depth=0.1)
            .scale(text_scale, inplace=True)
            .translate((0, 0, y_axis_len_imu + 0.1), inplace=True)
        )
        text_z = (
            pv.Text3D("Z", depth=0.1)
            .scale(text_scale, inplace=True)
            .translate((0, z_axis_len_imu + 0.1, 0), inplace=True)
        )

        # Add 3D text actors to the plotter
        self.x_label_actor = self.plotter.add_mesh(text_x, color=(1.0, 0.4, 0.4))  # Red
        self.y_label_actor = self.plotter.add_mesh(
            text_y, color=(0.6, 1.0, 0.6)
        )  # Green (IMU Y)
        self.z_label_actor = self.plotter.add_mesh(
            text_z, color=(0.6, 0.6, 1.0)
        )  # Blue (IMU Z)
        # === END NEW 3D LABELS ===

        # --- 3. Link Actors to Transform ---

        # Set up a *single* vtkTransform object for all rotating actors
        self.transform = vtk.vtkTransform()
        self.cuboid_actor.SetUserTransform(self.transform)
        self.x_axis_actor.SetUserTransform(self.transform)
        self.y_axis_actor.SetUserTransform(self.transform)
        self.z_axis_actor.SetUserTransform(self.transform)

        # Add the new 3D label actors to the transform
        self.x_label_actor.SetUserTransform(self.transform)
        self.y_label_actor.SetUserTransform(self.transform)
        self.z_label_actor.SetUserTransform(self.transform)

        # --- 4. Set Camera and Disable Zoom/Pan ---

        self.plotter.camera_position = "iso"
        self.plotter.set_focus((0, 0, 0))  # Focus on the origin
        self.plotter.reset_camera()  # Frame all actors

        # Set a custom interactor style that only allows rotation
        style = RotateOnlyInteractorStyle()
        self.plotter.interactor.SetInteractorStyle(style)

        self.is_dark_theme = True  # Default
        self.set_theme(self.is_dark_theme)

    def set_theme(self, is_dark):
        """Updates the background color and model edge color for the theme."""
        self.is_dark_theme = is_dark

        if is_dark:
            top = (0.27, 0.278, 0.353)
            bottom = (0.117, 0.117, 0.180)
            edge_color = (1.0, 1.0, 1.0)  # White
        else:
            top = (0.937, 0.945, 0.960)
            bottom = (0.85, 0.87, 0.9)
            edge_color = (0.1, 0.1, 0.1)  # Black

        self.plotter.set_background(color=bottom, top=top)

        # Update edge color on the actor's property
        self.cuboid_actor.GetProperty().SetEdgeColor(edge_color)

        # Re-render to show theme change
        self.plotter.render()

    def set_rotation_from_quat(self, quat: QQuaternion):
        """
        Sets the rotation of the cuboid and axes by updating the shared vtkTransform.
        """
        axis, angle = quat.getAxisAndAngle()

        # Apply the same coordinate swap as the old OpenGL code
        # Old: glRotatef(angle, axis.x(), axis.z(), axis.y())
        # vtk transform: RotateWXYZ(angle, vtk_x, vtk_y, vtk_z)
        # We map the IMU's (x, y, z) axis to VTK's (x, z, y)
        imu_x = axis.x()
        imu_y = axis.y()
        imu_z = axis.z()

        vtk_x = imu_x
        vtk_y = imu_z
        vtk_z = imu_y

        # Update the single transform object
        self.transform.Identity()
        self.transform.RotateWXYZ(angle, vtk_x, vtk_y, vtk_z)

        # All actors sharing this transform will be updated on the next .render()
        # call from the main application.
