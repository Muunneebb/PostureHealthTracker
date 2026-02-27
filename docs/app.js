// Firebase Configuration
// REPLACE WITH YOUR FIREBASE CONFIG
const firebaseConfig = {
    apiKey: "YOUR_API_KEY",
    authDomain: "YOUR_PROJECT.firebaseapp.com",
    projectId: "YOUR_PROJECT_ID",
    storageBucket: "YOUR_PROJECT.appspot.com",
    messagingSenderId: "YOUR_SENDER_ID",
    appId: "YOUR_APP_ID"
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
            loadLeaderboard();
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
            document.getElementById('userDisplayName').textContent = 
                'Hello, ' + doc.data().username;
        }
    });
}

function switchTab(tab) {
    // Hide all tabs
    document.querySelectorAll('.tab-content').forEach(el => {
        el.classList.remove('active');
    });
    document.querySelectorAll('.tab-btn').forEach(el => {
        el.classList.remove('active');
    });

    // Show selected tab
    document.getElementById(tab + 'Tab').classList.add('active');
    event.target.classList.add('active');

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
        const twoWeeksAgo = new Date();
        twoWeeksAgo.setDate(twoWeeksAgo.getDate() - 14);

        const sessionsList = document.getElementById('sessionsList');
        sessionsList.innerHTML = '';

        sessionsSnapshot.forEach(doc => {
            const session = doc.data();
            const startTime = session.startTime.toDate();
            const endTime = session.endTime ? session.endTime.toDate() : new Date();
            const duration = (endTime - startTime) / 1000;
            
            totalSessions++;
            totalSitting += session.sitDuration || 0;
            totalScore += session.sessionScore || 0;

            if (startTime >= twoWeeksAgo) {
                twoWeekSessions.push({
                    ...session,
                    id: doc.id,
                    startTime: startTime,
                    duration: duration
                });
            }

            // Create session card
            const scoreClass = session.sessionScore >= 0.7 ? 'score-good' : 
                              session.sessionScore >= 0.4 ? 'score-medium' : 'score-poor';

            const card = document.createElement('div');
            card.className = 'session-card';
            card.onclick = () => showSessionDetail(doc.id, session);
            card.innerHTML = `
                <div class="session-card-header">
                    <span class="session-card-title">${startTime.toLocaleDateString()} at ${startTime.toLocaleTimeString()}</span>
                    <span class="session-card-score ${scoreClass}">${(session.sessionScore * 100).toFixed(0)}%</span>
                </div>
                <div class="session-card-details">
                    <div>Duration: ${Math.round(duration / 60)} min</div>
                    <div>Sitting: ${Math.round(session.sitDuration / 60)} min</div>
                    <div>Buzzer: ${session.buzzerCount} times</div>
                </div>
            `;
            sessionsList.appendChild(card);
        });

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

// Load Leaderboard
async function loadLeaderboard() {
    try {
        const twoWeeksAgo = new Date();
        twoWeeksAgo.setDate(twoWeeksAgo.getDate() - 14);

        // Get all sessions from last 2 weeks
        const sessionsSnapshot = await db.collection('sessions')
            .where('startTime', '>=', twoWeeksAgo)
            .get();

        // Group by user
        const userStats = {};
        
        for (const doc of sessionsSnapshot.docs) {
            const session = doc.data();
            
            if (!userStats[session.userId]) {
                // Get user info
                const userDoc = await db.collection('users').doc(session.userId).get();
                userStats[session.userId] = {
                    username: userDoc.data().username,
                    totalScore: 0,
                    sessionCount: 0,
                    totalTime: 0
                };
            }

            userStats[session.userId].totalScore += session.sessionScore || 0;
            userStats[session.userId].sessionCount += 1;
            
            const endTime = session.endTime ? session.endTime.toDate() : new Date();
            const duration = (endTime - session.startTime.toDate()) / 1000;
            userStats[session.userId].totalTime += duration;
        }

        // Sort by average score
        const leaderboard = Object.entries(userStats)
            .map(([userId, stats]) => ({
                userId,
                username: stats.username,
                avgScore: (stats.totalScore / stats.sessionCount * 100).toFixed(0),
                sessions: stats.sessionCount,
                totalTime: (stats.totalTime / 3600).toFixed(1)
            }))
            .sort((a, b) => b.avgScore - a.avgScore);

        // Display leaderboard
        const tbody = document.getElementById('leaderboardBody');
        tbody.innerHTML = '';

        leaderboard.forEach((user, index) => {
            const row = tbody.insertRow();
            row.innerHTML = `
                <td>${index + 1}</td>
                <td>${user.username}</td>
                <td>${user.avgScore}%</td>
                <td>${user.sessions}</td>
                <td>${user.totalTime}h</td>
            `;
        });

        // Community average
        const communityAvg = Object.values(userStats)
            .reduce((sum, stats) => sum + (stats.totalScore / stats.sessionCount), 0) / Object.keys(userStats).length;
        document.getElementById('statCommunityAvg').textContent = (communityAvg * 100).toFixed(0) + '%';

    } catch (error) {
        console.error('Error loading leaderboard:', error);
    }
}

// Session Detail Modal
function showSessionDetail(sessionId, session) {
    const modal = document.getElementById('sessionModal');
    const title = document.getElementById('sessionModalTitle');
    const body = document.getElementById('sessionModalBody');

    const startTime = session.startTime.toDate();
    const endTime = session.endTime ? session.endTime.toDate() : new Date();
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
                <span>${(session.sessionScore * 100).toFixed(0)}%</span>
            </div>
            <div class="stat-row">
                <span>Sitting Time:</span>
                <span>${Math.round(session.sitDuration / 60)} minutes</span>
            </div>
            <div class="stat-row">
                <span>Buzzer Activations:</span>
                <span>${session.buzzerCount}</span>
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
    if (event.target == modal) {
        modal.style.display = 'none';
    }
}
