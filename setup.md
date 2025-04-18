# Setup Instructions for Hydroponics COM-DB-API

This guide covers setup for both deployment on a Raspberry Pi (with multi-architecture Docker image) and development (Windows/WSL2).

---

## Raspberry Pi Deployment (Recommended for Production)

Quinn's instructions:
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
   ls /dev/ttyACM* /dev/ttyUSB* #This is where the arduino connects from, 
   sudo chmod 666 /dev/ttyACM0
   ```
3. **Pull the multi-arch image from Docker Hub:**
   ```bash
   docker pull takajirobson/rasppardapi:latest
   ```
4. **Run the container:**
   ```bash
   docker run --rm -it --device=/dev/ttyACM0 --env SERIAL_PORT=/dev/ttyACM0 -p 5000:5000 takajirobson/rasppardapi:latest
   ```
5. **Test the API:**
   ```bash
   curl http://localhost:5000/readings
   
   curl http://<raspberry-pi-ip>:5000/status

   ```
   Check this on the pi by doing 
   ```bash
   hostname -I 
   ```
That should be it. 

## (Optional, Recommended) Enable raspberrypi.local Access with Avahi

To access your Raspberry Pi using `raspberrypi.local` (instead of its numeric IP), enable the Avahi daemon. This allows other devices on your network to resolve the Pi's hostname automatically.

**On your Raspberry Pi, run:**
```bash
sudo apt update
sudo apt install avahi-daemon
sudo systemctl enable avahi-daemon
sudo systemctl start avahi-daemon
```

You can verify it's running with:
```bash
systemctl status avahi-daemon
```

Now, you can use `raspberrypi.middlebury.edu` in your browser or terminal to access the API! Note that you should use the `.middlebury.edu` hostname for both `curl` and browser access.

Things that work to access the api
```bash
curl http://raspberrypi.middlebury.edu:5000/readings
curl raspberrypi.middlebury.edu:5000/readings
```
---

## Building and Publishing the Multi-Architecture Docker Image (from your development machine)

1. **Enable Docker Buildx (first time only):**
   ```bash
   docker buildx create --use
   ```
2. **Build and push the multi-architecture image:**
   ```bash
   docker buildx build --platform linux/amd64,linux/arm/v7,linux/arm64 -t takajirobson/rasppardapi:latest --push .
   ```
- This will build and publish a single image compatible with x86_64 and all Raspberry Pi models.

---

## Notes
- Always check your Arduino's actual device name (`/dev/ttyACM0`, `/dev/ttyUSB0`, etc).
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
5. **Build and run Docker (for local testing):**
   ```bash
   docker build -t hydroponics-db-api .
   docker run --rm -it --device=/dev/ttyACM0 --env SERIAL_PORT=/dev/ttyACM0 -p 5000:5000 hydroponics-db-api
   ```
6. **Test the API:**
   ```bash
   curl http://localhost:5000/readings
   ```
