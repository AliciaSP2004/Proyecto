resource "aws_key_pair" "proxy" {
  key_name   = "labsuser-proy"
  public_key = file("C:/Users/asr209/.ssh/labsuser-proy.pub")
}