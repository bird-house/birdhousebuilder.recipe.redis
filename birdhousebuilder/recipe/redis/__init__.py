# -*- coding: utf-8 -*-

"""
Recipe redis:

* http://redis.io/
"""

import os
from mako.template import Template

import zc.buildout
from birdhousebuilder.recipe import conda, supervisor

templ_config = Template(filename=os.path.join(os.path.dirname(__file__), "redis.conf"))
templ_cmd = Template("${env_path}/bin/redis-server ${config}")

class Recipe(object):
    """This recipe is used by zc.buildout.
    It installs Redis with conda and setups the configuration."""

    def __init__(self, buildout, name, options):
        self.buildout, self.name, self.options = buildout, name, options
        b_options = buildout['buildout']

        deployment = self.deployment = options.get('deployment')
        if deployment:
            self.options['prefix'] = buildout[deployment].get('prefix')
            self.options['etc_prefix'] = buildout[deployment].get('etc-prefix')
            self.options['var_prefix'] = buildout[deployment].get('var-prefix')
        else:
            self.options['prefix'] = os.path.join(buildout['buildout']['parts-directory'], self.name)
            self.options['etc_prefix'] = os.path.join(self.options['prefix'], 'etc')
            self.options['var_prefix'] = os.path.join(self.options['prefix'], 'var')
        self.prefix = self.options['prefix']

        self.env_path = conda.conda_env_path(buildout, options)
        self.options['env_path'] = self.env_path

        self.options['program'] = self.options.get('program', self.name)
        self.options['user'] = options.get('user', '')
        self.options['port'] = options.get('port', '6379')
        self.options['loglevel'] = options.get('loglevel', 'warning')
        self.conf_filename = os.path.join(self.options['etc_prefix'], 'redis.conf')

        self.bin_dir = b_options.get('bin-directory')

    def install(self, update=False):
        installed = []
        installed += list(self.install_conda(update))
        installed += list(self.install_config())
        installed += list(self.install_supervisor(update))
        return installed

    def install_conda(self, update=False):
        script = conda.Recipe(
            self.buildout,
            self.name,
            {'pkgs': 'redis'})
        return script.install(update=update)

    def install_config(self):
        result = templ_config.render(**self.options)
        output = self.conf_filename
        conda.makedirs(os.path.dirname(output))
        conda.makedirs(os.path.join(self.options['var-prefix'], 'lib', 'redis'))

        try:
            os.remove(output)
        except OSError:
            pass

        with open(output, 'wt') as fp:
            fp.write(result)
        return [output]

    def install_supervisor(self, update=False):
        """
        install supervisor config for redis
        """
        script = supervisor.Recipe(
            self.buildout,
            self.name,
            {'deployment': self.deployment,
             'user': self.options.get('user'),
             'program': self.options.get('program'),
             'command': templ_cmd.render(config=self.conf_filename, env_path=self.env_path),
             'stopwaitsecs': '30',
             'killasgroup': 'true',
             })
        return script.install(update)

    def update(self):
       return self.install(update=True)

def uninstall(name, options):
    pass

