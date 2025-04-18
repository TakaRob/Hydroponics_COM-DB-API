# Setup Instructions for Hydroponics COM-DB-API

This guide covers setup for both deployment on a Raspberry Pi and development (Windows/WSL2).

---

## Raspberry Pi Deployment (Recommended for Production)

1. **Install Docker:**
   ```bash
   sudo apt-get update
   sudo apt-get install -y docker.io
   sudo systemctl enable --now docker
   sudo usermod -aG docker $USER
   # Log out and back in, or run: newgrp docker
   ```
2. **Plug in Arduino and check device:**
   ```bash
   ls /dev/ttyACM* /dev/ttyUSB*
   sudo chmod 666 /dev/ttyACM0
   ```
3. **Pull your image from Docker Hub:**
   ```bash
   docker pull yourusername/hydroponics-db-api:latest
   ```
4. **Run the container:**
   ```bash
   docker run --rm -it --device=/dev/ttyACM0 --env SERIAL_PORT=/dev/ttyACM0 -p 5000:5000 yourusername/hydroponics-db-api:latest
   ```
5. **Test the API:**
   ```bash
   curl http://localhost:5000/readings
   ```

---

## Notes
- Replace `yourusername` with your Docker Hub username.
- Always check your Arduino's actual device name (`/dev/ttyACM0`, `/dev/ttyUSB0`, etc).
- For multi-architecture Docker images (for Raspberry Pi), consider using `docker buildx`.
- For troubleshooting, check permissions and Docker logs.

---

## Quick Reference: Pull API Data

```bash
curl http://localhost:5000/readings
```

or to save to a file:

```bash
curl http://localhost:5000/readings -o readings.json
```

---

## Windows + WSL2 (with Arduino)

### 1. Windows: USB Serial Device to WSL2

1. **Install [usbipd-win](https://github.com/dorssel/usbipd-win/releases)**
   - Download and install the latest `.msi` file.
2. **Open PowerShell as Administrator**
   - List USB devices:
     ```powershell
     usbipd list
     ```
   - Bind your Arduino (replace `2-2` with your busid):
     ```powershell
     usbipd bind --busid 2-2
     ```
   - Attach it to WSL2:
     ```powershell
     usbipd attach --wsl --busid 2-2
     ```

### 2. WSL (Ubuntu-24.04)

1. **Install dependencies (first time only):**
   ```bash
   sudo apt-get update
   sudo apt-get install usbip docker.io -y
   sudo usermod -aG docker $USER
   # Log out and back in, or run: newgrp docker
   ```
2. **Check for Arduino serial device:**
   ```bash
   ls /dev/ttyACM* /dev/ttyUSB*
   ```
3. **(Optional) Set permissions:**
   ```bash
   sudo chmod 666 /dev/ttyACM0
   ```
4. **Change to your project directory:**
   ```bash
   cd /mnt/c/Users/takaj/Desktop/COM_DB_API
   ```
5. **Build and run Docker:**
   ```bash
   docker build -t hydroponics-db-api .
   docker run --rm -it --device=/dev/ttyACM0 --env SERIAL_PORT=/dev/ttyACM0 -p 5000:5000 hydroponics-db-api
   ```
6. **Test the API:**
   ```bash
   curl http://localhost:5000/readings
   ```
