#!/usr/bin/env python
# Copyright 2017 F5 Networks Inc.
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#    http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.
#

import json
import os
from pprint import pprint as pp

from f5_cccl.resource.ltm.pool import *

from mock import MagicMock
import pytest


bigip_pools_cfg = [
    {'description': None,
     'partition': 'Common',
     'loadBalancingMode': 'round-robin',
     'monitor': '/Common/http ',
     'membersReference': {
         'isSubcollection': True,
         'items': [
             {'ratio': 1,
              'name': '172.16.0.100:8080',
              'partition': 'Common',
              'session': 'monitor-enabled',
              'priorityGroup': 0,
              'connectionLimit': 0,
              'description': None},
             {'ratio': 1,
              'name': '172.16.0.101:8080',
              'partition': 'Common',
              'session': 'monitor-enabled',
              'priorityGroup': 0,
              'connectionLimit': 0,
              'description': None}
         ]
     },
     'name': u'pool1'
    },
    {'description': None,
     'partition': 'Common',
     'loadBalancingMode': 'round-robin',
     'monitor': '/Common/http ',
     'name': u'pool1'
    }
]

cccl_pools_cfg = [
    { "name": "pool0" },
    { "name": "pool1",
      "members": [
          {"address": "172.16.0.100", "port": 8080, "routeDomain": {"id": 0}},
          {"address": "172.16.0.101", "port": 8080, "routeDomain": {"id": 0}}
      ],
      "monitors": [{ "refname":  "/Common/http"}]
    },
    { "name": "pool2",
      "members": [
          {"address": "192.168.0.100", "port": 80, "routeDomain": {"id": 2}},
          {"address": "192.168.0.101", "port": 80, "routeDomain": {"id": 2}}
      ],
      "monitors": []
    },
    { "name": "pool3",
      "members": [],
      "description": "This is test pool 3",
      "monitors": []
    },
    { "name": "pool4",
      "members": [],
      "description": "This is test pool 4",
      "monitors": [{ "refname":  "/Common/http"}]
    },
    { "name": "pool1",
      "members": [
          {"address": "172.16.0.100", "port": 8080, "routeDomain": {"id": 0}},
          {"address": "172.16.0.102", "port": 8080, "routeDomain": {"id": 0}}
      ],
      "monitors": [{ "refname":  "/Common/http"}]
    }
]


@pytest.fixture
def bigip():
    bigip = MagicMock()
    return bigip


@pytest.fixture
def bigip_pool0():
    return bigip_pools_cfg[0]


@pytest.fixture
def bigip_pool1():
    return bigip_pools_cfg[1]


@pytest.fixture
def cccl_pool0():
    return cccl_pools_cfg[0]


@pytest.fixture
def cccl_pool1():
    return cccl_pools_cfg[1]


@pytest.fixture
def cccl_pool2():
    return cccl_pools_cfg[2]


@pytest.fixture
def cccl_pool3():
    return cccl_pools_cfg[3]


@pytest.fixture
def cccl_pool5():
    return cccl_pools_cfg[5]


@pytest.fixture
def bigip_members():
    members_filename = (
        os.path.join(os.path.dirname(os.path.abspath(__file__)),
                     './bigip-members.json'))
    with open(members_filename) as fp:
        json_data = fp.read()
        json_data = json.loads(json_data)
        members = [m for m in json_data['members']]
        pp(json_data)

    return members


def test_create_pool_minconfig(cccl_pool0):
    pool = F5CcclPool(partition="Common", **cccl_pool0)

    assert pool.name == "pool0"
    assert pool.partition == "Common"
    assert pool.data['loadBalancingMode'] == "round-robin"
    assert not pool.data['description']
    assert len(pool) == 0
    assert pool.data['monitor'] == "default"

def test_create_pool(cccl_pool1):
    pool = F5CcclPool(partition="Common", **cccl_pool1)

    assert pool.name == "pool1"
    assert pool.partition == "Common"
    assert pool.data['loadBalancingMode'] == "round-robin"
    assert not pool.data['description']
    assert pool.data['monitor'] == "/Common/http"

    assert len(pool) == 2


def test_create_pool_empty_lists(cccl_pool3):
    pool = F5CcclPool(partition="Common", **cccl_pool3)

    assert pool.name == "pool3"
    assert pool.partition == "Common"
    assert pool.data['loadBalancingMode'] == "round-robin"
    assert pool.data['description'] == "This is test pool 3"
    assert pool.data['monitor'] == "default"
    assert len(pool) == 0


def test_compare_equal_pools(cccl_pool0):
    p1 = F5CcclPool(partition="Common", **cccl_pool0)
    p2 = F5CcclPool(partition="Common", **cccl_pool0)

    assert id(p1) != id(p2)
    assert p1 == p2


def test_compare_pool_and_dict(cccl_pool0):
    pool = F5CcclPool(partition="Common", **cccl_pool0)
    with pytest.raises(ValueError):
        pool == cccl_pool0


def test_get_uri_path(bigip, cccl_pool0):
    pool = F5CcclPool(partition="Common", **cccl_pool0)

    assert pool._uri_path(bigip) == bigip.tm.ltm.pools.pool


def test_pool_hash(bigip, cccl_pool0):
    pool = F5CcclPool(partition="Common", **cccl_pool0)

    assert hash(pool) == hash((pool.name, pool.partition))


def test_compare_bigip_cccl_pools(cccl_pool1, bigip_pool0):
    bigip_pool = BigIPPool(**bigip_pool0)
    cccl_pool = F5CcclPool(partition="Common", **cccl_pool1)

    assert bigip_pool == cccl_pool


def test_create_bigip_pool_no_members(bigip_pool1):

    bigip_pool = BigIPPool(**bigip_pool1)

    assert bigip_pool.data['membersReference']
    assert bigip_pool.data['membersReference']['items'] == []


def test_compare_pools_unequal_members(bigip, cccl_pool1, cccl_pool2, cccl_pool5):
    pool1 = F5CcclPool(partition="Common", **cccl_pool1)
    pool2 = F5CcclPool(partition="Common", **cccl_pool2)
    pool5 = F5CcclPool(partition="Common", **cccl_pool5)

    pool1_one_member_cfg = { "name": "pool1",
      "members": [
          {"address": "172.16.0.100", "port": 8080, "routeDomain": {"id": 0}},
      ],
      "monitors": [{ "refname":  "/Common/http"}]
    }
    pool1_one_member = F5CcclPool(partition="Common",
                                  **pool1_one_member_cfg)


    pool2_with_monitor = { "name": "pool2",
      "members": [
          {"address": "192.168.0.100", "port": 80, "routeDomain": {"id": 2}},
          {"address": "192.168.0.101", "port": 80, "routeDomain": {"id": 2}}
      ],
      "monitors": [{ "refname":  "/Common/http"}]
    }
    pool2_with_monitor = F5CcclPool(partition="Common",
                                    **pool2_with_monitor)

    assert not pool1 == pool2
    assert pool1 != pool2

    assert not pool1_one_member == pool1
    assert not pool2_with_monitor == pool2

    assert not pool1 == pool5
    assert pool1 != pool5
    assert pool5 != pool1