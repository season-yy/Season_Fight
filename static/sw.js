/* ==========================================
 * Season_Fight Service Worker
 * 离线缓存策略：HTML/CSS/JS 走 cache-first，API 走 network-first
 * ========================================== */

const CACHE_NAME = 'season-fight-v1';
const STATIC_ASSETS = [
    '/',
    '/static/css/main.css',
    '/static/css/timer.css',
    '/static/css/calendar.css',
    '/static/css/stats.css',
    '/static/js/utils.js',
    '/static/js/app.js',
    '/static/js/tasks.js',
    '/static/js/timer.js',
    '/static/js/calendar.js',
    '/static/js/stats.js',
    '/static/manifest.json',
    '/static/icons/icon.svg',
    '/static/icons/icon-192.png',
    '/static/icons/icon-512.png',
];

// 安装：预缓存关键资源
self.addEventListener('install', event => {
    event.waitUntil(
        caches.open(CACHE_NAME)
            .then(cache => cache.addAll(STATIC_ASSETS))
            .then(() => self.skipWaiting())
    );
});

// 激活：清理旧缓存
self.addEventListener('activate', event => {
    event.waitUntil(
        caches.keys().then(keys => Promise.all(
            keys.filter(key => key !== CACHE_NAME)
                .map(key => caches.delete(key))
        )).then(() => self.clients.claim())
    );
});

// 拦截请求
self.addEventListener('fetch', event => {
    const req = event.request;

    // 仅处理 GET
    if (req.method !== 'GET') return;

    const url = new URL(req.url);

    // API 请求：网络优先，离线时回退缓存
    if (url.pathname.startsWith('/api/')) {
        event.respondWith(networkFirst(req));
        return;
    }

    // 第三方 CDN（Chart.js）
    if (url.hostname !== self.location.hostname) {
        event.respondWith(cacheFirst(req));
        return;
    }

    // 静态资源 / 页面：缓存优先
    event.respondWith(cacheFirst(req));
});

// ====== 策略实现 ======

async function cacheFirst(req) {
    const cached = await caches.match(req);
    if (cached) return cached;
    try {
        const fresh = await fetch(req);
        if (fresh.ok) {
            const cache = await caches.open(CACHE_NAME);
            cache.put(req, fresh.clone());
        }
        return fresh;
    } catch (e) {
        return cached || Response.error();
    }
}

async function networkFirst(req) {
    try {
        const fresh = await fetch(req);
        if (fresh.ok) {
            const cache = await caches.open(CACHE_NAME);
            cache.put(req, fresh.clone());
        }
        return fresh;
    } catch (e) {
        const cached = await caches.match(req);
        return cached || new Response(
            JSON.stringify({ error: 'offline', message: '当前离线，无法连接服务器' }),
            { status: 503, headers: { 'Content-Type': 'application/json' } }
        );
    }
}