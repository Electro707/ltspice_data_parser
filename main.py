#!/usr/bin/python3
import os
import sys
import typing
import argparse
import logging
import enum
import re
import matplotlib
import matplotlib.pyplot as plt

INTRO = "LTspice Data Exporter by Arya Daroui\nDrag and drop LTspice data .txt file to export to .tsv or just enter \'h\' for help"
HELP_SCREEN = "add the following switches after file to modify output.\n\n-c\t.csv\n-s\tkeep scientific notation\n"


class LTSpiceDataAnalyzer:
    class InvalidFileException(Exception):
        def __init__(self):
            super().__init__('Invalid LTSpice Data File')

    class InvalidDataException(Exception):
        def __init__(self):
            super().__init__('Invalid data')

    class LTSpiceDataAnalyzerGenericException(Exception):
        def __init__(self, error_message):
            super().__init__(error_message)

    class FileType(enum.Enum):
        INVALID = 0
        TRANSIENT = 1
        AC_FREQUENCY_PHASE = 2
        AC_REAL_IMAG = 3

    class DataType(enum.Enum):
        FREQ_MAG_PHASE = 1
        XY = 2

    class StepInfo:
        label: typing.Union[str, None] = None
        values: dict = {}

    def __init__(self):
        self.log = logging.getLogger('ltspice_praser')
        self.file_type: 'LTSpiceDataAnalyzer.FileType' = None
        self.param_step_info: 'LTSpiceDataAnalyzer.StepInfo' = None
        self.data_type: 'LTSpiceDataAnalyzer.DataType' = None
        self.probe_points: list = None
        self.runs_label: list = None
        self.data: dict = None
    
    @staticmethod
    def matplotlib_latex_get_figsize(columnwidth, wf=0.5, hf=(5.**0.5-1.0)/2.0, ):
      """
        Copied from https://stackoverflow.com/questions/29187618/matplotlib-and-latex-beamer-correct-size
        Parameters:
        - wf [float]:  width fraction in columnwidth units
        - hf [float]:  height fraction in columnwidth units.
                       Set by default to golden ratio.
        - columnwidth [float]: width of the column in latex. Get this from LaTeX 
                               using \showthe\columnwidth
      Returns:  [fig_width,fig_height]: that should be given to matplotlib
      """
      fig_width_pt = columnwidth*wf 
      inches_per_pt = 1.0/72.27               # Convert pt to inch
      fig_width = fig_width_pt*inches_per_pt  # width in inches
      fig_height = fig_width*hf      # height in inches
      return [fig_width, fig_height]

    def parse_data_file(self, file_name):
        self.file_type = self.FileType.INVALID
        self.probe_points = []
        self.param_step_info = self.StepInfo()
        self.data = {}
        try:
            file = open(file_name, 'r', encoding='cp1252')
        except IOError:
            raise self.InvalidFileException()
        self.log.debug('Started parsing the given file')
        # Read first line, and determine what kind of plot and the voltage/current points
        line = file.readline()
        line = line.split('\t')
        if 'Freq.' in line[0]:
            self.file_type = self.FileType.AC_FREQUENCY_PHASE
        elif 'time' in line[0]:
            self.file_type = self.FileType.TRANSIENT
        self.log.debug('File Data Type: %s' % self.file_type)
        line = line[1:]
        print(line)
        for probe_point in line:
            self.probe_points.append(probe_point.rstrip())
        self.log.debug('Probe points: %s' % self.probe_points)
        # Read next line, see if there is a step info
        if self.file_type == self.FileType.AC_FREQUENCY_PHASE:
            self._parse_freq_file(file)
        elif self.file_type == self.FileType.TRANSIENT:
            self.parse_transient_file(file)

        file.close()

    def _parse_freq_file(self, file):
        current_step_number = 0
        self.data[current_step_number] = []
        for line in file:
            if 'Step Information:' in line:
                current_step_number = self._parse_parameter_step(line)
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

    def parse_transient_file(self, file):
        current_step_number = 0
        self.data[current_step_number] = []
        for line in file:
            if 'Step Information:' in line:
                current_step_number = self._parse_parameter_step(line)
                self.data[current_step_number] = []
                continue
            matches = line.split('\t')
            if len(matches) != len(self.probe_points)+1:
                self.log.error('Incorrect data format')
                raise self.InvalidDataException()
            data = {
                'time': float(matches[0]),
                'output': {}
            }
            for index, probe in enumerate(self.probe_points):
                data['output'][probe] = float(matches[index+1])
            self.data[current_step_number].append(data)

    def _parse_parameter_step(self, line) -> int:
        matches = re.match(r'^Step\ Information: ([^=]*)=([^\(\ ]*)[\ (]*Run: ([^\/]*)\/([^)]*)\)', line)
        if len(matches.groups()) != 4:
            self.log.error('Incorrect Step Information Format')
            raise self.InvalidDataException()
        self.param_step_info.label = matches.group(1)
        self.param_step_info.values[int(matches.group(3))] = str(matches.group(2)).rstrip()
        current_step_number = matches.group(3)
        try:
            current_step_number = int(current_step_number)
        except ValueError:
            sys.exit(-1)
        self.log.debug('Parsed step with label %s, value %s, step %s/%s', self.param_step_info.label, matches.group(2), current_step_number, matches.group(4))
        return current_step_number

    def _plot_frequency_frepha(self, ax, param_step_numb: int = 0, single_probe_index: int = None):
        x = [x['frequency'] for x in self.data[param_step_numb]]
        for index, probe_name in enumerate(self.probe_points):
            if single_probe_index is not None:
                if index != single_probe_index:
                    continue
            y = [x['amplitude'] for x in self.data[param_step_numb]]
            label = None
            if self.param_step_info.label is not None:
                label = '%s=%s' % (self.param_step_info.label, self.param_step_info.values[param_step_numb])
            ax.plot(x, y, label=label)

    def _plot_transient_(self, ax, param_step_numb: int = 0, single_probe_index: int = None):
        x = [x['time'] for x in self.data[param_step_numb]]
        for index, probe_name in enumerate(self.probe_points):
            if single_probe_index is not None:
                if index != single_probe_index:
                    continue
            y = [x['output'][probe_name] for x in self.data[param_step_numb]]
            ax.plot(x, y, label='%s %s=%s' % (probe_name, self.param_step_info.label, self.param_step_info.values[param_step_numb]))

    def plot(self, **kwargs):
        probe_point = None
        single_parameter_selection = None
        export_latex_path = None
        latex_plot_size = None
        if 'single_probe' in kwargs:
            probe_point = kwargs['single_probe']
        if 'single_parameter' in kwargs:
            single_parameter_selection = kwargs['single_parameter']
        if 'export_latex_plot' in kwargs:
            export_latex_path = kwargs['export_latex_plot']
            if not export_latex_path.endswith('.pgf'):
                export_latex_path += '.pgf'
            if 'latex_plot_size' in kwargs:
                latex_plot_size = kwargs['latex_plot_size']

        fig, ax = plt.subplots()
        if self.file_type == self.FileType.AC_FREQUENCY_PHASE:
            if self.param_step_info.label is not None:
                for step in self.param_step_info.values:
                    if single_parameter_selection is not None:
                        if self.param_step_info.values[step] != single_parameter_selection:
                            continue
                    self._plot_frequency_frepha(ax, step, probe_point)
                ax.legend()
            else:
                self._plot_frequency_frepha(ax, param_step_numb=0, single_probe_index=probe_point)
        elif self.file_type == self.FileType.TRANSIENT:
            # Plot the data depending if there are parameter steps or not
            if self.param_step_info.label is not None:
                for step in self.param_step_info.values:
                    if single_parameter_selection is not None:
                        print(self.param_step_info.values[step], single_parameter_selection, str(self.param_step_info.values[step]).strip('') == str(single_parameter_selection).strip(''))
                        if self.param_step_info.values[step] != single_parameter_selection:
                            continue
                    self._plot_transient_(ax, step, probe_point)
                ax.legend()
            else:
                self._plot_transient_(ax, param_step_numb=0, single_probe_index=probe_point)
        
        if 'plot_name' in kwargs:
            ax.set_title(kwargs['plot_name'])
        else:
            ax.set_title('Plot')
        
        # Add axis labels
        if self.file_type == self.FileType.TRANSIENT:
            ax.set_xlabel('Time (sec)')
            ax.set_ylabel('Amplitude (V)')
        elif self.file_type == self.FileType.AC_FREQUENCY_PHASE:
            ax.set_xlabel('Frequency (Hz)')
            ax.set_ylabel('Amplitude (db)')
        
        if 'x_log' in kwargs:
            if kwargs['x_log'] is True:
                ax.set_xscale('log', base=10)
        plt.show()
        
        if export_latex_path is not None:
            matplotlib.use("pgf")
            matplotlib.rcParams.update({
              "pgf.texsystem": "lualatex",
              'font.family': 'serif',
              'text.usetex': True,
              'pgf.rcfonts': False,
            })
            if latex_plot_size is not None:
                fig.set_size_inches(self.matplotlib_latex_get_figsize(latex_plot_size, wf=1.0, hf=0.7))
            fig.savefig("%s" % export_latex_path, bbox_inches='tight', transparent=True)


