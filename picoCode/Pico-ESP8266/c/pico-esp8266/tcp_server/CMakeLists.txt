add_executable(tcp_server
        tcp_server.cpp
        )

# Pull in our pico_stdlib which pulls in commonly used features
target_link_libraries(tcp_server pico_stdlib)

# enable usb output, disable uart output
pico_enable_stdio_usb(tcp_server 1)
pico_enable_stdio_uart(tcp_server 0)

# create map/bin/hex file etc.
pico_add_extra_outputs(tcp_server)

# add url via pico_set_program_url
example_auto_set_url(tcp_server)
