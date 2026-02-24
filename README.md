# kvmboi — Python KVM Control Library

## What This Is

`kvmboi` is a Python library for controlling GL.iNet Comet KVM (and other PiKVM-compatible) devices over the network. It provides full remote control of a physical computer: seeing its screen, typing on its keyboard, moving/clicking its mouse, managing virtual media (ISO mounting), and ATX power control.

**This is hardware-level control.** The KVM sits between you and the target machine's keyboard/video/mouse ports. It works regardless of what OS is running (or even if no OS is booted). You can interact with BIOS, boot menus, OS installers, lock screens — anything that appears on the physical display.

## Setup

```bash
pip install httpx websockets
```

```python
from kvmboi import KVMClient

kvm = KVMClient("your-kvm-hostname.local", username="admin", password="your-password")
# ... do things ...
kvm.close()
```

Or use as a context manager:

```python
with KVMClient("your-kvm-hostname.local", password="your-password") as kvm:
    kvm.screenshot("/tmp/screen.jpg")
```

### Configuration via Environment Variables

```bash
export KVMBOI_HOST="your-kvm-hostname.local"
export KVMBOI_PASSWORD="your-password"
```

## Coordinate System

Mouse coordinates map directly to the captured screen resolution. For example, if the KVM captures at **2560x1440**:
- Top-left: (0, 0)
- Center: (1280, 720)
- Bottom-right: (2560, 1440)

Check the actual resolution with:
```python
info = kvm.video.streamer_info()
res = info["streamer"]["source"]["resolution"]  # {"width": 2560, "height": 1440}
```

**Always take a screenshot first** to determine where UI elements are before clicking. The coordinates in the screenshot image map directly to the mouse coordinate system.

## Core Operations

### Screenshots — Seeing the Screen

```python
# Save to file and get bytes
jpg_bytes = kvm.screenshot("/tmp/screen.jpg")

# Just get bytes (no file save)
jpg_bytes = kvm.screenshot()

# Get video stream metadata
info = kvm.video.streamer_info()
# info["streamer"]["source"]["resolution"] = {"width": 2560, "height": 1440}
# info["streamer"]["source"]["captured_fps"] = 60
# info["streamer"]["hdmi"]["signal"] = True/False  (is something plugged in?)
```

The screenshot is a JPEG image at the native capture resolution, typically 100-200KB. Use this to observe the current state of the target machine before deciding what to do.

### Keyboard — Typing and Key Presses

#### Type text strings (best for alphanumeric input)
```python
kvm.keyboard.type("hello world")          # Types the literal string
kvm.keyboard.type("ls -la /tmp")          # Type a command
kvm.keyboard.type("mypassword")           # Type a password into a field
```

`type()` uses the HID print endpoint and handles character-to-keypress mapping automatically. It's reliable for ASCII text. For special keys or key combinations, use `press()` or `shortcut()` instead.

#### Press individual keys
```python
kvm.keyboard.press("Enter")               # Press and release Enter
kvm.keyboard.press("Tab")                 # Tab key
kvm.keyboard.press("Escape")              # Escape key
kvm.keyboard.press("Space")               # Space bar
kvm.keyboard.press("Backspace")           # Backspace
kvm.keyboard.press("Delete")              # Delete
kvm.keyboard.press("ArrowUp")             # Arrow keys
kvm.keyboard.press("ArrowDown")
kvm.keyboard.press("ArrowLeft")
kvm.keyboard.press("ArrowRight")
kvm.keyboard.press("F1")                  # Function keys F1-F12
kvm.keyboard.press("F12")
kvm.keyboard.press("KeyA")                # Letter keys: KeyA through KeyZ
kvm.keyboard.press("Digit0")              # Number keys: Digit0 through Digit9
```

