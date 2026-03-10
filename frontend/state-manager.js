// frontend/state-manager.js
// State management with localStorage and MongoDB sync

class StateManager {
    constructor() {
        this.stateKey = 'cypress_playwright_state';
        this.sessionId = null;
    }

    /**
     * Save state to localStorage
     */
    saveState(data) {
        const state = {
            sessionId: this.sessionId,
            timestamp: new Date().toISOString(),
            data: data
        };
        localStorage.setItem(this.stateKey, JSON.stringify(state));
        console.log('💾 State saved to localStorage');
    }

    /**
     * Load state from localStorage
     */
    loadState() {
        try {
            const stored = localStorage.getItem(this.stateKey);
            if (stored) {
                const state = JSON.parse(stored);
                
                // Check if state is still valid (< 7 days old)
                const age = Date.now() - new Date(state.timestamp).getTime();
                const maxAge = 7 * 24 * 60 * 60 * 1000; // 7 days
                
                if (age < maxAge) {
                    console.log('✅ Loaded state from localStorage');
                    return state;
                } else {
                    console.log('⏰ State expired, clearing...');
                    this.clearState();
                }
            }
        } catch (error) {
            console.error('Error loading state:', error);
        }
        return null;
    }

    /**
     * Update specific state data
     */
    updateState(key, value) {
        const currentState = this.loadState();
        if (currentState) {
            currentState.data[key] = value;
            this.saveState(currentState.data);
        }
    }

    /**
     * Clear state from localStorage
     */
    clearState() {
        localStorage.removeItem(this.stateKey);
        console.log('🗑️ State cleared from localStorage');
    }

    /**
     * Restore session from backend
     */
    async restoreSession(sessionId) {
        try {
            const response = await fetch(`/api/session/${sessionId}`);
            if (response.ok) {
                const sessionData = await response.json();
                console.log('✅ Session restored from backend');
                return sessionData;
            }
        } catch (error) {
            console.error('Error restoring session:', error);
        }
        return null;
    }

    /**
     * Check for last session
     */
    async checkLastSession() {
        try {
            const response = await fetch('/api/last-session');
            if (response.ok) {
                const data = await response.json();
                return data;
            }
        } catch (error) {
            console.error('Error checking last session:', error);
        }
        return { exists: false };
    }

    /**
     * Set current session ID
     */
    setSessionId(sessionId) {
        this.sessionId = sessionId;
        this.saveState({ sessionId });
    }
}

// Create global instance
const stateManager = new StateManager();