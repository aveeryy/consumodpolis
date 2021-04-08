import json
import re
import getpass
import time
import requests
import seleniumwire
from seleniumwire.webdriver import Chrome as Driver
from urllib.parse import unquote


# Advertencia: esto se escribió en la decimosexta edición de Consumópolis
# y es posible que no funcione posteriormente.

print('''
Consumópolis Trainer (http://www.consumopolis.es/)
Licencia Creative Commons Zero v1.0 Universal
https://github.com/Aveeryy/consumodpolis
''')

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
    gameRegex = r'.+/(\d?)/\d?.+=(\d)'
        
    @classmethod
    def __init__(self):
        global driver

        # Crear una instancia de webdriver
        print('Inicializando instancia de ChromeDriver...')
        driver = Driver()
        driver.get('http://www.consumopolis.es/concurso/index.html')
        
        # Hacer click en el botón de inicio de sesión
        driver.find_element_by_id("city").click()

        # Esperar a que se realice el inicio de sesión
        print('Inicio de sesión')
        while True:
            user = input('Nombre de usuario: ')
            password = getpass.getpass('Contraseña: ')

            # Cambiar al iframe
            driver.switch_to.frame(0)
            # Obtener los campos de entrada de usuario y contraseña
            driver.find_element_by_id('inputUser').send_keys(user)
            driver.find_element_by_id('inputPassword').send_keys(password)
            driver.find_element_by_id('send-button').click()
            # Volver al contenido principal
            driver.switch_to.default_content()
            time.sleep(0.2)
            # Obtener código de error
            if driver.find_element_by_xpath('/html/body').get_attribute('class') == 'modal-open':
                # Mostrar código de error
                print('Ha ocurrido un error: ' + driver.find_element_by_xpath('/html/body/div[4]/div/div/div/div/div/div/div').text.split('\n')[0])
                # Cerrar el cuadro de error
                driver.find_element_by_xpath('/html/body/div[4]/div/div/div/div/div/div/div/button').click()
                # Limpiar los cuadros de entrada
                driver.switch_to.frame(0)
                driver.find_element_by_id('inputUser').clear()
                driver.find_element_by_id('inputPassword').clear()
                driver.switch_to.default_content()
                continue
            else:
                print('¡Sesión iniciada correctamente!')
                time.sleep(1)
                _session = (user, re.search(r'\d+', [r for r in driver.requests if 'Avatar.aspx' in r.url][0].body.decode()).group(0))
                print('Sesión iniciada como %s (ID: %s)' %(_session[0], _session[1]))
                break
                
        # Cambiar al contenido principal
        driver.switch_to.default_content()

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
        _r = requests.post('http://www.consumopolis.es/concurso/juegos/scripts/grabarPartida.aspx',
                           data={'juego': _s, 'alumno': self._session[1], 'puntos': _v})
        if b'ok' in _r.content:
            print('Cambiado el valor del juego "%s" a %d' %(self.games[str(_s)], _v))
        else:
            print('Ha ocurrido un error | https://github.com/Aveeryy/consumodpolis/issues/')
        
    @classmethod
    def get_answers(self):
        gameRegex = self.gameRegex
        # Esperar a que el usuario seleccione un juego
        _iframe = driver.find_element_by_xpath('/html/body/div[1]/div[3]/div[2]/iframe')  
        self._iframe = _iframe
        while True:        
            print('Esperando a que selecciones un juego...')
            while True:
                _iframe_url = _iframe.get_attribute('src')
                if re.match(gameRegex, _iframe_url) is None and re.match(alt_gameRegex, _iframe_url) is None:
                    continue
                break
            _game = re.match(gameRegex, _iframe_url)
            if _game is not None:
                _id = _game.group(1)
                _group = _game.group(2)
                _data = 'juego=%s&idioma=%s&ciclo=%s' %(_id, _group)

            self._game = _game      

            if not hasattr(self, 'game_' + _id):
                _current_game = _game.group(0)
                print('Juego no soportado.')
                while _current_game == _iframe.get_attribute('src'):
                    continue
                else:
                    pass
                continue
            else:
                print('Juego seleccionado: %s' % getattr(self, 'game_' + _id)(True))
                getattr(self, 'game_' + _id)()

    @classmethod
    def get_api_json(self):
        # Obtiene las respuestas de la memoria de Chrome
        print('Obteniendo JSON con las respuestas...')
        return [r for r in driver.requests if 'recuperarContenidos.aspx' in r.url][-1:][0].response.body.decode()

    @classmethod
    # 4 imágenes 1 palabra, juego 2
    def game_2(self, get_name=False):
        if get_name:
            return '4 imágenes 1 palabra'
        input('Pulsa ENTER en cuanto pulses el botón de iniciar juego')
        time.sleep(0.5)
        _parsed = self.get_api_json()
        # Escribe las palabras en orden
        for palabra in _parsed['palabras']:
            print('Respuesta: ' + palabra['palabra'])
        print('Esperando a que acabes...')
        # Esperar a que el juego acabe
        while self._game.group(0) ==  self._iframe.get_attribute('src'):
            continue
        pass
        


if __name__ == '__main__':
    Consumodpolis()
    