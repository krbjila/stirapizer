""" Default values for Function Generator Control """

#################### FG Addresses ####################
UP_ADDRESS = 9
DOWN_ADDRESS = 10


############# Dark Resonance Parameters ##############
UP_V_DR = 15.0
DOWN_V_DR = 400.0

DOWN_V_KILLING = 110.0


################## STIRAP Parameters #################
UP_V_STIRAP = 1500.0
DOWN_V_STIRAP = 900.0

T_ON = 4.0
T_STIRAP = 3.5
T_HOLD = 2.0
T_DELAY = -1


##################### FG Defaults ####################
########### DO NOT MODIFY THESE PARAMETERS ###########

T_MAX = 200.0		# Total sequence time [us]
V_MAX = 2000.0		# Maximum voltage [mV]
V_MIN = 0.0			# Minimum voltage [mV]
N = 2**16			# Number of bytes in memory

MODES = ['STIRAP', 'Dark Resonance']

############### Derived Quantities ##################

DT = T_MAX/float(N) # Time Step [us]
FREQ = 1.0E6/T_MAX	# Maximum frequency [Hz]

