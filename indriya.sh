#!/bin/bash
nohup ./indriya_autostart.py &
sleep 5
curl -X POST http://localhost:5000/reload_jobs
