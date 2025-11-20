import axios, { AxiosInstance } from 'axios';
import { ZohoAuth } from './zoho-auth.js';

export class ZohoClient {
  private auth: ZohoAuth;
  private axios: AxiosInstance;

  constructor(auth: ZohoAuth) {
    this.auth = auth;
    this.axios = axios.create({
      baseURL: this.auth.getApiDomain(),
    });
  }

  private async getHeaders() {
    const token = await this.auth.getAccessToken();
    return {
      'Authorization': `Zoho-oauthtoken ${token}`,
      'Content-Type': 'application/json',
    };
  }

  async getRecords(module: string, params: Record<string, any> = {}) {
    const headers = await this.getHeaders();
    const response = await this.axios.get(`/crm/v2/${module}`, {
      headers,
      params,
    });
    return response.data;
  }

  async getRecordById(module: string, recordId: string) {
    const headers = await this.getHeaders();
    const response = await this.axios.get(`/crm/v2/${module}/${recordId}`, {
      headers,
    });
    return response.data;
  }

  async createRecord(module: string, data: Record<string, any>) {
    const headers = await this.getHeaders();
    const response = await this.axios.post(
      `/crm/v2/${module}`,
      { data: [data] },
      { headers }
    );
    return response.data;
  }

  async updateRecord(module: string, recordId: string, data: Record<string, any>) {
    const headers = await this.getHeaders();
    const response = await this.axios.put(
      `/crm/v2/${module}/${recordId}`,
      { data: [data] },
      { headers }
    );
    return response.data;
  }

  async deleteRecord(module: string, recordId: string) {
    const headers = await this.getHeaders();
    const response = await this.axios.delete(`/crm/v2/${module}/${recordId}`, {
      headers,
    });
    return response.data;
  }

  async searchRecords(module: string, criteria: string, params: Record<string, any> = {}) {
    const headers = await this.getHeaders();
    const response = await this.axios.get(`/crm/v2/${module}/search`, {
      headers,
      params: {
        criteria,
        ...params,
      },
    });
    return response.data;
  }

  async getFields(module: string) {
    const headers = await this.getHeaders();
    const response = await this.axios.get(`/crm/v2/settings/fields`, {
      headers,
      params: { module },
    });
    return response.data;
  }

  async getModules() {
    const headers = await this.getHeaders();
    const response = await this.axios.get(`/crm/v2/settings/modules`, {
      headers,
    });
    return response.data;
  }
}
