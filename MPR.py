import sys
import os
import vtk
from PyQt5.QtWidgets import QApplication, QMainWindow, QGridLayout, QWidget, QFileDialog, QAction, QToolBar, QSlider, QVBoxLayout, QLabel, QPushButton, QHBoxLayout  # Add QHBoxLayout here
from vtkmodules.qt.QVTKRenderWindowInteractor import QVTKRenderWindowInteractor
from PyQt5.QtCore import Qt
from PyQt5.QtGui import QIcon, QFont

dark_stylesheet = """
QMainWindow {
    background-color: #2E2E2E;
}

QWidget {
    background-color: #3E3E3E;
    color: #FFFFFF;
}

QPushButton {
    background-color: #5A5A5A;
    color: #FFFFFF;
    border: 1px solid #6A6A6A;
    border-radius: 5px;
    padding: 5px;
}

QPushButton:hover {
    background-color: #7A7A7A;
}

QSlider::groove:vertical {
    border: none;
    background: #333333;  /* Dark background */
    width: 6px;
    border-radius: 3px;
    margin: 0px;
}

QSlider::handle:vertical {
    background: #666666;  /* Handle color (darker gray) */
    border: 1px solid #999999;  /* Optional handle border */
    height: 20px;
    width: 20px;
    border-radius: 10px;
    margin: -10px -7px; /* Centers the handle */
}

QSlider::sub-page:vertical {
    background: #4d4d4d;  /* The color below the handle */
}

QSlider::add-page:vertical {
    background: #1a1a1a;  /* The color above the handle */
}

QLabel {
    color: #FFFFFF;
}
"""
class MPRWindow(QMainWindow):
    def __init__(self):
        super().__init__()

        # Set up the main widget and layout
        self.main_widget = QWidget(self)
        self.setCentralWidget(self.main_widget)
        self.layout = QGridLayout(self.main_widget)
        self.setWindowIcon(QIcon(r"C:\Users\monae\Downloads\icon.png"))

        # Create VTK render windows and sliders for each panel except the 3D view
        self.axial_view, self.axial_slider, self.axial_reset = self.create_vtk_panel_with_slider(0, 0, "Axial View")
        self.coronal_view, self.coronal_slider, self.coronal_reset = self.create_vtk_panel_with_slider(0, 1, "Coronal View")
        self.sagittal_view, self.sagittal_slider, self.sagittal_reset = self.create_vtk_panel_with_slider(1, 1, "Sagittal View")
        self.three_d_view = self.create_vtk_panel(1, 0, "3D View")

        # Placeholder for reslice objects to update slices
        self.axial_reslice = None
        self.coronal_reslice = None
        self.sagittal_reslice = None

        # DICOM reader placeholder
        self.reader = None

        # Create a toolbar with an upload action
        self.create_toolbar()

        # Apply the dark mode stylesheet
        self.setStyleSheet(dark_stylesheet)

        # Variables to hold the number of slices for each view
        self.axial_slices = 0
        self.coronal_slices = 0
        self.sagittal_slices = 0

        # Set up the VTK interaction events
        self.setup_vtk_interaction()

    def create_toolbar(self):
        # Set up the toolbar
        toolbar = QToolBar("Main Toolbar")
        self.addToolBar(toolbar)

        # Create an upload action with an icon and tooltip
        upload_action = QAction(QIcon(r"C:\Users\monae\Downloads\download-removebg-preview.png"), "Upload DICOM", self)
        upload_action.setStatusTip("Upload DICOM files")
        upload_action.triggered.connect(self.upload_file)

        # Add the upload action to the toolbar
        toolbar.addAction(upload_action)

        # Create a mouse controls action with an icon and detailed tooltip
        mouse_controls_action = QAction(QIcon(r"C:\Users\monae\Downloads\1787045-removebg-preview.png"), "Pan: Shift+Hold and Drag\nZoom In/Out: Scroll through the image\nRotate: CTRL+Hold and Rotate\nBrightness and Contrast: Hold and Scroll", self)
        mouse_controls_action.setStatusTip(
            "Pan: Shift+Hold & Drag\nZoom In/Out: Scroll\nRotate: Alt+Hold & Rotate\nBrightness & Contrast: Hold & Scroll")

        # Add the mouse controls action to the toolbar
        toolbar.addAction(mouse_controls_action)

    def create_vtk_panel_with_slider(self, row, col, title):
        # Create a horizontal layout to combine the panel and the slider
        combined_layout = QHBoxLayout()

        # Create a layout for the VTK panel and title
        panel_layout = QVBoxLayout()

        # Create the title label
        title_label = QLabel(title)
        title_label.setFont(QFont("Stylus", 9, QFont.Bold))
        panel_layout.addWidget(title_label)

        # Create the VTK render window
        vtk_widget = QVTKRenderWindowInteractor(self.main_widget)
        panel_layout.addWidget(vtk_widget)

        # Add the VTK panel layout to the combined layout
        combined_layout.addLayout(panel_layout)

        # Create the vertical slider on the right
        slider = QSlider(Qt.Vertical)
        slider.setRange(0, 100)  # This range will be updated based on the data
        slider.valueChanged.connect(
            lambda value, col=col: self.update_slice(value, row, col))  # Connect slider to slice update

        # Add the slider to the combined layout
        combined_layout.addWidget(slider)

        # Create a reset button
        reset_button = QPushButton("Reset View")
        reset_button.setFixedSize(80, 30)  # Set a smaller size for the reset button
        reset_button.clicked.connect(lambda: self.reset_view(row, col))  # Connect reset button to reset view
        panel_layout.addWidget(reset_button)

        # Add the combined layout to the main grid layout
        self.layout.addLayout(combined_layout, row, col)

        return vtk_widget, slider, reset_button

    def create_vtk_panel(self, row, col, title):
        # Set up a layout for the panel, title, and reset button
        panel_layout = QVBoxLayout()

        # Create the title label
        title_label = QLabel(title)
        title_label.setFont(QFont("Stylus", 9, QFont.Bold))
        panel_layout.addWidget(title_label)

        # Create the VTK render window
        vtk_widget = QVTKRenderWindowInteractor(self.main_widget)
        panel_layout.addWidget(vtk_widget)

        # Create a reset button
        reset_button = QPushButton("Reset View")
        reset_button.setFixedSize(80, 30)  # Set a smaller size for the reset button
        reset_button.clicked.connect(lambda: self.reset_view(row, col))  # Connect reset button to reset view
        panel_layout.addWidget(reset_button)

        # Add the layout to the main grid layout
        self.layout.addLayout(panel_layout, row, col)

        return vtk_widget

    def reset_view(self, row, col):
        # Reset the view based on which panel's reset button is clicked
        if row == 0 and col == 0:  # Axial
            self.axial_slider.setValue(0)
            self.update_slice(0, 0, 0)
        elif row == 0 and col == 1:  # Coronal
            self.coronal_slider.setValue(0)
            self.update_slice(0, 0, 1)
        elif row == 1 and col == 1:  # Sagittal
            self.sagittal_slider.setValue(0)
            self.update_slice(0, 1, 1)  # Update slice correctly for sagittal view

    def upload_file(self):
        # Open a file dialog to select a DICOM or MHA file
        file_path, _ = QFileDialog.getOpenFileName(self, "Select File", "",
                                                   "DICOM Files (*.dcm);;MHA Files (*.mha);;All Files (*)")
        if file_path:
            # Check the file extension to determine the type
            if file_path.endswith('.dcm'):
                self.load_dicom_data(file_path)
            elif file_path.endswith('.mha'):
                self.load_mha_data(file_path)

    def load_dicom_data(self, dicom_file):
        try:
            # Load DICOM data using vtkDICOMImageReader
            reader = vtk.vtkDICOMImageReader()
            reader.SetDirectoryName(os.path.dirname(dicom_file))  # Set directory for DICOM files
            reader.Update()

            if reader.GetOutput() is None:
                print("Error: Failed to load DICOM data")
                return

            self.reader = reader

            # Get the number of slices for each orientation
            dimensions = reader.GetOutput().GetDimensions()  # Get dimensions of the volume
            self.axial_slices = dimensions[2]  # Depth
            self.coronal_slices = dimensions[1]  # Height
            self.sagittal_slices = dimensions[0]  # Width

            # Set slider ranges according to the number of slices
            self.axial_slider.setRange(0, self.axial_slices - 1)
            self.coronal_slider.setRange(0, self.coronal_slices - 1)
            self.sagittal_slider.setRange(0, self.sagittal_slices - 1)

            # Initialize sliders to the first slice
            self.axial_slider.setValue(0)
            self.coronal_slider.setValue(0)
            self.sagittal_slider.setValue(0)

            # Setup renderers for each view (axial, coronal, sagittal)
            self.axial_reslice = self.setup_slice_view(self.axial_view, reader, [1, 0, 0, 0, 1, 0, 0, 0, 1], 0)  # Axial
            self.coronal_reslice = self.setup_slice_view(self.coronal_view, reader, [1, 0, 0, 0, 0, 1, 0, -1, 0],
                                                         0)  # Coronal

            # Update sagittal orientation to switch axes
            self.sagittal_reslice = self.setup_slice_view(self.sagittal_view, reader, [0, 1, 0, 0, 0, 1, 1, 0, 0],
                                                          0)  # Sagittal

            # Create 3D volume rendering in the bottom-left panel
            self.setup_3d_view(self.three_d_view, reader)

        except Exception as e:
            print(f"Error loading DICOM file: {e}")

    def load_mha_data(self, mha_file):
        try:
            # Load MHA data using vtkMetaImageReader
            reader = vtk.vtkMetaImageReader()
            reader.SetFileName(mha_file)  # Set the MHA file
            reader.Update()

            if reader.GetOutput() is None:
                print("Error: Failed to load MHA data")
                return

            self.reader = reader

            # Get the number of slices for each orientation
            dimensions = reader.GetOutput().GetDimensions()  # Get dimensions of the volume
            self.axial_slices = dimensions[2]  # Depth
            self.coronal_slices = dimensions[1]  # Height
            self.sagittal_slices = dimensions[0]  # Width

            # Set slider ranges according to the number of slices
            self.axial_slider.setRange(0, self.axial_slices - 1)
            self.coronal_slider.setRange(0, self.coronal_slices - 1)
            self.sagittal_slider.setRange(0, self.sagittal_slices - 1)

            # Initialize sliders to the first slice
            self.axial_slider.setValue(0)
            self.coronal_slider.setValue(0)
            self.sagittal_slider.setValue(0)

            # Setup renderers for each view (axial, coronal, sagittal)
            self.axial_reslice = self.setup_slice_view(self.axial_view, reader, [1, 0, 0, 0, 1, 0, 0, 0, 1], 0)  # Axial
            self.coronal_reslice = self.setup_slice_view(self.coronal_view, reader, [1, 0, 0, 0, 0, 1, 0, -1, 0],
                                                         0)  # Coronal

            # Update sagittal orientation to switch axes
            self.sagittal_reslice = self.setup_slice_view(self.sagittal_view, reader, [0, 1, 0, 0, 0, 1, 1, 0, 0],
                                                          0)  # Sagittal

            # Create 3D volume rendering in the bottom-left panel
            self.setup_3d_view(self.three_d_view, reader)

        except Exception as e:
            print(f"Error loading MHA file: {e}")

    def calculate_window_level(self, image_data):
        scalar_range = image_data.GetScalarRange()
        min_val, max_val = scalar_range[0], scalar_range[1]

        # Compute window (contrast) and level (brightness)
        default_window = max_val - min_val  # Window is the range of intensity values
        default_level = (max_val + min_val) / 2  # Level is the midpoint

        return default_window, default_level

    def setup_slice_view(self, vtk_widget, reader, orientation, slice_index):
        # Set up a slice renderer
        reslice = vtk.vtkImageReslice()
        reslice.SetInputConnection(reader.GetOutputPort())
        reslice.SetOutputDimensionality(2)
        reslice.SetResliceAxesDirectionCosines(orientation)
        reslice.SetInterpolationModeToLinear()
        reslice.SetResliceAxesOrigin(0, 0, slice_index)

        # Get image data and calculate dynamic window/level
        image_data = reader.GetOutput()
        default_window, default_level = self.calculate_window_level(image_data)

        # Create a window/level filter to adjust brightness and contrast
        window_level = vtk.vtkImageMapToWindowLevelColors()
        window_level.SetInputConnection(reslice.GetOutputPort())

        # Set window (contrast) and level (brightness) dynamically
        window_level.SetWindow(default_window)  # Adjusted contrast
        window_level.SetLevel(default_level)  # Adjusted brightness
        # Mapper and actor for displaying the slice
        slice_mapper = vtk.vtkImageActor()
        slice_mapper.GetMapper().SetInputConnection(window_level.GetOutputPort())

        # Create a renderer for the specific view
        renderer = vtk.vtkRenderer()
        renderer.AddActor(slice_mapper)

        # Set up the VTK render window and interactor for the specific panel
        vtk_widget.GetRenderWindow().AddRenderer(renderer)

        # Set interactor style to lock view for 2D slices (Axial, Coronal, Sagittal)
        interactor = vtk_widget.GetRenderWindow().GetInteractor()
        interactor.SetInteractorStyle(vtk.vtkInteractorStyleImage())

        # Initialize and render the interactor
        vtk_widget.GetRenderWindow().Render()
        vtk_widget.GetRenderWindow().GetInteractor().Initialize()

        return reslice

    def setup_3d_view(self, vtk_widget, reader):
        # Create a 3D volume rendering of the data
        volume_mapper = vtk.vtkGPUVolumeRayCastMapper()
        volume_mapper.SetInputConnection(reader.GetOutputPort())

        # Get image data and calculate dynamic window/level
        image_data = reader.GetOutput()
        default_window, default_level = self.calculate_window_level(image_data)

        # Create a volume property
        volume_property = vtk.vtkVolumeProperty()
        volume_property.ShadeOn()
        volume_property.SetInterpolationTypeToLinear()

        # Set scalar opacity based on calculated window/level
        opacity = vtk.vtkPiecewiseFunction()
        opacity.AddPoint(default_level - default_window / 2, 0.0)
        opacity.AddPoint(default_level + default_window / 2, 1.0)
        volume_property.SetScalarOpacity(opacity)

        # Set color transfer function for brightness/contrast control
        color = vtk.vtkColorTransferFunction()
        color.AddRGBPoint(default_level - default_window / 2, 0.0, 0.0, 0.0)
        color.AddRGBPoint(default_level + default_window / 2, 1.0, 1.0, 1.0)
        volume_property.SetColor(color)

        # Create a volume actor
        volume = vtk.vtkVolume()
        volume.SetMapper(volume_mapper)
        volume.SetProperty(volume_property)

        # Create the renderer for the 3D view
        renderer = vtk.vtkRenderer()
        renderer.AddVolume(volume)
        vtk_widget.GetRenderWindow().AddRenderer(renderer)

        # Initialize the interactor for the 3D view
        interactor = vtk_widget.GetRenderWindow().GetInteractor()
        interactor.Initialize()
        vtk_widget.GetRenderWindow().Render()

    def update_slice(self, value, row, col):
        # Update the slice based on which panel's slider is moved
        if row == 0 and col == 0:  # Axial
            if self.axial_reslice:
                if value < self.axial_slices:  # Check within range
                    self.axial_reslice.SetResliceAxesOrigin(0, 0, value)  # Axial slices move along Z-axis
                    self.axial_view.GetRenderWindow().Render()
        elif row == 0 and col == 1:  # Coronal
            if self.coronal_reslice:
                if value < self.coronal_slices:  # Check within range
                    self.coronal_reslice.SetResliceAxesOrigin(0, value, 0)  # Coronal slices move along Y-axis
                    self.coronal_view.GetRenderWindow().Render()
        elif row == 1 and col == 1:  # Sagittal
            if self.sagittal_reslice:
                if value < self.sagittal_slices:  # Check within range
                    self.sagittal_reslice.SetResliceAxesOrigin(value, 0, 0)  # Sagittal slices move along X-axis
                    self.sagittal_view.GetRenderWindow().Render()

    def setup_vtk_interaction(self):
        # Set up interactor for axial, coronal, and sagittal views to capture mouse clicks
        self.setup_interactor(self.axial_view, self.on_click_axial)
        self.setup_interactor(self.coronal_view, self.on_click_coronal)
        self.setup_interactor(self.sagittal_view, self.on_click_sagittal)

    def setup_interactor(self, vtk_widget, click_callback):
        interactor = vtk_widget.GetRenderWindow().GetInteractor()
        style = vtk.vtkInteractorStyleImage()
        interactor.SetInteractorStyle(style)
        interactor.AddObserver("LeftButtonPressEvent", click_callback)

    def on_click_axial(self, obj, event):
        # Capture the point clicked in the axial view
        click_pos = obj.GetEventPosition()
        self.update_views_based_on_click(self.axial_view, click_pos, "axial")

    def on_click_coronal(self, obj, event):
        # Capture the point clicked in the coronal view
        click_pos = obj.GetEventPosition()
        self.update_views_based_on_click(self.coronal_view, click_pos, "coronal")

    def on_click_sagittal(self, obj, event):
        # Capture the point clicked in the sagittal view
        click_pos = obj.GetEventPosition()
        self.update_views_based_on_click(self.sagittal_view, click_pos, "sagittal")

    def update_views_based_on_click(self, vtk_widget, click_pos, view_type):
        # Create a picker
        picker = vtk.vtkCellPicker()  # Use vtkPointPicker if necessary
        picker.SetTolerance(0.005)

        # Pick based on the 2D click
        picker.Pick(click_pos[0], click_pos[1], 0, vtk_widget.GetRenderWindow().GetRenderers().GetFirstRenderer())
        picked_position = picker.GetPickPosition()  # Get 3D coordinates

        if picker.GetCellId() != -1:
            # Successfully picked a 3D point
            x, y, z = picked_position
            print(f"Clicked on {view_type} view at 3D position: ({x}, {y}, {z})")

            # Depending on which view was clicked, update the other views
            if view_type == "axial":
                self.update_coronal_view(x, y)  # Update coronal view
                self.update_sagittal_view(y, z)  # Update sagittal view
            elif view_type == "coronal":
                self.update_axial_view(x, y)  # Update axial view
                self.update_sagittal_view(y, z)

            elif view_type == "sagittal":
                self.update_axial_view(x, y)  # Update axial view
                self.update_coronal_view(x, y)  # Update coronal view
        else:
            print(f"No valid pick on {view_type} view")

    def update_axial_view(self, x, z):
        # Convert (x, z) to axial slice and update
        slice_index = int(z)
        if slice_index < self.axial_slices:
            self.axial_slider.setValue(slice_index)
            self.axial_reslice.SetResliceAxesOrigin(0, 0, slice_index)
            self.axial_view.GetRenderWindow().Render()

    def update_coronal_view(self, x, y):
        # Convert (x, y) to coronal slice and update
        slice_index = int(y)
        if slice_index < self.coronal_slices:
            self.coronal_slider.setValue(slice_index)
            self.coronal_reslice.SetResliceAxesOrigin(0, slice_index, 0)
            self.coronal_view.GetRenderWindow().Render()

    def update_sagittal_view(self, x, y):
        # Convert (x, y) to sagittal slice and update
        slice_index = int(x)
        if slice_index < self.sagittal_slices:
            self.sagittal_slider.setValue(slice_index)
            self.sagittal_reslice.SetResliceAxesOrigin(slice_index, 0, 0)
            self.sagittal_view.GetRenderWindow().Render()

if __name__ == "__main__":
    app = QApplication(sys.argv)
    window = MPRWindow()
    window.setWindowTitle("MultiPlanar Reconstruction (MPR) Viewer")
    window.resize(1200, 800)
    window.show()
    sys.exit(app.exec_())
