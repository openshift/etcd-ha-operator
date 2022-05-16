from __future__ import (absolute_import, division, print_function)
__metaclass__ = type
from ansible.errors import AnsibleError, AnsibleParserError
from ansible.plugins.lookup import LookupBase

import etcd3_py

try:
    from __main__ import display
except ImportError:
    from ansible.utils.display import Display

    display = Display()

class LookupModule(LookupBase):
    def run(self, terms, **kwargs):
        kwargs.setdefault('cert_cert', None)
        kwargs.setdefault('ca_cert', None)
        kwargs.setdefault('cert_key', None)
        kwargs.setdefault('username', 'root')
        kwargs.setdefault('password', 'password')
        kwargs.setdefault('cluster_host', '')
        kwargs.setdefault('cluster_port', 0)
        certpair=None;
        if kwargs['cert_cert'] is not None:
                certpair=(kwargs['cert_cert'],kwargs['cert_key'])          
        try:
            conn=etcd3_py.Client(host=kwargs['cluster_host'], port=kwargs['cluster_port'], cert=certpair,verify=kwargs['ca_cert'])
            conn.user_add(name=kwargs['username'],password=kwargs['password'])
            conn.role_add('root') 
            conn.user_grant_role(kwargs['username'],'root')  
            conn.auth_enable()
            conn.authenticate(name=kwargs['username'],password=kwargs['password'])
            return True
        except etcd3_py.errors.go_etcd_rpctypes_error.ErrUserNotFound:
            conn=etcd3_py.Client(host=kwargs['cluster_host'],port=kwargs['cluster_port'],username=kwargs['username'],password=kwargs['password'], cert=certpair,verify=kwargs['ca_cert']) 
            conn.auth()
            return (len(conn.user_list().users)>0)
        except etcd3_py.errors.go_etcd_rpctypes_error.ErrUserEmpty:
            conn=etcd3_py.Client(host=kwargs['cluster_host'],port=kwargs['cluster_port'],username=kwargs['username'],password=kwargs['password'], cert=certpair,verify=kwargs['ca_cert']) 
            conn.auth()
            return (len(conn.user_list().users)>0)
        except Exception as e:
            raise AnsibleError('Enabling authentication failed. Error: {0}'.format(str(e)))
