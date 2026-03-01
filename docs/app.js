// Firebase Configuration
const firebaseConfig = {
    apiKey: "AIzaSyDhVpz_D9OTfckaLA792N0c-bqmGnBd7G4",
    authDomain: "posturehealthtracker.firebaseapp.com",
    projectId: "posturehealthtracker",
    storageBucket: "posturehealthtracker.firebasestorage.app",
    messagingSenderId: "330967946233",
    appId: "1:330967946233:web:995732d6b544e67a46e328",
    measurementId: "G-5YG2GL2W9Z"
};

// Initialize Firebase
firebase.initializeApp(firebaseConfig);
const auth = firebase.auth();
const db = firebase.firestore();

let currentUser = null;
let chart = null;

// Initialize
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

// Auth Functions
function toggleForm() {
    document.getElementById('loginForm').style.display = 
        document.getElementById('loginForm').style.display === 'none' ? 'block' : 'none';
    document.getElementById('registerForm').style.display = 
        document.getElementById('registerForm').style.display === 'none' ? 'block' : 'none';
}

async function login() {
    const email = document.getElementById('loginEmail').value;
    const password = document.getElementById('loginPassword').value;
    const errorDiv = document.getElementById('loginError');

    if (!email || !password) {
        errorDiv.textContent = 'Please fill in all fields';
        errorDiv.classList.add('show');
        return;
    }

    try {
        await auth.signInWithEmailAndPassword(email, password);
    } catch (error) {
        errorDiv.textContent = error.message;
        errorDiv.classList.add('show');
    }
}

async function register() {
    const email = document.getElementById('registerEmail').value;
    const password = document.getElementById('registerPassword').value;
    const username = document.getElementById('registerUsername').value;
    const errorDiv = document.getElementById('registerError');

    if (!email || !password || !username) {
        errorDiv.textContent = 'Please fill in all fields';
        errorDiv.classList.add('show');
        return;
    }

    if (password.length < 6) {
        errorDiv.textContent = 'Password must be at least 6 characters';
        errorDiv.classList.add('show');
        return;
    }

    try {
        const result = await auth.createUserWithEmailAndPassword(email, password);
        
        // Create user document in Firestore
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
        errorDiv.textContent = error.message;
        errorDiv.classList.add('show');
    }
}

function logout() {
    auth.signOut().then(() => {
        showAuthPage();
    });
}

// UI Functions
function showAuthPage() {
    document.getElementById('authPage').style.display = 'block';
    document.getElementById('dashboardPage').style.display = 'none';
}

function showDashboard() {
    document.getElementById('authPage').style.display = 'none';
    document.getElementById('dashboardPage').style.display = 'block';
    
    // Get user display name from Firestore
    db.collection('users').doc(currentUser.uid).get().then(doc => {
        if (doc.exists) {
            document.getElementById('userDisplayName').textContent = doc.data().username;
        } else {
            document.getElementById('userDisplayName').textContent = currentUser.email.split('@')[0];
        }
    });
}

