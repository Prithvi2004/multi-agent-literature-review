# Quick Start Guide - New Features

## 🎯 What's New

Your Multi-Agent Literature Review System now has **10 new features**! Here's how to see and use them:

## 🚀 Starting the Application

### Backend
```bash
cd backend
python api_server.py
```

### Frontend
```bash
cd MALRS-Frontend
npm run dev
```

## ✨ New Features You'll See

### 1. **Session Manager** (Left Sidebar)
- **Location:** Left sidebar below the main navigation
- **What it does:** Auto-saves your work every 30 seconds
- **How to use:**
  - Click "Save" to manually save with a custom name
  - Click any session to load it
  - Click trash icon to delete
  - See "Saved X mins ago" indicator

### 2. **AI Research Chat** (Bottom Right)
- **Location:** Floating chat bubble in bottom-right corner
- **What it does:** Ask questions about your analysis
- **How to use:**
  - Click the chat bubble to open
  - Ask questions like "What are the main research gaps?"
  - Get AI responses with citations [P1], [P2]
  - Copy responses with the copy button

### 3. **Keyboard Shortcuts** (Everywhere)
- `Ctrl+Enter` - Run analysis
- `Ctrl+1/2/3` - Switch between tabs
- `Ctrl+S` - Save current session
- `Ctrl+T` - Toggle terminal
- `/` - Focus search (when implemented)

### 4. **Real Export** (Results Tab)
- **Location:** Results tab → Export Panel
- **What it does:** Download analysis in multiple formats
- **Formats:** PDF, LaTeX, Markdown
- **How to use:** Click "Export PDF" or other format buttons

### 5. **Terminal Persistence** (Results Tab)
- **What changed:** Terminal logs now persist when switching tabs
- **How to verify:** 
  1. Go to Results tab
  2. Click "Show Terminal"
  3. Switch to Input tab
  4. Switch back to Results
  5. Terminal logs are still there!

## 🎨 Visual Changes

### Sidebar
- Now wider (320px) to accommodate Session Manager
- Session list shows:
  - Session name
  - Last updated time
  - Number of sections and domains
  - Auto-save indicator

### Footer
- Added keyboard shortcut hints
- Shows: "Press Ctrl+1/2/3 to switch tabs • Ctrl+S to save • Ctrl+Enter to analyze"

### Chat Widget
- Floating orange/gold gradient bubble
- Opens to full chat interface
- Suggested questions on first open
- Message history with timestamps

## 🔧 Testing the Features

### Test Session Persistence:
1. Add some paper sections
2. Enter a research idea
3. Wait 30 seconds (auto-save)
4. Refresh the page (F5)
5. ✅ Your data should be restored!

### Test Export:
1. Run an analysis (or use existing results)
2. Go to Results tab
3. Click "Export PDF"
4. ✅ PDF should download automatically

### Test Chat:
1. Complete an analysis
2. Click chat bubble (bottom-right)
3. Click a suggested question OR type your own
4. ✅ Get AI response with citations

### Test Keyboard Shortcuts:
1. Press `Ctrl+1` → Should go to Input tab
2. Press `Ctrl+2` → Should go to Results tab
3. Press `Ctrl+S` → Should save session
4. ✅ All shortcuts working!

## 📝 Notes

- **Session data** is stored in IndexedDB (browser) and synced to backend
- **Terminal logs** persist across tab switches (fixed!)
- **Export** generates files server-side for consistency
- **Chat** uses your existing LLM configuration

## 🐛 Troubleshooting

**Can't see Session Manager?**
- Make sure browser window is wide enough (>1024px)
- Check browser console for errors

**Export not working?**
- Ensure backend is running on port 5000
- Check if `reportlab` is installed: `pip install reportlab`

**Chat not responding?**
- Verify LLM is configured in backend
- Check backend logs for errors

**Terminal still resetting?**
- Clear browser cache and reload
- Check if SSE connection is established (green dot in terminal header)

## 🎉 Enjoy!

All features are production-ready and fully integrated. Explore and enjoy your enhanced research workflow!
