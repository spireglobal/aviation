// Provide these variables either in a parent module, or as
// exported environment variables
// - TF_VAR_project_id;
// - TF_VAR_region; and
// - TF_VAR_airsafe2_token

variable "airsafe2_token" {
  type = string
}
variable "project_id" {
  type = string
}
variable "region" {
  type = string
}

variable "local_output_path" {
  default = "build"
}
variable "function_timeout" {
  type = number
  default = 300
}

provider "google" {
  region = var.region
  project = var.project_id
}


// Create a uniquely named bucket to store the Cloud Function source code
resource "random_id" "suffix" {
  byte_length = 4
}
resource "google_storage_bucket" "source_archives" {
  name = "streamer-source-archives-${random_id.suffix.hex}"
  storage_class = "REGIONAL"
  location = var.region
  force_destroy = true
}

// Archive the function code to a zip file
locals {
  streamer_src_name = "streamer-${timestamp()}.zip"
}
data "archive_file" "local_streamer_source" {
  type = "zip"
  source_dir = "./function"
  output_path = "${var.local_output_path}/${local.streamer_src_name}"
}
// Upload the function code to the source_archives bucket
resource "google_storage_bucket_object" "gcs_streamer_source" {
  cache_control = ""
  name = local.streamer_src_name
  bucket = google_storage_bucket.source_archives.name
  source = data.archive_file.local_streamer_source.output_path
}

// Create the Cloud Functions streamer function
resource "google_cloudfunctions_function" "function_streamer" {
  name = "streamer-${random_id.suffix.hex}"
  project = var.project_id
  region = var.region
  timeout = var.function_timeout
  entry_point = "handler"
  runtime = "python38"
  trigger_http = true
  source_archive_bucket = google_storage_bucket.source_archives.name
  source_archive_object = google_storage_bucket_object.gcs_streamer_source.name
  environment_variables = {
    TIMEOUT = var.function_timeout - 5
    AIRSAFE2_TOKEN = var.airsafe2_token
    LAST_POSITION_TOKEN_BUCKET = google_storage_bucket.source_archives.name
  }
}
// Prevent unauthenticated invocations
resource "google_service_account" "stream-account" {
  account_id = "stream-account"
  display_name = "Streamer Service Account"
}
resource "google_cloudfunctions_function_iam_binding" "streamer_disallow_unauthenticated" {
  project = var.project_id
  region = var.region
  cloud_function = google_cloudfunctions_function.function_streamer.name
  role = "roles/cloudfunctions.invoker"
  members = [
    "serviceAccount:${google_service_account.stream-account.email}"
  ]
  depends_on = [
    google_cloudfunctions_function.function_streamer
  ]
}

// Create a Cloud Scheduler job, that sends an event every N minutes to the PubSub topic
resource "google_cloud_scheduler_job" "stream-schedule" {
  name = "stream-schedule"
  description = "Trigger airsafe-2-stream cloud function"
  schedule = "*/5 * * * *"
  attempt_deadline = "${var.function_timeout}s"

  retry_config {
    retry_count = 0
  }

  http_target {
    uri = google_cloudfunctions_function.function_streamer.https_trigger_url
    oidc_token {
      service_account_email = google_service_account.stream-account.email
    }
  }
}
