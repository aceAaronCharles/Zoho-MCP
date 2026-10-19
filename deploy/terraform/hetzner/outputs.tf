output "server_ipv4" {
  description = "Public IPv4 address of the new server."
  value       = hcloud_server.zoho.ipv4_address
}

output "dns_instruction" {
  description = "Create this DNS record before the server requests a certificate."
  value       = "Point ${var.site_address} (A) at ${hcloud_server.zoho.ipv4_address}"
}

output "ssh_command" {
  description = "SSH into the new server."
  value       = "ssh root@${hcloud_server.zoho.ipv4_address}"
}

output "next_steps" {
  description = "What to do once apply finishes."
  value       = <<-EOT
    1. Create the DNS record:  ${var.site_address} A ${hcloud_server.zoho.ipv4_address}
    2. Wait for cloud-init to finish, then check:  ssh root@${hcloud_server.zoho.ipv4_address} tail -f /var/log/zoho-bootstrap.log
    3. Read the on-box checklist:  cat /root/NEXT-STEPS.txt
    4. Fill in OIDC settings:      sudoedit /opt/zoho-mcp/.env
    5. Start the stack:            cd /opt/zoho-mcp && docker compose -f docker-compose.prod.yml up -d --build
  EOT
}
