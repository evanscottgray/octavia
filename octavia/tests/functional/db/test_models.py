#    Copyright 2014 Rackspace
#
#    Licensed under the Apache License, Version 2.0 (the "License"); you may
#    not use this file except in compliance with the License. You may obtain
#    a copy of the License at
#
#         http://www.apache.org/licenses/LICENSE-2.0
#
#    Unless required by applicable law or agreed to in writing, software
#    distributed under the License is distributed on an "AS IS" BASIS, WITHOUT
#    WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied. See the
#    License for the specific language governing permissions and limitations
#    under the License.

import datetime

from oslo_utils import uuidutils

from octavia.common import constants
from octavia.common import data_models
from octavia.db import models
from octavia.tests.functional.db import base

from sqlalchemy.orm import collections


class ModelTestMixin(object):

    FAKE_IP = '10.0.0.1'
    FAKE_UUID_1 = uuidutils.generate_uuid()
    FAKE_UUID_2 = uuidutils.generate_uuid()

    def _insert(self, session, model_cls, model_kwargs):
        with session.begin():
            model = model_cls(**model_kwargs)
            session.add(model)
        return model

    def associate_amphora(self, load_balancer, amphora):
        load_balancer.amphorae.append(amphora)

    def create_listener(self, session, **overrides):
        kwargs = {'project_id': self.FAKE_UUID_1,
                  'id': self.FAKE_UUID_1,
                  'protocol': constants.PROTOCOL_HTTP,
                  'protocol_port': 80,
                  'provisioning_status': constants.ACTIVE,
                  'operating_status': constants.ONLINE,
                  'enabled': True}
        kwargs.update(overrides)
        return self._insert(session, models.Listener, kwargs)

    def create_listener_statistics(self, session, listener_id, **overrides):
        kwargs = {'listener_id': listener_id,
                  'bytes_in': 0,
                  'bytes_out': 0,
                  'active_connections': 0,
                  'total_connections': 0}
        kwargs.update(overrides)
        return self._insert(session, models.ListenerStatistics, kwargs)

    def create_pool(self, session, **overrides):
        kwargs = {'project_id': self.FAKE_UUID_1,
                  'id': self.FAKE_UUID_1,
                  'protocol': constants.PROTOCOL_HTTP,
                  'lb_algorithm': constants.LB_ALGORITHM_LEAST_CONNECTIONS,
                  'operating_status': constants.ONLINE,
                  'enabled': True}
        kwargs.update(overrides)
        return self._insert(session, models.Pool, kwargs)

    def create_session_persistence(self, session, pool_id, **overrides):
        kwargs = {'pool_id': pool_id,
                  'type': constants.SESSION_PERSISTENCE_HTTP_COOKIE}
        kwargs.update(overrides)
        return self._insert(session, models.SessionPersistence, kwargs)

    def create_health_monitor(self, session, pool_id, **overrides):
        kwargs = {'pool_id': pool_id,
                  'type': constants.HEALTH_MONITOR_HTTP,
                  'delay': 1,
                  'timeout': 1,
                  'fall_threshold': 1,
                  'rise_threshold': 1,
                  'enabled': True,
                  'project_id': self.FAKE_UUID_1}
        kwargs.update(overrides)
        return self._insert(session, models.HealthMonitor, kwargs)

    def create_member(self, session, pool_id, **overrides):
        kwargs = {'project_id': self.FAKE_UUID_1,
                  'id': self.FAKE_UUID_1,
                  'pool_id': pool_id,
                  'ip_address': '10.0.0.1',
                  'protocol_port': 80,
                  'operating_status': constants.ONLINE,
                  'enabled': True}
        kwargs.update(overrides)
        return self._insert(session, models.Member, kwargs)

    def create_load_balancer(self, session, **overrides):
        kwargs = {'project_id': self.FAKE_UUID_1,
                  'id': self.FAKE_UUID_1,
                  'provisioning_status': constants.ACTIVE,
                  'operating_status': constants.ONLINE,
                  'enabled': True}
        kwargs.update(overrides)
        return self._insert(session, models.LoadBalancer, kwargs)

    def create_vip(self, session, load_balancer_id, **overrides):
        kwargs = {'load_balancer_id': load_balancer_id}
        kwargs.update(overrides)
        return self._insert(session, models.Vip, kwargs)

    def create_sni(self, session, **overrides):
        kwargs = {'listener_id': self.FAKE_UUID_1,
                  'tls_container_id': self.FAKE_UUID_1}
        kwargs.update(overrides)
        return self._insert(session, models.SNI, kwargs)

    def create_amphora(self, session, **overrides):
        kwargs = {'id': self.FAKE_UUID_1,
                  'compute_id': self.FAKE_UUID_1,
                  'status': constants.ACTIVE,
                  'vrrp_ip': self.FAKE_IP,
                  'ha_ip': self.FAKE_IP,
                  'vrrp_port_id': self.FAKE_UUID_1,
                  'ha_port_id': self.FAKE_UUID_2,
                  'lb_network_ip': self.FAKE_IP,
                  'cert_expiration': datetime.datetime.utcnow(),
                  'cert_busy': False}
        kwargs.update(overrides)
        return self._insert(session, models.Amphora, kwargs)

    def create_amphora_health(self, session, **overrides):
        kwargs = {'amphora_id': self.FAKE_UUID_1,
                  'last_update': datetime.date.today(),
                  'busy': True}
        kwargs.update(overrides)
        return self._insert(session, models.AmphoraHealth, kwargs)

    def create_l7policy(self, session, listener_id, **overrides):
        kwargs = {'id': self.FAKE_UUID_1,
                  'listener_id': listener_id,
                  'action': constants.L7POLICY_ACTION_REJECT,
                  'position': 0,
                  'enabled': True}
        kwargs.update(overrides)
        return self._insert(session, models.L7Policy, kwargs)

    def create_l7rule(self, session, l7policy_id, **overrides):
        kwargs = {'id': self.FAKE_UUID_1,
                  'l7policy_id': l7policy_id,
                  'type': constants.L7RULE_TYPE_PATH,
                  'compare_type': constants.L7RULE_COMPARE_TYPE_STARTS_WITH,
                  'value': '/api'}
        kwargs.update(overrides)
        return self._insert(session, models.L7Rule, kwargs)


