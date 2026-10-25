---
source_url: https://openbot.run/download/linux
fetched: 2026-10-25
tool: firecrawl_scrape (markdown)
---

# OpenBot for Linux

Run a team of AI agents on your Linux computer with the ChatGPT, Claude, Gemini or Grok plan you already pay for, or with your own model. Your chats and files stay on your computer.

- [Download for Linux x64](https://openbot.run/download/linux/latest) (when `uname -m` shows x86_64)
- [Download for Linux arm64](https://openbot.run/download/linux/latest?arch=arm64) (when `uname -m` shows aarch64)

System: any 64-bit distribution. Processor: x64 or arm64. File: AppImage. Updates: automatic.

## Install on Linux

1. Download the AppImage for your processor. To find which one you need, run: x86_64 means x64, and aarch64 means arm64.

```
uname -m
```

2. Make the AppImage executable.

```
chmod +x OpenBot-*.AppImage
```

3. Run it. On the first start, OpenBot adds itself to your app launcher, so that openbot:// links open it.

```
./OpenBot-*.AppImage
```

4. Connect a provider, such as Codex with your ChatGPT plan or Claude Code with your Claude plan. Then describe the agent you want in one prompt and save it.

## Ubuntu 23.10 or newer, and Debian 13

1. These distributions restrict the user namespaces that the Electron sandbox needs, so OpenBot exits during launch until you install its AppArmor profile. Take the profile out of the AppImage:

```
./OpenBot-*.AppImage --appimage-extract resources/linux/openbot.apparmor
```

2. Install the profile, then reload AppArmor:

```
sudo install -m 0644 squashfs-root/resources/linux/openbot.apparmor /etc/apparmor.d/openbot
sudo systemctl reload apparmor
```

3. The profile applies to an AppImage in ~/Applications, ~/Desktop, ~/Downloads, ~/.local/bin or /opt/OpenBot. Keep it in one of these, or edit the path in the profile before you install it. Do not start OpenBot with --no-sandbox: the sandbox is the boundary between a web page and the rest of your computer.

## A server with no screen

1. On Ubuntu 24.04 or 26.04 with systemd, install OpenBot as an always-on server of your account, then sign in with an email code:

```
curl -fsSL https://raw.githubusercontent.com/nightly-labs/openbot/main/scripts/install-server.sh | sudo bash
sudo openbot login
```

2. Then use it from the desktop app, the mobile app or openbot.run/app.

## Good to know

- Each release is tested on Ubuntu 24.04 on x64. OpenBot also runs on Ubuntu 26.04.
- OpenBot checks for new versions and updates itself.
- The AI provider you choose needs an internet connection. A local model needs none.
- Remote desktop works with the x64 AppImage in an X11 session, such as Xorg or Xvfb. It does not work under Wayland, and the arm64 AppImage does not include it.

## Questions

**Is there an AI agent app for Linux?** Yes. OpenBot runs on Linux as an AppImage for x64 and arm64. It runs Codex, Claude Code, Gemini, Grok and OpenCode agents as a team, with the plans you already pay for or a local model.

**Why does OpenBot exit at once on Ubuntu?** Ubuntu 23.10 and newer, and Debian 13, restrict the user namespaces that the Electron sandbox needs. Install the AppArmor profile that ships in the AppImage, as the steps on this page show.

**Does OpenBot run on arm64 Linux?** Yes. Download the arm64 AppImage. It has the features of the x64 AppImage except remote desktop.

## Other systems

- [OpenBot for Mac](https://openbot.run/download/macos): macOS 13 Ventura or later, Apple silicon or Intel
- [OpenBot for Windows](https://openbot.run/download/windows): Windows 10 or 11, x64, Intel or AMD
- [OpenBot for iPhone](https://openbot.run/download/ios): iOS 16.4 or later, TestFlight public beta
- [OpenBot for Android](https://openbot.run/download/android): Android 7.0 or later, Google Play

[Release notes](https://openbot.run/changelog) | [All releases on GitHub](https://github.com/nightly-labs/openbot/releases) | [Troubleshooting](https://github.com/nightly-labs/openbot/blob/main/docs/TROUBLESHOOTING.md)
