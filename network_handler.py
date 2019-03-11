#!/usr/bin/env python
"""Openstack Network events handler script"""

import argparse
import ast
import ConfigParser
import json
import os.path
import signal
import pika


# Callback functions (change as needed)
def callback_delete_network(data):
    """Callback function for network delete"""
    print " * Running Callback: Network %s deleted" % data['id']


def callback_create_network(data):
    """Callback function for network delete"""
    print " * Running Callback: Network %s created" % data['id']


# Arguments
parser = argparse.ArgumentParser(
    description='Monitoring and handler neutron network creation/deletes')
parser.add_argument('-c', '--configfile',
                    default="./network_handler.config",
                    help='file to read the config from')
args = vars(parser.parse_args())

# Check if config file exists
if not os.path.isfile(args['configfile']):
    print " * ERROR: config file doesn't exist"
    exit(1)

# Read config
config_parser = ConfigParser.RawConfigParser()
config_parser.read(args['configfile'])

DEBUG = ast.literal_eval(config_parser.get('Default', 'debug'))
if DEBUG:
    print " [*] Debug mode enabled"

MONITORING_QUEUE = config_parser.get('RabbitMQ', 'monitoring_queue_name')
RABBITMQ_HOSTS = config_parser.get('RabbitMQ', 'rabbitmq_hosts').split(',')
RABBITMQ_PORT = int(config_parser.get('RabbitMQ', 'rabbitmq_port'))
RABBITMQ_USER = config_parser.get('RabbitMQ', 'user')
RABBITMQ_PASS = config_parser.get('RabbitMQ', 'pass')


# Functions
def _signal_handler(_signal, _frame):
    # pylint: disable=W0612,W0613
    """Signal handler func for CTRL+C"""
    print '[*] Stopping handling!'
    exit(0)


def _process_msg(_channel, _method, _properties, body):
    # pylint: disable=W0612,W0613

    payload = json.loads(body)

    if 'event_type' in payload:
        event_type = payload['event_type']
        payload_data = payload['payload']

        if DEBUG:
            print " * Received event type: %r" % event_type
        if DEBUG:
            print json.dumps(payload, sort_keys=True,
                             indent=4, separators=(',', ': '))

        if event_type == 'network.delete.end':
            print " * End of deleted network"

        elif event_type == 'network.create.end':
            print " * End of created network"

            if payload_data['network']['status'] == 'ACTIVE':
                callback_create_network(payload_data['network'])

            else:
                print " * Unknown operation"
                if DEBUG:
                    print json.dumps(payload, sort_keys=True, indent=4,
                                     separators=(',', ': '))
    else:
        if DEBUG:
            print " * Other event"
            print json.dumps(payload, sort_keys=True, indent=4,
                             separators=(',', ': '))


# Main loop
while True:
    for mq_host in RABBITMQ_HOSTS:
        try:
            print " [*] Connecting %s ..." % mq_host
            credentials = pika.PlainCredentials(RABBITMQ_USER,
                                                RABBITMQ_PASS)
            parameters = pika.ConnectionParameters(mq_host, RABBITMQ_PORT,
                                                   '/', credentials)
            connection = pika.BlockingConnection(parameters)
            channel = connection.channel()

            channel.queue_declare(queue=MONITORING_QUEUE,
                                  auto_delete=True)
            channel.queue_bind(queue=MONITORING_QUEUE,
                               exchange='neutron',
                               routing_key='notifications.info')

            channel.basic_consume(_process_msg,
                                  queue=MONITORING_QUEUE,
                                  no_ack=True)

            print ' [*] Waiting for Network operations. To exit press CTRL+C'
            signal.signal(signal.SIGINT, _signal_handler)
            channel.start_consuming()

        # Do not recover on channel errors
        except pika.exceptions.AMQPChannelError:
            break
        # Recover on all other connection errors
        except pika.exceptions.AMQPConnectionError:
            print " * ERROR Connection"
            continue