#### Key combinations (shortcuts)
```python
kvm.keyboard.shortcut("ControlLeft", "KeyC")           # Ctrl+C
kvm.keyboard.shortcut("ControlLeft", "KeyV")           # Ctrl+V
kvm.keyboard.shortcut("ControlLeft", "KeyA")           # Ctrl+A (select all)
kvm.keyboard.shortcut("AltLeft", "Tab")                # Alt+Tab
kvm.keyboard.shortcut("AltLeft", "F4")                 # Alt+F4
kvm.keyboard.shortcut("MetaLeft", "KeyA")              # Cmd+A (macOS)
kvm.keyboard.shortcut("MetaLeft", "Space")             # Cmd+Space (Spotlight on macOS)
kvm.keyboard.shortcut("MetaLeft", "Tab")               # Cmd+Tab (macOS app switcher)
kvm.keyboard.shortcut("ControlLeft", "AltLeft", "Delete")  # Ctrl+Alt+Delete
kvm.keyboard.shortcut("ControlLeft", "ShiftLeft", "Escape") # Ctrl+Shift+Esc (Task Manager)
```

`shortcut()` presses all keys in order, holds briefly, then releases in reverse order.

#### Hold and release (for drag operations, gaming, etc.)
```python
kvm.keyboard.hold("ShiftLeft")            # Hold Shift down
kvm.keyboard.type("hello")                # Types "HELLO" because Shift is held
kvm.keyboard.release("ShiftLeft")         # Release Shift
```

### Complete Key Name Reference

**Modifier keys:** `ControlLeft`, `ControlRight`, `ShiftLeft`, `ShiftRight`, `AltLeft`, `AltRight`, `MetaLeft`, `MetaRight`

**Letter keys:** `KeyA` through `KeyZ`

**Number keys:** `Digit0` through `Digit9`

**Function keys:** `F1` through `F12`

**Navigation:** `ArrowUp`, `ArrowDown`, `ArrowLeft`, `ArrowRight`, `Home`, `End`, `PageUp`, `PageDown`

**Editing:** `Enter`, `Tab`, `Space`, `Backspace`, `Delete`, `Insert`, `Escape`

**Punctuation:** `Minus`, `Equal`, `BracketLeft`, `BracketRight`, `Backslash`, `Semicolon`, `Quote`, `Backquote`, `Comma`, `Period`, `Slash`

**Lock keys:** `CapsLock`, `NumLock`, `ScrollLock`

**Numpad:** `Numpad0`-`Numpad9`, `NumpadAdd`, `NumpadSubtract`, `NumpadMultiply`, `NumpadDivide`, `NumpadEnter`, `NumpadDecimal`

**System:** `PrintScreen`, `Pause`

### Mouse — Movement and Clicking

```python
# Move to absolute position
kvm.mouse.move(1280, 720)                 # Move to center of screen

# Click (moves to position, then clicks)
kvm.mouse.click(1280, 720)                # Left-click at center
kvm.mouse.click(500, 300, button="left")  # Explicit left click
kvm.mouse.right_click(1280, 720)          # Right-click
kvm.mouse.middle_click(1280, 720)         # Middle-click
kvm.mouse.double_click(1280, 720)         # Double-click

# Click at current position (no move)
kvm.mouse.click()                         # Left-click where cursor is now

# Scroll
kvm.mouse.scroll(delta_y=-3)              # Scroll up (negative = up)
kvm.mouse.scroll(delta_y=3)               # Scroll down (positive = down)
kvm.mouse.scroll(delta_x=3)              # Scroll right

# Drag
kvm.mouse.drag(100, 100, 500, 500)        # Drag from (100,100) to (500,500)

# Relative move (offset from current position)
kvm.mouse.relative_move(10, -5)           # Move 10px right, 5px up
```

### Virtual Media (MSD) — ISO Mounting

Mount ISO images as virtual CD-ROM or USB drives to the target machine. Useful for OS installation, recovery tools, etc.

