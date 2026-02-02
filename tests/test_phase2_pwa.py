"""
Phase 2 PWA Tests
Tests for Progressive Web App features, service worker, and UI enhancements
"""
import pytest
import json
import os
from pathlib import Path


class TestPWAManifest:
    """Test PWA manifest.json configuration"""
    
    def test_manifest_exists(self):
        """Verify manifest.json file exists"""
        manifest_path = Path(__file__).parent.parent / 'backend' / 'dashboard' / 'static' / 'manifest.json'
        assert manifest_path.exists(), "manifest.json should exist"
    
    def test_manifest_valid_json(self):
        """Verify manifest.json is valid JSON"""
        manifest_path = Path(__file__).parent.parent / 'backend' / 'dashboard' / 'static' / 'manifest.json'
        with open(manifest_path, 'r') as f:
            data = json.load(f)
        assert isinstance(data, dict), "manifest.json should be a valid JSON object"
    
    def test_manifest_required_fields(self):
        """Verify manifest.json has required PWA fields"""
        manifest_path = Path(__file__).parent.parent / 'backend' / 'dashboard' / 'static' / 'manifest.json'
        with open(manifest_path, 'r') as f:
            data = json.load(f)
        
        required_fields = ['name', 'short_name', 'start_url', 'display', 'icons']
        for field in required_fields:
            assert field in data, f"manifest.json should have '{field}' field"
    
    def test_manifest_icons_format(self):
        """Verify manifest icons are properly configured"""
        manifest_path = Path(__file__).parent.parent / 'backend' / 'dashboard' / 'static' / 'manifest.json'
        with open(manifest_path, 'r') as f:
            data = json.load(f)
        
        assert 'icons' in data, "manifest.json should have icons"
        assert isinstance(data['icons'], list), "icons should be a list"
        assert len(data['icons']) >= 2, "Should have at least 2 icon sizes (192x192, 512x512)"
        
        # Verify at least one 192x192 icon
        sizes = [icon.get('sizes') for icon in data['icons']]
        assert '192x192' in sizes, "Should have 192x192 icon for PWA"
        assert '512x512' in sizes, "Should have 512x512 icon for splash screen"


class TestServiceWorker:
    """Test Service Worker implementation"""
    
    def test_service_worker_exists(self):
        """Verify service worker file exists"""
        sw_path = Path(__file__).parent.parent / 'backend' / 'dashboard' / 'static' / 'sw.js'
        assert sw_path.exists(), "Service Worker sw.js should exist"
    
    def test_service_worker_has_cache_name(self):
        """Verify service worker defines a cache name"""
        sw_path = Path(__file__).parent.parent / 'backend' / 'dashboard' / 'static' / 'sw.js'
        with open(sw_path, 'r') as f:
            content = f.read()
        
        assert 'CACHE_NAME' in content or 'cacheName' in content, \
            "Service Worker should define a cache name"
    
    def test_service_worker_has_install_event(self):
        """Verify service worker has install event handler"""
        sw_path = Path(__file__).parent.parent / 'backend' / 'dashboard' / 'static' / 'sw.js'
        with open(sw_path, 'r') as f:
            content = f.read()
        
        assert "'install'" in content or '"install"' in content, \
            "Service Worker should handle install event"
    
    def test_service_worker_has_fetch_handler(self):
        """Verify service worker has fetch event handler"""
        sw_path = Path(__file__).parent.parent / 'backend' / 'dashboard' / 'static' / 'sw.js'
        with open(sw_path, 'r') as f:
            content = f.read()
        
        assert "'fetch'" in content or '"fetch"' in content, \
            "Service Worker should handle fetch events"


class TestPWAScripts:
    """Test PWA JavaScript files"""
    
    def test_pwa_js_exists(self):
        """Verify pwa.js file exists"""
        pwa_path = Path(__file__).parent.parent / 'backend' / 'dashboard' / 'static' / 'js' / 'pwa.js'
        assert pwa_path.exists(), "pwa.js should exist"
    
    def test_pwa_js_has_service_worker_registration(self):
        """Verify pwa.js registers service worker"""
        pwa_path = Path(__file__).parent.parent / 'backend' / 'dashboard' / 'static' / 'js' / 'pwa.js'
        with open(pwa_path, 'r') as f:
            content = f.read()
        
        assert 'serviceWorker.register' in content, \
            "pwa.js should register service worker"
    
    def test_pwa_js_handles_install_prompt(self):
        """Verify pwa.js handles install prompt"""
        pwa_path = Path(__file__).parent.parent / 'backend' / 'dashboard' / 'static' / 'js' / 'pwa.js'
        with open(pwa_path, 'r') as f:
            content = f.read()
        
        assert 'beforeinstallprompt' in content, \
            "pwa.js should handle install prompt"
    
    def test_sync_status_js_exists(self):
        """Verify sync-status.js file exists"""
        sync_path = Path(__file__).parent.parent / 'backend' / 'dashboard' / 'static' / 'js' / 'sync-status.js'
        assert sync_path.exists(), "sync-status.js should exist"
    
    def test_sync_status_js_has_online_handler(self):
        """Verify sync-status.js handles online/offline events"""
        sync_path = Path(__file__).parent.parent / 'backend' / 'dashboard' / 'static' / 'js' / 'sync-status.js'
        with open(sync_path, 'r') as f:
            content = f.read()
        
        assert "'online'" in content or '"online"' in content, \
            "sync-status.js should handle online event"
        assert "'offline'" in content or '"offline"' in content, \
            "sync-status.js should handle offline event"


