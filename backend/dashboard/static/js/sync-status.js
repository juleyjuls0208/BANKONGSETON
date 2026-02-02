/**
 * Sync Status and Queue Management
 * Bangko ng Seton - Phase 2 PWA Features
 */

class SyncManager {
    constructor() {
        this.lastSyncTime = null;
        this.pendingCount = 0;
        this.updateInterval = null;
        this.queueCheckInterval = 30000; // Check every 30 seconds
    }

    /**
     * Initialize sync manager
     */
    init() {
        console.log('[SyncManager] Initializing...');
        this.updateSyncStatus();
        this.checkQueueStatus();
        
        // Check queue status periodically
        this.updateInterval = setInterval(() => {
            this.checkQueueStatus();
        }, this.queueCheckInterval);
        
        // Update last synced time every minute
        setInterval(() => {
            this.updateLastSyncedDisplay();
        }, 60000);
    }

    /**
     * Update sync status based on network and queue
     */
    async updateSyncStatus() {
        const isOnline = navigator.onLine;
        
        if (!isOnline) {
            this.setStatus('offline', 'Offline');
            return;
        }
        
        // Check if there are pending items
        if (this.pendingCount > 0) {
            this.setStatus('syncing', `Syncing ${this.pendingCount} item(s)`);
        } else {
            this.setStatus('online', 'Online');
        }
    }

    /**
     * Set sync status indicator
     */
    setStatus(statusClass, text) {
        const indicators = document.querySelectorAll('.sync-status');
        indicators.forEach(indicator => {
            indicator.className = `sync-status ${statusClass}`;
            // Update text, preserving the status dot
            const dotHTML = '<span class="status-dot"></span>';
            const hiddenText = '<span class="visually-hidden-focusable">Network status: </span>';
            indicator.innerHTML = `${dotHTML}${hiddenText}${text}`;
        });
    }

    /**
     * Check queue status from backend
     */
    async checkQueueStatus() {
        if (!navigator.onLine) return;
        
        try {
            const response = await fetch('/api/queue/status');
            if (!response.ok) {
                console.error('[SyncManager] Failed to fetch queue status:', response.status);
                return;
            }
            
            const data = await response.json();
            this.pendingCount = data.pending || 0;
            
            // Update badges
            this.updatePendingBadges(this.pendingCount);
            
            // Update sync status
            this.updateSyncStatus();
            
            // Update last synced time
            if (data.last_processed) {
                this.lastSyncTime = new Date(data.last_processed);
                this.updateLastSyncedDisplay();
            }
            
            // Auto-sync if there are pending items
            if (this.pendingCount > 0) {
                console.log(`[SyncManager] Found ${this.pendingCount} pending item(s), triggering sync...`);
                await this.processPendingQueue();
            }
        } catch (error) {
            console.error('[SyncManager] Error checking queue:', error);
        }
    }

    /**
     * Process pending queue
     */
    async processPendingQueue() {
        if (!navigator.onLine) {
            console.log('[SyncManager] Cannot sync while offline');
            return;
        }
        
        try {
            this.setStatus('syncing', `Syncing ${this.pendingCount} item(s)`);
            
            const response = await fetch('/api/queue/process', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' }
            });
            
            if (!response.ok) {
                console.error('[SyncManager] Sync failed:', response.status);
                return;
            }
            
            const result = await response.json();
            console.log('[SyncManager] Sync result:', result);
            
            if (result.success > 0) {
                window.PWA?.showSyncIndicator(`✓ Synced ${result.success} transaction(s)`, 3000);
                this.lastSyncTime = new Date();
                this.updateLastSyncedDisplay();
            }
            
            // Update queue status after processing
            setTimeout(() => this.checkQueueStatus(), 1000);
            
        } catch (error) {
            console.error('[SyncManager] Error processing queue:', error);
            this.setStatus('online', 'Online');
        }
    }

    /**
     * Update pending badges on UI elements
     */
    updatePendingBadges(count) {
        const badges = document.querySelectorAll('.pending-badge');
        badges.forEach(badge => {
            if (count > 0) {
                badge.setAttribute('data-count', count);
                badge.style.display = 'inline-block';
            } else {
                badge.removeAttribute('data-count');
                badge.style.display = 'none';
            }
        });
    }

    /**
     * Update "last synced" timestamp display
     */
    updateLastSyncedDisplay() {
        if (!this.lastSyncTime) return;
        
        const elements = document.querySelectorAll('.last-synced');
        const timeAgo = this.getTimeAgo(this.lastSyncTime);
        
        elements.forEach(el => {
            el.textContent = `Last synced: ${timeAgo}`;
            el.title = this.lastSyncTime.toLocaleString();
        });
    }

    /**
     * Get human-readable time ago string
     */
    getTimeAgo(date) {
        const seconds = Math.floor((new Date() - date) / 1000);
        
        if (seconds < 60) return 'just now';
        if (seconds < 3600) return `${Math.floor(seconds / 60)} min ago`;
        if (seconds < 86400) return `${Math.floor(seconds / 3600)} hrs ago`;
        return `${Math.floor(seconds / 86400)} days ago`;
    }

    /**
     * Manually trigger sync
     */
    async manualSync() {
        console.log('[SyncManager] Manual sync triggered');
        await this.checkQueueStatus();
    }

    /**
     * Cleanup on unload
     */
    destroy() {
        if (this.updateInterval) {
            clearInterval(this.updateInterval);
        }
    }
}

// Create global instance
const syncManager = new SyncManager();

// Initialize when DOM is ready
if (document.readyState === 'loading') {
    document.addEventListener('DOMContentLoaded', () => syncManager.init());
} else {
    syncManager.init();
}

// Cleanup on page unload
window.addEventListener('beforeunload', () => syncManager.destroy());

// Network status listeners
window.addEventListener('online', () => {
    syncManager.updateSyncStatus();
    syncManager.checkQueueStatus();
});

window.addEventListener('offline', () => {
    syncManager.updateSyncStatus();
});

// Export for global access
window.SyncManager = syncManager;
