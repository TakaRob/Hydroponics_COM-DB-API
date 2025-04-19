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
4. **Run the container with your database file as a bind mount (Raspberry Pi/Linux):**
   > This command runs the image, but since data is stored inside once it ends the data is also lost. I am working on a fix.

   ```bash
   docker run --rm -it \
     --device=/dev/ttyACM0 \
     --env SERIAL_PORT=/dev/ttyACM0 \
     -p 5000:5000 \
     takajirobson/rasppardapi:latest
   ```
   - This is the basic command without bind mounts or volumes. The database will be stored inside the container and will be reset if the container is removed.
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

---


## Enable raspberrypi.local Access with Avahi

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
curl raspberrypi:5000/readings
```
---