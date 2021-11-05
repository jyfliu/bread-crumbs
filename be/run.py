#!/usr/bin/python

import asyncio

from easydict import EasyDict as edict

import server

def main():
  config = edict({
    'server_port': 6942,
    'tps': 60,
  });
  print("Config: ", config)
  print("Starting server")

  asyncio.run(server.run(config))

if __name__ == '__main__':
  main()
