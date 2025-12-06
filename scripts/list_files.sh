#!/usr/bin/env bash

DEVICE=${DEVICE:-"auto"}
PORT_CMD="mpremote ${DEVICE}"

echo "📁 Files on ESP32:"
$PORT_CMD fs ls recursive
