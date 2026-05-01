# Migration Guide: Flask → GitHub Pages Edition

## What Changed?

You now have **two versions** of PostureHealthTracker:

### Version 1: Flask Web App (Original)
📁 Location: Root directory
- `web_app.py` - Python Flask server
- `run_demo.py` - Demo script with test data
- Runs locally only
- Requires Python & Flask
- SQLite database

### Version 2: GitHub Pages Edition (NEW)
📁 Location: `docs/` folder  
- `index.html` - Web interface
- `app.js` - Firebase integration
- `styles.css` - Styling
- Runs in browser anywhere
- No server needed
- Cloud database (Firebase)
- **Can host on GitHub Pages** ✨

## Which Should You Use?

### Use Flask Version If:
- ✅ Testing sensors locally
- ✅ Don't need cloud access
- ✅ Want Python integration
- ✅ Need to modify backend logic

**Start**: `python web_app.py` then visit `http://localhost:5000`

### Use GitHub Pages Version If:
- ✅ Want to share/deploy globally
- ✅ Need multi-user support
- ✅ Want community features
- ✅ Don't want server maintenance
- ✅ Want to host on GitHub Pages

**Deploy**: Push to GitHub → Enable GitHub Pages → Done!

## Comparison Table

| Aspect | Flask | GitHub Pages |
|--------|-------|--------------|
| **Where to Run** | `python web_app.py` | GitHub Pages (automatic) |
| **Database** | SQLite (local file) | Firebase Firestore (cloud) |
| **Users** | Single (you only) | Multiple (global) |
| **Access** | `localhost:5000` only | `username.github.io/repo` |
| **Sensor Integration** | Python code | JavaScript needed |
| **Authentication** | Form-based | Firebase Auth |
| **Analytics** | Basic | Advanced (2-week dashboard) |
| **Community Stats** | None | Leaderboard ✨ |
| **Mobile Access** | No | Yes ✨ |
| **Cost** | Free | Free |
| **Setup Time** | 5 min | 10 min (first time) |
| **Deployment** | Run script | Git push |

## How to Use Both

### Flask Version (Local Testing)

1. Keep running:
   ```bash
   python web_app.py
   ```

2. Run demo data:
   ```bash
   python run_demo.py
   ```

3. Access at `http://localhost:5000`

4. Test with simulated sensor data

### GitHub Pages Version (Cloud Deployment)

1. Set up Firebase (see SETUP.md)

2. Update config in `docs/app.js`

3. Deploy:
   ```bash
   git add .
   git commit -m "Update GitHub Pages version"
   git push origin main
   ```

4. Access at `https://username.github.io/PostureHealthTracker`

5. Create accounts, share with others

## Migrating Data (Flask → GitHub Pages)

### Option 1: Manual Export
1. In Flask app, download CSV of sessions
2. Manually enter in GitHub Pages version

### Option 2: Direct Firebase Import
1. Export Flask SQLite data as JSON
2. Use Firebase Admin SDK to import
3. Advanced - requires Node.js/Firebase CLI

### Option 3: Start Fresh
- Simplest approach
- Both systems can coexist
- Users create new accounts on GitHub Pages version

## Technical Differences

### Flask Version
```
Browser → Flask Server → SQLite → Browser
```

### GitHub Pages Version  
```
Browser → Firebase Services → Firestore → Browser
```

### Sensor Integration

**Flask** (Python):
```python
from web_app_integration import WebAppIntegration

integration = WebAppIntegration('http://localhost:5000')
integration.send_reading(pitch, roll, ...)
```

**GitHub Pages** (JavaScript):
```javascript
const reading = {
    pitch: imuData.pitch,
    roll: imuData.roll,
    // ...
};

await db.collection('sessions')
    .doc(sessionId)
    .collection('readings')
    .add(reading);
```

## Step-by-Step: Enable GitHub Pages

### Setup

1. **Create GitHub Repository**
   ```bash
   cd c:\Users\HP\OneDrive\PostureHealthTracker
   git init
   git add .
   git commit -m "Initial commit"
   git remote add origin https://github.com/YOUR_USERNAME/PostureHealthTracker.git
   git push -u origin main
   ```

