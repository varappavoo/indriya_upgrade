#!/bin/bash
curl -X POST http://localhost:5000/hibernate
sleep 5
cd ~/indriya_upgrade && killall indriya_autostart.py
