from flask import Flask, render_template, request, jsonify, redirect, url_for, session, flash
from functools import wraps
import serial
import time
from datetime import datetime
import json
import os

app = Flask(__name__)
app.secret_key = 'ta_cle_secrete_ici'

# Fichier pour stocker les données
DATA_FILE = 'studios_data.json'

#les commande de visca
class SonyPTZController:
    def __init__(self, port='COM1', baudrate=9600, address=1):
        self.port = port
        self.baudrate = baudrate
        self.address = 0x80 + address
        self.ser = None
        self.connected = False
        self.last_command_time = time.time()
        self.commands = {
            'power_on': '81 01 04 00 02 FF',
            'power_off': '81 01 04 00 03 FF',
            'stop': '81 01 06 01 00 00 03 03 FF',
            'left': '81 01 06 01 07 00 01 03 FF',
            'right': '81 01 06 01 07 00 02 03 FF',
            'up': '81 01 06 01 00 07 03 01 FF',
            'down': '81 01 06 01 00 07 03 02 FF',
            'upleft': '81 01 06 01 0C 07 01 01 FF',
            'upright': '81 01 06 01 0C 07 02 01 FF',
            'downleft': '81 01 06 01 0C 0C 01 02 FF',
            'downright': '81 01 06 01 0C 0C 02 02 FF',
            'zoom in': '81 01 04 07 02 FF',
            'zoom out': '81 01 04 07 03 FF',
        }

    def connect(self):
        try:
            self.ser = serial.Serial(
                port=self.port,
                baudrate=self.baudrate,
                bytesize=8,
                parity='N',
                stopbits=1,
                timeout=1,
                xonxoff=False,
                rtscts=False,
                dsrdtr=False
            )
            time.sleep(2)
            self.connected = True
            return True
        except Exception as e:
            print(f"Connection error: {e}")
            self.connected = False
            return False

    def disconnect(self):
        if self.ser and self.ser.is_open:
            self.ser.close()
        self.connected = False

    def send_command(self, command_name):
        if not self.connected or not self.ser:
            return {'success': False, 'error': 'Not connected'}
        if command_name not in self.commands:
            return {'success': False, 'error': 'Unknown command'}
        try:
            current_time = time.time()
            if current_time - self.last_command_time < 0.1:
                time.sleep(0.1)
            self.ser.flushInput()
            self.ser.flushOutput()
            command_hex = self.commands[command_name]
            command_bytes = bytes.fromhex(command_hex.replace(' ', ''))
            self.ser.write(command_bytes)
            self.last_command_time = time.time()
            time.sleep(0.1)
            response = self.ser.read(10)
            return {
                'success': True,
                'command': command_name,
                'response': response.hex() if response else 'No response',
                'timestamp': datetime.now().strftime('%H:%M:%S')
            }
        except Exception as e:
            return {'success': False, 'error': str(e)}


camera = SonyPTZController()

# pour page de login
users = {
    'hasna': '200177',
    'oujamer': '1960',
    'rachid': '1994'
}
#afficher les studio sont deja connu
def load_studios_data():
    if os.path.exists(DATA_FILE):
        try:
            with open(DATA_FILE, 'r', encoding='utf-8') as f:
                return json.load(f)
        except:
            pass
    return {
        'Studio 1': {
            'location': 'Radio',
            'cameras': {
                'Camera 1': {
                    'ip': '192.168.1.101',
                    'port': '1',
                    'baudrate': '9600',
                    'model': 'Sony PTZ',
                    'resolution': '1920x1080',
                    'username': 'users',
                    'password': 'users'
                },
                'Camera 2': {
                    'ip': '192.168.1.102',
                    'port': '2',
                    'baudrate': '9600',
                    'model': 'Sony PTZ',
                    'username': 'admin',
                    'password': 'admin123'
                }
            }
        },
        'Studio 2': {
            'location': 'Radio',
            'cameras': {
                'Camera 3': {
                    'ip': '192.168.1.103',
                    'port': '3',
                    'baudrate': '9600',
                    'model': 'Sony PTZ',
                    'username': 'admin',
                    'password': 'admin123'
                },
                'Camera 4': {
                    'ip': '192.168.1.104',
                    'port': '4',
                    'baudrate': '9600',
                    'model': 'Sony PTZ',
                    'username': 'admin',
                    'password': 'admin123'
                }
            }
        },
        'TV': {
            'location': 'Radio',
            'cameras': {
                'Camera 7': {
                    'ip': '192.168.1.107',
                    'port': '5',
                    'baudrate': '9600',
                    'model': 'Sony PTZ',
                    'username': 'admin',
                    'password': 'admin123'
                },
                'Camera 8': {
                    'ip': '192.168.1.108',
                    'port': '6',
                    'baudrate': '9600',
                    'model': 'Sony PTZ',
                    'username': 'admin',
                    'password': 'admin123'
                }
            }
        }
    }
