#!/usr/bin/env pwsh
param(
    [string]$Device = "auto"
)

Write-Host "📁 Files on ESP32:"
& mpremote connect $Device fs ls -r