2. **Enable Pages in Settings**
   - Go to GitHub repo → Settings → Pages
   - Source: `main` branch, `/docs` folder
   - Wait 1-2 minutes

3. **Access Site**
   - URL: `https://YOUR_USERNAME.github.io/PostureHealthTracker`

### Configure Firebase

1. Go to [console.firebase.google.com](https://console.firebase.google.com)
2. Create new project
3. Add web app
4. Copy config
5. Update `docs/app.js`

### Deploy Updates

```bash
# Make changes to docs/
# Then:
git add docs/
git commit -m "Update GitHub Pages"
git push origin main
```

Site updates automatically!

## Feature Comparison

### Flask Version Has:
- ✅ Detailed sensor readings log
- ✅ CSV export
- ✅ OLED display integration
- ✅ Direct sensor hook-up
- ✅ Local database
- ✅ Dashboard with recent sessions
- ✅ Session detail view
- ✅ Basic charts

### GitHub Pages Version Has:
- ✅ Everything Flask has
- ✅ **2-week analytics dashboard** ✨
- ✅ **Community leaderboard** ✨
- ✅ **Multi-user support** ✨
- ✅ **Global accessibility** ✨
- ✅ **Real-time cloud sync** ✨
- ✅ **Mobile friendly** ✨
- ✅ **No server to maintain** ✨

## Troubleshooting Migration

### "I want to keep Flask version"
- Keep using it! Both can coexist
- Flask runs on `localhost:5000`
- GitHub Pages runs on your deployed URL

### "Can I transfer Flask data to GitHub Pages?"
- Technically yes, but complex
- Recommendation: Start fresh on GitHub Pages
- Import methods available in Firebase docs

### "Which should sensors connect to?"
- **Local testing**: Flask (easier Python integration)
- **Production/sharing**: GitHub Pages (always available)
- **Both**: Send data to both simultaneously if needed

### "How do I handle authentication?"
- **Flask**: Built-in form login
- **GitHub Pages**: Firebase handles it (better security)
- Choose based on deployment choice

## Example: Sensor Data Flow

### Flask Approach
```
Raspberry Pi Sensors
  ↓
Python (main.py)
  ↓
web_app_integration.py
  ↓
Flask Server (web_app.py)
  ↓
SQLite Database
  ↓
Web Browser (localhost:5000)
```

### GitHub Pages Approach
```
Raspberry Pi Sensors
  ↓
JavaScript (Node.js/Browser)
  ↓
Firebase SDK
  ↓
Firestore Database
  ↓
Web Browser (github.io)
```

## Recommendation

### For Development/Testing
1. Use **Flask** version first
2. Test with simulated sensor data via `run_demo.py`
3. Verify everything works locally

### For Production/Sharing
1. Use **GitHub Pages** version
2. Share URL with friends/team
3. Compare scores on leaderboard
4. Let GitHub handle hosting

### For Best of Both
1. Set up both versions
2. Flask for local sensor development
3. GitHub Pages for sharing/community
4. Export data between them as needed

## Files You Need

### To Use Flask Version
```
web_app.py
web_app_integration.py
run_demo.py
requirements.txt
templates/
static/
```

### To Use GitHub Pages Version
```
docs/
  ├── index.html
  ├── app.js
  ├── styles.css
  ├── README.md
  └── SETUP.md
```

## Security Considerations

### Flask Version
- Local only → No internet exposure
- SQLite passwords in plaintext
- Good for development

### GitHub Pages Version
- Public on internet
- Firebase handles encryption
- Use security rules (see SETUP.md)
- Better for production

## Questions?

### "Do I need to choose?"
No! Keep both. Flask for development, GitHub Pages for deployment.

### "Which is easier?"
GitHub Pages - less setup, automatic deployment.

### "Which is more scalable?"
GitHub Pages - Firebase handles unlimited users.

### "Which costs more?"
Both free! Flask uses free hosting, GitHub Pages is free, Firebase has free tier.

---

**Summary**: You now have two powerful options! Use Flask for local testing, GitHub Pages for sharing with the world. 🚀
