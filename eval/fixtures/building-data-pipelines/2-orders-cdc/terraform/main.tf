terraform {
  required_providers {
    aws = { source = "hashicorp/aws", version = "~> 6.0" }
  }
}

resource "aws_db_parameter_group" "shop_pg16" {
  name   = "shop-pg16"
  family = "postgres16"

  parameter {
    name         = "rds.logical_replication"
    value        = "1"
    apply_method = "pending-reboot"
  }
}

resource "aws_db_instance" "shop_primary" {
  identifier           = "shop-primary"
  engine               = "postgres"
  engine_version       = "16.4"
  instance_class       = "db.r6g.large"
  allocated_storage    = 400
  multi_az             = true
  parameter_group_name = aws_db_parameter_group.shop_pg16.name
  username             = "shop_admin"
  manage_master_user_password = true
}

resource "aws_db_instance" "shop_replica" {
  identifier           = "shop-replica"
  replicate_source_db  = aws_db_instance.shop_primary.identifier
  instance_class       = "db.r6g.large"
  parameter_group_name = aws_db_parameter_group.shop_pg16.name
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
