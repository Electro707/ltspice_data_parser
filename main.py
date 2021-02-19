#!/usr/bin/python3
import os, sys
import argparse
import logging
import enum
import re
import matplotlib
import matplotlib.pyplot as plt

INTRO = "LTspice Data Exporter by Arya Daroui\nDrag and drop LTspice data .txt file to export to .tsv or just enter \'h\' for help"
HELP_SCREEN = "add the following switches after file to modify output.\n\n-c\t.csv\n-s\tkeep scientific notation\n"


class LTSpiceDataAnalyzer:
	class InvalidDataException(Exception):
		def __init__(self):
			super().__init__('Invalid data')
	class LTSpiceDataAnalyzerGenericException(Exception):
		def __init__(self, error_message):
			super().__init__(error_message)

	class FileType(enum.Enum):
		INVALID = 0
		TRANSIENT = 1
		FREQUENCY = 2

	class DataType(enum.Enum):
		FREQ_MAG_PHASE = 1
		XY = 2

	class StepInfo:
		label: str = ''
		values: dict = {}

	def __init__(self):
		self.log = logging.getLogger('ltspice_praser')
		self.file_type: 'LTSpiceDataAnalyzer.FileType' = None
		self.step_info: 'LTSpiceDataAnalyzer.StepInfo' = None
		self.data_type: 'LTSpiceDataAnalyzer.DataType' = None
		self.probe_points: list = None
		self.runs_label: list = None
		self.data: dict = None
		self.available_steps: list = None

	def parse_data_file(self, file_name):
		self.file_type = self.FileType.INVALID
		self.probe_points = []
		self.step_info = self.StepInfo()
		self.data = {}
		self.available_steps = []
		try:
			file = open(file_name, 'r', encoding='cp1252')
		except IOError:
			self.log.error('Unable to open file')
			return
		self.log.debug('Started parsing the given file')
		# Read first line, and determine what kind of plot and the voltage/current points
		line = file.readline()
		line = line.split('\t')
		if 'Freq.' in line[0]:
			self.file_type = self.FileType.FREQUENCY
		elif 'time' in line[0]:
			self.file_type = self.FileType.TRANSIENT
		self.log.debug('File Data Type: %s' % self.file_type)
		# TODO: Add handling for more than 1 voltage probe point
		self.probe_points.append(line[1])
		# Read next line, see if there is a step info
		if self.file_type == self.FileType.FREQUENCY:
			self._parse_freq_file(file)

		file.close()

	def _parse_freq_file(self, file):
		current_step_number = 0
		self.data[current_step_number] = []
		for line in file:
			if 'Step Information:' in line:
				current_step_number = self._parse_step(line)
				self.data[current_step_number] = []
				continue
			matches = re.match(r'^([^\t]*)\t\(([^dB]*)dB,([^°]*)°\)', line)
			if len(matches.groups()) != 3:
				self.log.error('Incorrect data format')
				raise self.InvalidDataException()
			self.data[current_step_number].append({
				'frequency': float(matches.group(1)),
				'amplitude': float(matches.group(2)),
				'phase': float(matches.group(3)),
			})

	def _parse_step(self, line) -> int:
		matches = re.match(r'^Step\ Information: ([^=]*)=([^\(\ ]*)[\ (]*Run: ([^\/]*)\/([^)]*)\)', line)
		if len(matches.groups()) != 4:
			self.log.error('Incorrect Step Information Format')
			raise self.InvalidDataException()
		self.step_info.label = matches.group(1)
		self.step_info.values[int(matches.group(3))] = matches.group(2)
		current_step_number = matches.group(3)
		try:
			current_step_number = int(current_step_number)
		except ValueError:
			sys.exit(-1)
		self.log.debug('Parsed step with label %s, value %s, step %s/%s', self.step_info.label, matches.group(2), current_step_number, matches.group(4))
		self.available_steps.append(current_step_number)
		return current_step_number

	def plot_step(self, step_number: int):
		if step_number not in self.available_steps:
			raise self.LTSpiceDataAnalyzerGenericException('Step number not available')
		x = [x['frequency'] for x in self.data[step_number]]
		y = [x['amplitude'] for x in self.data[step_number]]
		fig, ax = plt.subplots()
		ax.plot(x, y)
		ax.set_title('Plot for Step %s' % step_number)
		ax.set_xlabel('Frequency')
		ax.set_ylabel('Amplitude')
		plt.show()

	def plot_all_steps(self, **kwargs):
		fig, ax = plt.subplots()
		for step in self.available_steps:
			x = [x['frequency'] for x in self.data[step]]
			y = [x['amplitude'] for x in self.data[step]]
			ax.plot(x, y, label='%s=%s' % (self.step_info.label,self.step_info.values[step]))
		ax.legend(loc='upper left')
		ax.set_title('Plot for All Steps')
		ax.set_xlabel('Frequency')
		ax.set_ylabel('Amplitude')
		if 'x_log' in kwargs:
			if kwargs['x_log'] is True:
				ax.set_xscale('log', base=10)
		plt.show()


def setup_logger():
	"""Create the logging format, by setting the root logger"""

	lg = logging.getLogger()
	lg.setLevel(logging.DEBUG)

	formatter = logging.Formatter(fmt='%(asctime)s - %(name)s - %(funcName)s - %(levelname)s - %(message)s')

	stream_handler = logging.StreamHandler()
	stream_handler.setLevel(logging.DEBUG)
	stream_handler.setFormatter(formatter)

	lg.addHandler(stream_handler)


def start_program():
	parser = argparse.ArgumentParser(description='LTSpice Graph Text file to usable CSV tool')
	parser.add_argument('file', metavar='F', type=str, help='The file to parse')
	args = parser.parse_args()
	print(args.file)

	data_parser = LTSpiceDataAnalyzer()
	data_parser.parse_data_file(args.file)
	data_parser.plot_all_steps(x_log=True)


if __name__ == '__main__':
	setup_logger()
	start_program()
