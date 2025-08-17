# Git Quick Reference

## Push
```bash
cd ~/rpi-demo-3
git add .
git commit -m "Update message here"
git push origin main
```

## Pull 
```bash
cd ~/rpi-demo-3
git fetch origin
git reset --hard origin/main
git clean -fd
npm install
chmod +x scripts/*.sh
npm run kiosk
```

## Troubleshooting Kiosk Mode
If you get "localhost:3000 can't be found" error:

```bash
# Method 1: Start server manually first
cd ~/rpi-demo-3
npm run serve &
sleep 5
npm run kiosk

# Method 2: Use development server
npm run dev

# Method 3: Check if http-server is installed
npm install http-server

# Method 4: Kill existing processes and restart
pkill -f http-server
pkill -f chromium
npm run kiosk
```

## Autostart Service Management
```bash
# Install autostart service (run once)
cd ~/rpi-demo-3
chmod +x scripts/*.sh
./scripts/install-autostart.sh

# Check service status
sudo systemctl status rpi-showcase.service

# View service logs (live)
sudo journalctl -u rpi-showcase.service -f

# View service logs (recent)
sudo journalctl -u rpi-showcase.service --since "5 minutes ago"

# View autostart log file
tail -f ~/rpi-demo-3/autostart.log

# Manually start/stop/restart service
sudo systemctl start rpi-showcase.service
sudo systemctl stop rpi-showcase.service
sudo systemctl restart rpi-showcase.service

# Test autostart manually (without reboot)
sudo systemctl stop rpi-showcase.service
sudo systemctl start rpi-showcase.service

# Disable autostart
sudo systemctl disable rpi-showcase.service

# Uninstall autostart service
./scripts/uninstall-autostart.sh
```

## Autostart Troubleshooting
```bash
# Quick status check
sudo systemctl status rpi-showcase.service

# Check what's actually running
ps aux | grep -E "http-server|chromium"

# Check if X server is available
echo $DISPLAY
xset q 2>/dev/null && echo "X server OK" || echo "X server NOT available"

# Check autostart logs
tail -f ~/rpi-demo-3/simple-autostart.log

# Manual test (kill service first)
sudo systemctl stop rpi-showcase.service
cd ~/rpi-demo-3
chmod +x scripts/simple-autostart.sh
./scripts/simple-autostart.sh

# Restart service with new config
sudo systemctl daemon-reload
sudo systemctl restart rpi-showcase.service

# Kill all processes and restart clean
pkill -f http-server
pkill -f chromium
sudo systemctl restart rpi-showcase.service
```
chmod +x scripts/*.sh
./scripts/install-emoji-fonts.sh
```

#Create and push your first revision tag
git tag -a rev1 -m "Rev 1 released"
git push origin main --tags

#When ready for the next release
git add -A
git commit -m "Prepare for Rev 2.9 release"
git tag -a rev2.9 -m "Rev 2.9 released"
git push origin main --tags


__________