"""
This folder contains any possible code used to develop specific functionalities
any module developed her shall not be used inside the main program

    Luca Lombardi
    Rev 0: First Draft

    next steps:
        - rebuild the background from the database
        - add text entities
    Help/About
"""
from tkinter import Tk
import ezdxf
import math

from TNSolver_GUI.Thermal_Network_TAB.graphic_frame import GraphicWindow
from TNSolver_GUI.Thermal_Network_TAB.gUtility import font, font_size, dxf_color


class DXFViewer:
    def __init__(self, canvas, dxf_filepath):
        self.dxf_filepath = dxf_filepath
        self.canvas = canvas
        self.canvas_width = float(self.canvas.cget("width"))
        self.canvas_height = float(self.canvas.cget("height"))/2.0

        self.scale_factor = 1.0
        self._draw_dxf()
        self._autoscale()

    def _draw_entity(self, entity):
        if entity.dxftype() == 'LINE':
            x1 = entity.dxf.start.x
            y1 = self.canvas_height - entity.dxf.start.y
            x2 = entity.dxf.end.x
            y2 = self.canvas_height - entity.dxf.end.y
            self.canvas.create_line(x1, y1, x2, y2, fill=dxf_color, tags="dxf_entity")
        elif entity.dxftype() == 'CIRCLE':
            r = entity.dxf.radius * self.scale_factor
            cx, cy = entity.dxf.center.x, self.canvas_height - entity.dxf.center.y
            self.canvas.create_oval(cx - r, cy - r, cx + r, cy + r, outline=dxf_color, tags="dxf_entity")
        elif entity.dxftype() == 'ARC':
            center_x, center_y = entity.dxf.center.x, self.canvas_height - entity.dxf.center.y
            radius = entity.dxf.radius * self.scale_factor
            start_angle_deg = entity.dxf.start_angle
            if entity.dxf.end_angle == 0:
                extend_angle = 360.0 - start_angle_deg
            else:
                extend_angle = entity.dxf.end_angle - start_angle_deg

            self.canvas.create_arc(center_x - radius, center_y - radius, center_x + radius, center_y + radius,
                                   start=start_angle_deg, extent=extend_angle, style='arc', outline=dxf_color,
                                   tags="dxf_entity")
        elif entity.dxftype() == 'ELLIPSE':
            center_x, center_y = entity.dxf.center.x, entity.dxf.center.y
            major_axis_length = 2 * entity.dxf.major_axis.magnitude * self.scale_factor
            minor_axis_length = major_axis_length * entity.dxf.ratio
            angle_deg = entity.dxf.major_axis.angle_deg
            start_param = entity.dxf.start_param
            end_param = entity.dxf.end_param

            x1 = center_x - major_axis_length / 2
            y1 = center_y - minor_axis_length / 2
            x2 = center_x + major_axis_length / 2
            y2 = center_y + minor_axis_length / 2

            tolerance = 1e-9  # Small tolerance for floating-point comparisons
            if abs(start_param - 0.0) < tolerance and abs(end_param - 2 * math.pi) < tolerance:
                self.canvas.create_polygon(tuple(self._poly_oval(x1, y1, x2, y2, start_angle=start_param,
                                                 end_angle=end_param, rotation=angle_deg, steps=20)),
                                           fill='', outline=dxf_color, tags="dxf_entity")
            else:
                points = self._poly_oval(x1, y1, x2, y2, start_angle=start_param, end_angle=end_param,
                                         rotation=angle_deg, steps=30)
                # Connect the rotated points with lines
                for i in range(0, len(points)-2, 2):
                    self.canvas.create_line(points[i], points[i+1], points[i+2], points[i+3], fill=dxf_color,
                                            tags="dxf_entity")
        elif entity.dxftype() == 'POINT':
            x, y = entity.dxf.location.x, self.canvas_height - entity.dxf.location.y
            point_size = 2 * self.scale_factor
            self.canvas.create_oval(x - point_size / 2, y - point_size / 2,
                                    x + point_size / 2, y + point_size / 2, fill=dxf_color, tags="dxf_entity")
        elif entity.dxftype() == 'LWPOLYLINE':
            points = [(p[0], self.canvas_height - p[1]) for p in entity.get_points()]
            self.canvas.create_polygon(points, fill='', outline=dxf_color, tags="dxf_entity")
        elif entity.dxftype() == 'SPLINE':
            points = [(p[0], self.canvas_height - p[1]) for p in entity.control_points]
            for i in range(len(points) - 1):
                self.canvas.create_line(points[i], points[i+1], outline=dxf_color, tags="dxf_entity")
        elif entity.dxftype() == 'POLYLINE':
            points = []
            for vertex in entity.vertices:
                if vertex.dxf.flags & 1 == 0:  # Non-curve vertex
                    x = vertex.dxf.location[0]
                    y = self.canvas_height - vertex.dxf.location[1]
                    points.append((x, y))
                # Handle curved segments based on bulge factor if needed
            for i in range(len(points) - 1):
                x1, y1 = points[i]
                x2, y2 = points[i + 1]
                self.canvas.create_line(x1, y1, x2, y2, fill=dxf_color, tags="dxf_entity")
        else:
            print(f'the entity {entity.dxftype()} is not present in the tkinter converter.')
        # Add handling for other entity types as needed

    def _draw_dxf(self):
        try:
            doc = ezdxf.readfile(self.dxf_filepath)
            msp = doc.modelspace()
            for entity in msp.entity_space:
                self._draw_entity(entity)
        except Exception as e:
            print(f"Error reading DXF file: {e}")

    def _poly_oval(self, x0, y0, x1, y1, start_angle=0, end_angle=2 * math.pi, steps=20, rotation=0.0):
        """return an oval as coordinates suitable for create_polygon"""
        rotation_rad = -math.radians(rotation)
        a = (x1 - x0) / 2.0 * self.scale_factor
        b = (y1 - y0) / 2.0 * self.scale_factor
        xc = x0 + (x1 - x0) / 2.0 * self.scale_factor
        yc = y0 + (y1 - y0) / 2.0 * self.scale_factor
        point_list = []
        d_theta = (end_angle - start_angle) / steps
        for i in range(steps):
            theta = d_theta * float(i) + start_angle
            x = a * math.cos(theta)
            y = b * math.sin(theta)
            x_rotated = (x * math.cos(rotation_rad)) + (y * math.sin(rotation_rad)) + xc
            y_rotated = (y * math.cos(rotation_rad)) - (x * math.sin(rotation_rad)) + yc
            point_list.append(x_rotated)
            point_list.append(self.canvas_height - y_rotated)
        return point_list

    def _autoscale(self):
        boundaries = self.canvas.bbox('dxf_entity')
        center = [(boundaries[0]+boundaries[2])/2.0, (boundaries[1]+boundaries[3])/2.0]

        canvas_center = [self.canvas_width/2, self.canvas_height/2]

        dx = canvas_center[0] - center[0]
        dy = canvas_center[1] - center[1]
        zoom_factor = min(self.canvas_height / (boundaries[3]-boundaries[1]),
                          self.canvas_width / (boundaries[2]-boundaries[0]))

        self.canvas.move('dxf_entity', dx, dy)
        self.canvas.scale('dxf_entity', canvas_center[0], canvas_center[1], zoom_factor, zoom_factor)
        self.scale_factor = zoom_factor

    def get_dimension(self):
        boundaries = self.canvas.bbox('dxf_entity')
        dx, dy = boundaries[2]-boundaries[0], boundaries[3]-boundaries[1]
        ref_dimension = max(dx, dy)
        real_dimension = ref_dimension/self.scale_factor
        return ref_dimension, real_dimension

    def draw_meter_scale(self, x, y, segment_, tot_dimension, unit):
        # draw the scale
        x0 = x
        y0 = y
        step = segment_/5.0
        dim = tot_dimension / 5.0
        thick = 10
        color_fill = 'white'
        text_step = 2
        for i in range(0, 5):
            # create the rectangle
            self.canvas.create_rectangle(x0+i*step, y0, x0+(i+1)*step, y0+thick, outline='white', fill=color_fill,
                                         tags='metric_scale')
            color_fill = 'black' if color_fill == 'white' else 'white'  # alternate the colors
            # add the text
            self.canvas.create_text(x0 + i * step, y0 + (text_step*thick), text=str(round(dim * i, 1)), anchor='center',
                                    fill='white', font=[font, font_size], tags='metric_scale_text')
            text_step = -1.0 if text_step == 2 else 2  # alternate the text side
        self.canvas.create_text(x0 + (i+1) * step, y0 + (text_step * thick), text=str(round(dim * (i + 1), 1)) + unit,
                                anchor='center', fill='white', font=[font, font_size], tags='metric_scale_text')


