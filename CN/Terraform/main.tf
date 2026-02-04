# VPC
resource "aws_vpc" "vpc" {
  cidr_block = var.vpc_cidr

  tags = {
    Name = "Destileria_Valles"
  }
}

# Subredes
resource "aws_subnet" "publica" {
  vpc_id                  = aws_vpc.vpc.id
  cidr_block              = var.publica_cidr
  map_public_ip_on_launch = true
  availability_zone       = var.az

  tags = {
    Name = "publica"
  }
}

resource "aws_subnet" "privada" {
  vpc_id            = aws_vpc.vpc.id
  cidr_block        = var.privada_cidr
  availability_zone = var.az

  tags = {
    Name = "privada"
  }
}

# Internet Gateway
resource "aws_internet_gateway" "igw" {
  vpc_id = aws_vpc.vpc.id
    tags = {
        Name = "igw"
    }
}

# Tabla de rutas pública
resource "aws_route_table" "publica_tr" {
  vpc_id = aws_vpc.vpc.id

  route {
    cidr_block = "0.0.0.0/0"
    gateway_id = aws_internet_gateway.igw.id
  }
  tags = {
        Name = "publica_tr"
    }
}

resource "aws_route_table_association" "publica_asoc" {
  subnet_id      = aws_subnet.publica.id
  route_table_id = aws_route_table.publica_tr.id
}

# Tabla de rutas privada
resource "aws_route_table" "privada_tr" {
  vpc_id = aws_vpc.vpc.id
  tags = {
        Name = "privada_tr"
    }

}

resource "aws_route_table_association" "privada_asoc" {
  subnet_id      = aws_subnet.privada.id
  route_table_id = aws_route_table.privada_tr.id
}

# Security Group Proxy
resource "aws_security_group" "proxy_sg" {
  name   = "proxy_sg"
  vpc_id = aws_vpc.vpc.id

  ingress {
    description = "HTTP desde Internet"
    from_port   = 80
    to_port     = 80
    protocol    = "tcp"
    cidr_blocks = ["0.0.0.0/0"]
  }

  ingress {
    description = "HTTPS desde Internet"
    from_port   = 443
    to_port     = 443
    protocol    = "tcp"
    cidr_blocks = ["0.0.0.0/0"]
  }

  egress {
    description = "Salida libre"
    from_port   = 0
    to_port     = 0
    protocol    = "-1"
    cidr_blocks = ["0.0.0.0/0"]
  }
}

# Security Group EC2 privadas
resource "aws_security_group" "privado_sg" {
  name   = "privado_sg"
  vpc_id = aws_vpc.vpc.id

  ingress {
    description     = "HTTP desde proxy"
    from_port       = 80
    to_port         = 80
    protocol        = "tcp"
    security_groups = [aws_security_group.proxy_sg.id]
  }

  ingress {
    description     = "HTTPS desde proxy"
    from_port       = 443
    to_port         = 443
    protocol        = "tcp"
    security_groups = [aws_security_group.proxy_sg.id]
  }

  egress {
    description = "Salida libre"
    from_port   = 0
    to_port     = 0
    protocol    = "-1"
    cidr_blocks = ["0.0.0.0/0"]
  }
}

# Instancias EC2 
resource "aws_instance" "proxy" {
  ami                    = var.ami_id
  instance_type          = var.tipo_instancia
  subnet_id              = aws_subnet.publica.id
  vpc_security_group_ids = [aws_security_group.proxy_sg.id]

  tags = {
    Name = "proxy"
  }
}


# EC2 privadas
resource "aws_instance" "www1" {
  ami                    = var.ami_id
  instance_type          = var.tipo_instancia
  subnet_id              = aws_subnet.privada.id
  vpc_security_group_ids = [aws_security_group.privado_sg.id]

  tags = {
    Name = "www1"
  }
}

resource "aws_instance" "www2" {
  ami                    = var.ami_id
  instance_type          = var.tipo_instancia
  subnet_id              = aws_subnet.privada.id
  vpc_security_group_ids = [aws_security_group.privado_sg.id]

  tags = {
    Name = "www2"
  }
}


