import sys
import matplotlib
matplotlib.use('Qt5Agg')
from matplotlib.backends.backend_qt5agg import FigureCanvasQTAgg as FigureCanvas
from matplotlib.figure import Figure
import matplotlib.ticker as ticker
from matplotlib.widgets import Cursor
import queue
import numpy as np
from PyQt5 import QtCore, QtWidgets, QtGui
from PyQt5.QtWidgets import QFileDialog
from PyQt5 import uic
from PyQt5.QtWidgets import QLabel
from PyQt5.QtCore import pyqtSlot
import time
from itertools import count, islice
from seabreeze.spectrometers import Spectrometer, list_devices

########################################################################
# IMPORT GUI FILE
from interface12 import *
########################################################################

class MplCanvas(FigureCanvas):
    def __init__(self, parent=None, width=5.0, height=4.95, dpi=100):
        # Create the figure with a dark background
        fig = Figure(figsize=(width, height), dpi=dpi, facecolor='black')  # Dark figure background
        self.axes = fig.add_subplot(111)
        super(MplCanvas, self).__init__(fig)
        
        # Custom layout adjustments (e.g., set padding, margins, etc.)
        self.adjust_layout()

    def adjust_layout(self):
        """Manually adjust layout to remove axes and ticks."""
        # Adjusting the subplot parameters for better spacing
        self.figure.subplots_adjust(left=0.1, right=0.9, top=0.95, bottom=0.125)        
        self.axes.set_axis_off()  # Remove axes, ticks, and labels        
        # Adjust the plot background color if needed (optional)
        self.axes.set_facecolor('black')  # Dark background for consistency

