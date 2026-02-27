# Firebase Configuration Template

## Instructions

1. **Create Firebase Project** (Free!)
   - Go to: https://console.firebase.google.com
   - Click "Add Project"
   - Name: `PostureHealthTracker`
   - Accept defaults
   - Click "Create project"

2. **Get Your Configuration**
   - In Firebase Console, click the **Web icon** (</> button)
   - Register app with any name
   - Copy the config object below

3. **Fill in the Values Below**

```javascript
// Copy-paste this into docs/app.js (replace the firebaseConfig object)
const firebaseConfig = {
    apiKey: "COPY_YOUR_API_KEY_HERE",
    authDomain: "your-project-id.firebaseapp.com",
    projectId: "your-project-id",
    storageBucket: "your-project-id.appspot.com",
    messagingSenderId: "123456789012",
    appId: "1:123456789012:web:abcdef1234567890"
};
```

## Where to Find Each Value in Firebase Console

After you click "Register app", you'll see a code box like this:

```javascript
const firebaseConfig = {
  apiKey: "AIzaSyDOCAbC1234567890abcdefghijklmnopqrs",
  authDomain: "my-project-12345.firebaseapp.com",
  projectId: "my-project-12345",
  storageBucket: "my-project-12345.appspot.com",
  messagingSenderId: "123456789012",
  appId: "1:123456789012:web:1a2b3c4d5e6f7g8h"
};
```

**Copy the entire object above** and paste into `docs/app.js` 

## After Firebase Setup

Once you have your config:

1. Open `docs/app.js`
2. Find line 1-8 with `firebaseConfig`
3. Replace the entire object with your values
4. Save the file
5. Commit: `git add docs/app.js && git commit -m "Update Firebase config"`
6. Push: `git push origin main`

## Enable Features in Firebase

After creating your project, enable these in Firebase Console:

### 1. Authentication
- Go to **Authentication** tab
- Click **"Sign-in method"**
- Enable **"Email/Password"**
- Click **Save**

### 2. Firestore Database
- Go to **Firestore Database** tab
- Click **"Create database"**
- Select **"Start in test mode"** (for development)
- Choose location (default is fine)
- Click **"Create"**

### 3. Security Rules (Optional for now)
Copy this into Firestore Rules tab:

```firestore
rules_version = '2';
service cloud.firestore {
  match /databases/{database}/documents {
    // Anyone can read public data
    match /users/{document=**} {
      allow read: if true;
      allow write: if request.auth.uid == resource.data.userId;
    }
    
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

## Testing After Setup

1. Open your GitHub Pages site: `https://YOUR_USERNAME.github.io/PostureHealthTracker`
2. Click **"Register"**
3. Create test account:
   - Email: `test@example.com`
   - Password: `Test123!`
   - Username: `testuser`
4. Click **"Create Account"**
5. Click **"Start Session"**
6. Check "My Sessions" tab
7. Switch to "2-Week Analytics" (should show chart)
8. Switch to "Community Leaderboard"

## Troubleshooting

**"Firebase is not defined"**
- Check browser console (F12)
- Make sure Firebase scripts loaded
- Check your config is correct

**"Permission denied" errors**
- Verify Firestore Database is created
- Check security rules are applied
- Try "Test Mode" first (allows all reads/writes)

**No sessions appearing**
- Check you're logged in
- Click "Start Session" at least once
- Wait 5 seconds for data
- Refresh page

**Can't login**
- Verify authentication is enabled in Firebase
- Email/Password method must be ON
- Try creating new account first (register)

## Quick Checklist

- [ ] Created Firebase project
- [ ] Got API credentials/config
- [ ] Updated `docs/app.js` with config
- [ ] Enabled Email/Password authentication
- [ ] Created Firestore Database
- [ ] Pushed to GitHub (`git push`)
- [ ] Enabled GitHub Pages (Settings → Pages → main branch, /docs folder)
- [ ] Waited 1-2 minutes for site to build
- [ ] Visited GitHub Pages URL
- [ ] Tested registration
- [ ] Tested starting a session
- [ ] Viewed session details

## Firebase Free Tier Includes

✅ 100 concurrent users
✅ 50,000 reads/day  
✅ 20,000 writes/day
✅ 1 GB storage
✅ All you need for personal use!

## Questions?

Refer to:
- `docs/SETUP.md` - Detailed setup
- `GITHUB_PAGES_GUIDE.md` - Architecture guide
- Firebase docs: https://firebase.google.com/docs

---

Once you complete these steps, your app will be live online! 🎉