class PoolModelTest(base.OctaviaDBTestBase, ModelTestMixin):

    def test_create(self):
        self.create_pool(self.session)

    def test_update(self):
        pool = self.create_pool(self.session)
        id = pool.id
        pool.name = 'test1'
        new_pool = self.session.query(
            models.Pool).filter_by(id=id).first()
        self.assertEqual('test1', new_pool.name)

    def test_delete(self):
        pool = self.create_pool(self.session)
        id = pool.id
        with self.session.begin():
            self.session.delete(pool)
            self.session.flush()
        new_pool = self.session.query(
            models.Pool).filter_by(id=id).first()
        self.assertIsNone(new_pool)

    def test_member_relationship(self):
        pool = self.create_pool(self.session)
        self.create_member(self.session, pool.id, id=self.FAKE_UUID_1,
                           ip_address="10.0.0.1")
        self.create_member(self.session, pool.id, id=self.FAKE_UUID_2,
                           ip_address="10.0.0.2")
        new_pool = self.session.query(
            models.Pool).filter_by(id=pool.id).first()
        self.assertIsNotNone(new_pool.members)
        self.assertEqual(2, len(new_pool.members))
        self.assertIsInstance(new_pool.members[0], models.Member)

    def test_health_monitor_relationship(self):
        pool = self.create_pool(self.session)
        self.create_health_monitor(self.session, pool.id)
        new_pool = self.session.query(models.Pool).filter_by(
            id=pool.id).first()
        self.assertIsNotNone(new_pool.health_monitor)
        self.assertIsInstance(new_pool.health_monitor,
                              models.HealthMonitor)

    def test_session_persistence_relationship(self):
        pool = self.create_pool(self.session)
        self.create_session_persistence(self.session, pool_id=pool.id)
        new_pool = self.session.query(models.Pool).filter_by(
            id=pool.id).first()
        self.assertIsNotNone(new_pool.session_persistence)
        self.assertIsInstance(new_pool.session_persistence,
                              models.SessionPersistence)

    def test_listener_relationship(self):
        pool = self.create_pool(self.session)
        listener = self.create_listener(self.session, default_pool_id=pool.id)
        new_pool = self.session.query(models.Pool).filter_by(
            id=pool.id).first()
        self.assertIsNotNone(new_pool.listeners)
        self.assertIsInstance(new_pool.listeners, list)
        self.assertIsInstance(new_pool.listeners[0], models.Listener)
        self.assertIn(listener.id, [l.id for l in new_pool.listeners])


class MemberModelTest(base.OctaviaDBTestBase, ModelTestMixin):

    def setUp(self):
        super(MemberModelTest, self).setUp()
        self.pool = self.create_pool(self.session)

    def test_create(self):
        self.create_member(self.session, self.pool.id)

    def test_update(self):
        member = self.create_member(self.session, self.pool.id)
        member_id = member.id
        member.name = 'test1'
        new_member = self.session.query(
            models.Member).filter_by(id=member_id).first()
        self.assertEqual('test1', new_member.name)

    def test_delete(self):
        member = self.create_member(self.session, self.pool.id)
        member_id = member.id
        with self.session.begin():
            self.session.delete(member)
            self.session.flush()
        new_member = self.session.query(
            models.Member).filter_by(id=member_id).first()
        self.assertIsNone(new_member)

    def test_pool_relationship(self):
        member = self.create_member(self.session, self.pool.id,
                                    id=self.FAKE_UUID_1,
                                    ip_address="10.0.0.1")
        self.create_member(self.session, self.pool.id, id=self.FAKE_UUID_2,
                           ip_address="10.0.0.2")
        new_member = self.session.query(models.Member).filter_by(
            id=member.id).first()
        self.assertIsNotNone(new_member.pool)
        self.assertIsInstance(new_member.pool, models.Pool)


class SessionPersistenceModelTest(base.OctaviaDBTestBase, ModelTestMixin):

    def setUp(self):
        super(SessionPersistenceModelTest, self).setUp()
        self.pool = self.create_pool(self.session)

    def test_create(self):
        self.create_session_persistence(self.session, self.pool.id)

    def test_update(self):
        session_persistence = self.create_session_persistence(self.session,
                                                              self.pool.id)
        session_persistence.name = 'test1'
        new_session_persistence = self.session.query(
            models.SessionPersistence).filter_by(pool_id=self.pool.id).first()
        self.assertEqual('test1', new_session_persistence.name)

    def test_delete(self):
        session_persistence = self.create_session_persistence(self.session,
                                                              self.pool.id)
        with self.session.begin():
            self.session.delete(session_persistence)
            self.session.flush()
        new_session_persistence = self.session.query(
            models.SessionPersistence).filter_by(pool_id=self.pool.id).first()
        self.assertIsNone(new_session_persistence)

    def test_pool_relationship(self):
        self.create_session_persistence(self.session, self.pool.id)
        new_persistence = self.session.query(
            models.SessionPersistence).filter_by(pool_id=self.pool.id).first()
        self.assertIsNotNone(new_persistence.pool)
        self.assertIsInstance(new_persistence.pool, models.Pool)


