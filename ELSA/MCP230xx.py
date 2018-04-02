import abe_mcp23008

io = abe_mcp23008.IOPi(0x20)
#io.set_port_direction(0,0x00)
#io.set_port_pullups(0, 0x00)
#io.set_pin_direction(1, 0)
#io.write_pin(1, 0)
io.set_port_direction(0, 0x00)
#io.write_port(0, 0x00)
io.write_pin(1, 1)
print(io.read_port(0))

#io.set_pin_direction(1, 0)
#io.write_pin(1, 1)
