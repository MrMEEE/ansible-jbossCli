#!/usr/bin/python
# -*- coding: utf-8 -*-

# (c) 2017, Antonio Insusti <antonio@insuasti.ec>
#
# This file is part of Ansible
#
# JBoss Cli module is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# JBoss Cli module is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# If not, see <http://www.gnu.org/licenses/>.

ANSIBLE_METADATA = {'metadata_version': '1.0',
                    'status': ['preview'],
                    'supported_by': 'community'}


DOCUMENTATION = """
module: jboss
short_description: deploy applications to JBoss
description:
  - Deploy applications to JBoss standalone using the filesystem
options:
  command:
    required: true
    description:
      - JBoss Cli command
  src:
    required: false
    description:
      - Batch file, valid if command is run-batch
  cli_path:
    required: false
    default: /usr/share/wildfly/bin
    description:
      - The location in the filesystem where jboss-cli.sh is
  user:
    required: false
    description:
      - Jboss management user
  password:
    required: false
    description:
      - Jboss management user password
  server:
    required: false
    default: localhost:9990
    description:
      - JBoss server or domain controller, whit management port

notes:
  - "jboss-cli.sh need to be runing on client host, and $JAVA_HOME/bin is needeth in Client $PATH"
  - ""
author: "Antonio Insuasti (@wolfantEc)"
"""

EXAMPLES = """
# chage scan-interval value, on user wildfy instalation
- jboss:
    command: /subsystem=deployment-scanner/scanner=default:write-attribute(name=scan-interval,value=6000)
    cli_path: /home/user/wildfly-10.1.0.Final/bin

#  change ExampleDS datasource user-name, on 192.168.20.55:9990 default instalation
- jboss:
    command: /subsystem=datasources/data-source=ExampleDS:write-attribute(name=user-name,value=other)
    server: 192.168.20.55:9990

# Undeploy the hello world application on wildfy server
- jboss:
    command: undeploy hello.war
    server: "{{ ansible_hostname}}:9990"
"""
import os
import shutil
import time
import grp
import platform
import json

def main():
    module = AnsibleModule(
        argument_spec = dict(
            src=dict(),
            user=dict(),
            password=dict(),
            command=dict(requiered=True),
            cli_path=dict(default='/usr/share/wildfly/bin'),
            server=dict(default='localhost:9990'),
        ),
    )



    changed = False

    src = module.params['src']
    user = module.params['user']
    password = module.params['password']
    command = module.params['command']
    cli_path = module.params['cli_path']
    server = module.params['server']

    if command == 'run-batch' and not src:
        module.fail_json(msg="Argument 'src' required when run-batch is the command")

    if user and not password:
        module.fail_json(msg="Argument 'user' need 'password' ")

    if not os.access(cli_path + "/jboss-cli.sh", os.X_OK):
        module.fail_json(msg="jboss-cli.sh in not found on cli_path ")

    cmd = [cli_path + "/jboss-cli.sh" ]
    cmd.append('-c')
    cmd.append("--controller=" + str(server))


    if user:
        cmd.append('--user='+str(user))
        cmd.append('--password='+str(password))

    if command == "run-batch":
        cmd.append('"%s --file %s "' % ( str(command), str(src) ) )
    else:
        cmd.append('%s' % str(command))

    rc = None
    out = ''
    err = ''
    result = {}
    result['name'] = 'jboss-cli'
    result['command'] = command

    (rc, out, err) = module.run_command(cmd,encoding='utf-8')

    if rc is None:
        result['changed'] = False
    else:
        result['changed'] = True
    jsout=None

    if out:
        if not out.find("outcome") < 0:
            decode=json.loads(out.replace("=>", ":"))
            jsout=decode
            if decode['outcome'] == 'success':
                result['changed']= True
                result['stdout'] = 'success'
            else:
                result['changed']= False
                result['stdout'] = decode['outcome']
                result['stderr']= decode['failure-description']
        else:
            result['changed'] = False
            result['stdout'] = out
    if rc != 0:
        module.fail_json(name='jbosscli', msg=jsout['failure-description'])

    if err:
        result['stderr'] = err

    module.exit_json(**result)


# import module snippets
from ansible.module_utils.basic import *

if __name__ == '__main__':
    main()
