# 9-key macropad + encoder + OLED

Homemade macropad: 9 keys in a 3x3 grid, a rotary encoder with a push button, and a 0.91" OLED screen. Every switch has its own RGB LED for backlighting, all chained together on a single data pin.

## Hardware

- Seeeduino XIAO 
- 0.91" I2C OLED
- Rotary encoder with built-in push button
- 9x mechanical switches, each with its own 1N4148 diode, 3x3 matrix
- 9x SK6812MINI-E LEDs daisy-chained for per-key backlighting

## Firmware

QMK Firmware.

## What it does

- 9 programmable keys, multiple layers
- Encoder: turning it forward/back seeks the currently playing track
- Encoder click: the screen switches to showing the volume bar for a few seconds
- Screen: shows the progress bar of whatever track is playing (see below, needs the companion script)
- Per-key RGB backlighting

## to-do

[ ] Finish this README
