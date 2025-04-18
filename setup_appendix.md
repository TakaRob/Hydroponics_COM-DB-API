git---

## Appendix: Bridging Windows COM Port to WSL Ubuntu (e.g., COM3 to /dev/ttyS3)

### Steps to Connect Arduino COM Port from Windows to WSL Ubuntu

This method uses usbipd-win to share the Arduino's COM port as a USB device into WSL, making it accessible as a Linux device (e.g., /dev/ttyACM0 or /dev/ttyS3).

1. **Install usbipd-win on Windows:**
   - Download from: https://github.com/dorssel/usbipd-win/releases
   - Install the latest `.msi` package.

2. **Open PowerShell as Administrator and list USB devices:**
   ```powershell
   usbipd list
   ```
   - Find your Arduino (look for device description and busid, e.g., `2-2`).

3. **Bind the Arduino for sharing:**
   ```powershell
   usbipd bind --busid 2-2
   ```

4. **Attach the device to WSL:**
   ```powershell
   usbipd attach --wsl --busid 2-2
   ```

5. **In WSL (Ubuntu), verify the device appears:**
   ```bash
   ls /dev/ttyACM* /dev/ttyUSB* /dev/ttyS*
   ```
   - Your Arduino should show up as `/dev/ttyACM0`, `/dev/ttyUSB0`, or `/dev/ttyS3` (depending on your system).

6. **(Optional) Set permissions if needed:**
   ```bash
   sudo chmod 666 /dev/ttyS3
   # or for ACM0/USB0:
   sudo chmod 666 /dev/ttyACM0
   ```

7. **Use this device in your Docker run command or application config:**
   - Example for ttyS3:
     ```bash
     docker run --rm -it --device=/dev/ttyS3 --env SERIAL_PORT=/dev/ttyS3 -p 5000:5000 takajirobson/rasppardapi:latest
     ```

**Troubleshooting:**
- If you don't see the device in WSL, make sure you have the correct busid and that usbipd-win is running as Administrator.
- Sometimes unplugging/replugging the Arduino or re-running the attach command is necessary.
- The device name may change depending on your system and how many serial devices are plugged in.

---
