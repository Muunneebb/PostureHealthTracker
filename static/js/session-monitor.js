// Session monitoring script
class SessionMonitor {
    constructor() {
        this.sessionId = localStorage.getItem('currentSessionId');
        this.isMonitoring = false;
    }

    async startMonitoring() {
        if (!this.sessionId) {
            console.log('No active session to monitor');
            return;
        }

        this.isMonitoring = true;
        console.log('Session monitoring started for session:', this.sessionId);

        // Real-time monitoring would happen here
        // This would connect to the sensor data stream
    }

    async sendReading(reading) {
        if (!this.sessionId) {
            console.error('No active session');
            return;
        }

        try {
            const response = await fetch(`/api/session/${this.sessionId}/readings`, {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                },
                body: JSON.stringify(reading)
            });

            if (!response.ok) {
                console.error('Error sending reading:', response.status);
            }

            // Check for alerts after each reading
            this.checkForAlerts();
        } catch (error) {
            console.error('Error sending reading:', error);
        }
    }

    async checkForAlerts() {
        try {
            const response = await fetch(`/api/session/${this.sessionId}/stats`);
            const stats = await response.json();

            if (stats.break_alert) {
                this.showBreakAlert();
            }

            if (stats.excessive_buzzer_alert) {
                this.showBuzzerAlert();
            }
        } catch (error) {
            console.error('Error checking stats:', error);
        }
    }

    showBreakAlert() {
        if (!Notification.permission === 'granted') {
            new Notification('PostureHealthTracker', {
                title: 'Time for a Break!',
                body: 'You have been sitting for more than 2 hours. Please take a break.',
                icon: '/static/img/icon.png',
                tag: 'break-alert'
            });
        }
        console.warn('BREAK ALERT: User has been sitting for over 2 hours');
    }

    showBuzzerAlert() {
        if (!Notification.permission === 'granted') {
            new Notification('PostureHealthTracker', {
                title: 'Excessive Posture Issues!',
                body: 'The buzzer has triggered 5 times. Please check your posture.',
                icon: '/static/img/icon.png',
                tag: 'buzzer-alert'
            });
        }
        console.warn('BUZZER ALERT: Buzzer triggered 5 times');
    }

    async endSession() {
        if (!this.sessionId) {
            return;
        }

        try {
            const response = await fetch(`/api/session/${this.sessionId}/end`, {
                method: 'POST'
            });

            if (response.ok) {
                localStorage.removeItem('currentSessionId');
                this.sessionId = null;
                this.isMonitoring = false;
                console.log('Session ended successfully');
            }
        } catch (error) {
            console.error('Error ending session:', error);
        }
    }
}

// Initialize session monitor on page load
let monitor;
document.addEventListener('DOMContentLoaded', () => {
    monitor = new SessionMonitor();
    
    // Request notification permission
    if ('Notification' in window && Notification.permission === 'default') {
        Notification.requestPermission();
    }
});

// End session when leaving the page
window.addEventListener('beforeunload', () => {
    if (monitor && monitor.sessionId) {
        monitor.endSession();
    }
});

// Export for use in other scripts
if (typeof module !== 'undefined' && module.exports) {
    module.exports = SessionMonitor;
}
