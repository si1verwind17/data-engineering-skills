provider "aws" {
  region = "eu-west-1"
}

resource "aws_s3_bucket" "lake_raw" {
  bucket = "shop-lake-raw"
}

resource "aws_s3_bucket" "lake_marts" {
  bucket = "shop-lake-marts"
}

resource "aws_glue_catalog_database" "raw" {
  name = "raw"
}

resource "aws_glue_catalog_database" "marts" {
  name = "marts"
}

resource "aws_athena_workgroup" "analytics" {
  name = "analytics"
}

module "eks" {
  source          = "terraform-aws-modules/eks/aws"
  cluster_name    = "shop-data"
  cluster_version = "1.33"
}

resource "aws_db_instance" "orders_replica" {
  identifier          = "orders-replica"
  replicate_source_db = "orders-primary"
  instance_class      = "db.r6g.large"
}
