# gl_widget.py
# This module contains the OpenGL widget for rendering the 3D cuboid.

from PyQt5.QtOpenGL import QGLWidget
from PyQt5.QtGui import QQuaternion

try:
    from OpenGL.GL import *
    from OpenGL.GLU import *
except ImportError:
    print("PyOpenGL is not installed. Please install it using: pip install PyOpenGL")
    exit(1)


class OpenGLCubeWidget(QGLWidget):
    """
    Widget for rendering the 3D cuboid.
    """

    def __init__(self, parent=None):
        super(OpenGLCubeWidget, self).__init__(parent)
        self.setMinimumSize(400, 400)
        self.quaternion = QQuaternion(1, 0, 0, 0)

        self.dark_gradient_top = (0.27, 0.278, 0.353)
        self.dark_gradient_bottom = (0.117, 0.117, 0.180)
        self.light_gradient_top = (0.937, 0.945, 0.960)
        self.light_gradient_bottom = (0.85, 0.87, 0.9)
        self.is_dark_theme = True

    def initializeGL(self):
        glEnable(GL_DEPTH_TEST)
        glEnable(GL_LIGHTING)
        glEnable(GL_LIGHT0)
        # glLightfv(GL_LIGHT0, GL_POSITION, (0, 0, 1, 0))
        glLightModelfv(GL_LIGHT_MODEL_AMBIENT, [0.9, 0.9, 0.9, 1.0])
        glEnable(GL_COLOR_MATERIAL)
        glColorMaterial(GL_FRONT_AND_BACK, GL_AMBIENT_AND_DIFFUSE)
        glEnable(GL_LINE_SMOOTH)

    def resizeGL(self, w, h):
        glViewport(0, 0, w, h)
        glMatrixMode(GL_PROJECTION)
        glLoadIdentity()
        if h == 0:
            h = 1
        gluPerspective(45.0, w / h, 0.1, 100.0)
        glMatrixMode(GL_MODELVIEW)
        glLoadIdentity()

    def paintGL(self):
        glClear(GL_COLOR_BUFFER_BIT | GL_DEPTH_BUFFER_BIT)
        self._draw_gradient_background()

        glMatrixMode(GL_MODELVIEW)
        glLoadIdentity()
        glTranslatef(0.0, 0.0, -5.0)
        glLightfv(GL_LIGHT0, GL_POSITION, [0.0, 0.0, 1.0, 0.0])

        # paintGL will now just read the latest self.quaternion
        # which is being set rapidly by update_data
        axis, angle = self.quaternion.getAxisAndAngle()
        glRotatef(angle, axis.x(), axis.z(), axis.y())

        self.draw_cuboid()
        self.draw_axes()

    def _draw_gradient_background(self):
        glMatrixMode(GL_PROJECTION)
        glPushMatrix()
        glLoadIdentity()
        glOrtho(0.0, 1.0, 1.0, 0.0, -1.0, 1.0)
        glMatrixMode(GL_MODELVIEW)
        glPushMatrix()
        glLoadIdentity()

        glPushAttrib(GL_ENABLE_BIT)
        glDisable(GL_DEPTH_TEST)
        glDisable(GL_LIGHTING)

        glBegin(GL_QUADS)
        colors = (
            (self.dark_gradient_top, self.dark_gradient_bottom)
            if self.is_dark_theme
            else (self.light_gradient_top, self.light_gradient_bottom)
        )
        glColor3fv(colors[0])
        glVertex2f(0, 0)
        glVertex2f(1, 0)
        glColor3fv(colors[1])
        glVertex2f(1, 1)
        glVertex2f(0, 1)
        glEnd()

        glPopAttrib()
        glMatrixMode(GL_PROJECTION)
        glPopMatrix()
        glMatrixMode(GL_MODELVIEW)
        glPopMatrix()

    def set_rotation(self, q0, q1, q2, q3):
        """
        Sets the rotation quaternion. This function does NOT
        trigger a repaint (updateGL).
        """
        self.quaternion = QQuaternion(q0, q1, q2, q3)

    def set_theme(self, is_dark):
        self.is_dark_theme = is_dark
        self.updateGL()

    def draw_cuboid(self):
        w, d, h = 1.0, 0.6, 0.2
        vertices = [
            [w, -h, -d],
            [w, h, -d],
            [-w, h, -d],
            [-w, -h, -d],
            [w, -h, d],
            [w, h, d],
            [-w, -h, d],
            [-w, h, d],
        ]
        edges = [
            (0, 1),
            (1, 2),
            (2, 3),
            (3, 0),
            (4, 5),
            (5, 7),
            (7, 6),
            (6, 4),
            (0, 4),
            (1, 5),
            (2, 7),
            (3, 6),
        ]
        surfaces = [
            (0, 1, 2, 3),
            (4, 5, 7, 6),
            (0, 3, 6, 4),
            (1, 2, 7, 5),
            (3, 2, 7, 6),
            (0, 1, 5, 4),
        ]
        colors = [
            (0.8, 0.2, 0.2),
            (0.2, 0.8, 0.2),
            (0.2, 0.2, 0.8),
            (0.8, 0.8, 0.2),
            (0.8, 0.2, 0.8),
            (0.2, 0.8, 0.8),
        ]
        glBegin(GL_QUADS)
        for i, surface in enumerate(surfaces):
            glColor3fv(colors[i])
            for vertex_index in surface:
                glVertex3fv(vertices[vertex_index])
        glEnd()

        if self.is_dark_theme:
            glColor3f(0.9, 0.9, 0.9)
        else:
            glColor3f(0.1, 0.1, 0.1)

        glLineWidth(2.0)
        glBegin(GL_LINES)
        for edge in edges:
            for vertex_index in edge:
                glVertex3fv(vertices[vertex_index])
        glEnd()

    def draw_axes(self):
        glLineWidth(3.0)
        glBegin(GL_LINES)
        # Brighter colors for axes
        glColor3f(1.0, 0.3, 0.3)  # Red (X)
        glVertex3f(0, 0, 0)
        glVertex3f(1.5, 0, 0)
        glColor3f(0.3, 1.0, 0.3)  # Green (Y)
        glVertex3f(0, 0, 0)
        glVertex3f(0, 0.75, 0)
        glColor3f(0.3, 0.5, 1.0)  # Light Blue (Z)
        glVertex3f(0, 0, 0)
        glVertex3f(0, 0, 1.25)
        glEnd()