class ListenerModelTest(base.OctaviaDBTestBase, ModelTestMixin):

    def test_create(self):
        self.create_listener(self.session)

    def test_update(self):
        listener = self.create_listener(self.session)
        listener_id = listener.id
        listener.name = 'test1'
        new_listener = self.session.query(
            models.Listener).filter_by(id=listener_id).first()
        self.assertEqual('test1', new_listener.name)

    def test_delete(self):
        listener = self.create_listener(self.session)
        listener_id = listener.id
        with self.session.begin():
            self.session.delete(listener)
            self.session.flush()
        new_listener = self.session.query(
            models.Listener).filter_by(id=listener_id).first()
        self.assertIsNone(new_listener)

    def test_load_balancer_relationship(self):
        lb = self.create_load_balancer(self.session)
        listener = self.create_listener(self.session, load_balancer_id=lb.id)
        new_listener = self.session.query(
            models.Listener).filter_by(id=listener.id).first()
        self.assertIsNotNone(new_listener.load_balancer)
        self.assertIsInstance(new_listener.load_balancer, models.LoadBalancer)

    def test_listener_statistics_relationship(self):
        listener = self.create_listener(self.session)
        self.create_listener_statistics(self.session, listener_id=listener.id)
        new_listener = self.session.query(models.Listener).filter_by(
            id=listener.id).first()
        self.assertIsNotNone(new_listener.stats)
        self.assertIsInstance(new_listener.stats, models.ListenerStatistics)

    def test_default_pool_relationship(self):
        pool = self.create_pool(self.session)
        listener = self.create_listener(self.session, default_pool_id=pool.id)
        new_listener = self.session.query(models.Listener).filter_by(
            id=listener.id).first()
        self.assertIsNotNone(new_listener.default_pool)
        self.assertIsInstance(new_listener.default_pool, models.Pool)
        self.assertIsInstance(new_listener.pools, list)
        self.assertIn(pool.id, [p.id for p in new_listener.pools])

    def test_sni_relationship(self):
        listener = self.create_listener(self.session)
        self.create_sni(self.session, listener_id=listener.id,
                        tls_container_id=self.FAKE_UUID_1)
        self.create_sni(self.session, listener_id=listener.id,
                        tls_container_id=self.FAKE_UUID_2)
        new_listener = self.session.query(models.Listener).filter_by(
            id=listener.id).first()
        self.assertIsNotNone(new_listener.sni_containers)
        self.assertEqual(2, len(new_listener.sni_containers))

    def test_pools_list(self):
        pool = self.create_pool(self.session)
        listener = self.create_listener(self.session, default_pool_id=pool.id)
        new_listener = self.session.query(models.Listener).filter_by(
            id=listener.id).first()
        self.assertIsNotNone(new_listener.pools)
        self.assertIsInstance(new_listener.pools, list)
        self.assertIsInstance(new_listener.pools[0], models.Pool)


class ListenerStatisticsModelTest(base.OctaviaDBTestBase, ModelTestMixin):

    def setUp(self):
        super(ListenerStatisticsModelTest, self).setUp()
        self.listener = self.create_listener(self.session)

    def test_create(self):
        self.create_listener_statistics(self.session, self.listener.id)

    def test_update(self):
        stats = self.create_listener_statistics(self.session, self.listener.id)
        stats.name = 'test1'
        new_stats = self.session.query(models.ListenerStatistics).filter_by(
            listener_id=self.listener.id).first()
        self.assertEqual('test1', new_stats.name)

    def test_delete(self):
        stats = self.create_listener_statistics(self.session, self.listener.id)
        with self.session.begin():
            self.session.delete(stats)
            self.session.flush()
        new_stats = self.session.query(models.ListenerStatistics).filter_by(
            listener_id=self.listener.id).first()
        self.assertIsNone(new_stats)

    def test_listener_relationship(self):
        self.create_listener_statistics(self.session, self.listener.id)
        new_stats = self.session.query(models.ListenerStatistics).filter_by(
            listener_id=self.listener.id).first()
        self.assertIsNotNone(new_stats.listener)
        self.assertIsInstance(new_stats.listener, models.Listener)


class HealthMonitorModelTest(base.OctaviaDBTestBase, ModelTestMixin):

    def setUp(self):
        super(HealthMonitorModelTest, self).setUp()
        self.pool = self.create_pool(self.session)

    def test_create(self):
        self.create_health_monitor(self.session, self.pool.id)

    def test_update(self):
        health_monitor = self.create_health_monitor(self.session, self.pool.id)
        health_monitor.name = 'test1'
        new_health_monitor = self.session.query(
            models.HealthMonitor).filter_by(
                pool_id=health_monitor.pool_id).first()
        self.assertEqual('test1', new_health_monitor.name)

    def test_delete(self):
        health_monitor = self.create_health_monitor(self.session, self.pool.id)
        with self.session.begin():
            self.session.delete(health_monitor)
            self.session.flush()
        new_health_monitor = self.session.query(
            models.HealthMonitor).filter_by(
                pool_id=health_monitor.pool_id).first()
        self.assertIsNone(new_health_monitor)

    def test_pool_relationship(self):
        health_monitor = self.create_health_monitor(self.session, self.pool.id)
        new_health_monitor = self.session.query(
            models.HealthMonitor).filter_by(
                pool_id=health_monitor.pool_id).first()
        self.assertIsNotNone(new_health_monitor.pool)
        self.assertIsInstance(new_health_monitor.pool, models.Pool)


class LoadBalancerModelTest(base.OctaviaDBTestBase, ModelTestMixin):

    def test_create(self):
        self.create_load_balancer(self.session)

    def test_update(self):
        load_balancer = self.create_load_balancer(self.session)
        lb_id = load_balancer.id
        load_balancer.name = 'test1'
        new_load_balancer = self.session.query(
            models.LoadBalancer).filter_by(id=lb_id).first()
        self.assertEqual('test1', new_load_balancer.name)

    def test_delete(self):
        load_balancer = self.create_load_balancer(self.session)
        lb_id = load_balancer.id
        with self.session.begin():
            self.session.delete(load_balancer)
            self.session.flush()
        new_load_balancer = self.session.query(
            models.LoadBalancer).filter_by(id=lb_id).first()
        self.assertIsNone(new_load_balancer)

    def test_listener_relationship(self):
        load_balancer = self.create_load_balancer(self.session)
        self.create_listener(self.session, load_balancer_id=load_balancer.id)
        new_load_balancer = self.session.query(
            models.LoadBalancer).filter_by(id=load_balancer.id).first()
        self.assertIsNotNone(new_load_balancer.listeners)
        self.assertEqual(1, len(new_load_balancer.listeners))

    def test_load_balancer_amphora_relationship(self):
        load_balancer = self.create_load_balancer(self.session)
        amphora = self.create_amphora(self.session)
        self.associate_amphora(load_balancer, amphora)
        new_load_balancer = self.session.query(
            models.LoadBalancer).filter_by(id=load_balancer.id).first()
        self.assertIsNotNone(new_load_balancer.amphorae)
        self.assertEqual(1, len(new_load_balancer.amphorae))

    def test_load_balancer_vip_relationship(self):
        load_balancer = self.create_load_balancer(self.session)
        self.create_vip(self.session, load_balancer.id)
        new_load_balancer = self.session.query(
            models.LoadBalancer).filter_by(id=load_balancer.id).first()
        self.assertIsNotNone(new_load_balancer.vip)
        self.assertIsInstance(new_load_balancer.vip, models.Vip)


