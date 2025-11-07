module.exports = {
  apps: [
    {
      name: 'backend',
      script: 'venv/bin/python',
      args: 'app.py',
      cwd: '/godfather/backend',
      interpreter: 'none',
      out_file: '/var/log/godfather-backend.log',
      error_file: '/var/log/godfather-backend-error.log',
      time: true,
      autorestart: true,
      max_restarts: 10,
      min_uptime: '10s',
    },
    {
      name: 'frontend',
      script: 'node_modules/.bin/next',
      args: 'start',
      cwd: '/godfather/frontend',
      interpreter: 'node',
      out_file: '/var/log/godfather-frontend.log',
      error_file: '/var/log/godfather-frontend-error.log',
      time: true,
      autorestart: true,
      max_restarts: 10,
      min_uptime: '10s',
      env: {
        NODE_ENV: 'production',
      },
    },
  ],
};
