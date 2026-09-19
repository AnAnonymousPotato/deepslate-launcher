# Deepslate Launcher

A modern, high-performance Minecraft-themed desktop launcher for **Minecraft Bedrock Edition on Linux**, replacing the default `bedrock-on-linux` GUI.

Designed with inspiration from the **Official Minecraft Launcher** layout and the **Bedrock Ore UI (Dark Emerald)** aesthetic.

---

## ✨ Features

- **🎮 Authentic Minecraft Launcher Experience**:
  - Left navigation sidebar (*Play, Installations, Settings, Tools & Diag, Profiles, Patch Notes*).
  - Rich Bedrock cavern panorama hero banner with 3D stone Minecraft title.
  - Prominent 9-slice emerald green **PLAY** button with real-time process monitoring (**STOP** button when running).
  - Quick toggles on the play screen: MangoHud, Ray Tracing (DXR 1.1), Wayland native driver.
- **💎 Bedrock Ore UI (Dark Emerald) Theming**:
  - Stone-slate palette (`#161718`, `#202122`, `#303133`).
  - Pixel-perfect 9-slice beveled buttons, switches, and checkboxes.
  - Authentic Minecraft pixel typography.
  - Emerald green highlights (`#4B9736` / `#2ECC71`).
- **📦 Complete Version & Installation Manager**:
  - Browse downloaded builds with disk usage, path, and active edition badges.
  - Set active version, open file manager, or delete installations.
  - Download new Bedrock builds (Release and Preview) with real-time download progress bar.
- **👤 Xbox Account & Isolated Profiles**:
  - Live account card displaying Xbox Gamertag (`AnonSpud`) and online status.
  - Microsoft OAuth device-code sign-in dialog (code display + automatic browser opening).
  - Microsoft Store account linking via Xodus.
  - Isolated profile creation and custom desktop shortcut generation.
- **⚙️ Comprehensive Settings**:
  - General: Close on launch, beta editions, Discord Rich Presence, Xbox Friends, controller navigation, custom environment variables (`MANGOHUD=1`).
  - Graphics & Engine: Ray Tracing (VKD3D universal), Wayland input driver, GPU crash safety barrier acknowledgment.
  - Storage: View storage path and open local data directory.
- **🛠️ Tools & Diagnostics**:
  - One-click **System Doctor** report (Python, Vulkan, WineGDK, dependencies).
  - **Network Diagnostics** (Xbox Live and Microsoft ping/route inspection).
  - **Prefix Repair** (reset Wine prefix while preserving worlds and settings).
  - **Content Importer** (.mcpack, .mcaddon, .mcworld, .mcskin).
- **📜 Live Console Drawer & Patch Notes**:
  - Collapsible bottom drawer streaming live Wine, Proton, and launcher output.
  - Integrated Markdown release notes / changelog viewer.

---

## 🛡️ Update-Proof Architecture

Deepslate runs **independently alongside `bedrock-on-linux-bin`** (installed via AUR).

- It **never modifies installed system files** in `/usr` or `/opt`.
- Whenever `bedrock-on-linux-bin` updates via `yay` / `paru` / `pacman`:
  - Deepslate's backend bridge detects the updated AppImage in `/opt/bedrock-on-linux-bin/`.
  - It automatically extracts and refreshes the cached `bol` Python runtime in ~50ms.
  - **Zero manual intervention is required after system updates!**
- Also features a complete subprocess CLI fallback (`bedrock-on-linux {play, setup, versions, doctor, etc.}`).

---

## 🚀 Running Deepslate

You can run Deepslate directly from the terminal or your application menu:

```bash
# Launch directly
~/Projects/deepslate/deepslate
```

Or search for **"Deepslate Launcher"** in your application launcher (KDE Plasma, GNOME, Rofi, etc.).

---

## 📦 AUR Package

A `PKGBUILD` is provided in the repository root for packaging Deepslate as `deepslate-launcher-git`.

```bash
cd ~/Projects/deepslate
makepkg -si
```

---

## 📜 License

MIT License.
Minecraft assets and textures are copyright Mojang AB / Microsoft Corporation.
