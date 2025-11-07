require('dotenv').config({ path: '/godfather/.env' });

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
      env: {
        RUNPOD_API_KEY: process.env.RUNPOD_API_KEY,
        CLERK_SECRET_KEY: process.env.CLERK_SECRET_KEY,
        DISCORD_BOT_TOKEN: process.env.DISCORD_BOT_TOKEN,
        DISCORD_GUILD_ID: process.env.DISCORD_GUILD_ID,
        ADMIN_ROLE_ID: process.env.ADMIN_ROLE_ID,
        MONGODB_URI: process.env.MONGODB_URI,
        JWT_SECRET: process.env.JWT_SECRET,
        LOG_LEVEL: process.env.LOG_LEVEL || 'INFO',
      },
    },
    {
      name: 'frontend',
      script: 'npm',
      args: 'start',
      cwd: '/godfather/frontend',
      interpreter: 'none',
      out_file: '/var/log/godfather-frontend.log',
      error_file: '/var/log/godfather-frontend-error.log',
      time: true,
      autorestart: true,
      max_restarts: 10,
      min_uptime: '10s',
      env: {
        NODE_ENV: 'production',
        HOSTNAME: '0.0.0.0',
        PORT: '3000',
      },
    },
  ],
};
