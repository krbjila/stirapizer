from PyQt4 import QtGui, QtCore
from matplotlib.backends.backend_qt4agg import FigureCanvasQTAgg as FigureCanvas
from matplotlib.backends.backend_qt4agg import NavigationToolbar2QT as NavigationToolbar
from matplotlib.figure import Figure
from stirap_defaults import *
import numpy as np
import visa
from time import sleep

class voltage_grid(QtGui.QWidget):
	def __init__(self, Parent=None):
		super(voltage_grid, self).__init__(Parent)
		self.up_max_v = QtGui.QLineEdit('{0:.1f}'.format(UP_V_STIRAP))
		self.down_max_v = QtGui.QLineEdit('{0:.1f}'.format(DOWN_V_STIRAP))
		self.setup()

	def setup(self):
		self.grid = QtGui.QGridLayout()
		set_voltage_labels = ['Up', 'Down']
		for k, val in enumerate(set_voltage_labels):
			x = QtGui.QLabel(val)
			self.grid.addWidget(x, 0, k+1, 1, 1)
		self.grid.addWidget(QtGui.QLabel('Max Voltage (mV)'), 1, 0, 1, 1)
		self.grid.addWidget(self.up_max_v, 1, 1, 1, 1)
		self.grid.addWidget(self.down_max_v, 1, 2, 1, 1)

		self.setLayout(self.grid)

class time_grid(QtGui.QWidget):
	def __init__(self, Parent=None):
		super(time_grid, self).__init__(Parent)

		self.t_on = QtGui.QLineEdit('{0:.1f}'.format(T_ON))
		self.t_hold = QtGui.QLineEdit('{0:.1f}'.format(T_HOLD))
		self.t_stirap = QtGui.QLineEdit('{0:.1f}'.format(T_STIRAP))
		self.t_off = QtGui.QLineEdit('{0:.1f}'.format(T_OFF))
		self.t_max = QtGui.QLineEdit('{0:.1f}'.format(T_MAX))
		self.t_seq = QtGui.QLineEdit()
		
		self.t_max.setDisabled(True)
		self.t_seq.setDisabled(True)


		self.setup()

	def setup(self):
		self.grid = QtGui.QGridLayout()

		self.grid.addWidget(QtGui.QLabel('T_On'), 0, 0, 1, 1)
		self.grid.addWidget(self.t_on, 0, 1, 1, 1)
		self.grid.addWidget(QtGui.QLabel('T_Stirap'), 0, 2, 1, 1)
		self.grid.addWidget(self.t_stirap, 0, 3, 1, 1)
		self.grid.addWidget(QtGui.QLabel('T_Hold'), 1, 0, 1, 1)
		self.grid.addWidget(self.t_hold, 1, 1, 1, 1)
		self.grid.addWidget(QtGui.QLabel('T_Off'), 1, 2, 1, 1)
		self.grid.addWidget(self.t_off, 1, 3, 1, 1)
		self.grid.addWidget(QtGui.QLabel('T_Max'), 2, 0, 1, 1)
		self.grid.addWidget(self.t_max, 2, 1, 1, 1)
		self.grid.addWidget(QtGui.QLabel('T_seq'), 2, 2, 1, 1)
		self.grid.addWidget(self.t_seq, 2, 3, 1, 1)

		self.setLayout(self.grid)


class plot_window(QtGui.QWidget):
	def __init__(self,Parent=None):
		super(plot_window,self).__init__(Parent)
		self.setup()

	def setup(self):
		self.figure = Figure()
		self.canvas = FigureCanvas(self.figure)
		self.toolbar = NavigationToolbar(self.canvas,self)
		self.ax = self.figure.add_subplot(111)

		self.layout = QtGui.QGridLayout()
		self.layout.addWidget(self.toolbar,0,0,1,4)
		self.layout.addWidget(self.canvas,1,0,4,4)

		self.setLayout(self.layout)

