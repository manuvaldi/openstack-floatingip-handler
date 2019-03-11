# Openstack Event handler

Python script to monitor and handler events from Openstack neutron. This script create a queue with `auto_delete` feature binding to `neutron` exchange with `routing_key` equal to `notifications.info`

## Installation
```
pip install -r requirements.txt
```

## Use
```
python fliatingip_handler.py -c floatingip_handler.config.example
```

## Configuration
```
[Default]
debug = False

[RabbitMQ]
monitoring_queue_name = floatingip
rabbitmq_hosts = rabbitmq01,rabbitmq02,rabbitmq03
rabbitmq_port = 5672
user = guest
pass = guest
```
Options:
- `debug`: Enable or disable debug trace logs.
- `monitoring_queue_name`: RabbitMQ queue name to create and manage (auto_delete queue)
- `rabbitmq_hosts`: Comman-separated list of rabbitmq servers
- `rabbitmq_port`: RabbitMQ port
- `user`: RabbitMQ user name
- `pass`: RabbitMQ password

## Configure/Dev handler actions
By default, no action is configure to do either UP or DOWN floating IP. If you want to handler these actions you should modified the code. There are 2 functions on the top of script:

- `callback_create_floating_ip`: Handler function for floating IP association
- `callback_delete_floating_ip`: Handler function for floating IP disassociation

An example:

```
from httplib2 import Http
def callback_delete_floating_ip(data):
    """Callback function for floating ip disassociation"""
    h = Http()
    print " * Floating IP %s disassociated" % data['floating_ip_address']
    unregister = json.loads(urllib2.urlopen("http://10.10.10.10/release/ipv4address?ip_address="+data['floating_ip_address']).read())

```

## Test
```
sh test.sh
```


## Additional Scripts

In this repo there are other scripts with similar installation, configuration and working

- `network_handler.py`: listen for network creation / delete operations