# Sauvegarde les données des studios dans le fichier JSON #
def save_studios_data(data):

    try:
        with open(DATA_FILE, 'w', encoding='utf-8') as f:
            json.dump(data, f, indent=2, ensure_ascii=False)
        return True
    except Exception as e:
        print(f"Erreur lors de la sauvegarde: {e}")
        return False

def get_studios_for_camera_settings():
    """Convertit les données complètes en format simple pour camera_settings"""
    full_data = load_studios_data()
    simple_format = {}
    for studio_name, studio_data in full_data.items():
        simple_format[studio_name] = list(studio_data['cameras'].keys())
    return simple_format

def login_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if 'username' not in session:
            return redirect(url_for('login'))
        return f(*args, **kwargs)

    return decorated_function
#page d'acueil#
@app.route('/')
def index():
    return render_template('index.html')
#page de login #
@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        if users.get(username) == password:
            session['username'] = username
            flash("Connexion réussie!", "success")
            return redirect(url_for('ptz_control'))
        else:
            flash("Nom d'utilisateur ou mot de passe incorrect.", "danger")
    return render_template('login.html')

#deconnexion#
@app.route('/logout')
def logout():
    session.pop('username', None)
    flash("Déconnecté.", "info")
    return redirect(url_for('index'))
#page de ptz control#
@app.route('/ptz_control')
@login_required
def ptz_control():
    baudrates = [9600, 34000]
    com_ports = [f"COM{i}" for i in range(1, 10)]
    return render_template('ptz_control.html', baudrates=baudrates, com_ports=com_ports)
@app.route('/connect', methods=['POST'])
def connect_camera():
    data = request.get_json()
    port = data.get('port', 'COM1')
    baudrate = int(data.get('baudrate', 9600))
    global camera
    camera = SonyPTZController(port=port, baudrate=baudrate)
    if camera.connect():
        return jsonify({'success': True, 'message': 'Camera connected successfully'})
    else:
        return jsonify({'success': False, 'message': 'Failed to connect to camera'})
@app.route('/disconnect', methods=['POST'])
def disconnect_camera():
    camera.disconnect()
    return jsonify({'success': True, 'message': 'Camera disconnected'})
# verifier la commande envoyer #
@app.route('/command/<command_name>', methods=['POST'])
def send_camera_command(command_name):
    result = camera.send_command(command_name)
    return jsonify(result)
#statu de camera connect ou non #
@app.route('/status')
def get_status():
    return jsonify({
        'connected': camera.connected,
        'port': camera.port,
        'baudrate': camera.baudrate
    })
#la page de camera settings #
@app.route('/camera_settings')
@login_required
def camera_settings():
    studios = get_studios_for_camera_settings()
    return render_template('camera_settings.html', studios=studios)


@app.route('/studio_settings')
@login_required
def studio_settings():
    studios_data = load_studios_data()
    return render_template('studio_settings.html', studios_data=studios_data)


# API Routes pour la gestion des studios et caméras

@app.route('/api/studios', methods=['GET'])
@login_required
def get_studios():
    """Récupère tous les studios avec leurs données complètes"""
    return jsonify(load_studios_data())


@app.route('/api/studios', methods=['POST'])
@login_required
def add_studio():
    """Ajoute un nouveau studio"""
    data = request.get_json()
    studio_name = data.get('name')
    location = data.get('location', '')


    if not studio_name:
        return jsonify({'success': False, 'error': 'Nom du studio requis'}), 400

    studios_data = load_studios_data()

    if studio_name in studios_data:
        return jsonify({'success': False, 'error': 'Un studio avec ce nom existe déjà'}), 409

    studios_data[studio_name] = {
        'location': location,

        'cameras': {}
    }

    if save_studios_data(studios_data):
        return jsonify({'success': True, 'message': f'Studio "{studio_name}" créé avec succès'})
    else:
        return jsonify({'success': False, 'error': 'Erreur lors de la sauvegarde'}), 500


