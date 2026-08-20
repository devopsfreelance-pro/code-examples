# GCP: VPC + Cloud Storage multi-región
# Servicios: VPC + Cloud Storage (equivalentes a VPC+S3 en AWS y VNet+Blob en Azure)

resource "google_compute_network" "main" {
  name                    = "demo-vpc"
  auto_create_subnetworks = false
}

resource "google_compute_subnetwork" "private" {
  name          = "demo-private-subnet"
  ip_cidr_range = "10.0.1.0/24"
  region        = "us-central1"
  network       = google_compute_network.main.id

  private_ip_google_access = true
}

resource "google_storage_bucket" "demo" {
  name          = "demo-comparativa-cloud-bucket-gcp"
  location      = "US"
  storage_class = "STANDARD"

  versioning {
    enabled = true
  }
}