if __name__ == "__main__":
    win = Tk()
    win.title('Test of DXF import')
    dxf_file = 'C:/Users/Luca_Lombardi/Documents/My CAD Projects/TestUG/2D_step_test.dxf'

    test_board = GraphicWindow(win)
    test_board.naming("DXF viewer in Tkinter")
    test_board.pack(padx=10)

    # let's place a small item on the SE corner to prevent the automatic resizing of the canvas
    test_board.th_canvas.create_rectangle(9999, 9999, 10000, 10000, outline="black", fill="black",
                                          activefill="black",
                                          tags=str('SE - angle'))
    # import the dxf file
    viewer = DXFViewer(test_board.th_canvas, dxf_file)
    segment, dimension = viewer.get_dimension()
    viewer.draw_meter_scale(300, 500, segment, dimension, 'mm')

    # let's place a rectangle with the size of the canvas.
    test_board.th_canvas.create_rectangle(0, 0, 10000, 10000, outline="white", tags=str('canvas frame'))

    test_board.th_canvas.create_text(50, 10, anchor="nw", fill="white", font=test_board.font,
                                     text="Click and drag to move the viewer frame\nScroll to zoom.")

    test_board.th_canvas.bind("<ButtonPress-2>", test_board.move_start)
    test_board.th_canvas.bind("<B2-Motion>", test_board.move_move)
    test_board.th_canvas.bind("<ButtonRelease-2>", test_board.offset_calc)
    test_board.th_canvas.bind("<ButtonRelease-1>", test_board.print_coord)
    test_board.th_canvas.bind("<MouseWheel>", test_board.zoom)

    win.mainloop()

