variable "hcloud_token" {
  description = "Hetzner Cloud API token with read/write access. Prefer exporting HCLOUD_TOKEN instead of setting this."
  type        = string
  sensitive   = true
  default     = null
}

variable "name" {
  description = "Name of the server and firewall."
  type        = string
  default     = "zoho-mcp"
}

variable "server_type" {
  description = "Hetzner server type. cx22 (2 vCPU / 4 GB) is ample."
  type        = string
  default     = "cx22"
}

variable "image" {
  description = "Operating system image."
  type        = string
  default     = "ubuntu-24.04"
}

variable "location" {
  description = "Hetzner location, e.g. fsn1, nbg1, hel1, ash, hil."
  type        = string
  default     = "fsn1"
}

variable "ssh_key_name" {
  description = "Name of the SSH key already registered in the Hetzner project."
  type        = string
}

variable "ssh_allowed_cidrs" {
  description = "CIDR ranges allowed to reach port 22. Narrow this to your own address; the default is deliberately open but you should not leave it."
  type        = list(string)
  default     = ["0.0.0.0/0", "::/0"]
}

variable "site_address" {
  description = "Public hostname that resolves to this server, e.g. mcp.example.com. Create the A/AAAA record after apply."
  type        = string
}

variable "acme_email" {
  description = "Contact email for Let's Encrypt certificate notifications."
  type        = string
}

variable "repo_url" {
  description = "Git repository to deploy."
  type        = string
  default     = "https://github.com/aceAaronCharles/Zoho-MCP.git"
}

variable "repo_ref" {
  description = "Branch or tag to check out."
  type        = string
  default     = "main"
}

variable "autostart" {
  description = "Bring the Docker stack up during cloud-init (yes) or leave it for you to configure and start over SSH (no)."
  type        = string
  default     = "no"

  validation {
    condition     = contains(["yes", "no"], var.autostart)
    error_message = "autostart must be \"yes\" or \"no\"."
  }
}
