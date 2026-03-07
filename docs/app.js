const firebaseConfig = {
    apiKey: "AIzaSyDhVpz_D9OTfckaLA792N0c-bqmGnBd7G4",
    authDomain: "posturehealthtracker.firebaseapp.com",
    projectId: "posturehealthtracker",
    storageBucket: "posturehealthtracker.firebasestorage.app",
    messagingSenderId: "330967946233",
    appId: "1:330967946233:web:995732d6b544e67a46e328",
    measurementId: "G-5YG2GL2W9Z"
};

firebase.initializeApp(firebaseConfig);
const auth = firebase.auth();
const db = firebase.firestore();

let currentUser = null;
let chart = null;
let activeSessionInterval = null; 
let currentActiveSessionId = null; 
const POSTURE_ALERT_SCORE_PENALTY = 0.01;

function getSessionScore(session) {
    const postureAlerts = session?.postureAlertCount ?? session?.buzzerCount ?? 0;
    const rawScore = session?.sessionScore;

    // Legacy fallback: old sessions were initialized at 0 with zero alerts.
    if (typeof rawScore === 'number') {
        if (rawScore <= 0 && postureAlerts === 0) {
            return 1.0;
        }
        return Math.max(0, Math.min(1, rawScore));
    }

    if (postureAlerts > 0) {
        return Math.max(0, 1.0 - (postureAlerts * POSTURE_ALERT_SCORE_PENALTY));
    }

    return 1.0;
}

document.addEventListener('DOMContentLoaded', () => {
    auth.onAuthStateChanged(user => {
        if (user) {
            currentUser = user;
            showDashboard();
            loadUserData();
        } else {
            showAuthPage();
        }
    });
});

function toggleForm() {
    document.getElementById('loginForm').style.display = 
        document.getElementById('loginForm').style.display === 'none' ? 'block' : 'none';
    document.getElementById('registerForm').style.display = 
        document.getElementById('registerForm').style.display === 'none' ? 'block' : 'none';
    
    document.getElementById('loginError').classList.remove('show');
    document.getElementById('registerError').classList.remove('show');
}

async function login() {
    const email = document.getElementById('loginEmail').value;
    const password = document.getElementById('loginPassword').value;
    const errorDiv = document.getElementById('loginError');

    errorDiv.classList.remove('show');

    if (!email || !password) {
        errorDiv.textContent = 'Please fill in all fields.';
        errorDiv.classList.add('show');
        return;
    }

    try {
        await auth.signInWithEmailAndPassword(email, password);
    } catch (error) {
        if (error.code === 'auth/wrong-password' || error.code === 'auth/user-not-found' || error.code === 'auth/invalid-credential') {
            errorDiv.textContent = 'Invalid email or password. Please try again.';
        } else {
            errorDiv.textContent = error.message;
        }
        errorDiv.classList.add('show');
    }
}

async function register() {
    const email = document.getElementById('registerEmail').value;
    const password = document.getElementById('registerPassword').value;
    const username = document.getElementById('registerUsername').value;
    const errorDiv = document.getElementById('registerError');

    errorDiv.classList.remove('show');

    if (!email || !password || !username) {
        errorDiv.textContent = 'Please fill in all fields.';
        errorDiv.classList.add('show');
        return;
    }

    if (password.length < 6) {
        errorDiv.textContent = 'Password must be at least 6 characters.';
        errorDiv.classList.add('show');
        return;
    }

    try {
        const result = await auth.createUserWithEmailAndPassword(email, password);
        
        await db.collection('users').doc(result.user.uid).set({
            username: username,
            email: email,
            createdAt: new Date(),
            totalSessions: 0,
            totalSittingTime: 0
        });

        currentUser = result.user;
        showDashboard();
    } catch (error) {
        if (error.code === 'auth/email-already-in-use') {
            errorDiv.textContent = 'An account with this email already exists.';
        } else {
            errorDiv.textContent = error.message;
        }
        errorDiv.classList.add('show');
    }
}

function logout() {
    if (activeSessionInterval) {
        clearInterval(activeSessionInterval);
        activeSessionInterval = null;
    }
    currentActiveSessionId = null;

    auth.signOut().then(() => {
        document.getElementById('loginEmail').value = '';
        document.getElementById('loginPassword').value = '';
        showAuthPage();
    });
}

function showAuthPage() {
    document.getElementById('authPage').style.display = 'block';
    document.getElementById('dashboardPage').style.display = 'none';
}

