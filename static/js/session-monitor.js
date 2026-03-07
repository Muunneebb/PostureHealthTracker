// Session monitoring script
class SessionMonitor {
    constructor() {
        this.sessionId = localStorage.getItem('currentSessionId');
        this.isMonitoring = false;
        this.alertPollingInterval = null;
        this.takeBreakAlertShown = false;
    }

    async startMonitoring() {
        if (!this.sessionId) {
            console.log('No active session to monitor');
            return;
        }

        if (this.isMonitoring) {
            return;
        }

        this.isMonitoring = true;
        console.log('Session monitoring started for session:', this.sessionId);

        // Poll session stats periodically so alerts work for external sensor senders.
        await this.checkForAlerts();
        this.alertPollingInterval = setInterval(() => {
            this.checkForAlerts();
        }, 10000);
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
            if (!response.ok) {
                return;
            }

            const stats = await response.json();

            if (stats.take_break_alert) {
                if (!this.takeBreakAlertShown) {
                    this.showTakeBreakAlert(stats.take_break_reasons || []);
                    this.takeBreakAlertShown = true;
                }
            } else {
                this.takeBreakAlertShown = false;
            }
        } catch (error) {
            console.error('Error checking stats:', error);
        }
    }

    showTakeBreakAlert(reasons = []) {
        const reasonText = reasons.length > 0 ? reasons.join(', ') : 'session thresholds';

        if ('Notification' in window && Notification.permission === 'granted') {
            new Notification('PostureHealthTracker', {
                title: 'Time to Take a Break',
                body: `Break recommended due to: ${reasonText}`,
                icon: '/static/img/icon.png',
                tag: 'take-break-alert'
            });
        }

        console.warn(`TAKE BREAK ALERT: ${reasonText}`);
    }

    showBreakAlert() {
        if ('Notification' in window && Notification.permission === 'granted') {
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
        if ('Notification' in window && Notification.permission === 'granted') {
            new Notification('PostureHealthTracker', {
                title: 'Excessive Posture Issues!',
                body: 'The buzzer has triggered 3 times. Please check your posture.',
                icon: '/static/img/icon.png',
                tag: 'buzzer-alert'
            });
        }
        console.warn('BUZZER ALERT: Buzzer triggered 3 times');
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
                this.takeBreakAlertShown = false;
                if (this.alertPollingInterval) {
                    clearInterval(this.alertPollingInterval);
                    this.alertPollingInterval = null;
                }
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

    if (monitor.sessionId) {
        monitor.startMonitoring();
    }
    
    // Request notification permission
    if ('Notification' in window && Notification.permission === 'default') {
        Notification.requestPermission();
    }
});

// Export for use in other scripts
if (typeof module !== 'undefined' && module.exports) {
    module.exports = SessionMonitor;
}