def generate_stirap_sequence(voltage_data, time_data, down_leg_v):
	voltages = [] # List containing [up max voltage, down max voltage]
	times = []

	try:
		voltages.append(float(voltage_data.up_max_v.text()))
		voltages.append(float(voltage_data.down_max_v.text()))
	except ValueError:
		print('Voltage input could not be converted to float')
		return 0


	try:
		times.append(float(time_data.t_on.text()))
		times.append(float(time_data.t_hold.text()))
		times.append(float(time_data.t_stirap.text()))
		times.append(float(time_data.t_off.text()))
	except ValueError:
		print('Time input could not be converted to float')
		return 0

	t_sequence = sum(times)

	if t_sequence >= T_MAX/4.0:
		print('ERROR: Sequence time longer than T_MAX/4.')
		return 0
	else:
		time_data.t_seq.setText('{0:.1f}'.format(t_sequence))

	if voltages[0] > V_MAX:
		print('ERROR: Up leg voltage larger than V_MAX.')
	elif voltages[1] > V_MAX:
		print('ERROR: Down leg voltage larger than V_MAX.')
	else:
		v_up = voltages[0]/V_MAX
		v_down = voltages[1]/V_MAX

	###################### Generate sequences

	sequence_up = np.zeros(N)
	sequence_down = np.zeros(N)

	n_on = int(times[0]/DT)
	n_hold = int(times[1]/DT)
	n_stirap = int(times[2]/DT)
	n_off = int(times[2]/DT)
	n_sequence = n_on + n_hold + n_stirap + n_off

	t_up = 5
	t_down = 100 - 2 * t_up
	n_up = int(t_up/DT)
	n_down = int(t_down/DT)
	v_up_dr = 1500.0/V_MAX
	v_down_dr = min(down_leg_v,V_MAX)/V_MAX

	# Program in the up leg sequence
	sequence_up[n_on+n_hold : n_on+n_hold+n_stirap] = np.linspace(0.0, v_up, n_stirap)
	sequence_up[n_on+n_hold+n_stirap : n_sequence] = np.linspace(v_up, v_up, n_off)
	sequence_up[n_sequence : int(N/4)] = v_up * np.ones(int(N/4) - n_sequence)

	# Program in the down leg sequence
	sequence_down[0 : n_on] = np.linspace(0.0, v_down, n_on)
	sequence_down[n_on : n_on+n_hold] = v_down * np.ones(n_hold)
	sequence_down[n_on+n_hold : n_on+n_hold+n_stirap] = np.linspace(v_down, 0.0, n_stirap)

	# Mirror the sequences to generate dissociation pulse
	sequence_up[int(N/4) : int(N/4)+n_sequence] = np.flipud(sequence_up[0 : n_sequence])
	sequence_down[int(N/4) : int(N/4)+n_sequence] = np.flipud(sequence_down[0 : n_sequence])

	# Program in the dark resonance at the end
	sequence_up[-n_up:] = np.linspace(v_up_dr, 0, n_up)
	sequence_up[-(n_up+n_down):-n_up] = v_up_dr * np.ones(n_down)
	sequence_up[-(2*n_up+n_down):-(n_up+n_down)] = np.linspace(0, v_up_dr, n_up)

	sequence_down[-(n_up+n_down):-n_up] = v_down_dr * np.ones(n_down)

	return sequence_up, sequence_down

def makewaveform(sequence):
    string = ""
    for k in sequence:
        string += str(k)+', '
    return string[0:-2]

def write_stirap_to_fg(gpib_addr, seq, sysmsg):

	rm = visa.ResourceManager()
	resources = rm.list_resources()

	device = 0
	for k in gpib_addr:
		address = "GPIB0::{:d}::INSTR".format(k)

		if address in resources:
			sysmsg.setText("Communicating with device {0:d} at address: {1}.".format(device, address))
			sleep(1.0)

			instr = rm.open_resource(address)
			instr.write("*RST")
			instr.write("*CLS")
			instr.write("DATA:DEL:ALL")
			sysmsg.append(instr.query("*IDN?"))

			""" Upload waveform to volatile memory """
			sysmsg.append("Uploading data to volatile memory...")
			sleep(0.1)
			instr.write("DATA VOLATILE, " + makewaveform(seq[device]))
			sysmsg.append("Upload complete.")

			""" Set Waveform Parameters """
			instr.write("FREQ {0:.1f}Hz".format(FREQ))
			instr.write("VOLT {0:.3f}".format(V_MAX*1E-3))
			instr.write("VOLT:OFFS 0.0")

			""" Set up the burst """
			instr.write("BURS:MODE TRIG")
			instr.write("BURS:NCYC 1")
			instr.write("TRIG:SLOP POS")
			instr.write("TRIG:SOUR EXT")
			instr.write("BURS:STAT ON")               

			"""Copy data to non-volatile memory"""
			sysmsg.append("Copying data to non-volatile memory...")
			instr.write("DATA:COPY STIRAP, VOLATILE")
			sysmsg.append("Transfer complete.")

			"""Copy sequence to non-volatile memory"""
			"""Sequences stay stored in case function generator shuts off"""
			instr.write("FUNC:USER STIRAP")
			instr.write("FUNC:SHAP USER")

			"""Enable Output"""
			instr.write("OUTP:STAT ON")
			sysmsg.append("Device {0:d} output enabled. \n".format(device))
			device += 1
		else:
			print("Device {0:d} not found.".format(device))
			return 0
	return 1


def write_dr_to_fg(gpib_addr, voltages, sysmsg):

	rm = visa.ResourceManager()
	resources = rm.list_resources()

	device = 0
	for k in gpib_addr:
		address = "GPIB0::{:d}::INSTR".format(k)

		if address in resources:
			sysmsg.setText("Communicating with device {0:d} at address: {1}.".format(device, address))
			sleep(1.0)

			instr = rm.open_resource(address)
			instr.write("*RST")
			instr.write("*CLS")
			instr.write("DATA:DEL:ALL")
			sysmsg.append(instr.query("*IDN?"))

			""" Configure Function generator """

			instr.write("FUNC DC")
			instr.write("VOLT:OFFS {0:.3f} V".format(voltages[device]))


			"""Enable Output"""
			instr.write("OUTP:STAT ON")
			sysmsg.append("Device {0:d} DC output enabled. \n".format(device))
			device += 1
		else:
			print("Device {0:d} not found.".format(device))
			return 0
	return 1

def set_voltage_defaults(voltage_data, mode):
	
	if mode == 'STIRAP':
		voltage_data.up_max_v.setText('{0:.1f}'.format(UP_V_STIRAP))
		voltage_data.down_max_v.setText('{0:.1f}'.format(DOWN_V_STIRAP))
	elif mode == 'Dark Resonance':
		voltage_data.up_max_v.setText('{0:.1f}'.format(UP_V_DR))
		voltage_data.down_max_v.setText('{0:.1f}'.format(DOWN_V_DR))		

