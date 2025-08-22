# GUI-App-Ocean-Optics-QePro-Spectrometer
**📌 Overview**

The XEOL GUI is a PyQt5-based application developed for real-time acquisition, visualization, and mapping of optical luminescence spectra at the BM08-XAFS/XRF Beamline, SESAME Synchrotron Light Source.

This GUI integrates with Ocean Optics spectrometers (via seabreeze) and enables emission, absorption, and luminescence 2D mapping with live plotting, background subtraction, and flexible data saving.

---
**✨ Features**

**- 🎛️ Spectrometer Control**

- Adjustable integration time, acquisition interval, and averaging.

- Background subtraction for both emission and absorption spectra.

**- 📊 Real-time Visualization**

- Live spectral plotting with crosshair cursor support.

- Dynamic updates during acquisition.

**- 🧪 Measurement Modes**

- Emission Spectrum: Acquire dark background or emission spectra.

- Absorption Spectrum: Acquire reference, background, and absorption spectra.

- Luminescence 2D Map: Perform XEOL/fluorescence mapping with spatial resolution.

**- 💾 Data Handling**

- Save acquired data in .txt format.

- Organized export of emission, absorption, and mapping data.

**-⚡ Hardware Control**

- Toggle LASER/UV lamp for excitation.

---

**📂 Repository Structure**

SpectrometerApp/
│── main.py                # your main script (the code you pasted)
│── interface12.py          # your Qt Designer .ui converted to .py
│── requirements.txt        # dependencies
│── README.md               # project description
│── LICENSE                 # (optional) open-source license
│── data/                   # (optional) store saved spectra
│── docs/                   # (optional) documentation/screenshots

---
**⚙️ Installation**

**- Clone the repository**

git clone https://github.com/username/GUI-App-Ocean-Optics-QePro-Spectrometer.git

cd GUI-App-Ocean-Optics-QePro-Spectrometer

pip install -r requirements.txt

---
**▶️ Usage**

**Run the GUI with:**

python main.py


- Select acquisition type (Emission, Absorption, or 2D Map)

- Adjust acquisition parameters (integration time, scans, ranges, etc.)

- Save spectral data using the built-in save button

---

**🖼 Example Output**

- Live Spectrum Plot (emission spectrum)

- Absorption Spectra with reference and background correction

---

**👤 Author**

Latif Ullah Khan

BM08-XAFS/XRF Beamline, SESAME Synchrotron Light Source

📅 Date: 21 August 2025

**📜 License**

This project is licensed under the MIT License – see the LICENSE
 file for details.

 ---
**Citing this work**

If you use this GUI in your research, please cite it as:

Latif Ullah Khan, XEOL Spectral Map GUI – A PyQt5-based spectroscopic acquisition and mapping tool for Ocean Optics spectrometers, BM08-XAFS/XRF Beamline, SESAME Synchrotron Light Source, 2025.

BibTeX:

@software{Khan2025_XEOL_GUI,
  author       = {Latif Ullah Khan},
  
  title        = {XEOL/Fluorescence Map GUI: A PyQt5-based spectroscopic acquisition and mapping tool for Ocean Optics spectrometers},
  
  institution  = {BM08-XAFS/XRF Beamline, SESAME Synchrotron Light Source},
  
  year         = {2025},
  
  url          = {https://github.com/khanlatif001/GUI-App-Ocean-Optics-QePro-Spectrometer}
}

---