class VipModelTest(base.OctaviaDBTestBase, ModelTestMixin):

    def setUp(self):
        super(VipModelTest, self).setUp()
        self.load_balancer = self.create_load_balancer(self.session)

    def test_create(self):
        self.create_vip(self.session, self.load_balancer.id)

    def test_update(self):
        vip = self.create_vip(self.session, self.load_balancer.id)
        vip.ip_address = "10.0.0.1"
        new_vip = self.session.query(models.Vip).filter_by(
            load_balancer_id=self.load_balancer.id).first()
        self.assertEqual("10.0.0.1", new_vip.ip_address)

    def test_delete(self):
        vip = self.create_vip(self.session, self.load_balancer.id)
        with self.session.begin():
            self.session.delete(vip)
            self.session.flush()
        new_vip = self.session.query(models.Vip).filter_by(
            load_balancer_id=vip.load_balancer_id).first()
        self.assertIsNone(new_vip)

    def test_vip_load_balancer_relationship(self):
        self.create_vip(self.session, self.load_balancer.id)
        new_vip = self.session.query(models.Vip).filter_by(
            load_balancer_id=self.load_balancer.id).first()
        self.assertIsNotNone(new_vip.load_balancer)
        self.assertIsInstance(new_vip.load_balancer, models.LoadBalancer)


class SNIModelTest(base.OctaviaDBTestBase, ModelTestMixin):

    def setUp(self):
        super(SNIModelTest, self).setUp()
        self.listener = self.create_listener(self.session)

    def test_create(self):
        self.create_sni(self.session, listener_id=self.listener.id)

    def test_update(self):
        sni = self.create_sni(self.session, listener_id=self.listener.id)
        sni.tls_container_id = self.FAKE_UUID_2
        new_sni = self.session.query(
            models.SNI).filter_by(listener_id=self.FAKE_UUID_1).first()
        self.assertEqual(self.FAKE_UUID_2, new_sni.tls_container_id)

    def test_delete(self):
        sni = self.create_sni(self.session, listener_id=self.listener.id)
        with self.session.begin():
            self.session.delete(sni)
            self.session.flush()
        new_sni = self.session.query(
            models.SNI).filter_by(listener_id=self.listener.id).first()
        self.assertIsNone(new_sni)

    def test_sni_relationship(self):
        self.create_sni(self.session, listener_id=self.listener.id)
        new_sni = self.session.query(models.SNI).filter_by(
            listener_id=self.listener.id).first()
        self.assertIsNotNone(new_sni.listener)
        self.assertIsInstance(new_sni.listener, models.Listener)


class AmphoraModelTest(base.OctaviaDBTestBase, ModelTestMixin):

    def setUp(self):
        super(AmphoraModelTest, self).setUp()
        self.load_balancer = self.create_load_balancer(self.session)

    def test_create(self):
        self.create_amphora(self.session)

    def test_update(self):
        amphora = self.create_amphora(
            self.session)
        amphora.amphora_id = self.FAKE_UUID_2
        new_amphora = self.session.query(models.Amphora).filter_by(
            id=amphora.id).first()
        self.assertEqual(self.FAKE_UUID_2, new_amphora.amphora_id)

    def test_delete(self):
        amphora = self.create_amphora(
            self.session)
        with self.session.begin():
            self.session.delete(amphora)
            self.session.flush()
        new_amphora = self.session.query(
            models.Amphora).filter_by(id=amphora.id).first()
        self.assertIsNone(new_amphora)

    def test_load_balancer_relationship(self):
        amphora = self.create_amphora(self.session)
        self.associate_amphora(self.load_balancer, amphora)
        new_amphora = self.session.query(models.Amphora).filter_by(
            id=amphora.id).first()
        self.assertIsNotNone(new_amphora.load_balancer)
        self.assertIsInstance(new_amphora.load_balancer, models.LoadBalancer)


class AmphoraHealthModelTest(base.OctaviaDBTestBase, ModelTestMixin):
    def setUp(self):
        super(AmphoraHealthModelTest, self).setUp()
        self.amphora = self.create_amphora(self.session)

    def test_create(self):
        self.create_amphora_health(self.session)

    def test_update(self):
        amphora_health = self.create_amphora_health(self.session)
        d = datetime.date.today()
        newdate = d.replace(day=d.day)
        amphora_health.last_update = newdate
        new_amphora_health = self.session.query(
            models.AmphoraHealth).filter_by(
            amphora_id=amphora_health.amphora_id).first()
        self.assertEqual(newdate, new_amphora_health.last_update.date())

    def test_delete(self):
        amphora_health = self.create_amphora_health(
            self.session)
        with self.session.begin():
            self.session.delete(amphora_health)
            self.session.flush()
        new_amphora_health = self.session.query(
            models.AmphoraHealth).filter_by(
            amphora_id=amphora_health.amphora_id).first()
        self.assertIsNone(new_amphora_health)


