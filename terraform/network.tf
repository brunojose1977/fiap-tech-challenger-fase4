data "aws_availability_zones" "available" {
  state = "available"
}

data "aws_vpc" "default" {
  count   = var.create_dedicated_vpc ? 0 : 1
  default = true
}

data "aws_subnets" "default" {
  count = var.create_dedicated_vpc ? 0 : 1
  filter {
    name   = "vpc-id"
    values = [data.aws_vpc.default[0].id]
  }
}

# Na VPC default, filtra apenas subnets com rota 0.0.0.0/0 -> IGW (necessário para Fargate puxar imagem do ECR).
data "aws_route_table" "default_subnet" {
  for_each  = var.create_dedicated_vpc ? toset([]) : toset(data.aws_subnets.default[0].ids)
  subnet_id = each.value
}

locals {
  default_public_subnet_ids = [
    for sid in(var.create_dedicated_vpc ? [] : data.aws_subnets.default[0].ids) : sid
    if try(
      anytrue([
        for route in data.aws_route_table.default_subnet[sid].routes :
        route.cidr_block == "0.0.0.0/0" && startswith(route.gateway_id, "igw-")
      ]),
      false,
    )
  ]
}

resource "aws_vpc" "project" {
  count                = var.create_dedicated_vpc ? 1 : 0
  cidr_block           = var.vpc_cidr
  enable_dns_hostnames = true
  enable_dns_support   = true

  tags = {
    Name = "${local.name_prefix}-vpc"
  }
}

resource "aws_internet_gateway" "project" {
  count  = var.create_dedicated_vpc ? 1 : 0
  vpc_id = aws_vpc.project[0].id

  tags = {
    Name = "${local.name_prefix}-igw"
  }
}

resource "aws_subnet" "public" {
  count                   = var.create_dedicated_vpc ? 2 : 0
  vpc_id                  = aws_vpc.project[0].id
  cidr_block              = cidrsubnet(var.vpc_cidr, 8, count.index + 1)
  availability_zone       = data.aws_availability_zones.available.names[count.index]
  map_public_ip_on_launch = true

  tags = {
    Name = "${local.name_prefix}-public-${count.index + 1}"
  }
}

resource "aws_route_table" "public" {
  count  = var.create_dedicated_vpc ? 1 : 0
  vpc_id = aws_vpc.project[0].id

  route {
    cidr_block = "0.0.0.0/0"
    gateway_id = aws_internet_gateway.project[0].id
  }

  tags = {
    Name = "${local.name_prefix}-public-rt"
  }
}

resource "aws_route_table_association" "public" {
  count          = var.create_dedicated_vpc ? 2 : 0
  subnet_id      = aws_subnet.public[count.index].id
  route_table_id = aws_route_table.public[0].id
}
