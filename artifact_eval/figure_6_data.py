# ##########################################################################
# Data
# ##########################################################################

data = {}

#  - breakpoint at ngx_close_connection
#  - batching 8192
#  - no failures
data["nginx"] = {} 
data["nginx"]      ["native"] =  ( 9056.15,  9103.92,  9101.39,  9101.50,  9078.79 )
# using numbers from other benchmark run for consistency (all within stdev) between overall_with_failures.py figure and this one
# data["nginx"]["socket_rw_oc"] =  ( 5080.64,  5103.89,  5111.49,  5092.51,  5107.23 )
data["nginx"]["socket_rw_oc"] =  (5165.90,  5291.62,  5209.02,  5184.85,  5231.31,     5165.9,  5291.62,  5209.02,  5184.85,  5231.31)
data["nginx"]   ["socket_rw"] =  ( 3147.61,  3135.44,  3151.99,  3140.90,  3136.24 )
data["nginx"]        ["base"] =  ( 2142.35,  2130.28,  2130.52,  2128.78,  2121.09 )
data["nginx"]        ["full"] =  ( 2108.30,  2098.25,  2090.38,  2111.43,  2095.94 )

#  - breakpoint at connection_close
#  - policy socket_rw_oc
#  - no failures
data["lighttpd"] = {}
data["lighttpd"]      ["native"] =  (20969.04,  20949.82,  20972.21,  20966.31,  20985.39)
# using numbers from other benchmark run for consistency (all within stdev) between overall_with_failures.py figure and this one
#data["lighttpd"]["socket_rw_oc"] =  (14414.69,  14478.56,  14470.10,  14528.57,  14493.54 )
data["lighttpd"]["socket_rw_oc"] = (14767.79,  14702.79,  14694.63,  14851.75,  14902.31,   14767.79, 14702.79, 14694.63, 14851.75, 14902.31)
data["lighttpd"]   ["socket_rw"] =  ( 9307.26,   9285.00,   9280.25,   9371.10,   9316.34 )
data["lighttpd"]        ["base"] =  ( 4525.83,   4576.48,   4547.40,   4581.07,   4609.82 )
data["lighttpd"]        ["full"] =  ( 4477.18,   4494.20,   4462.54,   4477.00,   4480.46 )

#  - breakpoint at acceptTcpHandler
#  - policy socket_rw_oc
#  - no failures
data["redis"] = {}
data["redis"]      ["native"] =  (52002.60,  52220.37,  52219.32,  52273.91,  52246.60) 
# using numbers from other benchmark run for consistency (all within stdev) between overall_with_failures.py figure and this one
#data["redis"]["socket_rw_oc"] =  ( 27510.59, 27480.08, 27662.79, 27412.28, 27412.55)
data["redis"]["socket_rw_oc"] =  (27457.72,  27404.77,  27330.96,  27685.77,  27716.74,   27457.72, 27404.77, 27330.96, 27685.77, 27716.74)
data["redis"]   ["socket_rw"] =  ( 26874.77, 27732.11, 27662.52, 27662.79, 27670.17)
data["redis"]        ["base"] =  (  8919.81,  8884.15,  8795.85,   8826.9,  8861.32)
data["redis"]        ["full"] =  (  5027.65,  5040.32,  5032.71,   5081.3,  5055.61)

