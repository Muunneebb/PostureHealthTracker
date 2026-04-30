# PostureHealthTracker - GitHub Pages Edition

## What Changed?

### Before (Flask Web App)
- ❌ Requires server (Flask) to run
- ❌ Can't deploy to GitHub Pages
- ❌ Local SQLite database
- ❌ Single-user (local development only)

### Now (GitHub Pages Edition)
- ✅ No server needed
- ✅ Runs entirely in browser
- ✅ Global cloud database (Firebase)
- ✅ Multi-user with authentication
- ✅ Accessible from anywhere
- ✅ Realtime data sync

## File Structure

```
docs/
├── index.html          # Main UI
├── app.js              # Firebase logic & app code
├── styles.css          # Styling
├── SETUP.md            # Setup instructions
└── README.md           # This file
```

## Quick Start

1. **Firebase Setup** (5 minutes)
   - Create Firebase project
   - Get API credentials
   - Update `app.js` with your config

2. **Deploy** (2 minutes)
   - Push to GitHub `main` branch
   - Enable GitHub Pages in settings
   - Site goes live at `https://username.github.io/PostureHealthTracker`

3. **Use**
   - Register account
   - Start tracking sessions
   - View 2-week analytics
   - Compare with community

## Features

### Authentication
- Email/password login
- Secure Firebase authentication
- Encrypted passwords

### Session Tracking
- Start new monitoring sessions
- Simulated sensor data (30 seconds)
- Store all session metrics
- View history anytime

### Personal Analytics
- 2-week performance chart
- Best/worst/average scores
- Session count statistics
- Total sitting time

### Community Features
- Global leaderboard (last 2 weeks)
- Rank by average score
- See other users' stats
- Community average comparison

## Data Privacy

- Firebase encrypts all data in transit (HTTPS)
- Each user can only see their own sessions
- Leaderboard shows anonymized aggregate stats
- Firebase handles all authentication securely

## Detailed Steps