@app.route('/api/studios/<studio_name>', methods=['DELETE'])
@login_required
def delete_studio(studio_name):
    """Supprime un studio"""
    studios_data = load_studios_data()

    if studio_name not in studios_data:
        return jsonify({'success': False, 'error': 'Studio introuvable'}), 404

    del studios_data[studio_name]

    if save_studios_data(studios_data):
        return jsonify({'success': True, 'message': f'Studio "{studio_name}" supprimé avec succès'})
    else:
        return jsonify({'success': False, 'error': 'Erreur lors de la sauvegarde'}), 500


@app.route('/api/studios/<studio_name>/cameras', methods=['POST'])
@login_required
def add_camera(studio_name):
    """Ajoute une nouvelle caméra à un studio"""
    data = request.get_json()
    camera_name = data.get('name')

    if not camera_name:
        return jsonify({'success': False, 'error': 'Nom de la caméra requis'}), 400

    studios_data = load_studios_data()

    if studio_name not in studios_data:
        return jsonify({'success': False, 'error': 'Studio introuvable'}), 404

    if camera_name in studios_data[studio_name]['cameras']:
        return jsonify({'success': False, 'error': 'Une caméra avec ce nom existe déjà dans ce studio'}), 409

    # Ajouter la caméra avec ses paramètres
    studios_data[studio_name]['cameras'][camera_name] = {
        'ip': data.get('ip', ''),
        'port': data.get('port', '1'),
        'baudrate': data.get('baudrate', '9600'),
        'model': data.get('model', ''),
        'username': data.get('username', ''),
        'password': data.get('password', '')
    }

    if save_studios_data(studios_data):
        return jsonify({'success': True, 'message': f'Caméra "{camera_name}" ajoutée avec succès'})
    else:
        return jsonify({'success': False, 'error': 'Erreur lors de la sauvegarde'}), 500


@app.route('/api/studios/<studio_name>/cameras/<camera_name>', methods=['DELETE'])
@login_required
def delete_camera(studio_name, camera_name):
    """Supprime une caméra d'un studio"""
    studios_data = load_studios_data()

    if studio_name not in studios_data:
        return jsonify({'success': False, 'error': 'Studio introuvable'}), 404

    if camera_name not in studios_data[studio_name]['cameras']:
        return jsonify({'success': False, 'error': 'Caméra introuvable'}), 404

    del studios_data[studio_name]['cameras'][camera_name]

    if save_studios_data(studios_data):
        return jsonify({'success': True, 'message': f'Caméra "{camera_name}" supprimée avec succès'})
    else:
        return jsonify({'success': False, 'error': 'Erreur lors de la sauvegarde'}), 500


@app.route('/api/studios/<studio_name>/cameras/<camera_name>', methods=['PUT'])
@login_required
def update_camera(studio_name, camera_name):
    """Met à jour une caméra"""
    data = request.get_json()
    studios_data = load_studios_data()

    if studio_name not in studios_data:
        return jsonify({'success': False, 'error': 'Studio introuvable'}), 404

    if camera_name not in studios_data[studio_name]['cameras']:
        return jsonify({'success': False, 'error': 'Caméra introuvable'}), 404

    # Mettre à jour les paramètres de la caméra
    camera_data = studios_data[studio_name]['cameras'][camera_name]
    camera_data.update({
        'ip': data.get('ip', camera_data.get('ip', '')),
        'port': data.get('port', camera_data.get('port', '8')),
        'baudrate': data.get('baudrate', camera_data.get('baudrate', '9600')),
        'model': data.get('model', camera_data.get('model', '')),
        'username': data.get('username', camera_data.get('username', '')),
        'password': data.get('password', camera_data.get('password', ''))
    })

    if save_studios_data(studios_data):
        return jsonify({'success': True, 'message': f'Caméra "{camera_name}" mise à jour avec succès'})
    else:
        return jsonify({'success': False, 'error': 'Erreur lors de la sauvegarde'}), 500


if __name__ == '__main__':
    app.run(debug=True)