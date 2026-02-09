output "ip_publica_proxy" {
  description = "IP pública del Proxy"
  value       = aws_eip.proxy_ip.public_ip
}

output "ip_privada_proxy" {
  description = "IP privada del Proxy"
  value       = aws_instance.proxy.private_ip
}

output "ip_www1" {
  description = "IP privada de la EC2 privada 1"
  value       = aws_instance.www1.private_ip
}

output "ip_www2" {
  description = "IP privada de la EC2 privada 2"
  value       = aws_instance.www2.private_ip
}

output "ip_moni" {
  description = "IP privada de la EC2 monitorizacion"
  value       = aws_instance.moni.private_ip
}

output "ip_bd" {
  description = "IP privada de la EC2 base_datos"
  value       = aws_instance.bd.private_ip
}