function showDashboard() {
    document.getElementById('authPage').style.display = 'none';
    document.getElementById('dashboardPage').style.display = 'block';
    
    db.collection('users').doc(currentUser.uid).get().then(doc => {
        if (doc.exists) {
            document.getElementById('userDisplayName').textContent = doc.data().username;
        } else {
            document.getElementById('userDisplayName').textContent = currentUser.email.split('@')[0];
        }
    });
}

function switchTab(tab, button) {
    document.querySelectorAll('.tab-content').forEach(el => {
        el.classList.remove('active');
        el.style.display = 'none';
    });
    document.querySelectorAll('.tab-btn').forEach(el => {
        el.classList.remove('active');
    });

    const selectedTab = document.getElementById(tab + 'Tab');
    selectedTab.classList.add('active');
    selectedTab.style.display = 'block';
    if (button) {
        button.classList.add('active');
    }

    if (tab === 'analytics') {
        loadAnalytics();
    }
}

async function startNewSession() {
    document.getElementById('startSessionBtn').style.display = 'none';
    document.getElementById('stopSessionBtn').style.display = 'inline-block';

    const sessionData = {
        userId: currentUser.uid,
        startTime: new Date(),
        endTime: null,
        readings: [],
        sessionScore: 1.0,
        sitDuration: 0,
        buzzerCount: 0,
        postureAlertCount: 0,
        breakAlertCount: 0
    };

    try {
        const docRef = await db.collection('sessions').add(sessionData);
        currentActiveSessionId = docRef.id;
        simulateSessionData(docRef.id);
        loadUserData();
    } catch (error) {
        console.error('Error starting session:', error);
        document.getElementById('startSessionBtn').style.display = 'inline-block';
        document.getElementById('stopSessionBtn').style.display = 'none';
    }
}

async function stopSession() {
    if (!currentActiveSessionId) return;

    if (activeSessionInterval) {
        clearInterval(activeSessionInterval);
        activeSessionInterval = null;
    }

    try {
        await db.collection('sessions').doc(currentActiveSessionId).update({
            endTime: new Date()
        });
        
        document.getElementById('startSessionBtn').style.display = 'inline-block';
        document.getElementById('stopSessionBtn').style.display = 'none';
        
        currentActiveSessionId = null;
        loadUserData();
    } catch (error) {
        console.error('Error stopping session:', error);
    }
}

function simulateSessionData(sessionId) {
    let readingCount = 0;
    
    activeSessionInterval = setInterval(async () => {
        readingCount++;
        
        const reading = {
            timestamp: new Date(),
            pitch: 15 + Math.random() * 10,
            roll: Math.random() * 10 - 5,
            fsrLeft: 45000 + Math.random() * 5000,
            fsrRight: 48000 + Math.random() * 5000,
            fsrCenter: 50000 + Math.random() * 3000,
            stressScore: 0.5 + Math.random() * 0.3,
            seated: true,
            buzzerTriggered: Math.random() < 0.1
        };

        try {
            await db.collection('sessions').doc(sessionId).collection('readings').add(reading);
        } catch (error) {
            console.error('Error adding reading:', error);
        }

        if (readingCount >= 3600) {
            stopSession();
        }
    }, 1000);
}

async function deleteSession(event, sessionId) {
    if (event) {
        event.stopPropagation();
    }

    if (confirm("Are you sure you want to permanently delete this session?")) {
        try {
            const readings = await db.collection('sessions').doc(sessionId).collection('readings').get();
            const batch = db.batch();
            readings.forEach(doc => batch.delete(doc.ref));
            
            batch.delete(db.collection('sessions').doc(sessionId));
            await batch.commit();

            closeSessionModal();
            loadUserData(); 
        } catch(error) {
            console.error("Error deleting session:", error);
            alert("Failed to delete session.");
        }
    }
}

