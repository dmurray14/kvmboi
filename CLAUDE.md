# kvmboi Project

This project is a Python library (`kvmboi`) for controlling GL.iNet Comet KVM (PiKVM-compatible) devices on the local network.

**Full API reference and usage patterns are in `KVMBOI.md` — read that file before using the library.**

## Quick Reference

```python
from kvmboi import KVMClient
import time

kvm = KVMClient("your-kvm-hostname.local", password="your-password")

kvm.screenshot("/tmp/screen.jpg")          # See the screen (JPEG)
kvm.keyboard.type("hello")                 # Type text
kvm.keyboard.press("Enter")                # Press a key
kvm.keyboard.shortcut("MetaLeft", "Space") # Key combo (Cmd+Space)
kvm.mouse.click(1280, 720)                 # Click at coordinates
kvm.mouse.scroll(delta_y=-3)               # Scroll up

kvm.close()
```

## Configuration

Set your KVM connection details via environment variables or pass them directly:

```bash
export KVMBOI_HOST="your-kvm-hostname.local"
export KVMBOI_PASSWORD="your-password"
```
