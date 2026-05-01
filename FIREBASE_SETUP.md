# Firebase Setup Guide

**Required to get the Posture Tracker working end-to-end**

## 1. Create Firebase Project

1. Go to https://console.firebase.google.com
2. Click **Create a new project**
3. Name: `posturehealthtracker`
4. Accept terms, create project
5. Skip Google Analytics (optional)

## 2. Enable Realtime Database

1. In Firebase Console, go to **Build → Realtime Database**
2. Click **Create Database**
3. **Location:** Closest region to you (default OK)
4. **Security Rules:** Start in **Test Mode** (we'll fix this next)
5. Click **Enable**

## 3. Enable Firestore

1. Go to **Build → Firestore Database**
2. Click **Create database**
3. **Location:** Same as above
4. **Security Rules:** Start in **Test Mode**
5. Click **Enable**

## 4. Set Security Rules (IMPORTANT!)

Go to **Build → Realtime Database → Rules** tab:

```json
{
  "rules": {
    "system_state": {
      ".read": true,
      ".write": "root.child('users').child(auth.uid).exists()"
    },
    "live_data": {
      ".read": true,
      ".write": "root.child('users').child(auth.uid).exists()"
    },
    "users": {
      "$uid": {
        ".read": "auth.uid === $uid",
        ".write": "auth.uid === $uid"
      }
    }
  }
}
```

This allows:
- Anyone to READ system_state and live_data
- Authenticated users to WRITE system_state and live_data
- Users to read/write their own profile

Click **Publish**

## 5. Set Firestore Rules

Go to **Build → Firestore Database → Rules** tab:

```javascript
rules_version = '2';
service cloud.firestore {
  match /databases/{database}/documents {
    match /sessions/{document=**} {
      allow read, write: if request.auth != null;
    }
    match /users/{uid}/{document=**} {
      allow read, write: if request.auth.uid == uid;
    }
  }
}
```

Click **Publish**

## 6. Enable Authentication

1. Go to **Build → Authentication → Sign-in method**
2. Click **Email/Password**
3. Enable **Email/Password** (keep "Email link" disabled)
4. Click **Save**

## 7. Get Firebase Config

1. Go to **Project Settings** (gear icon)
2. Copy your Firebase config
3. Paste into `docs/index.html` (look for `firebaseConfig` object)

The config already exists in index.html, but verify it matches your project.

## 8. Create a Test User

1. Go to **Build → Authentication → Users**
2. Click **Add user**
3. Email: `test@example.com`
4. Password: `Test123!`  (min 6 chars)
5. Click **Add user**

## 9. Test the Full Flow

### On Dashboard (Browser)

1. Open: https://muunneebb.github.io/PostureHealthTracker/docs/index.html
2. Click **Sign in**
3. Use `test@example.com` / `Test123!`
4. Click **Start Monitoring**
5. You should see:
   - Camera status changes to "active"
   - Status dot turns green

### On Raspberry Pi

```bash
# Pull latest code
git pull origin main

# Run the hardware loop
cd hardware
python3 src/main.py
```

You should see:
```
[Pi] Hardware Booted. Connecting to Firebase...
[Pi] Waiting for camera_command from dashboard...
[Pi] ✓ START command received. Session: session_XXXXX
[Pi] ✓ Camera is ready
[Pi] Frame captured and analyzed...
```

### Back on Dashboard

- Camera preview should update every 2 seconds
- Score bar should show current posture score
- Metrics should display live data

## Troubleshooting

### Dashboard shows "Permission denied" error

**Solution:** Check Firestore and RTDB security rules. They should be set to the rules above, not "Test Mode" (which auto-rejects after 30 days).

### Pi says "STOP command" immediately after START

**Solution:** Firebase rules probably blocking writes. Verify rules above are published correctly.

### Camera doesn't start on Pi

Check:
1. Pi can reach Firebase: `curl -I https://posturehealthtracker-default-rtdb.firebaseio.com`
2. Camera is enabled: `vcgencmd get_camera`
3. Read Pi logs: `python3 hardware/src/main.py 2>&1 | head -30`

### Slow network (300ms+ latency)

The code handles this - timeouts are set to 30 seconds. But if network is really bad:
1. Edit `hardware/src/main.py`
2. Change timeout values: `timeout=60` (60 seconds)
3. Restart loop

### Firebase rules won't publish

Common issues:
- Syntax error (check JSON/JavaScript validity)
- Missing semicolon in Firestore rules
- Make sure you're in the right project

## Production Checklist

- [ ] Security rules configured (not Test Mode)
- [ ] Test user created
- [ ] Dashboard login works
- [ ] Pi can reach Firebase
- [ ] Camera starts when clicking "Start Monitoring"
- [ ] Live data updates on dashboard
- [ ] Sessions saved to Firestore after stop

## Support

If still having issues:
1. Check browser console (F12 → Console)
2. Check Pi output: `tail -50 hardware.log`
3. Verify Firebase config in `docs/index.html` matches your project
4. Check user has correct email/password

---

**Next:** Once everything works, see [DEPLOYMENT.md](DEPLOYMENT.md) for production setup