class TestPWAStyles:
    """Test PWA CSS files"""
    
    def test_pwa_css_exists(self):
        """Verify pwa.css file exists"""
        css_path = Path(__file__).parent.parent / 'backend' / 'dashboard' / 'static' / 'css' / 'pwa.css'
        assert css_path.exists(), "pwa.css should exist"
    
    def test_pwa_css_has_sync_status_styles(self):
        """Verify pwa.css has sync status indicator styles"""
        css_path = Path(__file__).parent.parent / 'backend' / 'dashboard' / 'static' / 'css' / 'pwa.css'
        with open(css_path, 'r') as f:
            content = f.read()
        
        assert '.sync-status' in content, "pwa.css should have .sync-status styles"
        assert '.online' in content, "pwa.css should have .online styles"
        assert '.offline' in content, "pwa.css should have .offline styles"
    
    def test_pwa_css_has_install_banner_styles(self):
        """Verify pwa.css has install banner styles"""
        css_path = Path(__file__).parent.parent / 'backend' / 'dashboard' / 'static' / 'css' / 'pwa.css'
        with open(css_path, 'r') as f:
            content = f.read()
        
        assert '.install-banner' in content, "pwa.css should have .install-banner styles"
    
    def test_pwa_css_has_accessibility_features(self):
        """Verify pwa.css has accessibility support"""
        css_path = Path(__file__).parent.parent / 'backend' / 'dashboard' / 'static' / 'css' / 'pwa.css'
        with open(css_path, 'r') as f:
            content = f.read()
        
        assert 'focus-visible' in content or ':focus' in content, \
            "pwa.css should have focus styles for keyboard navigation"
        assert 'prefers-reduced-motion' in content, \
            "pwa.css should support reduced motion preference"


class TestPWAIcons:
    """Test PWA icon files"""
    
    def test_icons_directory_exists(self):
        """Verify icons directory exists"""
        icons_dir = Path(__file__).parent.parent / 'backend' / 'dashboard' / 'static' / 'icons'
        assert icons_dir.exists(), "icons directory should exist"
    
    def test_required_icon_sizes_exist(self):
        """Verify required icon sizes are present"""
        icons_dir = Path(__file__).parent.parent / 'backend' / 'dashboard' / 'static' / 'icons'
        
        # PWA requires at least 192x192 and 512x512
        required_sizes = ['192x192', '512x512']
        
        for size in required_sizes:
            icon_path = icons_dir / f'icon-{size}.png'
            assert icon_path.exists(), f"Icon {size} should exist for PWA"
    
    def test_icon_files_are_png(self):
        """Verify icon files are PNG format"""
        icons_dir = Path(__file__).parent.parent / 'backend' / 'dashboard' / 'static' / 'icons'
        
        for icon_file in icons_dir.glob('icon-*.png'):
            # Check file signature (PNG magic bytes)
            with open(icon_file, 'rb') as f:
                header = f.read(8)
                assert header == b'\x89PNG\r\n\x1a\n', f"{icon_file.name} should be valid PNG"


