# device-error

**Rank:** 3

## Goal

`DeviceError` in `inkcut/device/plugin.py` is not an unused
declaration. Nothing raises it, catches it, or subclasses it.
Remove the class. Do not add a caller in order to keep it.

## Guide

[Architecture](../../architecture.md), the device row in Layers.
Do not copy it. Do not edit the guide.

## Checks

A search of the repo finds no `DeviceError`. The device tests
named by the task still pass.
