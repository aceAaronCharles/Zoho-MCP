import axios from 'axios';

interface TokenResponse {
  access_token: string;
  expires_in: number;
  api_domain: string;
  token_type: string;
}

export class ZohoAuth {
  private clientId: string;
  private clientSecret: string;
  private refreshToken: string;
  private accessToken: string | null = null;
  private tokenExpiry: number = 0;
  private apiDomain: string;

  constructor() {
    this.clientId = process.env.ZOHO_CLIENT_ID || '';
    this.clientSecret = process.env.ZOHO_CLIENT_SECRET || '';
    this.refreshToken = process.env.ZOHO_REFRESH_TOKEN || '';
    this.apiDomain = process.env.ZOHO_API_DOMAIN || 'https://www.zohoapis.com';

    if (!this.clientId || !this.clientSecret) {
      throw new Error('ZOHO_CLIENT_ID and ZOHO_CLIENT_SECRET are required');
    }
  }

  async getAccessToken(): Promise<string> {
    if (this.accessToken && Date.now() < this.tokenExpiry) {
      return this.accessToken;
    }

    if (!this.refreshToken) {
      throw new Error('ZOHO_REFRESH_TOKEN not found. Please set it in environment variables.');
    }

    try {
      const response = await axios.post<TokenResponse>(
        'https://accounts.zoho.com/oauth/v2/token',
        null,
        {
          params: {
            refresh_token: this.refreshToken,
            client_id: this.clientId,
            client_secret: this.clientSecret,
            grant_type: 'refresh_token'
          }
        }
      );

      this.accessToken = response.data.access_token;
      this.tokenExpiry = Date.now() + (response.data.expires_in * 1000) - 60000;
      
      if (response.data.api_domain) {
        this.apiDomain = response.data.api_domain;
      }

      return this.accessToken;
    } catch (error: any) {
      throw new Error(`Failed to refresh access token: ${error.response?.data?.error || error.message}`);
    }
  }

  getApiDomain(): string {
    return this.apiDomain;
  }
}
