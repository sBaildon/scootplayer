from flask import Flask, render_template, jsonify
import threading
import time
import flot
import pprint
import ConfigParser
import yaml
import glob

app = Flask(__name__)
report = { 'playback': {}, 'download': {} }
graphing_data = { 'playback': {}, 'download': {} }
info = {}

@app.route('/')
def homepage():
    return render_template('index.html', playback=graphing_data['playback'], download=graphing_data['download'])

@app.route('/<buffer_>')
def return_graphing_data(buffer_):
    if (buffer_ == 'sys'):
        return jsonify(info)
    return jsonify(graphing_data[buffer_])

@app.route('/<buffer_>/<metric>')
def metric_data(buffer_, metric):
    return jsonify({metric: report[buffer_][metric], 'time_elapsed': report[buffer_]['time_elapsed']})

def send_data(buffer_, data):
    if buffer_ not in report:
        value = {}
        for metric in data:
            value[metric] = [data[metric]]
        report[buffer_] = value
    else:
        for metric in data:
            try:
                report[buffer_][metric].append(data[metric])
            except KeyError:
                report[buffer_][metric] = [data[metric]]
    prepare_graphing_data(buffer_)

def prepare_graphing_data(buffer_):
    for metric in report[buffer_]:
        if metric not in graphs_to_display[buffer_]:
            continue
        temp_array = []
        for idx, val in enumerate(report[buffer_][metric]):
            temp_array.append((report[buffer_]['time_elapsed'][idx], report[buffer_][metric][idx]))
        graphing_data[buffer_][metric] = temp_array

def get_graphs_to_display(config):
    graphs_to_display = {}
    for buffer_ in config:
        graphs_to_display[buffer_] = []
        for metric in config[buffer_]:
            if config[buffer_][metric]['display']:
                graphs_to_display[buffer_].append(metric)

    return graphs_to_display

def parse_config():
    stream = open("gui_config.yaml", 'r')
    return yaml.load(stream)

config = parse_config()
graphs_to_display = get_graphs_to_display(config)

def open_info():
    global info
    files = glob.glob('out/*/info.csv')
    with open(files[0], 'r') as file_:
        for line in file_:
            split = line.split(',')
            info[split[0]] = split[1]

    files = glob.glob('out/*/stats/playback.csv')
    print '-'*72
    print str(files[0])
    with open(files[0], 'r') as file_:
        for line in file_:
            if "startup" in line:
                print '\n\n\nfound startup\n\n\n'
                split = line.split(',')
                info[split[0]] = split[1]
    print str(info)
    print '-'*72

class get_info_thread(threading.Thread):
    def __init__(self):
        threading.Thread.__init__(self)

    def run(self):
        time.sleep(7)
        open_info()

get_thread = get_info_thread()
get_thread.start()

class webserver_thread(threading.Thread):
    daemon = True
    def __init__(self):
        threading.Thread.__init__(self)

    def run(self):
        app.run()

webserver = webserver_thread()
webserver.start()
