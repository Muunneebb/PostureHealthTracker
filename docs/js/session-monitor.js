/**
 * SessionMonitor: Handles live session state, Firebase camera triggers,
 * and browser notifications for posture alerts.
 */
class SessionMonitor {
    constructor() {
        this.sessionId = localStorage.getItem('currentSessionId');
        this.isMonitoring = false;
        this.alertPollingInterval = null;
        this.takeBreakAlertShown = false;
    }

    async startMonitoring() {
        if (!this.sessionId || this.isMonitoring) return;

        this.isMonitoring = true;
        console.log('Monitoring started for session:', this.sessionId);

        // TRIGGER HARDWARE: Switch Firebase command to ON
        this.toggleHardwareCamera("ON");

        // Start polling for alerts/stats every 10 seconds
        await this.checkForAlerts();
        this.alertPollingInterval = setInterval(() => this.checkForAlerts(), 10000);
    }

    async toggleHardwareCamera(status) {
        try {
            if (typeof firebase !== 'undefined' && firebase.apps.length) {
                await firebase.database().ref('system_state/camera_command').set(status);
                console.log(`Hardware camera command sent: ${status}`);
            }
        } catch (error) {
            console.error("Hardware trigger failed:", error);
        }
    }

    async checkForAlerts() {
        if (!this.sessionId) return;
        try {
            const response = await fetch(`/api/session/${this.sessionId}/stats`);
            if (!response.ok) return;

            const stats = await response.json();

            if (stats.take_break_alert) {
                if (!this.takeBreakAlertShown) {
                    this.notify('Time to Take a Break', `Reason: ${stats.take_break_reasons?.join(', ') || 'threshold reached'}`);
                    this.takeBreakAlertShown = true;
                }
            } else {
                this.takeBreakAlertShown = false;
            }
        } catch (error) {
            console.error('Alert check failed:', error);
        }
    }

    notify(title, body) {
        if ('Notification' in window && Notification.permission === 'granted') {
            new Notification('PostureHealthTracker', { title, body, icon: '/static/img/icon.png' });
        }
        console.warn(`${title.toUpperCase()}: ${body}`);
    }

    async endSession() {
        if (!this.sessionId) return;

        try {
            const response = await fetch(`/api/session/${this.sessionId}/end`, { method: 'POST' });
            if (response.ok) {
                // SHUTDOWN HARDWARE
                this.toggleHardwareCamera("OFF");

                // Cleanup State
                localStorage.removeItem('currentSessionId');
                this.sessionId = null;
                this.isMonitoring = false;
                this.takeBreakAlertShown = false;
                if (this.alertPollingInterval) clearInterval(this.alertPollingInterval);
                
                console.log('Session ended successfully');
                window.location.reload(); // Refresh to show the final score in history
            }
        } catch (error) {
            console.error('Error ending session:', error);
        }
    }
}

// Global initialization
let monitor;
document.addEventListener('DOMContentLoaded', () => {
    monitor = new SessionMonitor();
    if (monitor.sessionId) monitor.startMonitoring();
    
    if ('Notification' in window && Notification.permission === 'default') {
        Notification.requestPermission();
    }
});