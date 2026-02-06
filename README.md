# 👣 Footprints Navigator

Footprints Navigator is a cross-platform tool for Windows and macOS that automatically records and searches your file and folder navigation history.

Have you ever thought:
"Which folder was I working in when I did that task?"

This tool eliminates that lost time by keeping a complete, searchable record of where you've been.

---

## 🌟 Why This Exists

During daily PC work, we constantly move across countless folders and files.  
However, standard "Recent Items" features mainly focus on files and provide little visibility into folder navigation history.

I wanted a solution that:

- Is independent of the OS
- Records every place I've walked through ("Footprints")
- Allows instant revisits with minimal friction

Based on that idea, Footprints Navigator was designed with the following principles:

- Separation of Concerns  
  Monitoring, persistence, and UI are separated into independent modules for maintainability and extensibility.

- Lightweight and Robust  
  Uses SQLite in WAL mode to ensure low overhead and strong data consistency for a background application.

- Cross-Platform Oriented  
  Designed with Windows Explorer monitoring and macOS path compatibility in mind.

---

## 🚀 Key Features

- Automatic Footprint Recording  
  Explorer navigation and shortcut executions are detected automatically in the background.

- High-Speed Incremental Search  
  Instantly search through tens of thousands of accumulated records using keywords.

- System Tray Resident  
  Runs quietly in the system tray with a minimal UI, always ready when needed.

- Single-Instance Search Window  
  If the search UI is already open, it is brought to the foreground instead of launching a duplicate.

---

## 🛠 Tech Stack

- Language  
  Python 3.10+

- GUI  
  Tkinter (Custom Modern Style)

- Database  
  SQLite3  
  - WAL mode enabled  
  - Indexed for fast search

- Libraries  
  - pystray: System tray management  
  - pywin32: Windows API interaction  
  - pathlib: Cross-platform path handling

---

## ⚡ Setup & Usage

### 1. Install Dependencies

Clone the repository and install the required libraries:

```bash
pip install -r requirements.txt
```

Python 3.10 or later is required.  
Make sure `python` points to the correct version in your environment.

---

### 2. Run the Application

Footprints Navigator consists of two components:

- Background Monitor (runs continuously)
- Search UI (opened on demand)

#### Start Background Monitoring

Launch the background process by running `main.pyw`:

```bash
python main.pyw
```

Once started:

- A system tray icon will appear
- Folder navigation will begin recording automatically

#### Open the Search UI

You can open the search window in either of the following ways:

- Right-click the tray icon and select "Open Search"
- Run `search.py` directly

---

### 3. (Optional) Build a Standalone Executable

If you want to run the application on a machine without Python installed, you can create an executable using PyInstaller.

Install PyInstaller:

```bash
pip install pyinstaller
```

Build the executable:

```bash
pyinstaller --noconsole --onefile --icon=app_icon.ico main.pyw
```

The generated executable (`main.exe`) will be located in the `dist` directory.

---

## 📂 Project Structure

```
Footprints-Navigator/
├── main.pyw          # Entry point (OS detection & system tray)
├── main.py           # Monitoring engine (OS-specific thread control)
├── database.py       # Persistence layer (SQLite)
├── search.py         # Search UI
├── requirements.txt  # Dependencies
└── data/             # Database storage (auto-created on first run)
```

---

## 📝 License

MIT License

---

## 🤝 Contributing

Bug reports, feature requests, and pull requests are welcome.  
Feel free to open an Issue or submit a Pull Request.
