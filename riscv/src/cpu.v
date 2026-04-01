module cpu(
    input clk,
    input rst,
    output reg [31:0] debug_out
);
    always @(*) begin
        debug_out = 32'd0;
    end
endmodule