async function loadUserData() {
    try {
        const sessionsSnapshot = await db.collection('sessions')
            .where('userId', '==', currentUser.uid)
            .orderBy('startTime', 'desc')
            .get();

        let totalSessions = 0;
        let totalSitting = 0;
        let totalScore = 0;
        let scoreSampleCount = 0;
        let recentSessions = [];
        let activeSession = null;

        const currentSessionList = document.getElementById('currentSessionList');
        const previousSessionsList = document.getElementById('previousSessionsList');
        
        if(currentSessionList) currentSessionList.innerHTML = '';
        if(previousSessionsList) previousSessionsList.innerHTML = '';

        sessionsSnapshot.forEach(doc => {
            const session = doc.data();
            const startTime = session.startTime.toDate();
            const endTime = session.endTime ? session.endTime.toDate() : new Date();
            const duration = (endTime - startTime) / 1000;
            const normalizedScore = getSessionScore(session);
            
            if (session.endTime) {
                totalSessions++;
                totalSitting += session.sitDuration || 0;
                totalScore += normalizedScore;
                scoreSampleCount++;
            }

            if (!session.endTime && !activeSession) {
                activeSession = {
                    ...session,
                    sessionScore: normalizedScore,
                    id: doc.id,
                    startTime: startTime,
                    duration: duration,
                };
                totalScore += normalizedScore;
                scoreSampleCount++;
            }

            if (session.endTime && recentSessions.length < 20) {
                recentSessions.push({
                    ...session,
                    sessionScore: normalizedScore,
                    id: doc.id,
                    startTime: startTime,
                    duration: duration,
                });
            }
        });

        if (activeSession) {
            document.getElementById('startSessionBtn').style.display = 'none';
            document.getElementById('stopSessionBtn').style.display = 'inline-block';
            currentActiveSessionId = activeSession.id;

            const activeScoreClass = activeSession.sessionScore >= 0.7 ? 'score-good' : 
                activeSession.sessionScore >= 0.4 ? 'score-medium' : 'score-poor';

            const activeCard = document.createElement('div');
            activeCard.className = 'session-card';
            activeCard.onclick = () => showSessionDetail(activeSession.id, activeSession);
            activeCard.innerHTML = `
                <div class="session-card-header">
                    <span class="session-card-title">Session Started at ${activeSession.startTime.toLocaleTimeString()}</span>
                    <span class="session-card-score ${activeScoreClass}">${(getSessionScore(activeSession) * 100).toFixed(0)}%</span>
                </div>
                <div class="session-card-details">
                    <div>Status: Active</div>
                    <div>Elapsed: ${Math.round(activeSession.duration / 60)}m</div>
                    <div>Alerts: ${activeSession.buzzerCount || 0}</div>
                </div>
                <div style="text-align: right; margin-top: 10px;">
                    <button onclick="deleteSession(event, '${activeSession.id}')" style="background: transparent; border: none; color: var(--danger); cursor: pointer; font-weight: 600; text-decoration: underline;">Delete Session</button>
                </div>
            `;
            if(currentSessionList) currentSessionList.appendChild(activeCard);
        } else {
            document.getElementById('startSessionBtn').style.display = 'inline-block';
            document.getElementById('stopSessionBtn').style.display = 'none';
            if(currentSessionList) currentSessionList.innerHTML = '<p class="no-data">No active session. Click Start Session to begin.</p>';
        }

        if (recentSessions.length > 0) {
            recentSessions.forEach(session => {
                const scoreClass = session.sessionScore >= 0.7 ? 'score-good' : 
                                session.sessionScore >= 0.4 ? 'score-medium' : 'score-poor';

                const card = document.createElement('div');
                card.className = 'session-card';
                card.onclick = () => showSessionDetail(session.id, session);
                card.innerHTML = `
                    <div class="session-card-header">
                        <span class="session-card-title">${session.startTime.toLocaleDateString()} at ${session.startTime.toLocaleTimeString()}</span>
                        <span class="session-card-score ${scoreClass}">${(getSessionScore(session) * 100).toFixed(0)}%</span>
                    </div>
                    <div class="session-card-details">
                        <div>Duration: ${Math.round(session.duration / 60)}m</div>
                        <div>Sitting: ${Math.round((session.sitDuration || 0) / 60)}m</div>
                        <div>Alerts: ${session.buzzerCount || 0}</div>
                    </div>
                    <div style="text-align: right; margin-top: 10px;">
                        <button onclick="deleteSession(event, '${session.id}')" style="background: transparent; border: none; color: var(--danger); cursor: pointer; font-weight: 600; text-decoration: underline;">Delete Session</button>
                    </div>
                `;
                if(previousSessionsList) previousSessionsList.appendChild(card);
            });
        } else {
            if(previousSessionsList) previousSessionsList.innerHTML = '<p class="no-data">No previous sessions available.</p>';
        }

        document.getElementById('statTotalSessions').textContent = totalSessions;
        document.getElementById('statTotalSitting').textContent = Math.floor(totalSitting / 3600) + 'h ' + Math.floor((totalSitting % 3600) / 60) + 'm';
        
        const avgScore = scoreSampleCount ? (totalScore / scoreSampleCount * 100).toFixed(0) : 0;
        document.getElementById('statAvgScore').textContent = avgScore + '%';

        window.userRecentSessions = recentSessions;

    } catch (error) {
        console.error('Error loading user data:', error);
    }
}

