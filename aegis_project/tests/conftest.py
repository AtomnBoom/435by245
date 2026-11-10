import sys
import os

# Этот код берет папку "src", превращает её в абсолютный путь 
# и насильно добавляет в оперативную память Python, где он ищет модули.
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '../src')))
