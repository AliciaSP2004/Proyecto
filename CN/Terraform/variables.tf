
variable "region" {
  type        = string
  default     = "us-east-1"
}
variable "az" {
  type        = string
  default     = "us-east-1a"
}

variable "vpc_cidr" {
  default = "10.0.0.0/16"
}

variable "publica_cidr" {
  default = "10.0.1.0/24"
}

variable "privada_cidr" {
  default = "10.0.2.0/24"
}

variable "tipo_instancia" {
  default = "t2.micro"
}

variable "ami_id" {
  description = "AMI Ubuntu"
  default     = "ami-028f6d7ddc3079baf"
}
variable "usuario_db" {
  default = "wordpress"
}

variable "contrasena_db" {
  description = "Contrasena BD"
  type        = string
  sensitive   = true
  default     = "usuario@1"
}
