#Variables para la región y zona de disponibilidad
variable "region" {
  type        = string
  default     = "us-east-1"
}
variable "az" {
  type        = string
  default     = "us-east-1a"
}



# Variables para asignar bloques CIDR
variable "vpc_cidr" {
  default = "10.0.0.0/16"
}

variable "publica_cidr" {
  default = "10.0.1.0/24"
}

variable "privada_cidr" {
  default = "10.0.2.0/24"
}



# Variables para las instancias EC2
variable "tipo_instancia" {
  default = "t3.small"
}

variable "ami_id" {
  description = "AMI Ubuntu"
  default     = "ami-0b6c6ebed2801a5cb"
}
variable "ip_www1" {
  description = "IP privada para la EC2 www1"
  default     = "10.0.2.31"
}
variable "ip_www2" {
  description = "IP privada para la EC2 www2"
  default     = "10.0.2.106"
}