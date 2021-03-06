#!/usr/bin/env python
"""ip_arb_mux_64

Generates an arbitrated IP mux with the specified number of ports

Usage: ip_arb_mux_64 [OPTION]...
  -?, --help     display this help and exit
  -p, --ports    specify number of ports
  -n, --name     specify module name
  -o, --output   specify output file name
"""

import io
import sys
import getopt
from math import *
from jinja2 import Template

class Usage(Exception):
    def __init__(self, msg):
        self.msg = msg

def main(argv=None):
    if argv is None:
        argv = sys.argv
    try:
        try:
            opts, args = getopt.getopt(argv[1:], "?n:p:o:", ["help", "name=", "ports=", "output="])
        except getopt.error as msg:
             raise Usage(msg)
        # more code, unchanged  
    except Usage as err:
        print(err.msg, file=sys.stderr)
        print("for help use --help", file=sys.stderr)
        return 2

    ports = 4
    name = None
    out_name = None

    # process options
    for o, a in opts:
        if o in ('-?', '--help'):
            print(__doc__)
            sys.exit(0)
        if o in ('-p', '--ports'):
            ports = int(a)
        if o in ('-n', '--name'):
            name = a
        if o in ('-o', '--output'):
            out_name = a

    if name is None:
        name = "ip_arb_mux_64_{0}".format(ports)

    if out_name is None:
        out_name = name + ".v"

    print("Opening file '%s'..." % out_name)

    try:
        out_file = open(out_name, 'w')
    except Exception as ex:
        print("Error opening \"%s\": %s" %(out_name, ex.strerror), file=sys.stderr)
        exit(1)

    print("Generating {0} port AXI Stream arbitrated mux {1}...".format(ports, name))

    select_width = ceil(log2(ports))

    t = Template(u"""/*

Copyright (c) 2014 Alex Forencich

Permission is hereby granted, free of charge, to any person obtaining a copy
of this software and associated documentation files (the "Software"), to deal
in the Software without restriction, including without limitation the rights
to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
copies of the Software, and to permit persons to whom the Software is
furnished to do so, subject to the following conditions:

The above copyright notice and this permission notice shall be included in
all copies or substantial portions of the Software.

THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY
FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN
THE SOFTWARE.

*/

// Language: Verilog 2001

`timescale 1ns / 1ps

/*
 * IP {{n}} port arbitrated multiplexer (64 bit datapath)
 */
module {{name}} #
(
    // arbitration type: "PRIORITY" or "ROUND_ROBIN"
    parameter ARB_TYPE = "PRIORITY",
    // LSB priority: "LOW", "HIGH"
    parameter LSB_PRIORITY = "HIGH"
)
(
    input  wire        clk,
    input  wire        rst,
    
    /*
     * IP frame inputs
     */
{%- for p in ports %}
    input  wire        input_{{p}}_ip_hdr_valid,
    output wire        input_{{p}}_ip_hdr_ready,
    input  wire [47:0] input_{{p}}_eth_dest_mac,
    input  wire [47:0] input_{{p}}_eth_src_mac,
    input  wire [15:0] input_{{p}}_eth_type,
    input  wire [3:0]  input_{{p}}_ip_version,
    input  wire [3:0]  input_{{p}}_ip_ihl,
    input  wire [5:0]  input_{{p}}_ip_dscp,
    input  wire [1:0]  input_{{p}}_ip_ecn,
    input  wire [15:0] input_{{p}}_ip_length,
    input  wire [15:0] input_{{p}}_ip_identification,
    input  wire [2:0]  input_{{p}}_ip_flags,
    input  wire [12:0] input_{{p}}_ip_fragment_offset,
    input  wire [7:0]  input_{{p}}_ip_ttl,
    input  wire [7:0]  input_{{p}}_ip_protocol,
    input  wire [15:0] input_{{p}}_ip_header_checksum,
    input  wire [31:0] input_{{p}}_ip_source_ip,
    input  wire [31:0] input_{{p}}_ip_dest_ip,
    input  wire [63:0] input_{{p}}_ip_payload_tdata,
    input  wire [7:0]  input_{{p}}_ip_payload_tkeep,
    input  wire        input_{{p}}_ip_payload_tvalid,
    output wire        input_{{p}}_ip_payload_tready,
    input  wire        input_{{p}}_ip_payload_tlast,
    input  wire        input_{{p}}_ip_payload_tuser,
{% endfor %}
    /*
     * IP frame output
     */
    output wire        output_ip_hdr_valid,
    input  wire        output_ip_hdr_ready,
    output wire [47:0] output_eth_dest_mac,
    output wire [47:0] output_eth_src_mac,
    output wire [15:0] output_eth_type,
    output wire [3:0]  output_ip_version,
    output wire [3:0]  output_ip_ihl,
    output wire [5:0]  output_ip_dscp,
    output wire [1:0]  output_ip_ecn,
    output wire [15:0] output_ip_length,
    output wire [15:0] output_ip_identification,
    output wire [2:0]  output_ip_flags,
    output wire [12:0] output_ip_fragment_offset,
    output wire [7:0]  output_ip_ttl,
    output wire [7:0]  output_ip_protocol,
    output wire [15:0] output_ip_header_checksum,
    output wire [31:0] output_ip_source_ip,
    output wire [31:0] output_ip_dest_ip,
    output wire [63:0] output_ip_payload_tdata,
    output wire [7:0]  output_ip_payload_tkeep,
    output wire        output_ip_payload_tvalid,
    input  wire        output_ip_payload_tready,
    output wire        output_ip_payload_tlast,
    output wire        output_ip_payload_tuser
);

wire [{{n-1}}:0] request;
wire [{{n-1}}:0] acknowledge;
wire [{{n-1}}:0] grant;
wire grant_valid;
wire [{{w-1}}:0] grant_encoded;
{% for p in ports %}
assign acknowledge[{{p}}] = input_{{p}}_ip_payload_tvalid & input_{{p}}_ip_payload_tready & input_{{p}}_ip_payload_tlast;
assign request[{{p}}] = input_{{p}}_ip_hdr_valid;
{%- endfor %}

// mux instance
ip_mux_64_{{n}}
mux_inst (
    .clk(clk),
    .rst(rst),
{%- for p in ports %}
    .input_{{p}}_ip_hdr_valid(input_{{p}}_ip_hdr_valid & grant[{{p}}]),
    .input_{{p}}_ip_hdr_ready(input_{{p}}_ip_hdr_ready),
    .input_{{p}}_eth_dest_mac(input_{{p}}_eth_dest_mac),
    .input_{{p}}_eth_src_mac(input_{{p}}_eth_src_mac),
    .input_{{p}}_eth_type(input_{{p}}_eth_type),
    .input_{{p}}_ip_version(input_{{p}}_ip_version),
    .input_{{p}}_ip_ihl(input_{{p}}_ip_ihl),
    .input_{{p}}_ip_dscp(input_{{p}}_ip_dscp),
    .input_{{p}}_ip_ecn(input_{{p}}_ip_ecn),
    .input_{{p}}_ip_length(input_{{p}}_ip_length),
    .input_{{p}}_ip_identification(input_{{p}}_ip_identification),
    .input_{{p}}_ip_flags(input_{{p}}_ip_flags),
    .input_{{p}}_ip_fragment_offset(input_{{p}}_ip_fragment_offset),
    .input_{{p}}_ip_ttl(input_{{p}}_ip_ttl),
    .input_{{p}}_ip_protocol(input_{{p}}_ip_protocol),
    .input_{{p}}_ip_header_checksum(input_{{p}}_ip_header_checksum),
    .input_{{p}}_ip_source_ip(input_{{p}}_ip_source_ip),
    .input_{{p}}_ip_dest_ip(input_{{p}}_ip_dest_ip),
    .input_{{p}}_ip_payload_tdata(input_{{p}}_ip_payload_tdata),
    .input_{{p}}_ip_payload_tkeep(input_{{p}}_ip_payload_tkeep),
    .input_{{p}}_ip_payload_tvalid(input_{{p}}_ip_payload_tvalid & grant[{{p}}]),
    .input_{{p}}_ip_payload_tready(input_{{p}}_ip_payload_tready),
    .input_{{p}}_ip_payload_tlast(input_{{p}}_ip_payload_tlast),
    .input_{{p}}_ip_payload_tuser(input_{{p}}_ip_payload_tuser),
{%- endfor %}
    .output_ip_hdr_valid(output_ip_hdr_valid),
    .output_ip_hdr_ready(output_ip_hdr_ready),
    .output_eth_dest_mac(output_eth_dest_mac),
    .output_eth_src_mac(output_eth_src_mac),
    .output_eth_type(output_eth_type),
    .output_ip_version(output_ip_version),
    .output_ip_ihl(output_ip_ihl),
    .output_ip_dscp(output_ip_dscp),
    .output_ip_ecn(output_ip_ecn),
    .output_ip_length(output_ip_length),
    .output_ip_identification(output_ip_identification),
    .output_ip_flags(output_ip_flags),
    .output_ip_fragment_offset(output_ip_fragment_offset),
    .output_ip_ttl(output_ip_ttl),
    .output_ip_protocol(output_ip_protocol),
    .output_ip_header_checksum(output_ip_header_checksum),
    .output_ip_source_ip(output_ip_source_ip),
    .output_ip_dest_ip(output_ip_dest_ip),
    .output_ip_payload_tdata(output_ip_payload_tdata),
    .output_ip_payload_tkeep(output_ip_payload_tkeep),
    .output_ip_payload_tvalid(output_ip_payload_tvalid),
    .output_ip_payload_tready(output_ip_payload_tready),
    .output_ip_payload_tlast(output_ip_payload_tlast),
    .output_ip_payload_tuser(output_ip_payload_tuser),
    .enable(grant_valid),
    .select(grant_encoded)
);

// arbiter instance
arbiter #(
    .PORTS({{n}}),
    .TYPE(ARB_TYPE),
    .BLOCK("ACKNOWLEDGE"),
    .LSB_PRIORITY(LSB_PRIORITY)
)
arb_inst (
    .clk(clk),
    .rst(rst),
    .request(request),
    .acknowledge(acknowledge),
    .grant(grant),
    .grant_valid(grant_valid),
    .grant_encoded(grant_encoded)
);

endmodule

""")
    
    out_file.write(t.render(
        n=ports,
        w=select_width,
        name=name,
        ports=range(ports)
    ))
    
    print("Done")

if __name__ == "__main__":
    sys.exit(main())

