// Provide these variables either in a parent module, or as
// exported environment variables
// - TF_VAR_profile;
// - TF_VAR_region; and
// - TF_VAR_airsafe2_token
variable "profile" {
  type = string
}
variable "region" {
  type = string
}
variable "airsafe2_token" {
  type = string
}

provider "aws" {
  profile = var.profile
  region = var.region
}

//THE AWS LAMBDA FUNCTION
resource "aws_lambda_function" "airsafe-2-streamer" {
  function_name = "airsafe-2-streamer"
  role = aws_iam_role.streamer-execution-role.arn

  runtime = "python3.8"
  handler = "handler.handler"
  filename = "lambda.zip"
  timeout = 300

  environment {
    variables = {
      AIRSAFE2_TOKEN = var.airsafe2_token
      LAST_POSITION_TOKEN_BUCKET = aws_s3_bucket.last-position-token.bucket
    }
  }
}
// Create a basic execution role for the streamer lambda
resource "aws_iam_role" "streamer-execution-role" {
  name = "streamer-execution-role"
  assume_role_policy = data.aws_iam_policy_document.streamer-execution-role-policy-doc.json
}
data "aws_iam_policy_document" "streamer-execution-role-policy-doc" {
  statement {
    actions = [
      "sts:AssumeRole"]
    principals {
      identifiers = [
        "lambda.amazonaws.com"
      ]
      type = "Service"
    }
  }
}
// Attach permissions to write Logs
resource "aws_iam_role_policy_attachment" "streamer_basic-execution-role" {
  role = aws_iam_role.streamer-execution-role.name
  policy_arn = "arn:aws:iam::aws:policy/service-role/AWSLambdaBasicExecutionRole"
}

// THE AWS CLOUDWATCH EVENT
resource "aws_cloudwatch_event_rule" "lambda-scheduler" {
  name = "airsafe-2-stream-scheduler"
  schedule_expression = "rate(5 minutes)"
}
// Configure CloudWatch to target the Lambda
resource "aws_cloudwatch_event_target" "airsafe-2-lambda" {
  arn = aws_lambda_function.airsafe-2-streamer.arn
  rule = aws_cloudwatch_event_rule.lambda-scheduler.name
}
// Open the lambda towards the CloudWatch trigger
resource "aws_lambda_permission" "get-triggered-by-cloudwatch-events" {
  action = "lambda:InvokeFunction"
  function_name = aws_lambda_function.airsafe-2-streamer.function_name
  principal = "events.amazonaws.com"
  source_arn = aws_cloudwatch_event_rule.lambda-scheduler.arn
}

// THE S3 BUCKET that stores the position token
resource "aws_s3_bucket" "last-position-token" {
  bucket = "airsafe2-last-position-token"
  acl = "private"
}
// The bucket policy that opens the bucket towards the streamer Lambda
resource "aws_s3_bucket_policy" "latest-position-token-policy" {
  bucket = aws_s3_bucket.last-position-token.id
  policy = data.aws_iam_policy_document.bucket__allow-access-to-streamer-lambda.json
}
data "aws_iam_policy_document" "bucket__allow-access-to-streamer-lambda" {
  statement {
    actions = [
      "s3:*"]
    resources = [
      aws_s3_bucket.last-position-token.arn,
      "${aws_s3_bucket.last-position-token.arn}/*"
    ]
    principals {
      identifiers = [
        aws_iam_role.streamer-execution-role.arn
      ]
      type = "AWS"
    }
  }
}

// The IAM policy that allows the streamer lambda to access the bucket
resource "aws_iam_policy" "access_to-latest_position_token_bucket" {
  name = "access_to-latest_position_token_bucket"
  policy = data.aws_iam_policy_document.lambda__allow-to-access-position_token_bucket.json
}
data "aws_iam_policy_document" "lambda__allow-to-access-position_token_bucket" {
  statement {
    actions = [
      "s3:*"]
    resources = [
      aws_s3_bucket.last-position-token.arn,
      "${aws_s3_bucket.last-position-token.arn}/*"
    ]
  }
}
// Attach the above policy to the Lambda IAM role
resource "aws_iam_role_policy_attachment" "streamer-bucket" {
  role = aws_iam_role.streamer-execution-role.name
  policy_arn = aws_iam_policy.access_to-latest_position_token_bucket.arn
}