class L7PolicyModelTest(base.OctaviaDBTestBase, ModelTestMixin):
    def setUp(self):
        super(L7PolicyModelTest, self).setUp()
        self.listener = self.create_listener(self.session)

    def test_create(self):
        l7policy = self.create_l7policy(self.session, self.listener.id)
        self.assertIsInstance(l7policy, models.L7Policy)

    def test_update(self):
        l7policy = self.create_l7policy(self.session, self.listener.id)
        pool = self.create_pool(self.session)
        l7policy.action = constants.L7POLICY_ACTION_REDIRECT_TO_POOL
        l7policy.redirect_pool_id = pool.id
        new_l7policy = self.session.query(
            models.L7Policy).filter_by(id=l7policy.id).first()
        self.assertEqual(pool.id, new_l7policy.redirect_pool_id)
        self.assertEqual(constants.L7POLICY_ACTION_REDIRECT_TO_POOL,
                         new_l7policy.action)

    def test_delete(self):
        l7policy = self.create_l7policy(self.session, self.listener.id)
        l7policy_id = l7policy.id
        with self.session.begin():
            self.session.delete(l7policy)
            self.session.flush()
        new_l7policy = self.session.query(
            models.L7Policy).filter_by(id=l7policy_id).first()
        self.assertIsNone(new_l7policy)

    def test_l7rule_relationship(self):
        l7policy = self.create_l7policy(self.session, self.listener.id)
        self.create_l7rule(
            self.session, l7policy.id, id=self.FAKE_UUID_1,
            type=constants.L7RULE_TYPE_HOST_NAME,
            compare_type=constants.L7RULE_COMPARE_TYPE_EQUAL_TO,
            value='www.example.com')
        self.create_l7rule(
            self.session, l7policy.id, id=self.FAKE_UUID_2,
            type=constants.L7RULE_TYPE_PATH,
            compare_type=constants.L7RULE_COMPARE_TYPE_EQUAL_TO,
            value='/api')
        new_l7policy = self.session.query(
            models.L7Policy).filter_by(id=l7policy.id).first()
        self.assertIsNotNone(new_l7policy.l7rules)
        self.assertEqual(2, len(new_l7policy.l7rules))
        self.assertIsInstance(new_l7policy.l7rules[0], models.L7Rule)
        self.assertIsInstance(new_l7policy.l7rules[1], models.L7Rule)

    def test_pool_relationship(self):
        l7policy = self.create_l7policy(self.session, self.listener.id)
        self.create_pool(self.session, id=self.FAKE_UUID_2)
        l7policy.action = constants.L7POLICY_ACTION_REDIRECT_TO_POOL
        l7policy.redirect_pool_id = self.FAKE_UUID_2
        new_l7policy = self.session.query(
            models.L7Policy).filter_by(id=l7policy.id).first()
        self.assertIsNotNone(new_l7policy.redirect_pool)
        self.assertIsInstance(new_l7policy.redirect_pool, models.Pool)

    def test_listener_relationship(self):
        l7policy = self.create_l7policy(self.session, self.listener.id,
                                        id=self.FAKE_UUID_1)
        self.create_l7policy(self.session, self.listener.id,
                             id=self.FAKE_UUID_2, position=1)
        new_l7policy = self.session.query(models.L7Policy).filter_by(
            id=l7policy.id).first()
        self.assertIsNotNone(new_l7policy.listener)
        self.assertIsInstance(new_l7policy.listener, models.Listener)

    def test_listeners_pools_refs_with_l7policy_with_l7rule(self):
        pool = self.create_pool(self.session, id=self.FAKE_UUID_2)
        l7policy = self.create_l7policy(
            self.session, self.listener.id,
            action=constants.L7POLICY_ACTION_REDIRECT_TO_POOL,
            redirect_pool_id=pool.id)
        self.create_l7rule(self.session, l7policy.id, id=self.FAKE_UUID_1)
        new_pool = self.session.query(models.Pool).filter_by(
            id=pool.id).first()
        new_listener = self.session.query(models.Listener).filter_by(
            id=self.listener.id).first()
        self.assertIsInstance(new_pool.listeners, list)
        self.assertIn(new_listener.id, [l.id for l in new_pool.listeners])
        self.assertIsInstance(new_listener.pools, list)
        self.assertIn(new_pool.id, [p.id for p in new_listener.pools])

    def test_listeners_pools_refs_with_l7policy_without_l7rule(self):
        pool = self.create_pool(self.session, id=self.FAKE_UUID_2)
        self.create_l7policy(
            self.session, self.listener.id,
            action=constants.L7POLICY_ACTION_REDIRECT_TO_POOL,
            redirect_pool_id=pool.id)
        new_pool = self.session.query(models.Pool).filter_by(
            id=pool.id).first()
        new_listener = self.session.query(models.Listener).filter_by(
            id=self.listener.id).first()
        self.assertIsInstance(new_pool.listeners, list)
        self.assertNotIn(new_listener.id, [l.id for l in new_pool.listeners])
        self.assertIsInstance(new_listener.pools, list)
        self.assertNotIn(new_pool.id, [p.id for p in new_listener.pools])

    def test_listeners_pools_refs_with_disabled_l7policy(self):
        pool = self.create_pool(self.session, id=self.FAKE_UUID_2)
        l7policy = self.create_l7policy(
            self.session, self.listener.id,
            action=constants.L7POLICY_ACTION_REDIRECT_TO_POOL,
            redirect_pool_id=pool.id, enabled=False)
        self.create_l7rule(self.session, l7policy.id, id=self.FAKE_UUID_1)
        new_pool = self.session.query(models.Pool).filter_by(
            id=pool.id).first()
        new_listener = self.session.query(models.Listener).filter_by(
            id=self.listener.id).first()
        self.assertIsInstance(new_pool.listeners, list)
        self.assertNotIn(new_listener.id, [l.id for l in new_pool.listeners])
        self.assertIsInstance(new_listener.pools, list)
        self.assertNotIn(new_pool.id, [p.id for p in new_listener.pools])


class L7RuleModelTest(base.OctaviaDBTestBase, ModelTestMixin):

    def setUp(self):
        super(L7RuleModelTest, self).setUp()
        self.listener = self.create_listener(self.session)
        self.l7policy = self.create_l7policy(self.session, self.listener.id)

    def test_create(self):
        l7rule = self.create_l7rule(self.session, self.l7policy.id)
        self.assertIsInstance(l7rule, models.L7Rule)

    def test_update(self):
        l7rule = self.create_l7rule(self.session, self.l7policy.id)
        l7rule_id = l7rule.id
        l7rule.value = '/images'
        new_l7rule = self.session.query(
            models.L7Rule).filter_by(id=l7rule_id).first()
        self.assertEqual('/images', new_l7rule.value)

    def test_delete(self):
        l7rule = self.create_l7rule(self.session, self.l7policy.id)
        l7rule_id = l7rule.id
        with self.session.begin():
            self.session.delete(l7rule)
            self.session.flush()
        new_l7rule = self.session.query(
            models.L7Rule).filter_by(id=l7rule_id).first()
        self.assertIsNone(new_l7rule)

    def test_l7policy_relationship(self):
        l7rule = self.create_l7rule(
            self.session, self.l7policy.id, id=self.FAKE_UUID_1,
            type=constants.L7RULE_TYPE_HOST_NAME,
            compare_type=constants.L7RULE_COMPARE_TYPE_EQUAL_TO,
            value='www.example.com')
        self.create_l7rule(
            self.session, self.l7policy.id, id=self.FAKE_UUID_2,
            type=constants.L7RULE_TYPE_PATH,
            compare_type=constants.L7RULE_COMPARE_TYPE_EQUAL_TO,
            value='/api')
        new_l7rule = self.session.query(models.L7Rule).filter_by(
            id=l7rule.id).first()
        self.assertIsNotNone(new_l7rule.l7policy)
        self.assertIsInstance(new_l7rule.l7policy, models.L7Policy)


