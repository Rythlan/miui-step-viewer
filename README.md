# MIUI Step Counter Viewer

A simple desktop application built with Python and PyQt6 to view and analyze step counter data from the built-in MIUI Health app. This tool directly pulls the database from a rooted Android device.

**Disclaimer:** This is a personal hobby project created for my own specific use case. It is not actively maintained, and updates should not be expected.

---

### Key Features

*   Connect to your device via USB or Wi-Fi (using ADB).
*   Pull the `Steps.db` database from your phone to your computer.
*   Visualize step data with daily, monthly, and yearly graphs.
*   See hourly breakdowns for any selected day.

### Requirements

*   **OS:** Tested primarily on **Linux**. It may work on Windows/macOS if ADB is correctly configured in the system's PATH.
*   **Phone:** Tested on **MIUI 14**. It might work on other versions but is not guaranteed.
*   **Python:** Python 3.11 or newer.
*   **Root Access:** Your device **must be rooted** (e.g., with Magisk). This is non-negotiable as the app needs to access the `/data` partition.

---

### 1. Device Preparation (Crucial First Step)

Before using the app, you must prepare your device:

1.  **Enable Developer Options:** Go to `Settings > About phone` and tap on the `MIUI version` repeatedly until you see the "You are now a developer!" message.
2.  **Enable Debugging:** Go to `Settings > Additional settings > Developer options` and enable:
    *   **USB debugging**
    *   **Wireless debugging** (for connecting over Wi-Fi)
3.  **Grant Root to ADB Shell:**
    *   The application uses ADB shell with root (`su`) to copy the database file.
    *   You must grant root privileges to the "Shell" (`com.android.shell`) process in your root management app (e.g., Magisk).
    *   The first time the app tries to sync, you will likely see a root request pop up on your phone. **You must grant it permanently.**

### 2. Installation and Setup

The project uses a virtual environment to manage dependencies.

1.  **Clone the repository:**
    ```bash
    git clone https://github.com/Rythlan/miui-steps-viewer.git
    cd miui-steps-viewer
    ```

2.  **Create and activate a virtual environment:**
    ```bash
    # Create the virtual environment
    python -m venv venv

    # Activate it (on Linux/macOS)
    source venv/bin/activate

    # Activate it (on Windows)
    .\venv\Scripts\activate
    ```

3.  **Install the required packages:**
    ```bash
    pip install -r requirements.txt
    ```

### 3. How to Use

1.  **Run the application:**
    ```bash
    python main.py
    ```
2.  **Connect to your Device:**
    *   **USB:** Connect your phone via USB. Click the "Refresh" button, and your device should appear in the dropdown list.
    *   **Wi-Fi:** Ensure your phone and computer are on the same network. Enter your phone's IP address and port (found in the *Wireless debugging* settings) into the IP field and click "Connect to IP".
3.  **Sync the Database:**
    *   Once your device is selected in the dropdown, click the **"Sync Steps from Device (Root)"** button.
    *   The app will copy the database, process it, and load the charts.

---
*This project is provided as-is, without warranty of any kind.*