class TestHTMLPWAIntegration:
    """Test PWA integration in HTML templates"""
    
    def test_dashboard_has_manifest_link(self):
        """Verify dashboard.html links to manifest.json"""
        template_path = Path(__file__).parent.parent / 'backend' / 'dashboard' / 'templates' / 'dashboard.html'
        with open(template_path, 'r', encoding='utf-8') as f:
            content = f.read()
        
        assert 'manifest.json' in content, "dashboard.html should link to manifest.json"
    
    def test_dashboard_has_theme_color(self):
        """Verify dashboard.html has theme-color meta tag"""
        template_path = Path(__file__).parent.parent / 'backend' / 'dashboard' / 'templates' / 'dashboard.html'
        with open(template_path, 'r', encoding='utf-8') as f:
            content = f.read()
        
        assert 'theme-color' in content, "dashboard.html should have theme-color meta tag"
    
    def test_dashboard_has_apple_touch_icon(self):
        """Verify dashboard.html has apple-touch-icon"""
        template_path = Path(__file__).parent.parent / 'backend' / 'dashboard' / 'templates' / 'dashboard.html'
        with open(template_path, 'r', encoding='utf-8') as f:
            content = f.read()
        
        assert 'apple-touch-icon' in content, "dashboard.html should have apple-touch-icon"
    
    def test_dashboard_loads_pwa_scripts(self):
        """Verify dashboard.html loads PWA scripts"""
        template_path = Path(__file__).parent.parent / 'backend' / 'dashboard' / 'templates' / 'dashboard.html'
        with open(template_path, 'r', encoding='utf-8') as f:
            content = f.read()
        
        assert 'pwa.js' in content, "dashboard.html should load pwa.js"
        assert 'sync-status.js' in content, "dashboard.html should load sync-status.js"
    
    def test_dashboard_loads_pwa_css(self):
        """Verify dashboard.html loads PWA CSS"""
        template_path = Path(__file__).parent.parent / 'backend' / 'dashboard' / 'templates' / 'dashboard.html'
        with open(template_path, 'r', encoding='utf-8') as f:
            content = f.read()
        
        assert 'pwa.css' in content, "dashboard.html should load pwa.css"
    
    def test_dashboard_has_sync_status_indicator(self):
        """Verify dashboard.html has sync status indicator"""
        template_path = Path(__file__).parent.parent / 'backend' / 'dashboard' / 'templates' / 'dashboard.html'
        with open(template_path, 'r', encoding='utf-8') as f:
            content = f.read()
        
        assert 'sync-status' in content, "dashboard.html should have sync status indicator"
    
    def test_dashboard_has_accessibility_skip_link(self):
        """Verify dashboard.html has skip-to-content link for accessibility"""
        template_path = Path(__file__).parent.parent / 'backend' / 'dashboard' / 'templates' / 'dashboard.html'
        with open(template_path, 'r', encoding='utf-8') as f:
            content = f.read()
        
        assert 'skip-to-content' in content, "dashboard.html should have skip-to-content link"


class TestOfflineSupport:
    """Test offline functionality configuration"""
    
    def test_service_worker_caches_static_assets(self):
        """Verify service worker caches essential assets"""
        sw_path = Path(__file__).parent.parent / 'backend' / 'dashboard' / 'static' / 'sw.js'
        with open(sw_path, 'r') as f:
            content = f.read()
        
        # Should cache some static assets
        assert 'cache.addAll' in content or 'cache.put' in content, \
            "Service Worker should cache static assets"
    
    def test_service_worker_handles_offline_requests(self):
        """Verify service worker handles offline requests"""
        sw_path = Path(__file__).parent.parent / 'backend' / 'dashboard' / 'static' / 'sw.js'
        with open(sw_path, 'r') as f:
            content = f.read()
        
        assert 'catch' in content, \
            "Service Worker should handle failed requests (offline scenarios)"


class TestProgressiveEnhancements:
    """Test progressive UI enhancements"""
    
    def test_skeleton_loading_styles_exist(self):
        """Verify skeleton/loading styles are defined"""
        css_path = Path(__file__).parent.parent / 'backend' / 'dashboard' / 'static' / 'css' / 'pwa.css'
        with open(css_path, 'r') as f:
            content = f.read()
        
        assert '.skeleton' in content, "pwa.css should have skeleton loading styles"
    
    def test_pending_badge_styles_exist(self):
        """Verify pending transaction badge styles are defined"""
        css_path = Path(__file__).parent.parent / 'backend' / 'dashboard' / 'static' / 'css' / 'pwa.css'
        with open(css_path, 'r') as f:
            content = f.read()
        
        assert '.pending-badge' in content, "pwa.css should have pending badge styles"
    
    def test_responsive_mobile_styles(self):
        """Verify responsive mobile styles are present"""
        css_path = Path(__file__).parent.parent / 'backend' / 'dashboard' / 'static' / 'css' / 'pwa.css'
        with open(css_path, 'r') as f:
            content = f.read()
        
        assert '@media' in content, "pwa.css should have responsive media queries"
        assert 'max-width' in content or 'min-width' in content, \
            "pwa.css should have mobile breakpoints"


if __name__ == '__main__':
    pytest.main([__file__, '-v'])
