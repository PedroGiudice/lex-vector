# -----------------------------------------------------------------------------
# Data Sources
# -----------------------------------------------------------------------------

# Get the latest Oracle Linux image for ARM (A1)
data "oci_core_images" "oracle_linux_arm" {
  compartment_id           = var.compartment_ocid
  operating_system         = "Oracle Linux"
  operating_system_version = "8"
  shape                    = var.instance_shape
  sort_by                  = "TIMECREATED"
  sort_order               = "DESC"

  filter {
    name   = "display_name"
    values = ["^Oracle-Linux-8\\.[0-9]+-aarch64-.*$"]
    regex  = true
  }
}

# Get availability domains
data "oci_identity_availability_domains" "ads" {
  compartment_id = var.tenancy_ocid
}

# -----------------------------------------------------------------------------
# Compute Instance - Always Free Tier (VM.Standard.A1.Flex)
# -----------------------------------------------------------------------------
resource "oci_core_instance" "app" {
  compartment_id      = var.compartment_ocid
  availability_domain = data.oci_identity_availability_domains.ads.availability_domains[0].name
  display_name        = "${var.project_name}-instance-${var.environment}"
  shape               = var.instance_shape

  # Always Free: Up to 4 OCPUs and 24GB RAM total for A1 shapes
  shape_config {
    ocpus         = var.instance_ocpus
    memory_in_gbs = var.instance_memory_gb
  }

  source_details {
    source_type             = "image"
    source_id               = data.oci_core_images.oracle_linux_arm.images[0].id
    boot_volume_size_in_gbs = var.boot_volume_size_gb
  }

  create_vnic_details {
    subnet_id                 = oci_core_subnet.public.id
    assign_public_ip          = true
    display_name              = "${var.project_name}-vnic-${var.environment}"
    hostname_label            = "legalwb"
    nsg_ids                   = [oci_core_network_security_group.app.id]
    skip_source_dest_check    = false
    assign_ipv6ip             = false
  }

  metadata = {
    ssh_authorized_keys = var.ssh_public_key
    user_data = base64encode(<<-EOF
      #!/bin/bash

      # Update system
      dnf update -y

      # Install essential packages
      dnf install -y git curl wget vim nano htop

      # Install Node.js 20.x (LTS)
      dnf module enable -y nodejs:20
      dnf install -y nodejs

      # Install Bun
      curl -fsSL https://bun.sh/install | bash

      # Install Docker
      dnf config-manager --add-repo https://download.docker.com/linux/centos/docker-ce.repo
      dnf install -y docker-ce docker-ce-cli containerd.io docker-compose-plugin
      systemctl enable docker
      systemctl start docker

      # Add opc user to docker group
      usermod -aG docker opc

      # Install Nginx
      dnf install -y nginx
      systemctl enable nginx

      # Install Certbot for SSL
      dnf install -y certbot python3-certbot-nginx

      # Create application directory
      mkdir -p /opt/legal-workbench
      chown opc:opc /opt/legal-workbench

      # Configure firewall
      firewall-cmd --permanent --add-service=http
      firewall-cmd --permanent --add-service=https
      firewall-cmd --permanent --add-port=3000/tcp
      firewall-cmd --reload

      # Log completion
      echo "Cloud-init completed at $(date)" >> /var/log/cloud-init-complete.log
    EOF
    )
  }

  agent_config {
    is_management_disabled = false
    is_monitoring_disabled = false
    plugins_config {
      name          = "Vulnerability Scanning"
      desired_state = "ENABLED"
    }
    plugins_config {
      name          = "OS Management Service Agent"
      desired_state = "ENABLED"
    }
    plugins_config {
      name          = "Compute Instance Run Command"
      desired_state = "ENABLED"
    }
    plugins_config {
      name          = "Compute Instance Monitoring"
      desired_state = "ENABLED"
    }
  }

  freeform_tags = {
    Environment = var.environment
    Project     = var.project_name
    ManagedBy   = "terraform"
    AlwaysFree  = "true"
  }

  # Preserve boot volume on instance termination
  preserve_boot_volume = true
}

# -----------------------------------------------------------------------------
# Reserved Public IP (Optional - for static IP)
# -----------------------------------------------------------------------------
resource "oci_core_public_ip" "app" {
  compartment_id = var.compartment_ocid
  display_name   = "${var.project_name}-public-ip-${var.environment}"
  lifetime       = "RESERVED"
  private_ip_id  = data.oci_core_private_ips.app.private_ips[0].id

  freeform_tags = {
    Environment = var.environment
    Project     = var.project_name
    ManagedBy   = "terraform"
  }
}

data "oci_core_private_ips" "app" {
  vnic_id = oci_core_instance.app.create_vnic_details[0].vnic_id

  depends_on = [oci_core_instance.app]
}

data "oci_core_vnic_attachments" "app" {
  compartment_id = var.compartment_ocid
  instance_id    = oci_core_instance.app.id
}

data "oci_core_vnic" "app" {
  vnic_id = data.oci_core_vnic_attachments.app.vnic_attachments[0].vnic_id
}
