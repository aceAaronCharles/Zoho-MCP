import http from 'http';
import { exec } from 'child_process';
import * as url from 'url';

const CLIENT_ID = 'REMOVED_CLIENT_ID';
const CLIENT_SECRET = 'REMOVED_CLIENT_SECRET';
const REDIRECT_URI = 'http://localhost:8080/callback';
const SCOPES = 'ZohoCRM.modules.ALL,ZohoCRM.settings.ALL';

console.log('\n🔐 Zoho CRM OAuth Setup\n');
console.log('Follow these steps to get your refresh token:\n');

// Step 1: Generate authorization URL
const authUrl = `https://accounts.zoho.com/oauth/v2/auth?scope=${SCOPES}&client_id=${CLIENT_ID}&response_type=code&access_type=offline&redirect_uri=${encodeURIComponent(REDIRECT_URI)}`;

console.log('1. Opening browser to authorize the application...\n');
console.log('   Authorization URL:');
console.log(`   ${authUrl}\n`);

// Create a simple HTTP server to receive the callback
const server = http.createServer(async (req, res) => {
  const parsedUrl = url.parse(req.url, true);
  
  if (parsedUrl.pathname === '/callback') {
    const code = parsedUrl.query.code;
    
    if (code) {
      res.writeHead(200, { 'Content-Type': 'text/html' });
      res.end('<h1>Authorization successful!</h1><p>You can close this window and return to the terminal.</p>');
      
      console.log('\n✅ Authorization code received!\n');
      console.log('2. Exchanging code for refresh token...\n');
      
      // Exchange code for refresh token
      try {
        const response = await fetch('https://accounts.zoho.com/oauth/v2/token', {
          method: 'POST',
          headers: {
            'Content-Type': 'application/x-www-form-urlencoded',
          },
          body: new URLSearchParams({
            code: code,
            client_id: CLIENT_ID,
            client_secret: CLIENT_SECRET,
            redirect_uri: REDIRECT_URI,
            grant_type: 'authorization_code',
          }),
        });
        
        const data = await response.json();
        
        if (data.refresh_token) {
          console.log('✅ Success! Your refresh token is:\n');
          console.log(`   ${data.refresh_token}\n`);
          console.log('3. Add this to your .env file:\n');
          console.log(`   ZOHO_REFRESH_TOKEN=${data.refresh_token}\n`);
          console.log('4. Or set it as an environment variable when configuring the MCP server in Warp.\n');
        } else {
          console.error('❌ Error:', data);
        }
      } catch (error) {
        console.error('❌ Error exchanging code:', error.message);
      }
      
      server.close();
      process.exit(0);
    } else {
      res.writeHead(400, { 'Content-Type': 'text/plain' });
      res.end('No authorization code received');
      server.close();
      process.exit(1);
    }
  }
});

server.listen(8080, () => {
  console.log('2. Waiting for authorization callback on http://localhost:8080/callback\n');
  
  // Try to open the browser automatically
  const start = process.platform === 'darwin' ? 'open' :
                process.platform === 'win32' ? 'start' : 'xdg-open';
  
  exec(`${start} "${authUrl}"`, (error) => {
    if (error) {
      console.log('   (Could not open browser automatically. Please copy the URL above into your browser)\n');
    }
  });
});
