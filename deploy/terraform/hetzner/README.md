# Hetzner Cloud example

Provisions a single server that bootstraps itself with
[`deploy/cloud-init.yaml`](../../cloud-init.yaml): Docker, a firewall, the
repository at `/opt/zoho-mcp`, and a generated `MCP_SECRET_KEY`. It does **not**
place any Zoho or OIDC secret in the instance's user-data.

## Usage

```bash
# 1. API token (read/write) from the Hetzner Cloud console
export HCLOUD_TOKEN="..."

# 2. Your SSH key must already be registered in the project
ssh-keygen -t ed25519 -f ~/.ssh/zoho_mcp        # if you don't have one
#    Hetzner console -> Security -> SSH keys -> Add, or:
#    hcloud ssh-key create --name my-laptop --public-key-from-file ~/.ssh/zoho_mcp.pub

cd deploy/terraform/hetzner
cp terraform.tfvars.example terraform.tfvars
$EDITOR terraform.tfvars        # ssh_key_name, site_address, acme_email

terraform init
terraform plan
terraform apply
```

Then create the DNS record it prints, wait for cloud-init, and follow
`/root/NEXT-STEPS.txt` on the server. The full runbook is in
[DEPLOY.md](../../../DEPLOY.md).

## Other providers

`deploy/cloud-init.yaml` is not Hetzner specific. Any provider that accepts
cloud-init user-data works — DigitalOcean, Linode, Vultr, Oracle Cloud, AWS
EC2 (use an `ubuntu-24.04` AMI and pass the file as `user_data`). Replace the
`@@PLACEHOLDERS@@` by hand or with your own templating, and open ports 22, 80
and 443 in the provider's firewall/security group.

## Costs

A `cx22` (2 vCPU / 4 GB) runs comfortably in the low single-digit euros per
month. The workload is I/O bound; a `cx22` or smaller is plenty.
