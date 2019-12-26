import os
from trcdash.run import TRCDashRunner
from trcdash.node import LocalNode
import gevent
import socket
import unittest2
import tempfile
import time


class TestRunner(unittest2.TestCase):
    def test_args_log(self):
        _, filename = tempfile.mkstemp()
        r = TRCDashRunner(args=['-l', filename])
        self.assertEqual(r.app.config['TRCDASH_LOGS'][0], filename)

    def test_args_bind(self):
        r = TRCDashRunner(args=['-b', '10.0.0.1'])
        self.assertEqual(r.app.config['TRCDASH_BIND_HOST'], '10.0.0.1')

    def test_args_port(self):
        r = TRCDashRunner(args=['-p', '5555'])
        self.assertEqual(r.app.config['TRCDASH_PORT'], 5555)

    def test_args_debug(self):
        r = TRCDashRunner(args=['-d'])
        self.assertTrue(r.app.debug)

    def test_default_args_dont_override_config(self):
        _, filename = tempfile.mkstemp()
        with open(filename, "w") as f:
            f.write("TRCDASH_LOGS = ['/var/log/boot.log', '/var/log/dmesg']\n")
            f.flush()
        os.environ['TRCDASH_CONFIG'] = filename
        r = TRCDashRunner()
        self.assertEquals(r.app.config['TRCDASH_LOGS'], ['/var/log/boot.log', '/var/log/dmesg'])
        del os.environ['TRCDASH_CONFIG']

    def test_reload_logs(self):
        _, filename = tempfile.mkstemp()
        r = TRCDashRunner(args=['-l', filename])
        pre_count = len(r.get_local_node().logs.available)
        r.get_local_node().logs.add_patterns(r.app.config['TRCDASH_LOGS'])
        post_count = len(r.get_local_node().logs.available)
        self.assertEqual(pre_count, post_count)

    def test_update_net_io_counters(self):
        r = TRCDashRunner()
        socket.getaddrinfo('example.org', 80)
        counters = r.get_local_node().net_io_counters.update()

        for c in counters.itervalues():
            if c['rx_per_sec'] > 0 and c['tx_per_sec'] > 0:
                break
        else:
            self.fail("Didn't find any changed network interface")

    def test_local_node_is_added(self):
        r = TRCDashRunner()
        self.assertIsInstance(r.get_local_node(), LocalNode)

    def test_register_node_creates_proper_node_dict(self):
        r = TRCDashRunner()
        now = int(time.time())
        node = r.register_node('examplehost', 'example.org', 5000)
        self.assertEqual(node.host, 'example.org')
        self.assertEqual(node.port, 5000)
        self.assertEqual(node.last_registered, now)

    def test_reregister_node(self):
        r = TRCDashRunner()
        now = int(time.time())
        r.register_node('examplehost', 'example.org', 5000)
        node = r.register_node('examplehost', 'example.org', 5000)
        self.assertEqual(node.host, 'example.org')
        self.assertEqual(node.port, 5000)
        self.assertEqual(node.last_registered, now)

    def test_get_all_nodes(self):
        r = TRCDashRunner()
        r.register_node('examplehost', 'example.org', 5000)
        self.assertEqual(len(r.get_nodes()), 2) # local + registered

    def test_nodes_from_config(self):
        config = {
            'TRCDASH_NODES': [
                {
                    'name': 'test-node',
                    'host': 'remotehost.org',
                    'port': 5000
                }
            ]
        }
        r = TRCDashRunner(config)
        self.assertEqual(len(r.get_nodes()), 2)
        self.assertIn('remotehost.org:5000', r.get_nodes())
        self.assertEqual(r.get_nodes()['remotehost.org:5000'].name, 'test-node')
        self.assertEqual(r.get_nodes()['remotehost.org:5000'].host, 'remotehost.org')
        self.assertEqual(r.get_nodes()['remotehost.org:5000'].port, 5000)

    def test_register_agent(self):
        jobs = []
        agent_options = {
            'TRCDASH_AGENT': True,
            'TRCDASH_PORT': 5001,
            'TRCDASH_REGISTER_TO': 'http://localhost:5000',
            'TRCDASH_REGISTER_AS': 'the_agent'
        }
        r = TRCDashRunner()
        agent = TRCDashRunner(agent_options)
        jobs.append(gevent.spawn(r.run))
        gevent.sleep(0.3)
        jobs.append(gevent.spawn(agent.run))
        gevent.sleep(0.3)

        self.assertIn('127.0.0.1:5001', r.get_nodes())
        self.assertEquals(r.get_node('127.0.0.1:5001').name, 'the_agent')
        self.assertEquals(r.get_node('127.0.0.1:5001').port, 5001)

        r.server.close()
        agent.server.close()
        gevent.killall(jobs)

    def test_register_agent_without_name_defaults_to_hostname(self):
        agent_options = {
            'TRCDASH_AGENT': True,
            'TRCDASH_PORT': 5001,
            'TRCDASH_REGISTER_TO': 'http://localhost:5000'
        }
        r = TRCDashRunner()
        agent = TRCDashRunner(agent_options)
        jobs = []
        jobs.append(gevent.spawn(r.run))
        gevent.sleep(0.3)
        jobs.append(gevent.spawn(agent.run))
        gevent.sleep(0.3)

        self.assertIn('127.0.0.1:5001', r.get_nodes())
        self.assertEquals(r.get_node('127.0.0.1:5001').name, socket.gethostname())
        self.assertEquals(r.get_node('127.0.0.1:5001').port, 5001)

        r.server.close()
        agent.server.close()
        gevent.killall(jobs)

    def test_register_agent_to_auth_protected_host(self):
        r = TRCDashRunner({
            'TRCDASH_AUTH_USERNAME': 'user',
            'TRCDASH_AUTH_PASSWORD': 'pass'
        })
        agent = TRCDashRunner({
            'TRCDASH_AGENT': True,
            'TRCDASH_PORT': 5001,
            'TRCDASH_REGISTER_TO': 'http://localhost:5000',
            'TRCDASH_AUTH_USERNAME': 'user',
            'TRCDASH_AUTH_PASSWORD': 'pass'
        })
        jobs = []
        jobs.append(gevent.spawn(r.run))
        gevent.sleep(0.3)
        jobs.append(gevent.spawn(agent.run))
        gevent.sleep(0.3)

        self.assertIn('127.0.0.1:5001', r.get_nodes())
        self.assertEquals(r.get_node('127.0.0.1:5001').name, socket.gethostname())
        self.assertEquals(r.get_node('127.0.0.1:5001').port, 5001)

        r.server.close()
        agent.server.close()
        gevent.killall(jobs)

