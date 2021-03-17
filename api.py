import configparser
from flask import Flask, jsonify
import json
from subprocess import call
from tempfile import TemporaryFile

app = Flask(__name__, static_folder='./')

SCENARIOS = {
	'spotify': [
		'ambilight_color_hot_lava',
		"launch_app --body '" + '{"label":"Spotify","intent":{"component":{"packageName":"com.spotify.tv.android","className":"com.spotify.tv.android.SpotifyTVActivity"},"action":"android.intent.action.MAIN"},"order":0,"id":"com.spotify.tv.android.SpotifyTVActivity-com.spotify.tv.android","type":"app"}' + "'",
	],
	'netflix': [
		'ambilight_video_natural',
		"launch_app --body '" + '{"label":"Netflix","intent":{"component":{"packageName":"com.netflix.ninja","className":"com.netflix.ninja.MainActivity"},"action":"Intent { act=android.intent.action.MAIN cat=[android.intent.category.LAUNCHER] flg=0x10000000 pkg=com.netflix.ninja cmp=com.netflix.ninja/.MainActivity }"},"order":0,"id":"com.netflix.ninja.MainActivity-com.netflix.ninja","type":"app"}' + "'",
	],
	'plex': [
		'ambilight_video_natural',
		"launch_app --body '" + '{"label":"Plex","intent":{"component":{"packageName":"com.plexapp.android","className":"com.plexapp.plex.activities.SplashActivity"},"action":"android.intent.action.MAIN"},"order":0,"id":"com.plexapp.plex.activities.SplashActivity-com.plexapp.android","type":"app"}' + "'",
	],
}

config = configparser.ConfigParser()
config.read('./settings.ini')

SCENARIO_RUNNING = False

def exec(command):
	try:
		cmd = '{} ./pylips.py --command {}'.format(config['API']['python_path'], command)
		print('\nexec: {}'.format(cmd))
		
		stdout = TemporaryFile()
		call(cmd, stdout=stdout, shell=True)
		stdout.seek(0)

		bufferStdout = str(stdout.read(), 'utf-8')
		print('stdout: {}'.format(bufferStdout))

		return json.loads(bufferStdout)
	except Exception as e:
		print(e)

	return None

def execCmd(command, key = None):
	try:
		if key is None:
			return exec(command)[command]
		else:
			return exec(command)[key]
	except Exception as e:
		print(e)

	return None

def TvInfos():
	try:
		return {
			# "current_app": execCmd('current_app'), # Not working
			"powerstate": execCmd('powerstate'),
		}
	except Exception as e:
		return {
			"powerstate": 'Off'
		}

@app.route('/', methods=['GET'])
def index():
	return app.send_static_file('index.html')

@app.route('/info', methods=['GET'])
def infoRoute():
	return jsonify(TvInfos())

@app.route('/scenario', methods=['GET'])
def scenario():
	return jsonify(list(SCENARIOS.keys()))

@app.route('/key/<string:key>', methods=['GET'])
def sendKey(key):
	try:
		exec(key)
		return jsonify({
			'key': key,
			'status': 'completed'
		})
	except Exception as e:
		print(e)

		return jsonify({
			'key': key,
			'status': 'error',
			'error': e
		})

@app.route('/scenario/<string:name>', methods=['GET'])
def startScenario(name):

	if name not in SCENARIOS.keys():
		return None

	if SCENARIO_RUNNING == True:
		return jsonify({'error': 'scenario is running'})


	SCENARIO_RUNNING = True
	infos = TvInfos()

	if infos['powerstate'] == 'Off':
		print("turn on tv")
		# exec('allow_power_on')
		exec('power_on')

	if infos['powerstate'] == 'Standby' or infos['powerstate'] == 'StandbyKeep':
		print("take the tv out of standby")
		exec('standby')

	scenario = SCENARIOS[name]
	tasks = {}
	for task in scenario:
		try:
			exec(task)
			tasks[task] = 'completed'
		except Exception as e:
			tasks[task] = 'error'
			print(e)

	SCENARIO_RUNNING = False
	return jsonify({
		'scenario': scenario,
		'status': 'completed'
	})

if __name__ == '__main__':
  api = config['API']
  app.run(api['host'], port=api['port'], debug=api['debug'])
