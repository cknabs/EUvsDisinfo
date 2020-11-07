from app import app
from layouts import main_layout
import callbacks

app.layout = main_layout

if __name__ == '__main__':
    app.run_server(debug=True)