function switchTab(tab, button) {
    // Hide all tabs
    document.querySelectorAll('.tab-content').forEach(el => {
        el.classList.remove('active');
        el.style.display = 'none';
    });
    document.querySelectorAll('.tab-btn').forEach(el => {
        el.classList.remove('active');
    });

    // Show selected tab
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

// Session Management
async function startNewSession() {
    const sessionData = {
        userId: currentUser.uid,
        startTime: new Date(),
        endTime: null,
        readings: [],
        sessionScore: 0,
        sitDuration: 0,
        buzzerCount: 0
    };

    try {
        const docRef = await db.collection('sessions').add(sessionData);
        console.log('Session started:', docRef.id);
        
        // Simulate sensor data collection
        simulateSessionData(docRef.id);
        
        loadUserData();
    } catch (error) {
        console.error('Error starting session:', error);
    }
}

function simulateSessionData(sessionId) {
    // Simulate 30 seconds of sensor readings
    let readingCount = 0;
    
    const interval = setInterval(async () => {
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

        if (readingCount >= 30) {
            clearInterval(interval);
            
            // End session
            await db.collection('sessions').doc(sessionId).update({
                endTime: new Date()
            });
            
            loadUserData();
        }
    }, 1000);
}

// Load User Data
async function loadUserData() {
    try {
        // Get user sessions
        const sessionsSnapshot = await db.collection('sessions')
            .where('userId', '==', currentUser.uid)
            .orderBy('startTime', 'desc')
            .get();

        let totalSessions = 0;
        let totalSitting = 0;
        let totalScore = 0;
        let twoWeekSessions = [];
        let activeSession = null;
        const twoWeeksAgo = new Date();
        twoWeeksAgo.setDate(twoWeeksAgo.getDate() - 14);

        const currentSessionList = document.getElementById('currentSessionList');
        const previousSessionsList = document.getElementById('previousSessionsList');
        currentSessionList.innerHTML = '';
        previousSessionsList.innerHTML = '';

        sessionsSnapshot.forEach(doc => {
            const session = doc.data();
            const startTime = session.startTime.toDate();
            const endTime = session.endTime ? session.endTime.toDate() : new Date();
            const duration = (endTime - startTime) / 1000;
            
            totalSessions++;
            totalSitting += session.sitDuration || 0;
            totalScore += session.sessionScore || 0;

            if (!session.endTime && !activeSession) {
                activeSession = {
                    ...session,
                    id: doc.id,
                    startTime: startTime,
                    duration: duration
                };
            }

            if (startTime >= twoWeeksAgo && session.endTime) {
                twoWeekSessions.push({
                    ...session,
                    id: doc.id,
                    startTime: startTime,
                    duration: duration
                });
            }
        });

        if (activeSession) {
            const activeScoreClass = activeSession.sessionScore >= 0.7 ? 'score-good' : 
                activeSession.sessionScore >= 0.4 ? 'score-medium' : 'score-poor';

            const activeCard = document.createElement('div');
            activeCard.className = 'session-card';
            activeCard.onclick = () => showSessionDetail(activeSession.id, activeSession);
            activeCard.innerHTML = `
                <div class="session-card-header">
                    <span class="session-card-title">Started ${activeSession.startTime.toLocaleDateString()} at ${activeSession.startTime.toLocaleTimeString()}</span>
                    <span class="session-card-score ${activeScoreClass}">${((activeSession.sessionScore || 0) * 100).toFixed(0)}%</span>
                </div>
                <div class="session-card-details">
                    <div>Status: Active</div>
                    <div>Elapsed: ${Math.round(activeSession.duration / 60)} min</div>
                    <div>Buzzer: ${activeSession.buzzerCount || 0} times</div>
                </div>
            `;
            currentSessionList.appendChild(activeCard);
        } else {
            currentSessionList.innerHTML = '<p class="no-data">No active session. Click Start Session to begin.</p>';
        }

        if (twoWeekSessions.length > 0) {
            twoWeekSessions.forEach(session => {
                const scoreClass = session.sessionScore >= 0.7 ? 'score-good' : 
                                session.sessionScore >= 0.4 ? 'score-medium' : 'score-poor';

                const card = document.createElement('div');
                card.className = 'session-card';
                card.onclick = () => showSessionDetail(session.id, session);
                card.innerHTML = `
                    <div class="session-card-header">
                        <span class="session-card-title">${session.startTime.toLocaleDateString()} at ${session.startTime.toLocaleTimeString()}</span>
                        <span class="session-card-score ${scoreClass}">${((session.sessionScore || 0) * 100).toFixed(0)}%</span>
                    </div>
                    <div class="session-card-details">
                        <div>Duration: ${Math.round(session.duration / 60)} min</div>
                        <div>Sitting: ${Math.round((session.sitDuration || 0) / 60)} min</div>
                        <div>Buzzer: ${session.buzzerCount || 0} times</div>
                    </div>
                `;
                previousSessionsList.appendChild(card);
            });
        } else {
            previousSessionsList.innerHTML = '<p class="no-data">No previous sessions in the last 2 weeks.</p>';
        }

        // Update stats
        document.getElementById('statTotalSessions').textContent = totalSessions;
        document.getElementById('statTotalSitting').textContent = (totalSitting / 3600).toFixed(1) + 'h';
        
        const avgScore = totalSessions ? (totalScore / totalSessions * 100).toFixed(0) : 0;
        document.getElementById('statAvgScore').textContent = avgScore + '%';

        // Store for analytics
        window.userTwoWeekSessions = twoWeekSessions;

    } catch (error) {
        console.error('Error loading user data:', error);
    }
}

// Load Analytics
function loadAnalytics() {
    if (!window.userTwoWeekSessions || window.userTwoWeekSessions.length === 0) {
        document.getElementById('analyticsChart').style.display = 'none';
        document.getElementById('bestScore').textContent = '-';
        document.getElementById('worstScore').textContent = '-';
        document.getElementById('periodAvgScore').textContent = '-';
        document.getElementById('periodSessionCount').textContent = '0';
        return;
    }

    const sessions = window.userTwoWeekSessions;
    const scores = sessions.map(s => s.sessionScore * 100);
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
                borderColor: '#2196F3',
                backgroundColor: 'rgba(33, 150, 243, 0.1)',
                tension: 0.4,
                fill: true,
                pointRadius: 5,
                pointBackgroundColor: '#2196F3'
            }]
        },
        options: {
            responsive: true,
            maintainAspectRatio: true,
            plugins: {
                title: {
                    display: true,
                    text: '2-Week Session Scores'
                }
            },
            scales: {
                y: {
                    min: 0,
                    max: 100,
                    title: {
                        display: true,
                        text: 'Score (%)'
                    }
                }
            }
        }
    });

    // Update analytics stats
    if (scores.length > 0) {
        document.getElementById('bestScore').textContent = Math.max(...scores).toFixed(0) + '%';
        document.getElementById('worstScore').textContent = Math.min(...scores).toFixed(0) + '%';
        document.getElementById('periodAvgScore').textContent = 
            (scores.reduce((a, b) => a + b) / scores.length).toFixed(0) + '%';
        document.getElementById('periodSessionCount').textContent = scores.length;
    }
}

