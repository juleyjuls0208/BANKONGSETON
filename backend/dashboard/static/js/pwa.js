/**
 * PWA Initialization and Service Worker Registration
 * Bangko ng Seton
 */

// PWA Installation Banner
let deferredPrompt;

// Check if PWA is installed
function isPWAInstalled() {
  return window.matchMedia('(display-mode: standalone)').matches ||
         window.navigator.standalone === true;
}

// Register Service Worker
if ('serviceWorker' in navigator) {
  window.addEventListener('load', () => {
    navigator.serviceWorker.register('/static/sw.js')
      .then((registration) => {
        console.log('[PWA] Service Worker registered:', registration.scope);
        
        // Check for updates every 1 hour
        setInterval(() => {
          registration.update();
        }, 60 * 60 * 1000);
      })
      .catch((error) => {
        console.error('[PWA] Service Worker registration failed:', error);
      });
  });
}

// Install PWA prompt
window.addEventListener('beforeinstallprompt', (event) => {
  event.preventDefault();
  deferredPrompt = event;
  showInstallButton();
});

// Show install button
function showInstallButton() {
  if (isPWAInstalled()) return;
  
  const installBanner = document.createElement('div');
  installBanner.className = 'install-banner';
  installBanner.innerHTML = `
    <div class="install-content">
      <div class="install-icon">📱</div>
      <div class="install-text">
        <strong>Install Bangko ng Seton</strong>
        <span>Add to home screen for quick access</span>
      </div>
      <button onclick="installPWA()" class="btn-install">Install</button>
      <button onclick="dismissInstall(this)" class="btn-dismiss-install">×</button>
    </div>
  `;
  document.body.appendChild(installBanner);
}

// Install PWA
async function installPWA() {
  if (!deferredPrompt) return;
  deferredPrompt.prompt();
  const { outcome } = await deferredPrompt.userChoice;
  console.log('[PWA] Install prompt:', outcome);
  deferredPrompt = null;
  document.querySelector('.install-banner')?.remove();
}

// Dismiss install banner
function dismissInstall(button) {
  button.closest('.install-banner').remove();
}

// Online/Offline detection
window.addEventListener('online', () => {
  console.log('[PWA] Back online');
  updateOnlineStatus(true);
  syncQueuedData();
});

window.addEventListener('offline', () => {
  console.log('[PWA] Gone offline');
  updateOnlineStatus(false);
});

// Update online status indicator
function updateOnlineStatus(isOnline) {
  const statusIndicator = document.querySelector('.sync-status');
  if (!statusIndicator) return;
  
  if (isOnline) {
    statusIndicator.className = 'sync-status online';
    statusIndicator.innerHTML = '<span class="status-dot"></span> Online';
  } else {
    statusIndicator.className = 'sync-status offline';
    statusIndicator.innerHTML = '<span class="status-dot"></span> Offline';
  }
}

// Sync queued data
async function syncQueuedData() {
  if (!navigator.onLine) return;
  
  try {
    const response = await fetch('/api/queue/status');
    const status = await response.json();
    
    if (status.pending > 0) {
      showSyncIndicator('Syncing ' + status.pending + ' transaction(s)...');
      const syncResponse = await fetch('/api/queue/process', { method: 'POST' });
      const result = await syncResponse.json();
      showSyncIndicator('Synced ' + result.success + ' transaction(s)!', 3000);
    }
  } catch (error) {
    console.error('[PWA] Sync failed:', error);
  }
}

// Show sync indicator
function showSyncIndicator(message, duration = null) {
  let indicator = document.querySelector('.sync-indicator');
  
  if (!indicator) {
    indicator = document.createElement('div');
    indicator.className = 'sync-indicator';
    document.body.appendChild(indicator);
  }
  
  indicator.textContent = message;
  indicator.classList.add('show');
  
  if (duration) {
    setTimeout(() => {
      indicator.classList.remove('show');
    }, duration);
  }
}

// Export functions
window.PWA = {
  installPWA,
  syncQueuedData,
  updateOnlineStatus,
  showSyncIndicator,
  isPWAInstalled
};
