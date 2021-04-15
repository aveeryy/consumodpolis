import json
import re
import requests
import selenium
import seleniumwire
from selenium import webdriver
from selenium.common.exceptions import NoSuchWindowException
from seleniumwire.webdriver import Chrome as Driver
from urllib.parse import unquote

# Advertencia: esto se escribió en la decimosexta edición de Consumópolis
# y es posible que no funcione posteriormente.

__version__ = '0.9.1'

print('''
Consumópolis Trainer %s (http://www.consumopolis.es/)
Licencia Creative Commons Zero v1.0 Universal
https://github.com/Aveeryy/consumodpolis
''' % __version__)

class Consumodpolis():
    # Juegos
    games = {
        '1': '¿Dónde se deposita?',
        '2': '4 imágenes, 1 palabra',
        '3': 'Cadena de preguntas (1)',
        '4': 'Cadena de preguntas (2)',
        '5': 'Ordena las letras',
        '6': 'Verdadero o falso',
        '7': 'Buena memoria',
        '8': 'Trotamundos',
        '9': 'La ciudad misteriosa',
        '10': 'Black Friday',
    }

    # Expresiones regulares
    gameRegex = r'.+/\d?/.+o=(\d+).+=(\d+)'
        
    @classmethod
    def __init__(self):
        global driver, _session

        # Ajustar el nivel de registro a debug
        options = webdriver.ChromeOptions()
        options.add_argument('--log-level=3')

        # Crear una instancia de webdriver
        print('Inicializando instancia de ChromeDriver...')
        driver = Driver(options=options)
        driver.get('https://consumopolis.consumo.gob.es/concurso/index.html')

        # Esperar a que se realice el inicio de sesión
        print('Esperando inicio de sesión')
        # Cambiar al iframe
        driver.switch_to.frame(0)
        while True:
            # Obtener los campos de entrada de usuario y contraseña
            try: 
                _name = driver.find_element_by_id('nick').text
            except selenium.common.exceptions.NoSuchElementException:
                continue
            else:
                print('¡Sesión iniciada correctamente!')
                _session = (_name, re.search(r'\d+', [r for r in driver.requests if 'Avatar.aspx' in r.url][0].body.decode()).group(0))
                print('Sesión iniciada como %s (ID: %s)' %(_session[0], _session[1]))
                break
                
        # Cambiar al contenido principal
        driver.switch_to.default_content()

        def _menu():
            while True:
                print('1) Obtener respuestas del juego\n2) Modificar puntuaciones\n')
                _sel = input('Tu selección: ')
                if _sel == '1':
                    self.get_answers()
                elif _sel == '2':
                    self.modify_score()
                else:
                    print('Opción inválida')     

        _menu()

    @classmethod
    def modify_score(self):
        print('Selecciona el juego cuyo valor quieras modificar:')
        for name, value in self.games.items():
            print('%s) %s' %(name, value))
        while True:
            _s = int(input('Tu selección: '))
            if _s > 10 or _s < 1:
                print('Opción inválida')
                continue
            break
        _v = int(input('Nuevo valor (0-2500): '))
        if _v > 2500:
            _v = 2500
        _r = requests.post('http://consumopolis.consumo.gob.es/concurso/juegos/scripts/grabarPartida.aspx',
                           data={'juego': _s, 'alumno': _session[1], 'puntos': _v})
        if b'ok' in _r.content:
            print('Cambiado el valor del juego "%s" a %d\n' %(self.games[str(_s)], _v))
        else:
            print('Ha ocurrido un error | https://github.com/Aveeryy/consumodpolis/issues/\n')
        
    @classmethod
    def get_answers(self):
        global _last_json
        _last_json = ''
        gameRegex = self.gameRegex
        # Esperar a que el usuario seleccione un juego
        _iframe = driver.find_element_by_xpath('/html/body/div[1]/div[3]/div[2]/iframe')  
        self._iframe = _iframe
        while True:        
            print('Esperando a que selecciones un juego...')
            while True:
                _iframe_url = _iframe.get_attribute('src')
                if re.match(gameRegex, _iframe_url) is None:
                    continue
                break
            _game = re.match(gameRegex, _iframe_url)
            if _game is not None:
                _id = _game.group(1)
                _group = _game.group(2)
                _data = 'juego=%s&idioma=%s&ciclo=%s' %(_id, 'es', _group)

            self._game = _game
            _current_game = _game.group(0)

            if not hasattr(self, 'game_' + _id):
                print('Juego no soportado, buena suerte.')
                while _current_game in _iframe.get_attribute('src'):
                    continue
                else:
                    pass
                continue
            else:
                print('Juego seleccionado: %s' % getattr(self, 'game_' + _id)(True)) 
                getattr(self, 'game_' + _id)()

    @classmethod
    def get_api_json(self):
        global _last_json
        # Obtiene las respuestas de la memoria de Chrome
        print('Obteniendo JSON con las respuestas...')
        while True:
            try:
                _json = [r for r in driver.requests if 'recuperarContenidos.aspx' in r.url][-1].response.body.decode()
            except (AttributeError, IndexError):
                continue
            if _json != _last_json:
                break
        _last_json = _json
        return json.loads(_json)

    @classmethod
    def wait_until_finish(self):
        print('Esperando a que acabes...')
        # Esperar a que el juego acabe
        while self._game.group(0) in self._iframe.get_attribute('src'):
            continue
        return

    @classmethod
    # 4 imágenes 1 palabra, juego 2
    def game_2(self, get_name=False):
        if get_name:
            return '4 imágenes 1 palabra'
        input('Pulsa ENTER en cuanto pulses el botón de iniciar juego')
        _parsed = self.get_api_json()
        if _parsed == 'Failure':
            print('Ha ocurrido un error')
            return
        # Escribe las palabras en orden
        for palabra in _parsed['palabras']:
            print('Respuesta: ' + palabra['palabra'])
        self.wait_until_finish()

    @classmethod
    # Cadena de preguntas (1), juego 3
    def game_3(self, get_name=False):
        if get_name:
            return 'Cadena de preguntas (1)'
        _parsed = self.get_api_json()
        if _parsed == 'Failure':
            print('Ha ocurrido un error')
            return
        # Escribe las respuestas en orden
        for respuesta in _parsed['preguntas']:
            print('Respuesta: ' + respuesta['correcta'])
        self.wait_until_finish()

    @classmethod
    # Cadena de preguntas (2), juego 4
    def game_4(self, get_name=False):
        if get_name:
            return 'Cadena de preguntas (2)'
        self.game_3()
        return

    @classmethod
    # Ordena las letras, juego 5
    def game_5(self, get_name=False):
        if get_name:
            return 'Ordena las letras'
        input('Pulsa ENTER en cuanto pulses el botón de iniciar juego')
        self.game_2()
        return

    @classmethod
    # Verdadero o falso, juego 6
    def game_6(self, get_name=False):
        if get_name:
            return 'Verdadero o falso'
        _parsed = self.get_api_json()
        if _parsed == 'Failure':
            print('Ha ocurrido un error')
            return
        # Escribe las respuestas en orden
        for respuesta in _parsed['preguntas']:
            if respuesta['verdadero'] == 'true':
                res = 'Verdadera'
            else:
                res = 'Falsa'
            print('Respuesta: ' + res)
        self.wait_until_finish()

    @classmethod
    # Buena memoria, juego 7
    def game_7(self, get_name=False):
        if get_name:
            return 'Buena memoria'
        _parsed = self.get_api_json()
        if _parsed == 'Failure':
            print('Ha ocurrido un error')
            return
        # Escribe las respuestas en orden
        i = 0
        for respuesta in _parsed['preguntas']:
            print('Respuesta: ' + unquote(respuesta['correcta']).replace('+', ' '))
            i -=- 1
            if i >= 10:
                break
        self.wait_until_finish()


    # TODO: implementar trotamundos

    @classmethod
    # La ciudad misteriosa, juego 9
    def game_9(self, get_name=False):
        if get_name:
            return 'La ciudad misteriosa'
        _parsed = self.get_api_json()
        if _parsed == 'Failure':
            print('Ha ocurrido un error')
            return
        # Escribe las respuestas en orden
        print('Respuesta: ' + unquote(_parsed['ciudad']).replace('+', ' '))
        print('Latitud: ' + _parsed['latitud'])
        print('Longitud: ' + _parsed['longitud'])
        self.wait_until_finish()

    @classmethod
    # Black Friday, juego 10
    def game_10(self, get_name=False):
        if get_name:
            return 'Black Friday'
        self.game_7()
        return

if __name__ == '__main__':
    try:
        Consumodpolis()
    except (NoSuchWindowException, TypeError, KeyboardInterrupt):
        print('Saliendo...')
        pass
