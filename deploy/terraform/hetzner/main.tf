provider "hcloud" {
  token = var.hcloud_token
}

data "hcloud_ssh_key" "admin" {
  name = var.ssh_key_name
}

resource "hcloud_firewall" "zoho" {
  name = "${var.name}-fw"

  rule {
    description = "SSH"
    direction   = "in"
    protocol    = "tcp"
    port        = "22"
    source_ips  = var.ssh_allowed_cidrs
  }

  rule {
    description = "HTTP (ACME challenge + redirect)"
    direction   = "in"
    protocol    = "tcp"
    port        = "80"
    source_ips  = ["0.0.0.0/0", "::/0"]
  }

  rule {
    description = "HTTPS"
    direction   = "in"
    protocol    = "tcp"
    port        = "443"
    source_ips  = ["0.0.0.0/0", "::/0"]
  }

  rule {
    description = "HTTP/3"
    direction   = "in"
    protocol    = "udp"
    port        = "443"
    source_ips  = ["0.0.0.0/0", "::/0"]
  }
}

# Fill the cloud-init placeholders with the configured values.  A chained
# replace() is used (rather than templatefile) so the shell ${VAR} references
# inside the bootstrap script are left untouched.
locals {
  user_data = replace(
    replace(
      replace(
        replace(
          replace(
            file("${path.module}/../../cloud-init.yaml"),
            "@@SITE_ADDRESS@@", var.site_address,
          ),
          "@@ACME_EMAIL@@", var.acme_email,
        ),
        "@@REPO_URL@@", var.repo_url,
      ),
      "@@REPO_REF@@", var.repo_ref,
    ),
    "@@AUTOSTART@@", var.autostart,
  )
}

resource "hcloud_server" "zoho" {
  name         = var.name
  server_type  = var.server_type
  image        = var.image
  location     = var.location
  ssh_keys     = [data.hcloud_ssh_key.admin.id]
  firewall_ids = [hcloud_firewall.zoho.id]
  user_data    = local.user_data

  labels = {
    app = "zoho-mcp"
  }

  lifecycle {
    # cloud-init runs once; changing user_data would force a rebuild, so apply
    # configuration changes on the box instead (or taint deliberately).
    ignore_changes = [user_data]
  }
}
