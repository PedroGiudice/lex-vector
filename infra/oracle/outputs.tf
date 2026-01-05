# -----------------------------------------------------------------------------
# Network Outputs
# -----------------------------------------------------------------------------
output "vcn_id" {
  description = "OCID of the VCN"
  value       = oci_core_vcn.main.id
}

output "vcn_cidr" {
  description = "CIDR block of the VCN"
  value       = oci_core_vcn.main.cidr_blocks[0]
}

output "subnet_id" {
  description = "OCID of the public subnet"
  value       = oci_core_subnet.public.id
}

output "internet_gateway_id" {
  description = "OCID of the Internet Gateway"
  value       = oci_core_internet_gateway.main.id
}

output "network_security_group_id" {
  description = "OCID of the Network Security Group"
  value       = oci_core_network_security_group.app.id
}

# -----------------------------------------------------------------------------
# Compute Outputs
# -----------------------------------------------------------------------------
output "instance_id" {
  description = "OCID of the compute instance"
  value       = oci_core_instance.app.id
}

output "instance_state" {
  description = "Current state of the instance"
  value       = oci_core_instance.app.state
}

output "instance_shape" {
  description = "Shape of the compute instance"
  value       = oci_core_instance.app.shape
}

output "instance_ocpus" {
  description = "Number of OCPUs allocated"
  value       = oci_core_instance.app.shape_config[0].ocpus
}

output "instance_memory_gb" {
  description = "Memory allocated in GB"
  value       = oci_core_instance.app.shape_config[0].memory_in_gbs
}

# -----------------------------------------------------------------------------
# IP Address Outputs
# -----------------------------------------------------------------------------
output "instance_public_ip" {
  description = "Public IP address of the instance"
  value       = oci_core_instance.app.public_ip
}

output "instance_private_ip" {
  description = "Private IP address of the instance"
  value       = oci_core_instance.app.private_ip
}

output "reserved_public_ip" {
  description = "Reserved public IP address"
  value       = oci_core_public_ip.app.ip_address
}

# -----------------------------------------------------------------------------
# Connection Information
# -----------------------------------------------------------------------------
output "ssh_connection_command" {
  description = "SSH command to connect to the instance"
  value       = "ssh -i <your-private-key> opc@${oci_core_public_ip.app.ip_address}"
}

output "instance_hostname" {
  description = "Hostname of the instance"
  value       = "${oci_core_instance.app.display_name}.${oci_core_subnet.public.dns_label}.${oci_core_vcn.main.dns_label}.oraclevcn.com"
}

# -----------------------------------------------------------------------------
# Image Information
# -----------------------------------------------------------------------------
output "instance_image_id" {
  description = "OCID of the image used for the instance"
  value       = data.oci_core_images.oracle_linux_arm.images[0].id
}

output "instance_image_name" {
  description = "Name of the image used for the instance"
  value       = data.oci_core_images.oracle_linux_arm.images[0].display_name
}

# -----------------------------------------------------------------------------
# Deployment URLs
# -----------------------------------------------------------------------------
output "application_url_http" {
  description = "HTTP URL to access the application"
  value       = "http://${oci_core_public_ip.app.ip_address}"
}

output "application_url_https" {
  description = "HTTPS URL to access the application (after SSL setup)"
  value       = "https://${var.domain}"
}

output "application_direct_port" {
  description = "Direct access to application port"
  value       = "http://${oci_core_public_ip.app.ip_address}:3000"
}

# -----------------------------------------------------------------------------
# Resource Summary
# -----------------------------------------------------------------------------
output "deployment_summary" {
  description = "Summary of deployed resources"
  value = {
    environment      = var.environment
    project          = var.project_name
    region           = var.region
    availability_domain = data.oci_identity_availability_domains.ads.availability_domains[0].name
    instance_shape   = "${var.instance_shape} (${var.instance_ocpus} OCPU, ${var.instance_memory_gb} GB RAM)"
    public_ip        = oci_core_public_ip.app.ip_address
    always_free      = true
  }
}