def setup_logger():
    """Create the logging format, by setting the root logger"""

    lg = logging.getLogger()
    lg.setLevel(logging.DEBUG)

    formatter = logging.Formatter(fmt='%(asctime)s - %(name)s - %(funcName)s - %(levelname)s - %(message)s')

    stream_handler = logging.StreamHandler()
    stream_handler.setLevel(logging.DEBUG)
    stream_handler.setFormatter(formatter)
    lg.addHandler(stream_handler)

    logging.getLogger('matplotlib').setLevel(logging.INFO)


def start_program():
    parser = argparse.ArgumentParser(description='LTSpice Graph Text file to usable CSV tool')
    parser.add_argument('file', metavar='File', type=str, help='The file to parse')
    parser.add_argument('-p', '--plot_all', action='store_true', help='Plot the parsed data')
    parser.add_argument('--plot_log_x', action='store_true', help='Set to plot the x as a log axis')
    parser.add_argument('--plot_name', type=str, default='', help='The name of the plot')
    
    parser.add_argument('--export_latex_plot', type=str, default='', help='Exports the plot as a LaTeX file')
    parser.add_argument('--latex_plot_size', type=int, default=-1, help='The size of the LaTeX columnwidth to calculate the .pgf size')
    
    parser.add_argument('--plot_single_probe', type=int, default=-1, help='Plot only a single probe point (indexed)')
    parser.add_argument('--plot_single_parameter', type=str, default='', help='Plot only a single parameter\'s output')
    args = parser.parse_args()

    data_parser = LTSpiceDataAnalyzer()
    try:
        data_parser.parse_data_file(args.file)
    except data_parser.InvalidFileException:
        print("Unable to open file %s" % args.file)
        return

    if args.plot_all is True:
        kwag = {}
        kwag['x_log'] = args.plot_log_x
        if args.plot_single_probe != -1:
            kwag['single_probe'] = args.plot_single_probe
        if args.plot_name != '':
            kwag['plot_name'] = args.plot_name
        if args.plot_single_parameter != '':
            kwag['single_parameter'] = args.plot_single_parameter
        if args.export_latex_plot != '':
            kwag['export_latex_plot'] = args.export_latex_plot
        if args.latex_plot_size != -1:
            kwag['latex_plot_size'] = args.latex_plot_size
        data_parser.plot(**kwag)


if __name__ == '__main__':
    setup_logger()
    start_program()
