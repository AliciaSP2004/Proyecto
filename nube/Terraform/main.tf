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
  route {
    cidr_block  = "0.0.0.0/0"
    network_interface_id = aws_instance.proxy.primary_network_interface_id
  }
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
  ingress {
    description = "SSH desde Internet"
    from_port   = 22
    to_port     = 22
    protocol    = "tcp"
    cidr_blocks = ["0.0.0.0/0"]
  }
  ingress {
    description = "Trafico desde la subred privada para NAT"
    from_port   = 0
    to_port     = 0
    protocol    = "-1"
    cidr_blocks = [var.privada_cidr]
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
# Security Group www1 y www2
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
    ingress {
    description     = "SSH desde proxy"
    from_port       = 22
    to_port         = 22
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
# Security Group instancia de monitorización
resource "aws_security_group" "moni_sg" {
  name   = "moni_sg"
  vpc_id = aws_vpc.vpc.id
   ingress {
    description     = "SSH desde proxy"
    from_port       = 22
    to_port         = 22
    protocol        = "tcp"
    security_groups = [aws_security_group.proxy_sg.id]
  }
  ingress {
    description     = "Métricas desde las webs"
    from_port       = 3306
    to_port         = 3306
    protocol        = "tcp"
    security_groups = [aws_security_group.privado_sg.id]
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

# EC2 pública (Proxy)
resource "aws_instance" "proxy" {
  ami                    = var.ami_id
  instance_type          = var.tipo_instancia
  key_name = var.key_name
  subnet_id              = aws_subnet.publica.id
  vpc_security_group_ids = [aws_security_group.proxy_sg.id]
  source_dest_check      = false
  tags = {
    Name = "proxy"
  }
  user_data = <<-EOF
              #!/bin/bash
              # Esperar a que el sistema termine de arrancar procesos internos
              sleep 30
              
              # Habilitar forwarding (en caliente y permanente)
              sysctl -w net.ipv4.ip_forward=1
              echo "net.ipv4.ip_forward=1" >> /etc/sysctl.conf

              # Configurar NAT
              iptables -t nat -A POSTROUTING -o eth0 -j MASQUERADE
              
              # Instalación no interactiva para evitar que el script se cuelgue
              apt-get update
              echo iptables-persistent iptables-persistent/autosave_v4 boolean true | debconf-set-selections
              echo iptables-persistent iptables-persistent/autosave_v6 boolean true | debconf-set-selections
              DEBIAN_FRONTEND=noninteractive apt-get install -y iptables-persistent
              EOF
}
# IP Elástica para el Proxy
resource "aws_eip" "proxy_ip" {
  instance = aws_instance.proxy.id
  domain   = "vpc"
  tags     = { Name = "ip-proxy" }
}

# EC2 privadas
resource "aws_instance" "www1" {
  ami                    = var.ami_id
  instance_type          = var.tipo_instancia
  subnet_id              = aws_subnet.privada.id
  vpc_security_group_ids = [aws_security_group.privado_sg.id]
  private_ip    = var.ip_www1
  key_name = "vockey"
  tags = {
    Name = "www1"
  }
}

resource "aws_instance" "www2" {
  ami                    = var.ami_id
  instance_type          = var.tipo_instancia
  subnet_id              = aws_subnet.privada.id
  vpc_security_group_ids = [aws_security_group.privado_sg.id]
  private_ip    = var.ip_www2
  key_name = "vockey"
  tags = {
    Name = "www2"
  }
}

resource "aws_instance" "moni" {
  ami                    = var.ami_id
  instance_type          = var.tipo_instancia
  subnet_id              = aws_subnet.privada.id
  vpc_security_group_ids = [aws_security_group.moni_sg.id]
  private_ip    = var.ip_moni
  key_name = "vockey"
  tags = {
    Name = "moni"
  }
}