class TestDataModelConversionTest(base.OctaviaDBTestBase, ModelTestMixin):

    def setUp(self):
        super(TestDataModelConversionTest, self).setUp()
        self.lb = self.create_load_balancer(self.session)
        self.pool = self.create_pool(self.session, load_balancer_id=self.lb.id)
        self.hm = self.create_health_monitor(self.session, self.pool.id)
        self.member = self.create_member(self.session, self.pool.id,
                                         id=self.FAKE_UUID_1,
                                         ip_address='10.0.0.1')
        self.sp = self.create_session_persistence(self.session, self.pool.id)
        self.vip = self.create_vip(self.session, self.lb.id)
        self.listener = self.create_listener(self.session,
                                             default_pool_id=self.pool.id,
                                             load_balancer_id=self.lb.id)
        self.stats = self.create_listener_statistics(self.session,
                                                     self.listener.id)
        self.sni = self.create_sni(self.session, listener_id=self.listener.id)
        self.l7policy = self.create_l7policy(
            self.session, listener_id=self.listener.id,
            action=constants.L7POLICY_ACTION_REDIRECT_TO_POOL,
            redirect_pool_id=self.pool.id)
        self.l7rule = self.create_l7rule(self.session,
                                         l7policy_id=self.l7policy.id)

    @staticmethod
    def _get_unique_key(obj):
        """Returns a unique key for passed object for data model building."""
        # First handle all objects with their own ID, then handle subordinate
        # objects.
        if obj.__class__.__name__ in ['Member', 'Pool', 'LoadBalancer',
                                      'Listener', 'Amphora', 'L7Policy',
                                      'L7Rule']:
            return obj.__class__.__name__ + obj.id
        elif obj.__class__.__name__ in ['SessionPersistence', 'HealthMonitor']:
            return obj.__class__.__name__ + obj.pool_id
        elif obj.__class__.__name__ in ['ListenerStatistics', 'SNI']:
            return obj.__class__.__name__ + obj.listener_id
        elif obj.__class__.__name__ in ['VRRPGroup', 'Vip']:
            return obj.__class__.__name__ + obj.load_balancer_id
        elif obj.__class__.__name__ in ['AmphoraHealth']:
            return obj.__class__.__name__ + obj.amphora_id
        elif obj.__class__.__name__ in ['SNI']:
            return (obj.__class__.__name__ +
                    obj.listener_id + obj.tls_container_id)
        else:
            raise NotImplementedError

    def count_graph_nodes(self, node, _graph_nodes=None):
        """Counts connected BaseDataModel nodes in a graph given the

        starting node. Node should be a data model in any case.
        """
        _graph_nodes = _graph_nodes or []
        total = 0
        mykey = self._get_unique_key(node)
        if mykey in _graph_nodes:
            # Seen this node already
            return total
        else:
            total += 1
            _graph_nodes.append(mykey)
            attr_names = [attr_name for attr_name in dir(node)
                          if not attr_name.startswith('_')]
            for attr_name in attr_names:
                attr = getattr(node, attr_name)
                if isinstance(attr, data_models.BaseDataModel):
                    total += self.count_graph_nodes(
                        attr, _graph_nodes=_graph_nodes)
                elif isinstance(attr, (collections.InstrumentedList, list)):
                    for item in attr:
                        if isinstance(item, data_models.BaseDataModel):
                            total += self.count_graph_nodes(
                                item, _graph_nodes=_graph_nodes)
        return total

    def test_graph_completeness(self):
        # Generate equivalent graphs starting arbitrarily from different
        # nodes within it; Make sure the resulting graphs all contain the
        # same number of nodes.
        lb_dm = self.session.query(models.LoadBalancer).filter_by(
            id=self.lb.id).first().to_data_model()
        lb_graph_count = self.count_graph_nodes(lb_dm)
        ls_dm = self.session.query(models.ListenerStatistics).filter_by(
            listener_id=self.listener.id).first().to_data_model()
        ls_graph_count = self.count_graph_nodes(ls_dm)
        p_dm = self.session.query(models.Pool).filter_by(
            id=self.pool.id).first().to_data_model()
        p_graph_count = self.count_graph_nodes(p_dm)
        mem_dm = self.session.query(models.Member).filter_by(
            id=self.member.id).first().to_data_model()
        mem_graph_count = self.count_graph_nodes(mem_dm)
        self.assertNotEqual(0, lb_graph_count)
        self.assertNotEqual(1, lb_graph_count)
        self.assertEqual(lb_graph_count, ls_graph_count)
        self.assertEqual(lb_graph_count, p_graph_count)
        self.assertEqual(lb_graph_count, mem_graph_count)

    def test_data_model_graph_traversal(self):
        lb_dm = self.session.query(models.LoadBalancer).filter_by(
            id=self.lb.id).first().to_data_model()
        # This is an arbitrary traversal that covers one of each type
        # of parent an child relationship.
        lb_id = (lb_dm.listeners[0].default_pool.members[0].pool.
                 session_persistence.pool.health_monitor.pool.listeners[0].
                 stats.listener.sni_containers[0].listener.load_balancer.
                 listeners[0].load_balancer.pools[0].listeners[0].
                 load_balancer.listeners[0].pools[0].load_balancer.vip.
                 load_balancer.id)
        self.assertEqual(lb_dm.id, lb_id)
        mem_dm = self.session.query(models.Member).filter_by(
            id=self.member.id).first().to_data_model()
        # Same as the above, but we generate the graph starting with an
        # arbitrary member.
        m_lb_id = (mem_dm.pool.listeners[0].load_balancer.vip.load_balancer.
                   pools[0].session_persistence.pool.health_monitor.pool.
                   listeners[0].stats.listener.sni_containers[0].listener.
                   load_balancer.pools[0].members[0].pool.load_balancer.id)
        self.assertEqual(lb_dm.id, m_lb_id)

    def test_update_data_model_listener_default_pool_id(self):
        lb_dm = self.create_load_balancer(
            self.session, id=uuidutils.generate_uuid()).to_data_model()
        pool1_dm = self.create_pool(
            self.session, id=uuidutils.generate_uuid(),
            load_balancer_id=lb_dm.id).to_data_model()
        pool2_dm = self.create_pool(
            self.session, id=uuidutils.generate_uuid(),
            load_balancer_id=lb_dm.id).to_data_model()
        listener_dm = self.create_listener(
            self.session, id=uuidutils.generate_uuid(),
            load_balancer_id=lb_dm.id,
            default_pool_id=pool1_dm.id).to_data_model()
        self.assertEqual(pool1_dm.id, listener_dm.default_pool.id)
        listener_dm.update({'default_pool_id': pool2_dm.id})
        self.assertEqual(listener_dm.default_pool.id, pool2_dm.id)

    def test_load_balancer_tree(self):
        lb_db = self.session.query(models.LoadBalancer).filter_by(
            id=self.lb.id).first()
        self.check_load_balancer(lb_db.to_data_model())

    def test_vip_tree(self):
        vip_db = self.session.query(models.Vip).filter_by(
            load_balancer_id=self.lb.id).first()
        self.check_vip(vip_db.to_data_model())

    def test_listener_tree(self):
        listener_db = self.session.query(models.Listener).filter_by(
            id=self.listener.id).first()
        self.check_listener(listener_db.to_data_model())

    def test_sni_tree(self):
        sni_db = self.session.query(models.SNI).filter_by(
            listener_id=self.listener.id).first()
        self.check_sni(sni_db.to_data_model())

    def test_listener_statistics_tree(self):
        stats_db = self.session.query(models.ListenerStatistics).filter_by(
            listener_id=self.listener.id).first()
        self.check_listener_statistics(stats_db.to_data_model())

    def test_pool_tree(self):
        pool_db = self.session.query(models.Pool).filter_by(
            id=self.pool.id).first()
        self.check_pool(pool_db.to_data_model())

    def test_session_persistence_tree(self):
        sp_db = self.session.query(models.SessionPersistence).filter_by(
            pool_id=self.pool.id).first()
        self.check_session_persistence(sp_db.to_data_model())

    def test_health_monitor_tree(self):
        hm_db = self.session.query(models.HealthMonitor).filter_by(
            pool_id=self.hm.pool_id).first()
        self.check_health_monitor(hm_db.to_data_model())

    def test_member_tree(self):
        member_db = self.session.query(models.Member).filter_by(
            id=self.member.id).first()
        self.check_member(member_db.to_data_model())

    def test_l7policy_tree(self):
        l7policy_db = self.session.query(models.L7Policy).filter_by(
            id=self.l7policy.id).first()
        self.check_l7policy(l7policy_db.to_data_model())

    def test_l7rule_tree(self):
        l7rule_db = self.session.query(models.L7Rule).filter_by(
            id=self.l7rule.id).first()
        self.check_l7rule(l7rule_db.to_data_model())

    def check_load_balancer(self, lb, check_listeners=True,
                            check_amphorae=True, check_vip=True,
                            check_pools=True):
        self.assertIsInstance(lb, data_models.LoadBalancer)
        self.check_load_balancer_data_model(lb)
        self.assertIsInstance(lb.listeners, list)
        self.assertIsInstance(lb.amphorae, list)
        if check_listeners:
            for listener in lb.listeners:
                self.check_listener(listener, check_lb=False,
                                    check_pools=check_pools)
        if check_amphorae:
            for amphora in lb.amphorae:
                self.check_amphora(amphora, check_load_balancer=False)
        if check_vip:
            self.check_vip(lb.vip, check_lb=False)
        if check_pools:
            for pool in lb.pools:
                self.check_pool(pool, check_lb=False,
                                check_listeners=check_listeners)

    def check_vip(self, vip, check_lb=True):
        self.assertIsInstance(vip, data_models.Vip)
        self.check_vip_data_model(vip)
        if check_lb:
            self.check_load_balancer(vip.load_balancer, check_vip=False)

    def check_sni(self, sni, check_listener=True):
        self.assertIsInstance(sni, data_models.SNI)
        self.check_sni_data_model(sni)
        if check_listener:
            self.check_listener(sni.listener, check_sni=False)

    def check_listener_statistics(self, stats, check_listener=True):
        self.assertIsInstance(stats, data_models.ListenerStatistics)
        self.check_listener_statistics_data_model(stats)
        if check_listener:
            self.check_listener(stats.listener, check_statistics=False)

    def check_amphora(self, amphora, check_load_balancer=True):
        self.assertIsInstance(amphora, data_models.Amphora)
        self.check_amphora_data_model(amphora)
        if check_load_balancer:
            self.check_load_balancer(amphora.load_balancer)

    def check_listener(self, listener, check_sni=True, check_pools=True,
                       check_lb=True, check_statistics=True,
                       check_l7policies=True):
        self.assertIsInstance(listener, data_models.Listener)
        self.check_listener_data_model(listener)
        if check_lb:
            self.check_load_balancer(listener.load_balancer,
                                     check_listeners=False,
                                     check_pools=check_pools)
        if check_sni:
            c_containers = listener.sni_containers
            self.assertIsInstance(c_containers, list)
            for sni in c_containers:
                self.check_sni(sni, check_listener=False)
        if check_pools:
            for pool in listener.pools:
                self.check_pool(pool, check_listeners=False, check_lb=check_lb)
        if check_statistics:
            self.check_listener_statistics(listener.stats,
                                           check_listener=False)
        if check_l7policies:
            c_l7policies = listener.l7policies
            self.assertIsInstance(c_l7policies, list)
            for policy in c_l7policies:
                self.check_l7policy(policy, check_listener=False,
                                    check_pool=check_pools, check_lb=check_lb)

    def check_session_persistence(self, session_persistence, check_pool=True):
        self.assertIsInstance(session_persistence,
                              data_models.SessionPersistence)
        self.check_session_persistence_data_model(session_persistence)
        if check_pool:
            self.check_pool(session_persistence.pool, check_sp=False)

    def check_member(self, member, check_pool=True):
        self.assertIsInstance(member, data_models.Member)
        self.check_member_data_model(member)
        if check_pool:
            self.check_pool(member.pool, check_members=False)

    def check_l7policy(self, l7policy, check_listener=True, check_pool=True,
                       check_l7rules=True, check_lb=True):
        self.assertIsInstance(l7policy, data_models.L7Policy)
        self.check_l7policy_data_model(l7policy)
        if check_listener:
            self.check_listener(l7policy.listener, check_l7policies=False,
                                check_pools=check_pool, check_lb=check_lb)
        if check_l7rules:
            c_l7rules = l7policy.l7rules
            self.assertIsInstance(c_l7rules, list)
            for rule in c_l7rules:
                self.check_l7rule(rule, check_l7policy=False)
        if check_pool and l7policy.redirect_pool is not None:
            self.assertEqual(l7policy.action,
                             constants.L7POLICY_ACTION_REDIRECT_TO_POOL)
            self.check_pool(l7policy.redirect_pool,
                            check_listeners=check_listener,
                            check_l7policies=False, check_lb=check_lb)

    def check_l7rule(self, l7rule, check_l7policy=True):
        self.assertIsInstance(l7rule, data_models.L7Rule)
        self.check_l7rule_data_model(l7rule)
        if check_l7policy:
            self.check_l7policy(l7rule.l7policy)

    def check_health_monitor(self, health_monitor, check_pool=True):
        self.assertIsInstance(health_monitor, data_models.HealthMonitor)
        self.check_health_monitor_data_model(health_monitor)
        if check_pool:
            self.check_pool(health_monitor.pool, check_hm=False)

    def check_pool(self, pool, check_listeners=True, check_sp=True,
                   check_hm=True, check_members=True, check_l7policies=True,
                   check_lb=True):
        self.assertIsInstance(pool, data_models.Pool)
        self.check_pool_data_model(pool)
        if check_listeners:
            for listener in pool.listeners:
                self.check_listener(listener, check_pools=False,
                                    check_lb=check_lb)
        if check_sp:
            self.check_session_persistence(pool.session_persistence,
                                           check_pool=False)
        if check_members:
            c_members = pool.members
            self.assertIsNotNone(c_members)
            self.assertEqual(1, len(c_members))
            for c_member in c_members:
                self.check_member(c_member, check_pool=False)
        if check_hm:
            self.check_health_monitor(pool.health_monitor, check_pool=False)
        if check_lb:
            self.check_load_balancer(pool.load_balancer, check_pools=False,
                                     check_listeners=check_listeners)
        if check_l7policies:
            c_l7policies = pool.l7policies
            self.assertIsInstance(c_l7policies, list)
            for policy in c_l7policies:
                self.check_l7policy(policy, check_pool=False,
                                    check_listener=check_listeners,
                                    check_lb=check_lb)

    def check_load_balancer_data_model(self, lb):
        self.assertEqual(self.FAKE_UUID_1, lb.project_id)
        self.assertEqual(self.FAKE_UUID_1, lb.id)
        self.assertEqual(constants.ACTIVE, lb.provisioning_status)
        self.assertTrue(lb.enabled)

    def check_vip_data_model(self, vip):
        self.assertEqual(self.FAKE_UUID_1, vip.load_balancer_id)

    def check_listener_data_model(self, listener):
        self.assertEqual(self.FAKE_UUID_1, listener.project_id)
        self.assertEqual(self.FAKE_UUID_1, listener.id)
        self.assertEqual(constants.PROTOCOL_HTTP, listener.protocol)
        self.assertEqual(80, listener.protocol_port)
        self.assertEqual(constants.ACTIVE, listener.provisioning_status)
        self.assertEqual(constants.ONLINE, listener.operating_status)
        self.assertTrue(listener.enabled)

    def check_sni_data_model(self, sni):
        self.assertEqual(self.FAKE_UUID_1, sni.listener_id)
        self.assertEqual(self.FAKE_UUID_1, sni.tls_container_id)

    def check_listener_statistics_data_model(self, stats):
        self.assertEqual(self.listener.id, stats.listener_id)
        self.assertEqual(0, stats.bytes_in)
        self.assertEqual(0, stats.bytes_out)
        self.assertEqual(0, stats.active_connections)
        self.assertEqual(0, stats.total_connections)

    def check_pool_data_model(self, pool):
        self.assertEqual(self.FAKE_UUID_1, pool.project_id)
        self.assertEqual(self.FAKE_UUID_1, pool.id)
        self.assertEqual(constants.PROTOCOL_HTTP, pool.protocol)
        self.assertEqual(constants.LB_ALGORITHM_LEAST_CONNECTIONS,
                         pool.lb_algorithm)
        self.assertEqual(constants.ONLINE, pool.operating_status)
        self.assertTrue(pool.enabled)

    def check_session_persistence_data_model(self, sp):
        self.assertEqual(self.pool.id, sp.pool_id)
        self.assertEqual(constants.SESSION_PERSISTENCE_HTTP_COOKIE, sp.type)

    def check_health_monitor_data_model(self, hm):
        self.assertEqual(constants.HEALTH_MONITOR_HTTP, hm.type)
        self.assertEqual(1, hm.delay)
        self.assertEqual(1, hm.timeout)
        self.assertEqual(1, hm.fall_threshold)
        self.assertEqual(1, hm.rise_threshold)
        self.assertTrue(hm.enabled)

    def check_member_data_model(self, member):
        self.assertEqual(self.FAKE_UUID_1, member.project_id)
        self.assertEqual(self.FAKE_UUID_1, member.id)
        self.assertEqual(self.pool.id, member.pool_id)
        self.assertEqual('10.0.0.1', member.ip_address)
        self.assertEqual(80, member.protocol_port)
        self.assertEqual(constants.ONLINE, member.operating_status)
        self.assertTrue(member.enabled)

    def check_l7policy_data_model(self, l7policy):
        self.assertEqual(self.FAKE_UUID_1, l7policy.id)
        self.assertEqual(self.listener.id, l7policy.listener_id)
        self.assertEqual(constants.L7POLICY_ACTION_REDIRECT_TO_POOL,
                         l7policy.action)
        self.assertEqual(self.pool.id, l7policy.redirect_pool_id)
        self.assertEqual(0, l7policy.position)

    def check_l7rule_data_model(self, l7rule):
        self.assertEqual(self.FAKE_UUID_1, l7rule.id)
        self.assertEqual(self.l7policy.id, l7rule.l7policy_id)
        self.assertEqual(constants.L7RULE_TYPE_PATH, l7rule.type)
        self.assertEqual(constants.L7RULE_COMPARE_TYPE_STARTS_WITH,
                         l7rule.compare_type)
        self.assertEqual('/api', l7rule.value)
        self.assertFalse(l7rule.invert)

    def check_amphora_data_model(self, amphora):
        self.assertEqual(self.FAKE_UUID_1, amphora.id)
        self.assertEqual(self.FAKE_UUID_1, amphora.compute_id)
        self.assertEqual(constants.ONLINE, amphora.status)

    def check_load_balancer_amphora_data_model(self, amphora):
        self.assertEqual(self.FAKE_UUID_1, amphora.amphora_id)
        self.assertEqual(self.FAKE_UUID_1, amphora.load_balancer_id)
