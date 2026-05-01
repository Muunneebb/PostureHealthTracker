# GitHub Pages Edition - Setup Guide

This is a **fully browser-based** version of PostureHealthTracker that runs on **GitHub Pages** with **Firebase** for authentication and data storage.

## Architecture

```
GitHub Pages (Static Files)
    ↓
Firebase Authentication (Login)
    ↓
Firestore Database (User Data)
    ↓
Browser JavaScript (Real-time Sync)
```

## Features

✅ **User Login/Registration** - Secure authentication with Firebase
✅ **Personal Session History** - All your posture sessions stored  
✅ **2-Week Analytics** - Charts showing your last 2 weeks performance
✅ **Community Leaderboard** - See how you rank vs other users
✅ **Community Average** - Compare your score to community average
✅ **Real-time Data Sync** - All changes sync instantly across devices

## Prerequisites

1. GitHub account (for hosting)
2. Google account (for Firebase)
3. 5 minutes to set up Firebase

## Step-by-Step Setup

### 1. Create Firebase Project

1. Go to [Firebase Console](https://console.firebase.google.com)
2. Click **"Add project"**
3. Name it: `PostureHealthTracker`
4. Click **"Create project"**
5. Wait for project to be created

### 2. Configure Firebase

1. In Firebase Console, click **"Web"** icon to add web app
2. Give it a name: `PostureHealthTracker Web`
3. Click **"Register app"**
4. Copy the config object (you'll need this next)

### 3. Enable Authentication

1. In Firebase Console, go to **"Authentication"** → **"Sign-in method"**
2. Enable **"Email/Password"**
3. Click **"Save"**

### 4. Create Firestore Database

1. In Firebase Console, go to **"Firestore Database"**
2. Click **"Create database"**
3. Start in **"Test mode"** (for development)
4. Choose location and create

**Important**: Set up security rules in production!

### 5. Update Firebase Config

1. Open `docs/app.js` in your editor
2. Find the `firebaseConfig` object at the top (lines 1-8)
3. Replace with your Firebase config:

```javascript
const firebaseConfig = {
    apiKey: "YOUR_API_KEY",
    authDomain: "your-project.firebaseapp.com",
    projectId: "your-project-id",
    storageBucket: "your-project.appspot.com",
    messagingSenderId: "123456789",
    appId: "1:123456789:web:abcdef123456"
};
```

### 6. Deploy to GitHub Pages

#### Option A: Using Git (Recommended)

```bash
# If you don't have the files in git yet
cd "c:\Users\HP\OneDrive\PostureHealthTracker"
git init
git add .
git commit -m "Initial commit"
git branch -M main
git remote add origin https://github.com/YOUR_USERNAME/PostureHealthTracker.git
git push -u origin main
```

#### Option B: Configure GitHub Pages

1. Go to your GitHub repository
2. Settings → Pages
3. Under "Source", select `main` branch and `/docs` folder
4. Click **Save**
5. Your site will be live at: `https://YOUR_USERNAME.github.io/PostureHealthTracker`

### 7. First Test

1. Open your GitHub Pages URL: `https://YOUR_USERNAME.github.io/PostureHealthTracker`
2. Click **"Register"**
3. Create an account with any email
4. Start a session and verify data appears

## How to Use

### Personal Dashboard

- **Stats Cards**: Shows your total sessions, 2-week average, total sitting time
- **Start Session**: Generates 30 seconds of simulated sensor data
- **My Sessions**: View all your past sessions
- **2-Week Analytics**: Chart of your last 2 weeks with statistics
- **Community Leaderboard**: See top performers by average score

### Sensor Integration

To connect real sensors, modify the `simulateSessionData()` function in `docs/app.js` to send your actual sensor readings instead of simulated data.

Example with real sensor data:

```javascript
const reading = {
    timestamp: new Date(),
    pitch: imuData.pitch,          // Your IMU pitch
    roll: imuData.roll,            // Your IMU roll
    fsrLeft: ads.readFsrLeft(),    // Your FSR left
    fsrRight: ads.readFsrRight(),  // Your FSR right
    fsrCenter: ads.readFsrCenter(),// Your FSR center
    stressScore: calculateStress(),// Your stress calculation
    seated: true,
    buzzerTriggered: buzzerSignal
};
```

## Data Structure

### Users Collection

```
/users/{userId}
  ├── username: string
  ├── email: string
  ├── createdAt: timestamp
  ├── totalSessions: number
  └── totalSittingTime: number
```

### Sessions Collection

```
/sessions/{sessionId}
  ├── userId: string
  ├── startTime: timestamp
  ├── endTime: timestamp
  ├── sessionScore: number (0-1)
  ├── sitDuration: number (seconds)
  ├── buzzerCount: number
  └── /readings/{readingId}
      ├── timestamp: timestamp
      ├── pitch: number
      ├── roll: number
      ├── stressScore: number
      ├── fsrLeft, fsrRight, fsrCenter: numbers
      └── buzzerTriggered: boolean
```

## Features Explained

### 2-Week Analytics Tab

Shows:
- **Line Chart**: Session scores over last 14 days
- **Best Score**: Highest score in the period
- **Worst Score**: Lowest score in the period
- **Average**: Mean of all session scores
- **Session Count**: Total sessions in last 2 weeks

### Community Leaderboard

Ranks users by:
1. **Average Score** - Primary ranking metric
2. **Session Count** - Number of sessions in last 2 weeks
3. **Total Time** - Hours of sitting tracked
4. **Community Avg** - Overall community average score

Leaderboard filters data from last 2 weeks only.

## Troubleshooting

### "Firebase is not defined"

Make sure Firebase script is loaded:
```html
<script src="https://www.gstatic.com/firebasejs/10.7.1/firebase-app.js"></script>
<!-- All other Firebase scripts... -->
```

### "Permission denied" errors

Your Firestore security rules need updating:

```firestore
rules_version = '2';
service cloud.firestore {
  match /databases/{database}/documents {
    // Anyone can read user profiles
    match /users/{document=**} {
      allow read: if true;
      allow write: if request.auth.uid == resource.data.userId;
    }
    
    // Users can only write their own sessions
    match /sessions/{sessionId} {
      allow read: if true;
      allow create: if request.auth.uid != null;
      allow write: if request.auth.uid == resource.data.userId;
      
      match /readings/{readingId} {
        allow read: if true;
        allow write: if request.auth.uid == get(/databases/$(database)/documents/sessions/$(sessionId)).data.userId;
      }
    }
  }
}
```

### Sessions won't show up

1. Make sure you're logged in
2. Check browser console (F12) for errors
3. Verify Firebase config is correct
4. Check Firestore Database has rules allowing reads

### Chart not displaying

Make sure Chart.js loaded:
```html
<script src="https://cdn.jsdelivr.net/npm/chart.js"></script>
```

## Production Deployment

For production, you should:

1. **Update Security Rules** - See "Troubleshooting" section above
2. **Enable HTTPS** - GitHub Pages automatically uses HTTPS
3. **Add Custom Domain** - Configure in GitHub Pages settings
4. **Monitor Firestore Usage** - Watch your free tier quotas
5. **Add Terms & Privacy Policy** - Required for user data collection

## API References

- [Firebase Web SDK Docs](https://firebase.google.com/docs/web)
- [Firestore Documentation](https://firebase.google.com/docs/firestore)
- [Firebase Authentication](https://firebase.google.com/docs/auth)

## Next Steps

1. ✅ Create Firebase project
2. ✅ Configure authentication
3. ✅ Set up Firestore database
4. ✅ Update Firebase config in app.js
5. ✅ Deploy to GitHub Pages
6. ⭕ Test with real sensor data
7. ⭕ Customize appearance
8. ⭕ Add more analytics

## Support

For issues:
1. Check browser console (F12) for errors
2. Review Firebase console logs
3. Verify all config values
4. Check Firestore security rules
5. Review GitHub Pages deployment settings

Enjoy tracking your posture! 🎉