### Step 1: Firebase Project Creation
1. Visit [console.firebase.google.com](https://console.firebase.google.com)
2. Click "Add project"
3. Name: `PostureHealthTracker`
4. Follow the wizard (accept defaults)

### Step 2: Web App Configuration
1. In Firebase, click the Web icon (</> button)
2. Register a new web app
3. Copy the entire config object

### Step 3: Update Configuration
1. Open `docs/app.js`
2. Replace the `firebaseConfig` object with yours
3. Save the file

Example config (YOUR VALUES WILL DIFFER):
```javascript
const firebaseConfig = {
    apiKey: "AIzaSy3FjV2J9n4k7L5M6O7P8q9R0S1T2u3V4W5X",
    authDomain: "posture-tracker-abc123.firebaseapp.com",
    projectId: "posture-tracker-abc123",
    storageBucket: "posture-tracker-abc123.appspot.com",
    messagingSenderId: "123456789012",
    appId: "1:123456789012:web:abcdef123456789"
};
```

### Step 4: GitHub Pages Deployment
1. Push changes to GitHub
2. Go to repository Settings
3. Go to Pages section
4. Source: Select `main` branch and `/docs` folder
5. Save
6. Wait 1-2 minutes for site to build

### Step 5: Enable Firestore
1. In Firebase Console, go to Firestore Database
2. Click "Create Database"
3. Select "Test Mode" to start
4. Choose region (default is fine)
5. Create

### Step 6: Enable Authentication
1. In Firebase Console, go to Authentication
2. Go to "Sign-in method"
3. Enable "Email/Password"
4. Save

## Testing the App

### Test User Account
1. Visit your GitHub Pages URL
2. Click "Register"
3. Enter test email: `test@example.com`
4. Enter password: `Test123!`
5. Enter username: `testuser`
6. Click "Create Account"

### Generate Test Data
1. Once logged in, click "Start Session"
2. App generates 30 seconds of sample data
3. Check "My Sessions" tab to see it
4. Click on a session to view details

### View Analytics
1. Switch to "2-Week Analytics" tab
2. See chart of your session scores
3. View best/worst/average statistics

### Check Leaderboard
1. Go to "Community Leaderboard"
2. See all users ranked by their 2-week average
3. Compare your score to others

## Connecting Real Sensors

To use real sensor data instead of simulated:

1. In `docs/app.js`, find `simulateSessionData()` function
2. Replace the sensor reading generation with your actual data:

```javascript
async function sendRealSensorReading() {
    const reading = {
        timestamp: new Date(),
        pitch: await getRealPitch(),       // Your sensor
        roll: await getRealRoll(),         // Your sensor
        fsrLeft: await getFsrLeft(),       // Your sensor
        fsrRight: await getFsrRight(),     // Your sensor
        fsrCenter: await getFsrCenter(),   // Your sensor
        stressScore: calculateStress(),    // Your calculation
        seated: true,
        buzzerTriggered: checkBuzzer()     // Your sensor
    };
    
    // Send to Firestore
    await db.collection('sessions')
        .doc(currentSessionId)
        .collection('readings')
        .add(reading);
}
```

## Firebase Pricing

**Free Tier Includes:**
- 100 concurrent users
- 50,000 reads/day
- 20,000 writes/day
- 1 GB stored data

For personal use, the free tier is more than sufficient!

## Architecture Comparison

| Feature | Flask (Old) | GitHub Pages (New) |
|---------|------------|------------------|
| Hosting | Local server | GitHub Pages (free) |
| Database | SQLite (local) | Firebase Firestore (cloud) |
| Auth | Session-based | Firebase Auth |
| Cost | Free | Free |
| Scalability | Single user | Multi-user global |
| Deployment | Manual | Automatic (Git push) |
| 2-Week Analytics | Yes | Yes (better!) |
| Community Stats | No | Yes ✨ |
| Real-time Sync | No | Yes ✨ |
| Mobile Access | No | Yes ✨ |

## Troubleshooting

### "Can't login"
- Check email format is correct
- Password minimum 6 characters
- Check browser console (F12) for errors

### "No sessions showing"
- Make sure you're logged in
- Click "Start Session" to generate data
- Check Firebase is created and enabled
- Verify security rules are set to test mode

### "Chart not loading"
- Check Internet connection
- Verify Chart.js CDN is accessible
- Try refreshing page

### "GitHub Pages not updating"
- Check branch is set to `main`
- Folder is set to `/docs`
- Wait 2 minutes for GitHub to rebuild

## Security Notes

### For Development (Current)
- Firestore in "Test Mode" allows everyone to read/write
- Good for getting started
- Not suitable for production

### For Production (Later)
- Update Firestore security rules
- Use custom authentication domain
- Add HTTPS certificate (GitHub does this auto)
- Monitor usage and set billing alerts

Sample production rules:

```firestore
match /sessions/{sessionId} {
  allow read: if true;  // Anyone can read sessions
  allow create: if request.auth.uid != null;  // Only logged in users can create
  allow write: if request.auth.uid == resource.data.userId;  // Only owner can edit
}
```

## Files Summary

| File | Purpose | You Edit? |
|------|---------|-----------|
| `index.html` | Main UI/layout | No |
| `app.js` | Firebase config & logic | Only config! |
| `styles.css` | Styling | Optional |
| `SETUP.md` | Setup guide | No |
| `README.md` | This file | No |

## Next Steps

1. ✅ Follow SETUP.md for Firebase setup
2. ✅ Update Firebase config in app.js
3. ✅ Deploy to GitHub Pages
4. ✅ Create test account and verify it works
5. ⭕ If using real sensors, modify `simulateSessionData()` function
6. ⭕ Customize styles in `styles.css`
7. ⭕ Add production security rules to Firestore

## Support

If you have questions:
1. Check Firebase console for errors
2. Open browser DevTools (F12) and check console
3. Review SETUP.md for step-by-step instructions
4. Check firestore.google.com docs

Happy posture tracking! 🎉