```python
# Check current state
status = kvm.msd.status()
# status["drive"]["connected"] = True/False
# status["drive"]["image"]["name"] = "ubuntu.iso"
# status["drive"]["cdrom"] = True/False

# List available images on the KVM's storage
images = kvm.msd.list_images()
# {"ubuntu-24.04-live-server-amd64.iso": {"size": 3405469696, "complete": True}}

# Upload an ISO from local disk
kvm.msd.upload("/path/to/image.iso")

# Or download from URL directly to KVM storage
kvm.msd.upload_url("https://releases.ubuntu.com/24.04/ubuntu-24.04-live-server-amd64.iso")

# Select which image to use and set drive mode
kvm.msd.set_image("ubuntu-24.04-live-server-amd64.iso", cdrom=True)   # CD-ROM mode
kvm.msd.set_image("installer.img", cdrom=False)                        # Flash drive mode

# Connect/disconnect the virtual drive
kvm.msd.connect()       # Target machine sees the virtual drive appear
kvm.msd.disconnect()    # Target machine sees the drive disappear

# Remove an image from storage
kvm.msd.remove_image("old-image.iso")
```

### ATX Power Control

Control the target machine's power and reset buttons. **Note: ATX must be physically wired from the KVM to the target's front panel headers.**

```python
# Check power state
status = kvm.atx.status()
# status["power"] = "on" or "off"
# status["leds"]["power"] = True/False
# status["leds"]["hdd"] = True/False

# Power button (short press — normal power on/off)
kvm.atx.short_press()

# Power button (long press — force power off)
kvm.atx.long_press()

# Reset button
kvm.atx.reset()
```

### System Info

```python
info = kvm.info()
# info["system"]["kvmd"]["version"] = "4.82"
# info["system"]["streamer"]["app"] = "ustreamer"
```

## Async API

All operations are also available as async methods via `AsyncKVMClient`:

```python
import asyncio
from kvmboi import AsyncKVMClient

async def main():
    async with AsyncKVMClient("your-kvm.local", password="your-password") as kvm:
        await kvm.keyboard.type("hello")
        await kvm.mouse.click(1280, 720)
        jpg = await kvm.video.screenshot("/tmp/screen.jpg")

asyncio.run(main())
```

## Interaction Patterns for AI Agents

### The Screenshot-Act-Verify Loop

This is the fundamental pattern for all KVM interactions:

```python
import time

# 1. LOOK — Take a screenshot to see current state
kvm.screenshot("/tmp/step1.jpg")
# [Analyze the screenshot to understand what's on screen]

# 2. ACT — Perform the needed interaction
kvm.mouse.click(x, y)        # or keyboard.type(), etc.

# 3. WAIT — Give the target machine time to respond
time.sleep(1)                 # Adjust based on expected response time
                              # UI animations: 0.5-1s
                              # Application launch: 2-5s
                              # OS boot: 10-60s

# 4. VERIFY — Screenshot again to confirm the action worked
kvm.screenshot("/tmp/step2.jpg")
# [Analyze to verify expected result]
```

### Waking a Machine from Screensaver/Sleep

```python
import time
kvm.mouse.click(1280, 720)    # Move mouse to wake
time.sleep(1)
kvm.keyboard.press("Space")   # Press a key as backup
time.sleep(2)
kvm.screenshot("/tmp/check.jpg")
```

### Logging Into a macOS Lock Screen

```python
import time
# 1. Wake the machine
kvm.keyboard.press("Space")
time.sleep(2)

# 2. Screenshot to see the lock screen
kvm.screenshot("/tmp/lockscreen.jpg")

# 3. The password field should be focused automatically.
#    If not, click on it (centered, near bottom of screen)
kvm.mouse.click(1280, 1310)
time.sleep(0.5)

# 4. Type password and submit
kvm.keyboard.type("thepassword")
time.sleep(0.3)
kvm.keyboard.press("Enter")
time.sleep(3)

# 5. Verify login succeeded
kvm.screenshot("/tmp/desktop.jpg")
```

### Logging Into a Windows Lock Screen

```python
import time
# 1. Dismiss lock screen
kvm.keyboard.press("Escape")
time.sleep(1)

# 2. Ctrl+Alt+Delete if needed (for domain-joined machines)
kvm.keyboard.shortcut("ControlLeft", "AltLeft", "Delete")
time.sleep(2)

# 3. Type password and submit
kvm.keyboard.type("thepassword")
kvm.keyboard.press("Enter")
time.sleep(5)

kvm.screenshot("/tmp/desktop.jpg")
```