// Session Detail Modal
function showSessionDetail(sessionId, session) {
    const modal = document.getElementById('sessionModal');
    const title = document.getElementById('sessionModalTitle');
    const body = document.getElementById('sessionModalBody');

    const startTime = session.startTime && typeof session.startTime.toDate === 'function'
        ? session.startTime.toDate()
        : new Date(session.startTime);
    const endTime = session.endTime
        ? (typeof session.endTime.toDate === 'function' ? session.endTime.toDate() : new Date(session.endTime))
        : new Date();
    const duration = (endTime - startTime) / 1000;

    title.textContent = `Session - ${startTime.toLocaleDateString()}`;
    body.innerHTML = `
        <div class="session-detail">
            <div class="stat-row">
                <span>Start Time:</span>
                <span>${startTime.toLocaleString()}</span>
            </div>
            <div class="stat-row">
                <span>Duration:</span>
                <span>${Math.round(duration / 60)} minutes</span>
            </div>
            <div class="stat-row">
                <span>Score:</span>
                <span>${((session.sessionScore || 0) * 100).toFixed(0)}%</span>
            </div>
            <div class="stat-row">
                <span>Sitting Time:</span>
                <span>${Math.round((session.sitDuration || 0) / 60)} minutes</span>
            </div>
            <div class="stat-row">
                <span>Buzzer Activations:</span>
                <span>${session.buzzerCount || 0}</span>
            </div>
        </div>
    `;

    modal.style.display = 'flex';
}

function closeSessionModal() {
    document.getElementById('sessionModal').style.display = 'none';
}

// Close modal when clicking outside
window.onclick = function(event) {
    const modal = document.getElementById('sessionModal');
    const changePasswordModal = document.getElementById('changePasswordModal');
    const deleteAccountModal = document.getElementById('deleteAccountModal');
    
    if (event.target == modal) {
        modal.style.display = 'none';
    }
    if (event.target == changePasswordModal) {
        closeChangePassword();
    }
    if (event.target == deleteAccountModal) {
        closeDeleteAccount();
    }
    
    // Close user dropdown when clicking outside
    const userDropdown = document.getElementById('userDropdown');
    const userMenuBtn = document.querySelector('.user-menu-btn');
    if (!userMenuBtn.contains(event.target) && !userDropdown.contains(event.target)) {
        userDropdown.classList.remove('show');
    }
}

