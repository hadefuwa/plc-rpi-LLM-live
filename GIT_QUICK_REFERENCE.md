# Git Quick Reference

## Push
```bash
cd ~/plc-rpi-LLM-live
git add .
git commit -m "Update message here"
git push origin main
```

## Pull 
```bash
cd ~/plc-rpi-LLM-live
git fetch origin
git reset --hard origin/main
git clean -fd
npm install
chmod +x scripts/*.sh
npm run kiosk
```


#Create and push your first revision tag
git tag -a rev1 -m "Rev 1 released"
git push origin main --tags

#When ready for the next release
git add -A
git commit -m "Prepare for Rev 2.1 release"
git tag -a rev2.1 -m "Rev 2.1 released"
git push origin main --tags


__________