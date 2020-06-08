import os
import logging
import redis
import gevent
from flask import Flask, render_template
from flask_sockets import Sockets

app = Flask(__name__)
app.debug = 'DEBUG' in os.environ

sockets = Sockets(app)

class ChatBackend(object):
  """Interface for registering and updating WebSocket clients."""

  def __init__(self):
    self.clients = list()

  def register(self, client):
    self.clients.append(client)

  def send(self, client, data):
    try:
      client.send(data)
    except Exception:
      self.clients.remove(client)

  def send_to_all_clients(self, data):
    for client in self.clients:
      gevent.spawn(self.send, client, data)

chats=ChatBackend()

@app.route('/')
def hello():
  return render_template('index.html')

@sockets.route('/submit')
def inbox(ws):
  while not ws.closed:
    gevent.sleep(0.1)
    message = ws.receive()
    if message:
      app.logger.info(u'Got message: {}'.format(message))
      data = message.get('data')
      if message['type'] == 'message':
        app.logger.info(u'Broadcasting data: {}'.format(data))
        chats.send_to_all_clients(data)

@sockets.route('/receive/')
def outbox(ws):
  chats.register(ws)

  while not ws.closed:
    gevent.sleep(0.1)

