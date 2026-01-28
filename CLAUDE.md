# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

人狼GMツール (Jinro GM Tool) - A Game Master assistant application for the social deduction game Werewolf (人狼). Two implementations exist:

- **JinroGmApp/**: Kivy-based mobile app (Android/iOS/Desktop)
- **JinroGmAppForFlet/**: Flet-based desktop/web app

## Build & Run Commands

### JinroGmApp (Kivy)

```bash
# Run locally (requires Kivy)
cd JinroGmApp && python main.py

# Build Android APK (requires buildozer)
cd JinroGmApp && buildozer android debug

# Clean build artifacts
cd JinroGmApp && buildozer android clean
```

### JinroGmAppForFlet (Flet)

```bash
# Run locally (requires flet)
cd JinroGmAppForFlet && python jinrogm.py
```

## Architecture

### JinroGmApp Structure

- `main.py`: Main application with `JinroGmApp` class and `MainWidget` containing all game logic
- `jinrogmapp.kv`: Kivy UI layout (KV language)
- `textinput4ja.py`: Custom TextInput class handling Japanese IME input (MIT licensed third-party code)
- `buildozer.spec`: Android build configuration (API 35, min API 33, NDK 25c)

### Key Classes (JinroGmApp/main.py)

- `Player`: Game participant with name, position (役職), and alive status
- `MainWidget`: Core UI and game state management
  - Manages participant list (`memberList`) and game members (`regList`)
  - Role constants: `POS_JINRO` (人狼), `POS_URANAI` (占い師), `POS_REIBAI` (霊媒師), `POS_BODYGUARD`, `POS_KYOJIN` (狂人)
  - Day progression system with popups for execution, divination, protection, and attack selections

### Game Flow

1. Register participants (参加者登録)
2. Select game members from participants
3. Configure role counts and assign roles (auto or manual)
4. Start game and progress through days (up to 7 days)
5. Each day: execution → divination → protection → attack → win condition check

## Notes

- UI language is Japanese
- Uses M+ 2c Regular font for Japanese character support
- App runs fullscreen by default (`Window.fullscreen = 'auto'`)