class QePro_LIVE_PLOT_APP(QtWidgets.QMainWindow):
    def __init__(self):
        super().__init__()        
        self.ui = Ui_MainWindow()
        self.ui.setupUi(self)
        global widgets
        widgets = self.ui

        # Create canvas for spectrum page
        self.canvas = MplCanvas(self, width=5, height=4, dpi=100)
        # Add canvas to the spectrum page layout
        spectrum_layout = widgets.spectrum_page.layout()
        spectrum_layout.addWidget(self.canvas)  
        
        # Create a separate canvas for the background spectrum page
        self.bkg_canvas = MplCanvas(self, width=5, height=4, dpi=100)
        # Add canvas to the background spectrum page layout
        bkg_spectrum_layout = widgets.bkg_spectrum_page.layout()
        bkg_spectrum_layout.addWidget(self.bkg_canvas)

        # Create a separate canvas for the absorption spectrum page
        self.abs_canvas = MplCanvas(self, width=5, height=4, dpi=100)
        # Add canvas to the background spectrum page layout
        abs_spectrum_layout = widgets.abs_spectrum_page.layout()
        abs_spectrum_layout.addWidget(self.abs_canvas)
                  
        self.background_spectrum = None
        self.reference_spectrum = None
        self.q = queue.Queue(maxsize=20)

        ########################################################################
        # PUSHBUTTONS CLICK
        ########################################################################

        # ACQUIRE EMISSION SPECTRUM 
        widgets.pushButton_EmSpectrum.clicked.connect(self.on_acqSpectrum_pushButton_clicked)
        # ACQUIRE BACKGROUND
        widgets.pushButton_emBKG.clicked.connect(self.on_acqSpectrum_pushButton_clicked)
        widgets.pushButton_absBKG.clicked.connect(self.on_acqSpectrum_pushButton_clicked)
        # ACQUIRE REFERENCE SPECTRUM 
        widgets.pushButton_Reference.clicked.connect(self.on_acqSpectrum_pushButton_clicked)
        # ACQUIRE ABSORPTION SPECTRUM 
        widgets.pushButton_AbsSpectrum.clicked.connect(self.on_acqSpectrum_pushButton_clicked)
        # SAVE DATA
        widgets.pushButton_saveData.clicked.connect(self.on_saveSpectrum_pushButton_clicked)
        # RESET PLOTS
        widgets.pushButton_reset.clicked.connect(self.on_acqSpectrum_pushButton_clicked)

        # ADD ITEMS TO COMBOBOX
        widgets.comboBox.addItems(["Emission-bkg", "Emission", "Absorption"])


        ########################################################################
        # INITIALIZE SPECTROMETER
        ########################################################################

        self.spectrometer = self.initialize_spectrometer()

    def initialize_spectrometer(self):
        """Initialize the spectrometer or enter demo mode if none is found."""
        devices = list_devices()
        if devices:
            try:
                spec = Spectrometer.from_first_available()
                return spec
            except Exception as e:
                QtWidgets.QMessageBox.critical(self, "Error", f"Failed to open spectrometer: {e}")
                return None
        else:
            QtWidgets.QMessageBox.information(self, "Demo Mode", "No spectrometer found: Entering demo mode.")
            return None  # No spectrometer available, demo mode will be used

    ########################################################################
    # CAPTURE SPECTRA
    ########################################################################

    def capture_averaged_spectrum(self, integration_time_us, interval_s, max_samples=None):
        integration_time_us = int(widgets.integrationTime_doubleSpinBox.value() * 1e3)
        interval_s = float(widgets.interval__doubleSpinBox.value())
        max_samples = int(widgets.averageScans_doubleSpinBox.value())        
        if self.spectrometer:
            self.spectrometer.integration_time_micros(integration_time_us)
            if max_samples >= 2:
                if interval_s <= integration_time_us / 1_000_000:
                    QtWidgets.QMessageBox.critical(self, "Error", "Interval should be higher than Integration Time.")
                    return None
          
                intensities_list = []
                t0 = time.monotonic()
                for _ in islice(count(), max_samples):
                    intensities_list.append(self.spectrometer.intensities())
                    #dt = interval_s - ((time.monotonic() - t0) % interval_s)
                    dt = max(0, interval_s - ((time.monotonic() - t0) % interval_s))
                    time.sleep(dt)
                avg_intensities = np.mean(intensities_list, axis=0)
            else:
                avg_intensities = self.spectrometer.intensities()
        else:
            # Demo mode: Generate a synthetic spectrum
            wavelengths = np.linspace(400, 800, 3648)  # Simulate a typical spectrometer wavelength range
            avg_intensities = np.sin(0.01 * wavelengths) + np.random.normal(0, 0.1, wavelengths.shape)      
        return avg_intensities  

    def on_acqSpectrum_pushButton_clicked(self):
        # Disable the push button focus after clicking to avoid moving focus to the next widget
        widgets.pushButton_EmSpectrum.setFocusPolicy(QtCore.Qt.NoFocus)

        # Reset progress bar to 0% at the beginning
        widgets.progressBar.setValue(0)

        ascii_prefix = "spectra"
        integration_time_us = int(widgets.integrationTime_doubleSpinBox.value() * 1e3)
        interval_s = float(widgets.interval__doubleSpinBox.value())
        max_samples = int(widgets.averageScans_doubleSpinBox.value())
        btn = self.sender()
        btnName = btn.objectName()

        #if btnName in ("pushButton_emBKG", "pushButton_absBKG"):
        if btnName == "pushButton_emBKG" or btnName == "pushButton_absBKG":
            self.update_progress(25)  # Update progress to 25%
            # Capture and store the background spectrum
            self.background_spectrum = self.capture_averaged_spectrum(integration_time_us, interval_s, max_samples)
            self.update_progress(100)  # Set to 100% when done
            
            # Plot the background spectrum
            if self.background_spectrum is not None:
                if self.spectrometer:
                    wavelengths = self.spectrometer.wavelengths()
                else:
                    wavelengths = np.linspace(400, 800, len(self.background_spectrum))                    
                self.update_bkg_plot(wavelengths, self.background_spectrum)            
            # Set the current widget to show the background spectrum page
            widgets.stackedWidget.setCurrentWidget(widgets.bkg_spectrum_page)
            QtWidgets.QMessageBox.information(self, "Dark Background Captured", "Dark background spectrum has been captured successfully.")
        
        if btnName == "pushButton_EmSpectrum":
            self.update_progress(25)  # Update progress to 25%
            # Set the current widget to show the spectrum page            
            self.store_averaged_spectra(ascii_prefix, integration_time_us, interval_s, max_samples)
            self.update_progress(100)  # Set to 100% when done
            widgets.stackedWidget.setCurrentWidget(widgets.spectrum_page)

        if btnName == "pushButton_Reference":
            self.update_progress(25)  # Update progress to 25%
            # Capture and store the reference spectrum
            self.reference_spectrum = self.capture_averaged_spectrum(integration_time_us, interval_s, max_samples)
            self.update_progress(100)  # Set to 100% when done

            # Plot the reference spectrum
            if self.reference_spectrum is not None:
                if self.spectrometer:
                    wavelengths = self.spectrometer.wavelengths()
                else:
                    wavelengths = np.linspace(400, 800, len(self.reference_spectrum))  # Simulated wavelengths

                self.update_reference_plot(wavelengths, self.reference_spectrum)
            widgets.stackedWidget.setCurrentWidget(widgets.abs_spectrum_page)
            # Notify the user that the reference spectrum is captured
            QtWidgets.QMessageBox.information(self, "Reference Captured", "Reference spectrum has been captured successfully.")

        if btnName == "pushButton_AbsSpectrum":
                self.update_progress(25)  # Update progress to 25%
                if self.background_spectrum is None or self.reference_spectrum is None:
                    QtWidgets.QMessageBox.warning(self, "Warning", "No dark background or Reference spectrum captured.")
                    return

                # Disable the pushbutton while capturing
                widgets.pushButton_AbsSpectrum.setEnabled(False)
                # Capture the sample spectrum
                sample_spectrum = self.capture_averaged_spectrum(integration_time_us, interval_s, max_samples)
                self.update_progress(100)  # Set to 100% when done

                # Ensure the wavelengths are available (either from the spectrometer or simulated)
                if self.spectrometer:
                    wavelengths = self.spectrometer.wavelengths()
                else:
                    wavelengths = np.linspace(400, 800, len(sample_spectrum))  # Simulated wavelengths for demo

                # Prevent log issues by replacing zeros or negatives in the sample spectrum
                epsilon = 1e-12  # Small constant to avoid division by zero and log(0)
                sample_spectrum = np.clip(sample_spectrum, epsilon, None)
                background_spectrum = np.clip(self.background_spectrum, epsilon, None)
                reference_spectrum = np.clip(self.reference_spectrum, epsilon, None)
                # Calculate the absorption spectrum
                absorption_spectrum = -np.log10(sample_spectrum / background_spectrum)
                #absorption_spectrum = -np.log10((np.array(sample_spectrum) - np.array(background_spectrum)) /
                #       (np.array(reference_spectrum) - np.array(background_spectrum)))
                # 
                #absorption_spectrum = -np.log10((sample_spectrum - background_spectrum) /
                #                                (reference_spectrum - background_spectrum))                              
               

                # Plot the absorption spectrum
                self.update_absorption_plot(wavelengths, absorption_spectrum)
                widgets.stackedWidget.setCurrentWidget(widgets.abs_spectrum_page)

                # Enable the pushbutton after capturing
                widgets.pushButton_AbsSpectrum.setEnabled(True)
        
        if btnName == "pushButton_reset":
            """Resets and clears all plots and spectra, removes ticks and labels, and refreshes the entire GUI."""
            self.update_progress(25)  # Update progress to 25%

            # Clear the plots
            self.canvas.axes.clear()
            self.bkg_canvas.axes.clear()
            self.abs_canvas.axes.clear()             
            # Reset variables
            self.background_spectrum = None
            self.reference_spectrum = None
            self.emission_spectrum = None
            self.absorption_spectrum = None
            # Remove tick marks and axis labels from all canvases
            for ax in [self.canvas.axes, self.bkg_canvas.axes, self.abs_canvas.axes]:
                ax.set_xticks([])  # Remove x-axis ticks
                ax.set_yticks([])  # Remove y-axis ticks
                ax.set_xlabel('')  # Remove x-axis label
                ax.set_ylabel('')  # Remove y-axis label
            # Redraw the canvases to reflect the cleared plots and removed ticks/labels
            self.canvas.draw()
            self.bkg_canvas.draw()
            self.abs_canvas.draw()

            # Refresh the entire GUI
            self.update_gui()
            self.update_progress(100)  # Set to 100% when done

         # Reset progress bar after a short delay to show completion
        QtCore.QTimer.singleShot(500, lambda: widgets.progressBar.setValue(0))
        # Set focus back to the window or to a specific widget
        self.setFocus()

    def update_progress(self, value):
        """Updates the progress bar with the given value."""
        widgets.progressBar.setValue(value)
        QtWidgets.QApplication.processEvents()  # Ensure UI updates immediately

    def on_saveSpectrum_pushButton_clicked(self):
        options = QFileDialog.Options()
        options |= QFileDialog.DontUseNativeDialog
        save_file, _ = QFileDialog.getSaveFileName(self, "Save Spectra", "", "Text Files (*.txt);;All Files (*)", options=options)
        
        if save_file:
            self.save_spectrum_to_file(save_file)

    def store_averaged_spectra(self, ascii_prefix, integration_time_us, interval_s, max_samples=None):
        widgets.pushButton_EmSpectrum.setEnabled(False)

        self.avg_intensities = self.capture_averaged_spectrum(integration_time_us, interval_s, max_samples)

        if self.background_spectrum is not None:
            self.avg_intensities = self.avg_intensities - self.background_spectrum

        if self.spectrometer:
            self.wavelengths = self.spectrometer.wavelengths()
        else:
            self.wavelengths = np.linspace(400, 800, len(self.avg_intensities))  # Use simulated wavelengths in demo mode

        self.update_plot(self.wavelengths, self.avg_intensities)
        widgets.pushButton_EmSpectrum.setEnabled(True)

    ########################################################################
    # SAVE DATA
    ########################################################################

    def save_spectrum_to_file(self, save_file):
        if not hasattr(self, 'avg_intensities'):
            QtWidgets.QMessageBox.warning(self, "Warning", "No spectrum data to save.")
            return

        currentData = widgets.comboBox.currentText()    
        try:
            with open(save_file, mode='w') as f:
                # Capture the raw spectrum regardless of whether background subtraction is needed
                raw_intensities = self.capture_averaged_spectrum(
                    int(widgets.integrationTime_doubleSpinBox.value() * 1e3),  # Integration time in µs
                    float(widgets.interval__doubleSpinBox.value()),  # Interval in seconds
                    int(widgets.averageScans_doubleSpinBox.value())  # Number of scans
                )

                if self.spectrometer:
                    wavelengths = self.spectrometer.wavelengths()
                else:
                    wavelengths = np.linspace(400, 800, len(raw_intensities))  # Use simulated wavelengths

                # Save raw spectrum (no background subtraction)
                if currentData == "Emission":
                    f.write("# Raw Spectrum (without dark background subtraction)\n")
                    f.write("# Wavelength\tIntensity\n")
                    for wavelength, intensity in zip(wavelengths, raw_intensities):
                        f.write(f"{wavelength:0.2f}\t{intensity}\n")
                    QtWidgets.QMessageBox.information(self, "Saved Spectral Data", f"Raw spectrum saved to {save_file}")

                # Save background-subtracted spectrum if background exists
                elif currentData == "Emission-bkg":
                    if self.background_spectrum is None:
                        QtWidgets.QMessageBox.warning(self, "Warning", "No dark background spectrum to subtract.")
                        return

                    # Subtract the background
                    subtracted_intensities = raw_intensities - self.background_spectrum

                    f.write("# Spectrum with background subtraction\n")
                    f.write("# Wavelength\tIntensity\n")
                    for wavelength, intensity in zip(wavelengths, subtracted_intensities):
                        f.write(f"{wavelength:0.2f}\t{intensity}\n")
                    QtWidgets.QMessageBox.information(self, "Saved Spectral Data", f"Spectrum with background subtraction saved to {save_file}")

                elif currentData == "Absorption":
                    if self.background_spectrum is None or self.reference_spectrum is None:
                        QtWidgets.QMessageBox.warning(self, "Warning", "No dark background or Reference spectrum captured.")
                        return

                    sample_spectrum = raw_intensities
                    #Replace xero or negative value with small 1e-12 positive value to avoid the logarithm error
                    absorption_spectrum = -np.log10(np.maximum(sample_spectrum / self.background_spectrum, 1e-12))

                    #absorption_spectrum = -np.log10((sample_spectrum - self.background_spectrum) /
                    #                                (self.reference_spectrum - self.background_spectrum))
                    #
                    f.write("# Absorption Spectrum\n")
                    f.write("# Wavelength\tAbsorbance\n")
                    for wavelength, absorbance in zip(wavelengths, absorption_spectrum):
                        f.write(f"{wavelength:0.2f}\t{absorbance}\n")
                    QtWidgets.QMessageBox.information(self, "Saved Spectral Data", f"Absorption spectrum saved to {save_file}")

        except Exception as e:
            QtWidgets.QMessageBox.critical(self, "Error", f"Failed to save spectrum: {e}")

    def update_gui(self):
        """Refreshes the entire GUI to default state."""
        # Reset all SpinBoxes (integration time, interval, and average scans) to default values
        widgets.integrationTime_doubleSpinBox.setValue(10)  # Reset to default integration time (example)
        widgets.interval__doubleSpinBox.setValue(1)          # Reset to default interval (example)
        widgets.averageScans_doubleSpinBox.setValue(1)       # Reset to default number of scans (example)
        # Reset the ComboBox selection
        widgets.comboBox.setCurrentIndex(0)  # Reset to the first item in the ComboBox
        # widgets.someCheckBox.setChecked(False)  # Uncheck a checkbox
        
        # Force the GUI to repaint to reflect all the changes made to the widgets
        self.repaint()  # This will trigger the whole window to redraw

    ########################################################################
    # PLOT CAPTURED SPECTRA
    ########################################################################

    def update_plot(self, wavelengths, avg_intensities):
        """Update the plot for the emission spectrum and add crosshair cursor with annotations.
        """
        # Clear the canvas and set background color
        self.canvas.axes.clear()
        self.canvas.axes.set_facecolor('black')
        # Plot the emission spectrum
        self.canvas.axes.plot(wavelengths, avg_intensities, label='Emission Spectrum', color='cyan')
        # Enable gridlines
        self.canvas.axes.yaxis.grid(True, linestyle='--', color='gray')
        self.canvas.axes.xaxis.grid(True, linestyle='--', color='gray')
        # Define label and tick font sizes
        label_fontsize = 14
        tick_fontsize = 14
        # Set y-limits with a buffer or default limits for single-point data
        if len(avg_intensities) > 1:
            intensity_range = max(avg_intensities) - min(avg_intensities)
            buffer = intensity_range * 0.05  # 5% buffer
            self.canvas.axes.set_ylim(ymin=min(avg_intensities) - buffer, ymax=max(avg_intensities) + buffer)
        else:
            self.canvas.axes.set_ylim(ymin=0, ymax=1)  # Adjusted to handle single point data better
        # Set axis labels and customize appearance
        self.canvas.axes.set_xlabel('Wavelength (nm)', fontsize=label_fontsize, color="white", labelpad=5.0)
        self.canvas.axes.set_ylabel('Intensity (count)', fontsize=label_fontsize, color="white", labelpad=1.5)
        self.canvas.axes.tick_params(axis='both', labelsize=tick_fontsize, colors='white')
        # Add a legend
        self.canvas.axes.legend(fontsize=label_fontsize, loc='upper right', framealpha=0.5)

        # Clear existing cursor and annotations if they exist
        if hasattr(self, 'crosshair'):
            self.crosshair.remove()
        if hasattr(self, 'coord_text'):
            self.coord_text.remove()
        # Define a new cursor for crosshair functionality
        self.crosshair = self.canvas.axes.annotate("+", xy=(0, 0), xytext=(0, 0),
                                                   textcoords="offset points", color='yellow', fontsize=20,
                                                   ha='center', va='center', visible=False)
        self.coord_text = self.canvas.axes.annotate("", xy=(0, 0), xytext=(0, 15), textcoords="offset points",
                                                    color='yellow', fontsize=14, ha='left', va='bottom',
                                                    bbox=dict(boxstyle="round,pad=0.3", edgecolor='yellow', 
                                                              facecolor='black', alpha=0.6), visible=False)
        # Create a QLabel to display mouse coordinates
        self.coord_label = QLabel(self)
        self.coord_label.setStyleSheet("color: white; background-color: black; padding: 2px;")
        self.coord_label.move(10, 10)  # Position the label in the top-left corner of the window
        self.coord_label.resize(150, 20)
        # Define an event handler to update the crosshair and coordinate display on mouse hover
        def on_hover(event):
            if event.inaxes == self.canvas.axes:  # Ensure hover is within plot bounds
                x, y = event.xdata, event.ydata  # Using directly from event
                # Update crosshair position and make it visible
                self.crosshair.xy = (x, y)
                self.crosshair.set_visible(True)
                # Update coordinate text with x and y values and make it visible
                self.coord_text.xy = (x, y)
                self.coord_text.set_text(f"{x:.2f}, {y:.2f}")
                self.coord_text.set_visible(True)
                # Update QLabel with x and y coordinates
                self.coord_label.setText(f"Wavelength: {x:.2f} nm, Intensity: {y:.2f}")
                # Redraw the canvas with updated crosshair and coordinates only once
                self.canvas.draw_idle()  # Use draw_idle for better performance
            else:
                # Hide the crosshair and coordinate text if the cursor is outside the plot area
                self.crosshair.set_visible(False)
                self.coord_text.set_visible(False)
                self.coord_label.setText("Hover over the plot")  # Default message
        # Disconnect the previous hover event handler if it exists
        if hasattr(self, 'hover_connection'):
            self.canvas.mpl_disconnect(self.hover_connection)    
        # Connect the hover event to the handler and store the connection id
        self.hover_connection = self.canvas.mpl_connect('motion_notify_event', on_hover)

        # Draw the updated plot
        self.canvas.draw()


    def update_bkg_plot(self, wavelengths, bkg_intensities):
        """Update the plot for the dark background spectrum."""
        self.bkg_canvas.axes.clear()
        self.bkg_canvas.axes.set_facecolor('black')       
        self.bkg_canvas.axes.plot(wavelengths, bkg_intensities, label='Background Spectrum', color='yellow')
        self.bkg_canvas.axes.yaxis.grid(True, linestyle='--', color='gray')
        self.bkg_canvas.axes.xaxis.grid(True, linestyle='--', color='gray')    
        label_fontsize = 14
        tick_fontsize = 14
        # Check for empty or single-point data
        if len(bkg_intensities) > 1:
            intensity_range = max(bkg_intensities) - min(bkg_intensities)
            buffer = intensity_range * 0.05  # Add 5% buffer
            self.bkg_canvas.axes.set_ylim(ymin=min(bkg_intensities) - buffer, ymax=max(bkg_intensities) + buffer)
        else:
            self.bkg_canvas.axes.set_ylim(ymin=0, ymax=1)  # Default limits for single-point data
        # Set axis labels and tick parameters
        self.bkg_canvas.axes.set_xlabel('Wavelength (nm)', fontsize=label_fontsize, color="white", labelpad=5.0)
        self.bkg_canvas.axes.set_ylabel('Intensity (count)', fontsize=label_fontsize, color="white", labelpad=1.5)
        self.bkg_canvas.axes.tick_params(axis='both', labelsize=tick_fontsize, colors='white')
        # Add a legend
        self.bkg_canvas.axes.legend(fontsize=label_fontsize, loc='upper right', framealpha=0.5)
        # Draw the updated plot
        self.bkg_canvas.draw()

    def update_reference_plot(self, wavelengths, reference_spectrum):
        """Update the plot for the reference spectrum."""
        self.abs_canvas.axes.clear()
        self.abs_canvas.axes.set_facecolor('black')    
        # Plot the reference spectrum
        self.abs_canvas.axes.plot(wavelengths, reference_spectrum, label='Reference Spectrum', color='blue')
        self.abs_canvas.axes.yaxis.grid(True, linestyle='--', color='gray')
        self.abs_canvas.axes.xaxis.grid(True, linestyle='--', color='gray')
        label_fontsize = 14
        tick_fontsize = 14
        # Check for empty or single-point data
        if len(reference_spectrum) > 1:
            intensity_range = max(reference_spectrum) - min(reference_spectrum)
            buffer = intensity_range * 0.05  # Add 5% buffer
            self.abs_canvas.axes.set_ylim(ymin=min(reference_spectrum) - buffer, ymax=max(reference_spectrum) + buffer)
        else:
            self.abs_canvas.axes.set_ylim(ymin=0, ymax=1)  # Default limits for single-point data
        # Set axis labels and tick parameters
        self.abs_canvas.axes.set_xlabel('Wavelength (nm)', fontsize=label_fontsize, color='white', labelpad=5.0)
        self.abs_canvas.axes.set_ylabel('Intensity (count)', fontsize=label_fontsize, color='white', labelpad=1.5)
        self.abs_canvas.axes.tick_params(axis='both', labelsize=tick_fontsize, colors='white')
        # Add a legend
        self.abs_canvas.axes.legend(fontsize=label_fontsize, loc='upper right', framealpha=0.5)
        # Draw the updated plot
        self.abs_canvas.draw()
 
    def update_absorption_plot(self, wavelengths, absorption_spectrum):
        """Update the plot for the absorption spectrum and add crosshair cursor with annotations.    
        """
        # Clear the absorption canvas axes
        self.abs_canvas.axes.clear()
        self.abs_canvas.axes.set_facecolor('black')
        # Plot the absorption spectrum
        self.abs_canvas.axes.plot(wavelengths, absorption_spectrum, label='Absorption Spectrum', color='green')
        self.abs_canvas.axes.yaxis.grid(True, linestyle='--', color='gray')
        self.abs_canvas.axes.xaxis.grid(True, linestyle='--', color='gray')
        # Set font sizes for labels and ticks
        label_fontsize = 14
        tick_fontsize = 14
        # Check for empty or single-point data and set y-limits
        if len(absorption_spectrum) > 1:
            intensity_range = max(absorption_spectrum) - min(absorption_spectrum)
            buffer = intensity_range * 0.05  # Add 5% buffer
            self.abs_canvas.axes.set_ylim(ymin=min(absorption_spectrum) - buffer, ymax=max(absorption_spectrum) + buffer)
        else:
            self.abs_canvas.axes.set_ylim(ymin=0, ymax=1)  # Default limits for single-point data
        # Set axis labels and tick parameters
        self.abs_canvas.axes.set_xlabel('Wavelength (nm)', fontsize=label_fontsize, color='white', labelpad=5.0)
        self.abs_canvas.axes.set_ylabel('Absorbance', fontsize=label_fontsize, color='white', labelpad=1.5)
        self.abs_canvas.axes.tick_params(axis='both', labelsize=tick_fontsize, colors='white')
        # Add a legend
        self.abs_canvas.axes.legend(fontsize=label_fontsize, loc='upper right', framealpha=0.5)

        # Clear existing cursor and annotations if they exist
        if hasattr(self, 'abs_crosshair'):
            self.abs_crosshair.remove()
        if hasattr(self, 'abs_coord_text'):
            self.abs_coord_text.remove()
        # Define a new crosshair for absorption plot functionality
        self.abs_crosshair = self.abs_canvas.axes.annotate("+", xy=(0, 0), xytext=(0, 0),
                                                           textcoords="offset points", color='yellow', fontsize=20,
                                                           ha='center', va='center', visible=False)

        self.abs_coord_text = self.abs_canvas.axes.annotate("", xy=(0, 0), xytext=(0, 15), textcoords="offset points",
                                                            color='yellow', fontsize=14, ha='left', va='bottom',
                                                            bbox=dict(boxstyle="round,pad=0.3", edgecolor='yellow',
                                                                      facecolor='black', alpha=0.6), visible=False)
        # Create a QLabel to display mouse coordinates
        self.coord_label = QLabel(self)
        self.coord_label.setStyleSheet("color: white; background-color: black; padding: 2px;")
        self.coord_label.move(10, 10)  # Position the label in the top-left corner of the window
        self.coord_label.resize(150, 20)
        # Define an event handler to update the crosshair and coordinate display on mouse hover
        def on_hover(event):
            if event.inaxes == self.abs_canvas.axes:  # Ensure hover is within plot bounds
                x, y = event.xdata, event.ydata  # Using directly from event
                # Update crosshair position and make it visible
                self.abs_crosshair.xy = (x, y)
                self.abs_crosshair.set_visible(True)
                # Update coordinate text with x and y values and make it visible
                self.abs_coord_text.xy = (x, y)
                self.abs_coord_text.set_text(f"{x:.2f}, {y:.2f}")
                self.abs_coord_text.set_visible(True)
                # Update QLabel with x and y coordinates
                self.coord_label.setText(f"Wavelength: {x:.2f} nm, Absorption: {y:.2f}")
                # Redraw the canvas with updated crosshair and coordinates only once
                self.abs_canvas.draw_idle()  # Use draw_idle for better performance
            else:
                # Hide the crosshair and coordinate text if the cursor is outside the plot area
                self.abs_crosshair.set_visible(False)
                self.abs_coord_text.set_visible(False)
                self.coord_label.setText("Hover over the plot")  # Default message
        # Disconnect the previous hover event handler if it exists
        if hasattr(self, 'abs_hover_connection'):
            self.abs_canvas.mpl_disconnect(self.abs_hover_connection)
        # Connect the hover event to the handler and store the connection id
        self.abs_hover_connection = self.abs_canvas.mpl_connect('motion_notify_event', on_hover)
        # Draw the updated plot
        self.abs_canvas.draw()
    
class Worker(QtCore.QRunnable):
    def __init__(self, function, *args, **kwargs):
        super(Worker, self).__init__()
        self.function = function
        self.args = args
        self.kwargs = kwargs

    @pyqtSlot()
    def run(self):
        self.function(*self.args, **self.kwargs)


#if __name__ == "__main__":
#    app = QtWidgets.QApplication(sys.argv)
#    mainWindow = QePro_LIVE_PLOT_APP()
#    mainWindow.show()
#    sys.exit(app.exec_())

def run_app():
    app = QtWidgets.QApplication(sys.argv)
    mainWindow = QePro_LIVE_PLOT_APP()
    mainWindow.show()
    sys.exit(app.exec_())
