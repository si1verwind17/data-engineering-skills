terraform {
  required_providers {
    aws = { source = "hashicorp/aws", version = "~> 6.0" }
  }
}

resource "aws_rds_cluster_parameter_group" "shop_aurora16" {
  name   = "shop-aurora16"
  family = "aurora-postgresql16"

  parameter {
    name         = "rds.logical_replication"
    value        = "1"
    apply_method = "pending-reboot"
  }
}

resource "aws_rds_cluster" "shop" {
  cluster_identifier              = "shop"
  engine                          = "aurora-postgresql"
  engine_version                  = "16.4"
  db_cluster_parameter_group_name = aws_rds_cluster_parameter_group.shop_aurora16.name
  master_username                 = "shop_admin"
  manage_master_user_password     = true
}

resource "aws_rds_cluster_instance" "shop_writer" {
  identifier         = "shop-writer"
  cluster_identifier = aws_rds_cluster.shop.id
  instance_class     = "db.r6g.large"
  engine             = aws_rds_cluster.shop.engine
}

resource "aws_rds_cluster_instance" "shop_reader" {
  identifier         = "shop-reader"
  cluster_identifier = aws_rds_cluster.shop.id
  instance_class     = "db.r6g.large"
  engine             = aws_rds_cluster.shop.engine
}

resource "aws_db_instance" "warehouse" {
  identifier        = "warehouse"
  engine            = "postgres"
  engine_version    = "16.4"
  instance_class    = "db.r6g.xlarge"
  allocated_storage = 1000
  username          = "wh_admin"
  manage_master_user_password = true
}

resource "aws_ecs_cluster" "data" {
  name = "data-services"
}

resource "aws_kinesis_stream" "orders_changes" {
  name             = "orders-changes"
  retention_period = 168
  stream_mode_details { stream_mode = "ON_DEMAND" }
}
