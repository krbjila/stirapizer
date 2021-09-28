import sys, os
from PyQt4 import QtGui, QtCore
from stirap_lib import *
from stirap_defaults import *
import numpy as np



class stirap_gui(QtGui.QMainWindow):
		def __init__(self, Parent=None):
				super(stirap_gui, self).__init__(Parent)
				self.setWindowTitle('STIRAPizer')
				self.initialize()


				### Make program connections
				self.set_time.t_on.returnPressed.connect(self.update_sequence)
				self.set_time.t_hold.returnPressed.connect(self.update_sequence)
				self.set_time.t_stirap.returnPressed.connect(self.update_sequence)
				self.set_time.t_off.returnPressed.connect(self.update_sequence)

				self.set_voltage.up_max_v.returnPressed.connect(self.update_sequence)
				self.set_voltage.down_max_v.returnPressed.connect(self.update_sequence)
				self.down_leg_v.returnPressed.connect(self.update_sequence)

				self.connect_update.clicked.connect(self.FG_write)
				self.mode_select.currentIndexChanged.connect(self.mode_changed_update)


				self.update_sequence()


		def update_sequence(self):
			x = generate_stirap_sequence(self.set_voltage, self.set_time, float(self.down_leg_v.text()))
			if x:
				self.up_sequence, self.down_sequence = x[0], x[1]
			
			self.update_plot()

		def FG_write(self):
			self.update_sequence()
			gpib_addr = [int(self.down_leg_address.text()), int(self.up_leg_address.text())]
			seq = [self.down_sequence, self.up_sequence]
			voltages = [float(self.set_voltage.down_max_v.text())/1000.0, float(self.set_voltage.up_max_v.text())/1000.0]

			if self.mode_select.currentText() == 'STIRAP':
				write_stirap_to_fg(gpib_addr, seq, self.status_bar)

			elif self.mode_select.currentText() == 'Dark Resonance':
				write_dr_to_fg(gpib_addr, voltages, self.status_bar)
		
		def mode_changed_update(self):
			set_voltage_defaults(self.set_voltage, self.mode_select.currentText())
			self.update_sequence()	

		def update_plot(self):

			self.plot_window.ax.cla()

			if self.mode_select.currentText() == "STIRAP":
				self.plot_window.ax.plot(np.arange(N)*DT, self.up_sequence*V_MAX, 'r')
				self.plot_window.ax.plot(np.arange(N)*DT, self.down_sequence*V_MAX, 'b')
			elif self.mode_select.currentText() == "Dark Resonance":
				self.plot_window.ax.plot(np.arange(N)*DT, float(self.set_voltage.up_max_v.text()) * np.ones(N), 'r')
				self.plot_window.ax.plot(np.arange(N)*DT, float(self.set_voltage.down_max_v.text()) * np.ones(N), 'b')				

			self.plot_window.ax.set_xlabel(r'Time ($\mu$s)')
			self.plot_window.ax.set_ylabel(r'Voltage (mV)')
			self.plot_window.ax.set_xlim((0, T_MAX))
			self.plot_window.ax.legend(['Up Leg', 'Down Leg'])

			self.plot_window.figure.subplots_adjust(bottom=0.15, left=0.15)
			self.plot_window.canvas.draw()

		def initialize(self):

			self.connect_update = QtGui.QPushButton('Connect and Update!')
			self.up_leg_address = QtGui.QLineEdit('{0:d}'.format(UP_ADDRESS))
			self.down_leg_address = QtGui.QLineEdit('{0:d}'.format(DOWN_ADDRESS))
			self.down_leg_v = QtGui.QLineEdit('50.0')
			self.status_bar = QtGui.QTextBrowser()
			self.plot_window = plot_window()

			self.mode_select = QtGui.QComboBox()
			self.mode_select.addItems(MODES)

			self.up_sequence = np.zeros(N)
			self.down_sequence = np.zeros(N)

			title = QtGui.QLabel('STIRAPizer')
			title_font = QtGui.QFont("Helvetica [Cronyx]", 16, QtGui.QFont.Bold)
			title.setText("<font color=\"blue\">STI</font><font color=\"red\">RAP</font><font color=\"black\">izer</font>")
			title.setFont(title_font)

			h0Left = QtGui.QHBoxLayout()
			h0Left.addWidget(title)
			h0Left.addWidget(self.connect_update)

			h1Left = QtGui.QHBoxLayout()
			h1Left.addWidget(QtGui.QLabel('Up Leg Address: '))
			h1Left.addWidget(self.up_leg_address)
			h1Left.addWidget(QtGui.QLabel('Down Leg Address: '))
			h1Left.addWidget(self.down_leg_address)

			h3Left = QtGui.QHBoxLayout()
			h3Left.addWidget(QtGui.QLabel('Down Leg Darkly Resonant Voltage: '))
			h3Left.addWidget(self.down_leg_v)

			self.set_voltage = voltage_grid()			
			self.set_time = time_grid()

			h2Left = QtGui.QHBoxLayout()
			h2Left.stretch(1)
			h2Left.addWidget(self.mode_select)
			h2Left.stretch(1)


			vLeft = QtGui.QVBoxLayout()
			vLeft.addLayout(h0Left)
			vLeft.addLayout(h1Left)
			vLeft.addLayout(h3Left)
			vLeft.addWidget(self.status_bar)
			vLeft.addWidget(self.set_voltage)
			vLeft.addWidget(self.set_time)
			vLeft.addLayout(h2Left)


			hmain = QtGui.QHBoxLayout()
			hmain.addLayout(vLeft)
			hmain.addWidget(self.plot_window)


			self.mainWidget = QtGui.QWidget()
			self.mainWidget.setLayout(hmain)
			self.setCentralWidget(self.mainWidget)


if __name__ == "__main__":
		app = QtGui.QApplication(sys.argv)

		w = stirap_gui()
		w.setGeometry(100, 100, 800, 400)
		w.show()

		sys.exit(app.exec_())