function loadAnalytics() {
    if (!window.userRecentSessions || window.userRecentSessions.length === 0) {
        document.getElementById('analyticsChart').style.display = 'none';
        document.getElementById('bestScore').textContent = '-';
        document.getElementById('worstScore').textContent = '-';
        document.getElementById('periodAvgScore').textContent = '-';
        document.getElementById('periodSessionCount').textContent = '0';
        return;
    }

    document.getElementById('analyticsChart').style.display = 'block';

    const sessions = window.userRecentSessions;
    const scores = sessions.map(s => getSessionScore(s) * 100);
    const dates = sessions.map(s => s.startTime.toLocaleDateString());

    const ctx = document.getElementById('analyticsChart').getContext('2d');
    
    if (chart) {
        chart.destroy();
    }

    chart = new Chart(ctx, {
        type: 'line',
        data: {
            labels: dates.reverse(),
            datasets: [{
                label: 'Session Score (%)',
                data: scores.reverse(),
                borderColor: '#7E3EAC',
                backgroundColor: 'rgba(126, 62, 172, 0.15)',
                borderWidth: 2,
                tension: 0.1, 
                fill: true,
                pointRadius: 4,
                pointBackgroundColor: '#7E3EAC',
                pointBorderColor: '#ffffff'
            }]
        },
        options: {
            responsive: true,
            maintainAspectRatio: true,
            plugins: {
                title: { display: false },
                legend: { labels: { color: '#ffffff', font: { family: 'Segoe UI', size: 14 } } }
            },
            scales: {
                y: { 
                    min: 0, max: 100, 
                    ticks: { color: '#94a3b8', font: { family: 'Segoe UI' } }, 
                    grid: { color: '#2d2d35' } 
                },
                x: { 
                    ticks: { color: '#94a3b8', font: { family: 'Segoe UI' } }, 
                    grid: { color: '#2d2d35' } 
                }
            }
        }
    });

    if (scores.length > 0) {
        document.getElementById('bestScore').textContent = Math.max(...scores).toFixed(0) + '%';
        document.getElementById('worstScore').textContent = Math.min(...scores).toFixed(0) + '%';
        document.getElementById('periodAvgScore').textContent = (scores.reduce((a, b) => a + b) / scores.length).toFixed(0) + '%';
        document.getElementById('periodSessionCount').textContent = scores.length;
    }
}

function showSessionDetail(sessionId, session) {
    const modal = document.getElementById('sessionModal');
    const title = document.getElementById('sessionModalTitle');
    const body = document.getElementById('sessionModalBody');

    const startTime = session.startTime && typeof session.startTime.toDate === 'function' ? session.startTime.toDate() : new Date(session.startTime);
    const endTime = session.endTime ? (typeof session.endTime.toDate === 'function' ? session.endTime.toDate() : new Date(session.endTime)) : new Date();
    const duration = (endTime - startTime) / 1000;

    title.textContent = `Session Details`;
    body.innerHTML = `
        <div class="session-detail">
            <div class="stat-row cyber-row">
                <span>Date & Time:</span>
                <span class="neon-text">${startTime.toLocaleString()}</span>
            </div>
            <div class="stat-row cyber-row">
                <span>Total Duration:</span>
                <span class="neon-text">${Math.round(duration / 60)}m</span>
            </div>
            <div class="stat-row cyber-row">
                <span>Posture Score:</span>
                <span class="neon-text">${(getSessionScore(session) * 100).toFixed(0)}%</span>
            </div>
            <div class="stat-row cyber-row">
                <span>Time Sitting:</span>
                <span class="neon-text">${Math.round((session.sitDuration || 0) / 60)}m</span>
            </div>
            <div class="stat-row cyber-row">
                <span>Alerts Triggered:</span>
                <span class="neon-text">${session.buzzerCount || 0}</span>
            </div>
            <button onclick="deleteSession(event, '${sessionId}')" class="btn btn-danger" style="margin-top: 20px; width: 100%;">Delete Session</button>
        </div>
    `;

    modal.style.display = 'flex';
}

function closeSessionModal() {
    document.getElementById('sessionModal').style.display = 'none';
}

window.onclick = function(event) {
    const modal = document.getElementById('sessionModal');
    const changePasswordModal = document.getElementById('changePasswordModal');
    const deleteAccountModal = document.getElementById('deleteAccountModal');
    
    if (event.target == modal) { modal.style.display = 'none'; }
    if (event.target == changePasswordModal) { closeChangePassword(); }
    if (event.target == deleteAccountModal) { closeDeleteAccount(); }
    
    const userDropdown = document.getElementById('userDropdown');
    const userMenuBtn = document.querySelector('.user-menu-btn');
    if (userMenuBtn && !userMenuBtn.contains(event.target) && !userDropdown.contains(event.target)) {
        userDropdown.classList.remove('show');
    }
}

