# GUI-App-Ocean-Optics-QePro-Spectrometer
📌 Overview

The XEOL/Fluorescence Map GUI is a PyQt5-based application developed for real-time acquisition, visualization, and mapping of optical luminescence spectra at the BM08-XAFS/XRF Beamline, SESAME Synchrotron Light Source.

This GUI integrates with Ocean Optics spectrometers (via seabreeze) and enables emission, absorption, and luminescence 2D mapping with live plotting, background subtraction, and flexible data saving.

---
✨ *Features*

- Emission Spectrum Acquisition

- Adjustable integration time, interval, and scan averaging

- Dark background subtraction

- Live spectrum plotting with crosshair cursor

- Absorption Spectrum Acquisition

- Dark background and reference capture

- Absorption spectra measurement with reset/clear option

- Luminescence 2D Mapping

- User-defined X, Y, and Z scan ranges (in µm)

- Automated XEOL/Fluorescence 2D map acquisition

- Save spectral data in .txt format (emission, background, absorption)

- Laser/UV lamp control toggle

- Real-time progress bar indicator

---

📂 *Repository Structure*

SpectrometerApp/
│── main.py                # your main script (the code you pasted)
│── interface12.py          # your Qt Designer .ui converted to .py
│── requirements.txt        # dependencies
│── README.md               # project description
│── LICENSE                 # (optional) open-source license
│── data/                   # (optional) store saved spectra
│── docs/                   # (optional) documentation/screenshots

---
⚙️ Installation

- Clone the repository

git clone https://github.com/username/GUI-App-Ocean-Optics-QePro-Spectrometer.git

cd GUI-App-Ocean-Optics-QePro-Spectrometer

---
▶️ Usage

Run the GUI with:

python main.py


- Select acquisition type (Emission, Absorption, or 2D Map)

- Adjust acquisition parameters (integration time, scans, ranges, etc.)

- Save spectral data using the built-in save button

---

🖼 Example Output

- Live Spectrum Plot (emission spectrum)

- Absorption Spectra with reference and background correction

---

👤 Author

Latif Ullah Khan

BM08-XAFS/XRF Beamline, SESAME Synchrotron Light Source

📅 Date: 21 August 2025

📜 License

This project is licensed under the MIT License – see the LICENSE
 file for details.