### Opening a Terminal (macOS)

```python
import time
# Spotlight search
kvm.keyboard.shortcut("MetaLeft", "Space")
time.sleep(1)
kvm.keyboard.type("Terminal")
time.sleep(1)
kvm.keyboard.press("Enter")
time.sleep(2)
kvm.screenshot("/tmp/terminal.jpg")
```

### Running a Command in an Open Terminal

```python
import time
kvm.keyboard.type("ls -la /tmp")
kvm.keyboard.press("Enter")
time.sleep(1)
kvm.screenshot("/tmp/output.jpg")
```

### Navigating BIOS/UEFI

```python
import time
# Reboot and spam the BIOS key during POST
kvm.atx.reset()
time.sleep(2)
for _ in range(20):
    kvm.keyboard.press("Delete")    # or F2, F12 depending on vendor
    time.sleep(0.2)
time.sleep(3)
kvm.screenshot("/tmp/bios.jpg")
```

### Booting from Virtual CD-ROM

```python
import time
# Mount the ISO
kvm.msd.set_image("ubuntu-24.04-live-server-amd64.iso", cdrom=True)
kvm.msd.connect()
time.sleep(1)

# Reboot and enter boot menu
kvm.atx.reset()
time.sleep(2)
for _ in range(20):
    kvm.keyboard.press("F12")       # Boot menu key (varies by BIOS)
    time.sleep(0.2)
time.sleep(3)

# Screenshot to see boot menu, then select the virtual CD-ROM
kvm.screenshot("/tmp/bootmenu.jpg")
```

## Important Notes

### Timing
- Always add `time.sleep()` between actions. The target machine needs time to process input and update its display.
- Screenshots reflect what was on screen at the instant of capture. If you just sent a keystroke, wait before screenshotting.
- Typical wait times: keypress response 0.2-0.5s, UI navigation 1-2s, app launch 2-5s, OS boot 15-60s.

### Mouse Coordinates
- The coordinate space matches the native capture resolution (check with `streamer_info()`).
- Always screenshot first and locate UI elements visually before clicking.
- Common macOS UI positions: menu bar y≈15, dock y≈(height-30), window title bars y≈30-50.

### Keyboard
- `type()` is best for typing text strings. It handles character mapping automatically.
- `press()` is for individual special keys (Enter, Tab, arrows, function keys).
- `shortcut()` is for key combos (Ctrl+C, Cmd+Space, etc.).
- `type()` does NOT interpret `\n` as Enter — use `press("Enter")` separately.
- On macOS, the Command key is `MetaLeft`/`MetaRight`.

### Connection Lifecycle
- Always call `kvm.close()` when done, or use `with KVMClient(...) as kvm:`.
- The WebSocket connection is established lazily on first keyboard/mouse use.
- The HTTP client is reused across REST calls (screenshots, MSD, ATX, info).

### SSL
- KVM devices typically use self-signed certificates. SSL verification is disabled by default (`ssl_verify=False`).
- Pass `ssl_verify=True` if you've installed a proper certificate on the device.

### Error Handling
```python
from kvmboi import KVMClient, AuthError, APIError, KVMError

try:
    kvm = KVMClient("your-kvm.local", password="wrong")
    kvm.info()
except AuthError:
    print("Bad credentials")
except APIError as e:
    print(f"API error: {e.error}: {e.message}")
except KVMError as e:
    print(f"General KVM error: {e}")
```

### No HDMI Signal
If `kvm.video.streamer_info()["streamer"]["hdmi"]["signal"]` is `False`, the target machine's display output is off (powered down, in deep sleep, or cable disconnected). The screenshot will be blank/black.

## Compatibility

- **Python:** 3.9+
- **Tested devices:** GL.iNet Comet (GL-RM1)
- **Compatible with:** Any PiKVM-compatible device running KVMD (the PiKVM API)
- **Dependencies:** `httpx`, `websockets`