// User Menu Functions
function toggleUserMenu() {
    const dropdown = document.getElementById('userDropdown');
    dropdown.classList.toggle('show');
}

// Change Password Functions
function showChangePassword() {
    document.getElementById('userDropdown').classList.remove('show');
    document.getElementById('changePasswordModal').style.display = 'flex';
    // Clear previous inputs and messages
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
    
    // Clear previous messages
    errorDiv.classList.remove('show');
    successDiv.classList.remove('show');
    
    // Validation
    if (!currentPassword || !newPassword || !confirmPassword) {
        errorDiv.textContent = 'Please fill in all fields';
        errorDiv.classList.add('show');
        return;
    }
    
    if (newPassword.length < 6) {
        errorDiv.textContent = 'New password must be at least 6 characters';
        errorDiv.classList.add('show');
        return;
    }
    
    if (newPassword !== confirmPassword) {
        errorDiv.textContent = 'New passwords do not match';
        errorDiv.classList.add('show');
        return;
    }
    
    try {
        // Re-authenticate user with current password
        const credential = firebase.auth.EmailAuthProvider.credential(
            currentUser.email,
            currentPassword
        );
        
        await currentUser.reauthenticateWithCredential(credential);
        
        // Update password
        await currentUser.updatePassword(newPassword);
        
        successDiv.textContent = 'Password updated successfully!';
        successDiv.classList.add('show');
        
        // Close modal after 2 seconds
        setTimeout(() => {
            closeChangePassword();
        }, 2000);
        
    } catch (error) {
        console.error('Error changing password:', error);
        if (error.code === 'auth/wrong-password') {
            errorDiv.textContent = 'Current password is incorrect';
        } else if (error.code === 'auth/weak-password') {
            errorDiv.textContent = 'New password is too weak';
        } else {
            errorDiv.textContent = 'Error updating password: ' + error.message;
        }
        errorDiv.classList.add('show');
    }
}

// Delete Account Functions
function showDeleteAccount() {
    document.getElementById('userDropdown').classList.remove('show');
    document.getElementById('deleteAccountModal').style.display = 'flex';
    // Clear previous inputs and messages
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
    
    // Clear previous messages
    errorDiv.classList.remove('show');
    
    // Validation
    if (!password) {
        errorDiv.textContent = 'Please enter your password';
        errorDiv.classList.add('show');
        return;
    }
    
    if (!confirmed) {
        errorDiv.textContent = 'Please confirm that you understand this action';
        errorDiv.classList.add('show');
        return;
    }
    
    // Final confirmation
    if (!confirm('Are you absolutely sure? This cannot be undone!')) {
        return;
    }
    
    try {
        // Re-authenticate user
        const credential = firebase.auth.EmailAuthProvider.credential(
            currentUser.email,
            password
        );
        
        await currentUser.reauthenticateWithCredential(credential);
        
        const userId = currentUser.uid;
        
        // Delete user data from Firestore
        // 1. Delete all sessions and their readings
        const sessionsSnapshot = await db.collection('sessions')
            .where('userId', '==', userId)
            .get();
        
        for (const sessionDoc of sessionsSnapshot.docs) {
            // Delete all readings in this session
            const readingsSnapshot = await sessionDoc.ref.collection('readings').get();
            const readingBatch = db.batch();
            readingsSnapshot.docs.forEach(doc => readingBatch.delete(doc.ref));
            await readingBatch.commit();
            
            // Delete session
            await sessionDoc.ref.delete();
        }
        
        // 2. Delete user profile
        await db.collection('users').doc(userId).delete();
        
        // 3. Delete Firebase Authentication account
        await currentUser.delete();
        
        // User will be automatically logged out
        alert('Your account has been deleted successfully');
        
    } catch (error) {
        console.error('Error deleting account:', error);
        if (error.code === 'auth/wrong-password') {
            errorDiv.textContent = 'Password is incorrect';
        } else if (error.code === 'auth/requires-recent-login') {
            errorDiv.textContent = 'Please log out and log back in, then try again';
        } else {
            errorDiv.textContent = 'Error deleting account: ' + error.message;
        }
        errorDiv.classList.add('show');
    }
}