function toggleUserMenu() {
    document.getElementById('userDropdown').classList.toggle('show');
}

function showChangePassword() {
    document.getElementById('userDropdown').classList.remove('show');
    document.getElementById('changePasswordModal').style.display = 'flex';
    document.getElementById('currentPassword').value = '';
    document.getElementById('newPassword').value = '';
    document.getElementById('confirmNewPassword').value = '';
    document.getElementById('changePasswordError').classList.remove('show');
    document.getElementById('changePasswordSuccess').classList.remove('show');
}

function closeChangePassword() {
    document.getElementById('changePasswordModal').style.display = 'none';
}

async function changePassword() {
    const currentPassword = document.getElementById('currentPassword').value;
    const newPassword = document.getElementById('newPassword').value;
    const confirmPassword = document.getElementById('confirmNewPassword').value;
    const errorDiv = document.getElementById('changePasswordError');
    const successDiv = document.getElementById('changePasswordSuccess');
    
    errorDiv.classList.remove('show');
    successDiv.classList.remove('show');
    
    if (!currentPassword || !newPassword || !confirmPassword) {
        errorDiv.textContent = 'Please fill in all fields.';
        errorDiv.classList.add('show');
        return;
    }
    
    if (newPassword.length < 6) {
        errorDiv.textContent = 'New password must be at least 6 characters.';
        errorDiv.classList.add('show');
        return;
    }
    
    if (newPassword !== confirmPassword) {
        errorDiv.textContent = 'New passwords do not match.';
        errorDiv.classList.add('show');
        return;
    }
    
    try {
        const credential = firebase.auth.EmailAuthProvider.credential(currentUser.email, currentPassword);
        await currentUser.reauthenticateWithCredential(credential);
        await currentUser.updatePassword(newPassword);
        
        successDiv.textContent = 'Password updated successfully!';
        successDiv.classList.add('show');
        setTimeout(() => { closeChangePassword(); }, 2000);
    } catch (error) {
        if (error.code === 'auth/wrong-password') { errorDiv.textContent = 'Current password is incorrect.'; }
        else if (error.code === 'auth/weak-password') { errorDiv.textContent = 'New password is too weak.'; }
        else { errorDiv.textContent = 'Error updating password: ' + error.message; }
        errorDiv.classList.add('show');
    }
}

function showDeleteAccount() {
    document.getElementById('userDropdown').classList.remove('show');
    document.getElementById('deleteAccountModal').style.display = 'flex';
    document.getElementById('deleteAccountPassword').value = '';
    document.getElementById('deleteAccountConfirm').checked = false;
    document.getElementById('deleteAccountError').classList.remove('show');
}

function closeDeleteAccount() {
    document.getElementById('deleteAccountModal').style.display = 'none';
}

async function deleteAccount() {
    const password = document.getElementById('deleteAccountPassword').value;
    const confirmed = document.getElementById('deleteAccountConfirm').checked;
    const errorDiv = document.getElementById('deleteAccountError');
    
    errorDiv.classList.remove('show');
    
    if (!password) {
        errorDiv.textContent = 'Please enter your password.';
        errorDiv.classList.add('show');
        return;
    }
    
    if (!confirmed) {
        errorDiv.textContent = 'Please confirm that you understand this action.';
        errorDiv.classList.add('show');
        return;
    }
    
    if (!confirm('Are you absolutely sure? This cannot be undone!')) { return; }
    
    try {
        const credential = firebase.auth.EmailAuthProvider.credential(currentUser.email, password);
        await currentUser.reauthenticateWithCredential(credential);
        const userId = currentUser.uid;
        
        const sessionsSnapshot = await db.collection('sessions').where('userId', '==', userId).get();
        for (const sessionDoc of sessionsSnapshot.docs) {
            const readingsSnapshot = await sessionDoc.ref.collection('readings').get();
            const readingBatch = db.batch();
            readingsSnapshot.docs.forEach(doc => readingBatch.delete(doc.ref));
            await readingBatch.commit();
            await sessionDoc.ref.delete();
        }
        
        await db.collection('users').doc(userId).delete();
        await currentUser.delete();
        
        alert('Your account has been deleted successfully.');
    } catch (error) {
        if (error.code === 'auth/wrong-password') { errorDiv.textContent = 'Password is incorrect.'; }
        else if (error.code === 'auth/requires-recent-login') { errorDiv.textContent = 'Please log out and log back in, then try again.'; }
        else { errorDiv.textContent = 'Error deleting account: ' + error.message; }
        errorDiv.classList.add('show');
    }
}