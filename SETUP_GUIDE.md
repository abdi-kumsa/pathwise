# PathWise — Exhaustive Windows Setup & Deployment Guide
**Prepared for Dr. Endriss**

This document is a **100% foolproof, step-by-step guide** designed for a **brand-new Windows laptop** that has no developer tools, compilers, or databases pre-installed.

---

## 📑 Table of Contents
1. [Pre-Flight Checklist (Brand-New Laptop Setup)](#1-pre-flight-checklist-brand-new-laptop-setup)
2. [Step 1: Install Docker Desktop & Enable WSL 2](#step-1-install-docker-desktop--enable-wsl-2)
3. [Step 2: Extract Zip & Prepare Environment Configuration](#step-2-extract-zip--prepare-environment-configuration)
4. [Step 3: Opening PowerShell in the Folder (Easiest Method)](#step-3-opening-powershell-in-the-folder-easiest-method)
5. [Step 4: Launching PathWise & Watching the Startup Logs](#step-4-launching-pathwise--watching-the-startup-logs)
6. [Step 5: Accessing the Live Dashboards](#step-5-accessing-the-live-dashboards)
7. [Step 6: Stopping, Restarting & Diagnostics](#step-6-stopping-restarting--diagnostics)
8. [Comprehensive Windows Troubleshooting](#8-comprehensive-windows-troubleshooting)

---

## 1. Pre-Flight Checklist (Brand-New Laptop Setup)

Before downloading anything, ensure your Windows laptop meets these requirements:

### A. Windows Version
* **Supported**: Windows 10 (64-bit: Home, Pro, Enterprise) or Windows 11.
* **To check your OS**: Press `Windows Key + R`, type `winver`, and press `Enter`.

### B. Hardware Virtualization (Must be Enabled)
On brand-new laptops, hardware virtualization is almost always enabled by default in the factory BIOS.
* **How to verify**:
  1. Open Task Manager (`Ctrl + Shift + Esc`).
  2. Click the **Performance** tab and select **CPU**.
  3. Look at the bottom-right corner for **Virtualization: Enabled**.
  *(If it says "Disabled", you must turn on Intel VT-x / AMD-V in your laptop's BIOS/UEFI settings).*

---

## Step 1: Install Docker Desktop & Enable WSL 2

PathWise uses Docker containers. **You do NOT need to install Python, Node.js, PostgreSQL, or machine learning libraries.** Docker packages all dependencies isolated inside containers.

### 1.1 Download Docker Desktop
1. Open Microsoft Edge or Google Chrome and go to:  
   👉 **[https://www.docker.com/products/docker-desktop/](https://www.docker.com/products/docker-desktop/)**
2. Click **Download for Windows** to download `Docker Desktop Installer.exe`.

### 1.2 Run Installer & Enable WSL 2
1. Double-click `Docker Desktop Installer.exe`.
2. On the configuration screen, make sure **"Use WSL 2 instead of Hyper-V"** is **CHECKED**.
3. Click **OK** to install.
4. When installation finishes, click **Close and restart** to reboot Windows.

### 1.3 First Launch of Docker Desktop
1. After Windows restarts, open **Docker Desktop** from your Windows Start Menu.
2. Accept the Terms & Service agreement.
3. On the welcome screen, click **"Continue without signing in"** (or skip questionnaire).
4. Look at the bottom-left corner of Docker Desktop. Wait 1–2 minutes until the status turns **green ("Engine running")**.

> 💡 **What to do if Docker prompts "WSL 2 installation incomplete":**
> 1. Right-click your Windows Start Menu button and select **Terminal (Admin)** or **PowerShell (Admin)**.
> 2. Type: `wsl --install` or `wsl --update` and press `Enter`.
> 3. Restart Docker Desktop.

---

## Step 2: Extract Zip & Prepare Environment Configuration

### 2.1 Unzip the Folder
1. Locate your downloaded `PathWise.zip` file (usually in your `Downloads` folder).
2. Right-click `PathWise.zip` and click **Extract All...**.
3. Set destination to `C:\Users\YourUsername\Desktop\PathWise` and click **Extract**.

### 2.2 Verify `.env` File Exists
PathWise reads environment variables (database credentials, backend ports) from a file named `.env`.
1. Open the unzipped `PathWise` folder in Windows File Explorer.
2. Check if a file named `.env` is visible.
3. **If `.env` is missing** (because Windows hides dotfiles or zip stripped it):
   * Look for `.env.example` in the folder.
   * Right-click `.env.example`, click **Copy**, then **Paste** in the same folder.
   * Rename the copied file to **`.env`**.
   *(The default values inside `.env.example` work out-of-the-box with zero changes needed!)*

---

## Step 3: Opening PowerShell in the Folder (Easiest Method)

You do **not** need to manually type long file paths. Use this quick Windows Explorer shortcut:

1. Open the unzipped `PathWise` folder in **Windows File Explorer**.
2. Click directly on the **Address Bar** at the top (where it says `This PC > Desktop > PathWise`).
3. Type **`powershell`** or **`cmd`** and press **`Enter`**.
4. A black or blue terminal window will open immediately, positioned directly inside the `PathWise` folder!

---

## Step 4: Launching PathWise & Watching the Startup Logs

### 4.1 Test Docker Connection
In the terminal window, type:
```powershell
docker --version
```
Expected output: `Docker version 27.x.x` (or similar).

### 4.2 Run the Platform
Type the following command and press `Enter`:
```powershell
docker compose up
```

### 📋 What exact log messages should you expect?

1. **Step 1 — Downloading Base Images** (First run only):
   ```text
   [+] Pulling 3/3
   ✔ db Pulled
   ✔ backend Pulled
   ✔ frontend Pulled
   ```
2. **Step 2 — Database Ready**:
   ```text
   pathwise_db | PostgreSQL database system is ready to accept connections on port 5432
   ```
3. **Step 3 — Backend ML Pre-Warming**:
   ```text
   pathwise_backend | [ok] XGBoost placement classifier loaded.
   pathwise_backend | [ok] Prophet demand forecaster loaded.
   pathwise_backend | [ok] LSTM enrollment model loaded.
   pathwise_backend | PathWise API ready.
   ```
4. **Step 4 — Frontend Online**:
   ```text
   pathwise_frontend |  VITE v5.x.x  ready in 450 ms
   pathwise_frontend |  ➜  Local:   http://localhost:3000/
   ```
   > **Note:** Vite prints the port from *inside* the container (`3000`). The address
   > you actually open in your browser is **http://localhost:3001** — see Step 5.

Once you see `PathWise API ready`, **all services are active!**

---

## Step 5: Accessing the Live Dashboards

Open Google Chrome or Microsoft Edge and open these links:

* 📊 **Main Interactive Dashboard (Primary View):**  
  👉 [http://localhost:3001](http://localhost:3001)

* ⚙️ **Interactive API Documentation (Swagger UI):**  
  👉 [http://localhost:8000/docs](http://localhost:8000/docs)

* 🩺 **Backend Health & Model Status:**  
  👉 [http://localhost:8000/health](http://localhost:8000/health)

---

## Step 6: Stopping, Restarting & Diagnostics

### To Stop the Application:
In the PowerShell window running Docker, press **`Ctrl + C`**.  
Alternatively, open another PowerShell window in `PathWise` and run:
```powershell
docker compose down
```

### To Restart Later:
Ensure Docker Desktop is running in your system tray, open PowerShell in `PathWise`, and run:
```powershell
docker compose up
```
*(Subsequent startups complete in under 15 seconds because builds are cached!)*

### Diagnostic Commands (If something behaves strangely):
* **Check container status**:
  ```powershell
  docker compose ps
  ```
* **View backend logs**:
  ```powershell
  docker compose logs backend
  ```

---

## 8. Comprehensive Windows Troubleshooting

#### Q1: Terminal says `docker: The term 'docker' is not recognized`
* **Cause**: Docker Desktop is not running or installation was not completed.
* **Solution**: Search for **Docker Desktop** in Start Menu, open it, and wait for the bottom-left icon to turn green ("Engine running").

#### Q2: Error `port is already in use` / `bind: address already in use`
* **Cause**: Another local application (e.g., IIS, Skype, or another node/python app) already owns that port.
* **Solution**: You do **not** need to close the other program. Open `.env` and raise
  the matching **host** port, then run `docker compose down` followed by `docker compose up`:
  * frontend port taken → change `FRONTEND_HOST_PORT` (and set `FRONTEND_URL` to the same port)
  * API port taken → change `API_HOST_PORT` (and set `VITE_API_URL` to the same port)
  * database port taken → change `DB_HOST_PORT`
* **Do not change** `DB_PORT` or `API_PORT` — those are the ports *inside* the
  containers and changing them breaks communication between services.

#### Q3: Backend shows `connection refused to db:5432`
* **Cause**: Backend started before Postgres finished initializing on slow hard drives.
* **Solution**: Press `Ctrl + C`, then run `docker compose restart backend`.

#### Q4: How to reset database to pristine initial state on Windows?
Run:
```powershell
docker compose down -v
docker compose up
```
The `-v` flag removes volumes and forces PostgreSQL to re-seed all tables from scratch.
