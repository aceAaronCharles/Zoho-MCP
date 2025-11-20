#!/usr/bin/env node

import { Server } from '@modelcontextprotocol/sdk/server/index.js';
import { StdioServerTransport } from '@modelcontextprotocol/sdk/server/stdio.js';
import {
  CallToolRequestSchema,
  ListToolsRequestSchema,
} from '@modelcontextprotocol/sdk/types.js';
import { ZohoAuth } from './zoho-auth.js';
import { ZohoClient } from './zoho-client.js';

const server = new Server(
  {
    name: 'zoho-crm-mcp',
    version: '1.0.0',
  },
  {
    capabilities: {
      tools: {},
    },
  }
);

// Initialize Zoho client
const auth = new ZohoAuth();
const zohoClient = new ZohoClient(auth);

// List available tools
server.setRequestHandler(ListToolsRequestSchema, async () => {
  return {
    tools: [
      {
        name: 'get_crm_records',
        description: 'Retrieve records from a Zoho CRM module (Leads, Contacts, Accounts, Deals, etc.)',
        inputSchema: {
          type: 'object',
          properties: {
            module: {
              type: 'string',
              description: 'CRM module name (e.g., Leads, Contacts, Accounts, Deals)',
            },
            page: {
              type: 'number',
              description: 'Page number for pagination (default: 1)',
            },
            per_page: {
              type: 'number',
              description: 'Records per page (default: 200, max: 200)',
            },
            fields: {
              type: 'string',
              description: 'Comma-separated list of fields to retrieve',
            },
          },
          required: ['module'],
        },
      },
      {
        name: 'get_crm_record',
        description: 'Get a specific record by ID from Zoho CRM',
        inputSchema: {
          type: 'object',
          properties: {
            module: {
              type: 'string',
              description: 'CRM module name (e.g., Leads, Contacts, Accounts, Deals)',
            },
            record_id: {
              type: 'string',
              description: 'The record ID',
            },
          },
          required: ['module', 'record_id'],
        },
      },
      {
        name: 'search_crm_records',
        description: 'Search for records in Zoho CRM using criteria',
        inputSchema: {
          type: 'object',
          properties: {
            module: {
              type: 'string',
              description: 'CRM module name (e.g., Leads, Contacts, Accounts, Deals)',
            },
            criteria: {
              type: 'string',
              description: 'Search criteria (e.g., "(Email:equals:john@example.com)")',
            },
            page: {
              type: 'number',
              description: 'Page number for pagination',
            },
            per_page: {
              type: 'number',
              description: 'Records per page',
            },
          },
          required: ['module', 'criteria'],
        },
      },
      {
        name: 'create_crm_record',
        description: 'Create a new record in Zoho CRM',
        inputSchema: {
          type: 'object',
          properties: {
            module: {
              type: 'string',
              description: 'CRM module name (e.g., Leads, Contacts, Accounts, Deals)',
            },
            data: {
              type: 'object',
              description: 'Record data as JSON object',
            },
          },
          required: ['module', 'data'],
        },
      },
      {
        name: 'update_crm_record',
        description: 'Update an existing record in Zoho CRM',
        inputSchema: {
          type: 'object',
          properties: {
            module: {
              type: 'string',
              description: 'CRM module name (e.g., Leads, Contacts, Accounts, Deals)',
            },
            record_id: {
              type: 'string',
              description: 'The record ID to update',
            },
            data: {
              type: 'object',
              description: 'Updated record data as JSON object',
            },
          },
          required: ['module', 'record_id', 'data'],
        },
      },
      {
        name: 'delete_crm_record',
        description: 'Delete a record from Zoho CRM',
        inputSchema: {
          type: 'object',
          properties: {
            module: {
              type: 'string',
              description: 'CRM module name (e.g., Leads, Contacts, Accounts, Deals)',
            },
            record_id: {
              type: 'string',
              description: 'The record ID to delete',
            },
          },
          required: ['module', 'record_id'],
        },
      },
      {
        name: 'get_crm_modules',
        description: 'List all available CRM modules',
        inputSchema: {
          type: 'object',
          properties: {},
        },
      },
      {
        name: 'get_crm_fields',
        description: 'Get field metadata for a specific CRM module',
        inputSchema: {
          type: 'object',
          properties: {
            module: {
              type: 'string',
              description: 'CRM module name (e.g., Leads, Contacts, Accounts, Deals)',
            },
          },
          required: ['module'],
        },
      },
    ],
  };
});

// Handle tool calls
server.setRequestHandler(CallToolRequestSchema, async (request) => {
  try {
    const { name, arguments: args } = request.params;

    switch (name) {
      case 'get_crm_records': {
        const { module, page, per_page, fields } = args as any;
        const params: any = {};
        if (page) params.page = page;
        if (per_page) params.per_page = per_page;
        if (fields) params.fields = fields;

        const result = await zohoClient.getRecords(module, params);
        return {
          content: [
            {
              type: 'text',
              text: JSON.stringify(result, null, 2),
            },
          ],
        };
      }

      case 'get_crm_record': {
        const { module, record_id } = args as any;
        const result = await zohoClient.getRecordById(module, record_id);
        return {
          content: [
            {
              type: 'text',
              text: JSON.stringify(result, null, 2),
            },
          ],
        };
      }

      case 'search_crm_records': {
        const { module, criteria, page, per_page } = args as any;
        const params: any = {};
        if (page) params.page = page;
        if (per_page) params.per_page = per_page;

        const result = await zohoClient.searchRecords(module, criteria, params);
        return {
          content: [
            {
              type: 'text',
              text: JSON.stringify(result, null, 2),
            },
          ],
        };
      }

      case 'create_crm_record': {
        const { module, data } = args as any;
        const result = await zohoClient.createRecord(module, data);
        return {
          content: [
            {
              type: 'text',
              text: JSON.stringify(result, null, 2),
            },
          ],
        };
      }

      case 'update_crm_record': {
        const { module, record_id, data } = args as any;
        const result = await zohoClient.updateRecord(module, record_id, data);
        return {
          content: [
            {
              type: 'text',
              text: JSON.stringify(result, null, 2),
            },
          ],
        };
      }

      case 'delete_crm_record': {
        const { module, record_id } = args as any;
        const result = await zohoClient.deleteRecord(module, record_id);
        return {
          content: [
            {
              type: 'text',
              text: JSON.stringify(result, null, 2),
            },
          ],
        };
      }

      case 'get_crm_modules': {
        const result = await zohoClient.getModules();
        return {
          content: [
            {
              type: 'text',
              text: JSON.stringify(result, null, 2),
            },
          ],
        };
      }

      case 'get_crm_fields': {
        const { module } = args as any;
        const result = await zohoClient.getFields(module);
        return {
          content: [
            {
              type: 'text',
              text: JSON.stringify(result, null, 2),
            },
          ],
        };
      }

      default:
        throw new Error(`Unknown tool: ${name}`);
    }
  } catch (error: any) {
    return {
      content: [
        {
          type: 'text',
          text: `Error: ${error.message}`,
        },
      ],
      isError: true,
    };
  }
});

// Start the server
async function main() {
  const transport = new StdioServerTransport();
  await server.connect(transport);
  console.error('Zoho CRM MCP Server running on stdio');
}

main().catch((error) => {
  console.error('Server error:', error);
  process.exit(1);
});
