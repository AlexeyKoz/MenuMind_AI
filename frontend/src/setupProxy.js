const { createProxyMiddleware } = require('http-proxy-middleware');

module.exports = function(app) {
    app.use(
        '/api',
        createProxyMiddleware({
            target: 'http://localhost:8000',
            changeOrigin: true,
            logLevel: 'debug',
            timeout: 30000, // 30 seconds timeout
            proxyTimeout: 30000,
        })
    );
};

