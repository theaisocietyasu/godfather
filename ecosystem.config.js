const fs = require('fs');
const path = require('path');

// Read .env file if it exists
const envPath = '/godfather/.env';
const envVars = {};

if (fs.existsSync(envPath)) {
  const envContent = fs.readFileSync(envPath, 'utf8');
  envContent.split('\n').forEach(line => {
    line = line.trim();
    if (line && !line.startsWith('#')) {
      const match = line.match(/^([^=]+)=(.*)$/);
      if (match) {
        const key = match[1].trim();
        let value = match[2].trim();
        // Remove surrounding quotes if present
        if ((value.startsWith('"') && value.endsWith('"')) || 
            (value.startsWith("'") && value.endsWith("'"))) {
          value = value.slice(1, -1);
        }
        envVars[key] = value;
      }
    }
  });
}

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
        RUNPOD_API_KEY: envVars.RUNPOD_API_KEY,
        DISCORD_BOT_TOKEN: envVars.DISCORD_BOT_TOKEN,
        
        DISCORD_GUILD_ID: envVars.DISCORD_GUILD_ID,
        ADMIN_ROLE_ID: envVars.ADMIN_ROLE_ID,
        MONGODB_URI: envVars.MONGODB_URI || 'mongodb://localhost:27017/godfather',
        JWT_SECRET: envVars.JWT_SECRET || 'your-secret-key',
        LOG_LEVEL: envVars.LOG_LEVEL || 'INFO',
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
        BACKEND_URL: 'http://localhost:5000',
        RUNPOD_API_KEY: envVars.RUNPOD_API_KEY,
        DISCORD_CLIENT_ID: envVars.DISCORD_CLIENT_ID,
        DISCORD_CLIENT_SECRET: envVars.DISCORD_CLIENT_SECRET,
        NEXTAUTH_SECRET: envVars.NEXTAUTH_SECRET,
        NEXTAUTH_URL: envVars.NEXTAUTH_URL,
        DISCORD_BOT_TOKEN: envVars.DISCORD_BOT_TOKEN,
        DISCORD_GUILD_ID: envVars.DISCORD_GUILD_ID,
        ADMIN_ROLE_ID: envVars.ADMIN_ROLE_ID,
        MONGODB_URI: envVars.MONGODB_URI,
        NEXT_PUBLIC_APP_URL: envVars.NEXT_PUBLIC_APP_URL,
        JWT_SECRET: envVars.JWT_SECRET,
      },
    },
  ],
};
